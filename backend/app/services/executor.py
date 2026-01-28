"""
Model execution service - calls OpenRouter API.
"""
import asyncio
import uuid
import json
import httpx
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import TaskRun, ModelOutput, MetricsSnapshot, MonitorTask, TaskKeyword, TaskModel, TenantConfig
from app.services.calculator import (
    calculate_sov,
    calculate_accuracy_score,
    analyze_sentiment,
    calculate_citation_rate,
    check_positioning_hit,
)

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_SITE_URL = "https://geo-monitor.example.com"
OPENROUTER_APP_NAME = "GEO Monitor"


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, requests_per_minute: int = 20):
        self.requests_per_minute = requests_per_minute
        self.requests = []
        self.lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request."""
        async with self.lock:
            now = time.time()
            # Remove requests older than 1 minute
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]
            
            if len(self.requests) >= self.requests_per_minute:
                # Calculate wait time
                oldest_request = min(self.requests)
                wait_time = 60 - (now - oldest_request)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    return await self.acquire()
            
            self.requests.append(now)


class CostTracker:
    """Track API costs and enforce limits."""
    
    def __init__(self, max_cost_per_request: float = 1.0, max_daily_cost: float = 100.0):
        self.max_cost_per_request = Decimal(str(max_cost_per_request))
        self.max_daily_cost = Decimal(str(max_daily_cost))
        self.daily_cost = Decimal("0")
        self.last_reset = datetime.utcnow().date()
        self.lock = asyncio.Lock()
    
    async def check_cost_limit(self, estimated_cost: Decimal) -> bool:
        """Check if the estimated cost is within limits."""
        async with self.lock:
            # Reset daily cost if it's a new day
            today = datetime.utcnow().date()
            if today > self.last_reset:
                self.daily_cost = Decimal("0")
                self.last_reset = today
            
            # Check per-request limit
            if estimated_cost > self.max_cost_per_request:
                return False
            
            # Check daily limit
            if self.daily_cost + estimated_cost > self.max_daily_cost:
                return False
            
            return True
    
    async def add_cost(self, actual_cost: Decimal):
        """Add actual cost to the daily total."""
        async with self.lock:
            self.daily_cost += actual_cost


class CircuitBreaker:
    """Circuit breaker pattern for API calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
        self.lock = asyncio.Lock()
    
    async def can_execute(self) -> bool:
        """Check if execution is allowed."""
        async with self.lock:
            if self.state == "closed":
                return True
            elif self.state == "open":
                if self.last_failure_time and \
                   (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout:
                    self.state = "half_open"
                    return True
                return False
            elif self.state == "half_open":
                return True
            return False
    
    async def record_success(self):
        """Record a successful execution."""
        async with self.lock:
            self.failure_count = 0
            self.state = "closed"
    
    async def record_failure(self):
        """Record a failed execution."""
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"


class ModelExecutor:
    """
    Enhanced executor for calling LLM models via OpenRouter.
    """
    
    def __init__(self, api_key: str, tenant_config: Optional[TenantConfig] = None):
        self.api_key = api_key
        self.tenant_config = tenant_config
        self.max_retries = settings.RATE_LIMIT_MAX_RETRIES
        self.base_delay = settings.RATE_LIMIT_BASE_DELAY
        self.rate_limiter = RateLimiter(settings.RATE_LIMIT_REQUESTS_PER_MINUTE)
        self.cost_tracker = CostTracker(
            settings.MAX_COST_PER_REQUEST,
            100.0  # Daily limit
        )
        self.circuit_breaker = CircuitBreaker()
        self.session_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_cost": Decimal("0"),
            "total_tokens": 0
        }
    
    async def execute(
        self,
        keyword: str,
        model_id: str,
        run_id: uuid.UUID,
        task_id: uuid.UUID,
        priority: int = 10,
    ) -> ModelOutput:
        """
        Execute a single model call for a keyword.
        
        Args:
            keyword: The keyword to query.
            model_id: The model to use (e.g., "openai/gpt-4o").
            run_id: The task run ID.
            task_id: The task ID.
            
        Returns:
            ModelOutput record.
        """
        # Build the prompt
        prompt = self._build_prompt(keyword)
        
        # Create output record
        output = ModelOutput(
            run_id=run_id,
            keyword=keyword,
            model_id=model_id,
            status="pending",
        )
        
        # Estimate cost before execution
        estimated_cost = self._estimate_cost(model_id, prompt)
        
        # Check cost limits
        if not await self.cost_tracker.check_cost_limit(estimated_cost):
            output.status = "failed"
            output.error_message = "Cost limit exceeded"
            return output
        
        # Check circuit breaker
        if not await self.circuit_breaker.can_execute():
            output.status = "failed"
            output.error_message = "Circuit breaker open - too many failures"
            return output
        
        self.session_stats["total_requests"] += 1
        
        # Execute with retry and rate limiting
        for attempt in range(self.max_retries):
            try:
                # Apply rate limiting
                await self.rate_limiter.acquire()
                
                # Call API
                response = await self._call_api(prompt, model_id)
                
                # Parse the response
                content = response["choices"][0]["message"]["content"]
                usage = response.get("usage", {})
                
                # Validate and parse JSON response
                try:
                    parsed_response = json.loads(content) if content else {}
                    if not self._validate_response(parsed_response):
                        raise ValueError("Invalid response format")
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON response")
                
                # Calculate actual cost
                actual_cost = self._calculate_cost(model_id, usage)
                await self.cost_tracker.add_cost(actual_cost)
                
                # Update output
                output.raw_response = parsed_response
                output.token_usage = usage.get("total_tokens", 0)
                output.cost_usd = actual_cost
                output.status = "completed"
                
                # Update stats
                self.session_stats["successful_requests"] += 1
                self.session_stats["total_cost"] += actual_cost
                self.session_stats["total_tokens"] += output.token_usage
                
                # Record success in circuit breaker
                await self.circuit_breaker.record_success()
                
                break
                
            except Exception as e:
                # Record failure in circuit breaker
                await self.circuit_breaker.record_failure()
                
                if attempt == self.max_retries - 1:
                    output.status = "failed"
                    output.error_message = str(e)
                    self.session_stats["failed_requests"] += 1
                else:
                    # Exponential backoff with jitter
                    delay = self.base_delay * (2 ** attempt) + (time.time() % 1)
                    await asyncio.sleep(delay)
        
        return output
    
    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate the structure of the model response."""
        if not isinstance(response, dict):
            return False
        
        brands = response.get("brands", [])
        if not isinstance(brands, list):
            return False
        
        for brand in brands:
            if not isinstance(brand, dict):
                return False
            
            # Check required fields
            if "name" not in brand or not isinstance(brand["name"], str):
                return False
            
            # Check optional fields
            sentiment = brand.get("sentiment")
            if sentiment and sentiment not in ["Positive", "Neutral", "Negative"]:
                return False
            
            accuracy_score = brand.get("accuracy_score")
            if accuracy_score and (not isinstance(accuracy_score, int) or not 1 <= accuracy_score <= 10):
                return False
        
        return True
    
    def _estimate_cost(self, model_id: str, prompt: str) -> Decimal:
        """Estimate the cost of an API call based on prompt length."""
        # Rough estimation: 4 characters per token
        estimated_input_tokens = len(prompt) // 4
        estimated_output_tokens = 500  # Conservative estimate
        
        usage = {
            "prompt_tokens": estimated_input_tokens,
            "completion_tokens": estimated_output_tokens
        }
        
        return self._calculate_cost(model_id, usage)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current session statistics."""
        stats = self.session_stats.copy()
        stats["total_cost"] = float(stats["total_cost"])
        stats["success_rate"] = (
            stats["successful_requests"] / max(stats["total_requests"], 1) * 100
        )
        stats["circuit_breaker_state"] = self.circuit_breaker.state
        stats["daily_cost"] = float(self.cost_tracker.daily_cost)
        return stats
    
    def _build_prompt(self, keyword: str) -> str:
        """
        Build the prompt for brand monitoring.
        
        Args:
            keyword: The keyword to query.
            
        Returns:
            The formatted prompt.
        """
        return f"""You are a Brand Auditor analyzing AI model responses about brands and products.

User Query: "{keyword}"

Please provide a comprehensive analysis of brands mentioned in response to this query.

Output Requirements:
1. List ALL brands/companies mentioned in the response
2. For each brand, provide:
   - Sentiment analysis (Positive/Neutral/Negative)
   - Whether a URL/link is provided
   - Positioning keywords present (enterprise, reliable, fast, secure, etc.)
   - Accuracy score (1-10) based on factual correctness

IMPORTANT: Respond ONLY with valid JSON in the exact format below:

{{
  "brands": [
    {{
      "name": "Brand Name",
      "sentiment": "Positive",
      "has_link": true,
      "positioning_keywords_hit": ["enterprise", "reliable"],
      "accuracy_score": 8,
      "context": "Brief context about how the brand was mentioned"
    }}
  ],
  "total_brands_mentioned": 1,
  "query_category": "software",
  "response_quality": "high"
}}

Do not include any text outside the JSON response."""
    
    async def _call_api(
        self,
        prompt: str,
        model_id: str,
    ) -> Dict[str, Any]:
        """
        Call the OpenRouter API.
        
        Args:
            prompt: The prompt to send.
            model_id: The model to use.
            
        Returns:
            API response as a dictionary.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_SITE_URL,
            "X-Title": OPENROUTER_APP_NAME,
        }
        
        body = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": settings.MAX_TOKEN_PER_REQUEST,
            "temperature": 0.1,
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=body,
            )
            
            response.raise_for_status()
            return response.json()
    
    def _calculate_cost(self, model_id: str, usage: Dict) -> Decimal:
        """
        Calculate the cost of an API call.
        
        This is a simplified version - real implementation would use
        current model pricing from OpenRouter.
        
        Args:
            model_id: The model used.
            usage: Token usage from the API response.
            
        Returns:
            Cost in USD.
        """
        # Simplified pricing (per 1M tokens)
        pricing = {
            "openai/gpt-4o": {"input": 5.0, "output": 15.0},
            "openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "anthropic/claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
            "anthropic/claude-3-opus": {"input": 15.0, "output": 75.0},
            "google/gemini-1.5-pro": {"input": 7.0, "output": 21.0},
        }
        
        model_pricing = pricing.get(model_id, {"input": 5.0, "output": 15.0})
        
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)
        
        cost = (
            input_tokens / 1_000_000 * model_pricing["input"] +
            output_tokens / 1_000_000 * model_pricing["output"]
        )
        
        return Decimal(str(cost))


async def execute_task_run(run_id: uuid.UUID):
    """
    Execute all model calls for a task run with enhanced error handling and monitoring.
    
    Args:
        run_id: The ID of the task run to execute.
    """
    from app.models.database import async_session_factory
    import logging
    
    logger = logging.getLogger(__name__)
    
    async with async_session_factory() as session:
        try:
            # Get the task run
            result = await session.execute(
                select(TaskRun).where(TaskRun.id == run_id)
            )
            task_run = result.scalar_one_or_none()
            
            if not task_run:
                logger.error(f"Task run {run_id} not found")
                return
            
            # Get the task
            result = await session.execute(
                select(MonitorTask).where(MonitorTask.id == task_run.task_id)
            )
            task = result.scalar_one_or_none()
            
            if not task or not task.is_active:
                logger.error(f"Task {task_run.task_id} not found or inactive")
                task_run.status = "failed"
                task_run.error_message = "Task not found or inactive"
                await session.commit()
                return
            
            # Get tenant configuration
            result = await session.execute(
                select(TenantConfig).where(TenantConfig.tenant_id == task.tenant_id)
            )
            tenant_config = result.scalar_one_or_none()
            
            # Determine API key to use
            api_key = settings.OPENROUTER_API_KEY
            if tenant_config and tenant_config.openrouter_api_key_encrypted:
                # In production, decrypt the tenant's API key
                api_key = tenant_config.openrouter_api_key_encrypted
            
            # Update run status
            task_run.status = "running"
            task_run.started_at = datetime.utcnow()
            await session.commit()
            
            logger.info(f"Starting execution for task run {run_id}")
            
            # Get task keywords
            result = await session.execute(
                select(TaskKeyword.keyword).where(TaskKeyword.task_id == task.id)
            )
            keywords = [row[0] for row in result.all()]
            
            # Get task models (sorted by priority)
            result = await session.execute(
                select(TaskModel.model_id, TaskModel.priority)
                .where(TaskModel.task_id == task.id)
                .order_by(TaskModel.priority)
            )
            models_with_priority = result.all()
            
            if not keywords or not models_with_priority:
                task_run.status = "failed"
                task_run.error_message = "No keywords or models configured"
                await session.commit()
                return
            
            # Initialize enhanced executor
            executor = ModelExecutor(api_key, tenant_config)
            
            # Execute for each keyword and model combination
            total_tokens = 0
            total_cost = Decimal("0")
            successful_executions = 0
            failed_executions = 0
            
            for keyword in keywords:
                for model_id, priority in models_with_priority:
                    try:
                        logger.info(f"Executing {keyword} on {model_id} (priority: {priority})")
                        
                        output = await executor.execute(
                            keyword=keyword,
                            model_id=model_id,
                            run_id=run_id,
                            task_id=task.id,
                            priority=priority,
                        )
                        
                        session.add(output)
                        total_tokens += output.token_usage
                        total_cost += output.cost_usd
                        
                        if output.status == "completed":
                            successful_executions += 1
                            
                            # Create metrics snapshot if successful
                            if output.raw_response:
                                try:
                                    metrics = await calculate_metrics(
                                        output.raw_response,
                                        keyword,
                                        model_id,
                                        run_id,
                                    )
                                    session.add(metrics)
                                except Exception as metrics_error:
                                    logger.error(f"Error calculating metrics for {keyword} on {model_id}: {metrics_error}")
                        else:
                            failed_executions += 1
                            logger.warning(f"Failed execution for {keyword} on {model_id}: {output.error_message}")
                        
                        # Commit after each execution to avoid losing progress
                        await session.commit()
                        
                    except Exception as e:
                        failed_executions += 1
                        logger.error(f"Error executing {keyword} on {model_id}: {e}")
                        
                        # Create failed output record
                        failed_output = ModelOutput(
                            run_id=run_id,
                            keyword=keyword,
                            model_id=model_id,
                            status="failed",
                            error_message=str(e)
                        )
                        session.add(failed_output)
                        await session.commit()
            
            # Update run with totals and final status
            task_run.token_usage = total_tokens
            task_run.cost_usd = total_cost
            task_run.completed_at = datetime.utcnow()
            
            # Determine final status
            if successful_executions > 0:
                if failed_executions == 0:
                    task_run.status = "completed"
                else:
                    task_run.status = "partial"
                    task_run.error_message = f"{failed_executions} out of {successful_executions + failed_executions} executions failed"
            else:
                task_run.status = "failed"
                task_run.error_message = "All executions failed"
            
            await session.commit()
            
            # Log execution summary
            logger.info(f"Task run {run_id} completed: {successful_executions} successful, {failed_executions} failed, "
                       f"${total_cost} cost, {total_tokens} tokens")
            
            # Log executor statistics
            stats = executor.session_stats
            logger.info(f"Executor stats: {stats['successful_requests']}/{stats['total_requests']} successful, "
                       f"${stats['total_cost']} total cost")
            
        except Exception as e:
            logger.error(f"Critical error in execute_task_run for {run_id}: {e}")
            
            # Update task run with critical error
            try:
                task_run.status = "failed"
                task_run.error_message = f"Critical error: {str(e)}"
                task_run.completed_at = datetime.utcnow()
                await session.commit()
            except Exception as commit_error:
                logger.error(f"Failed to update task run status: {commit_error}")


async def calculate_metrics(
    response_data: Dict[str, Any],
    keyword: str,
    model_id: str,
    run_id: uuid.UUID,
) -> MetricsSnapshot:
    """
    Calculate enhanced metrics from model response.
    
    Args:
        response_data: Parsed JSON response from the model.
        keyword: The keyword queried.
        model_id: The model used.
        run_id: The task run ID.
        
    Returns:
        MetricsSnapshot record.
    """
    brands_data = response_data.get("brands", [])
    total_brands = response_data.get("total_brands_mentioned", len(brands_data))
    
    # Extract brand information
    brands_mentioned = [b.get("name") for b in brands_data if b.get("name")]
    
    # Calculate SOV (Share of Voice)
    # For single model execution, SOV is percentage of total brands mentioned
    sov_score = Decimal(str(len(brands_mentioned) / max(total_brands, 1) * 100)) if brands_mentioned else Decimal("0")
    
    # Calculate average accuracy score
    accuracy_scores = [
        b.get("accuracy_score", 5) for b in brands_data 
        if isinstance(b.get("accuracy_score"), int) and 1 <= b.get("accuracy_score") <= 10
    ]
    accuracy_score = int(sum(accuracy_scores) / len(accuracy_scores)) if accuracy_scores else None
    
    # Calculate sentiment score (-1 to 1)
    sentiment_mapping = {"Positive": 1, "Neutral": 0, "Negative": -1}
    sentiments = [
        sentiment_mapping.get(b.get("sentiment"), 0)
        for b in brands_data
        if b.get("sentiment") in sentiment_mapping
    ]
    sentiment_score = Decimal(str(sum(sentiments) / len(sentiments))) if sentiments else Decimal("0")
    
    # Calculate citation rate (percentage of brands with links)
    links_count = sum(1 for b in brands_data if b.get("has_link", False))
    citation_rate = Decimal(str(links_count / len(brands_mentioned) * 100)) if brands_mentioned else Decimal("0")
    
    # Check for positioning keyword hits
    positioning_hit = any(
        b.get("positioning_keywords_hit") and len(b.get("positioning_keywords_hit", [])) > 0
        for b in brands_data
    )
    
    # Collect all positioning keywords mentioned
    all_positioning_keywords = []
    for b in brands_data:
        keywords_hit = b.get("positioning_keywords_hit", [])
        if isinstance(keywords_hit, list):
            all_positioning_keywords.extend(keywords_hit)
    
    return MetricsSnapshot(
        run_id=run_id,
        model_id=model_id,
        keyword=keyword,
        sov_score=sov_score,
        accuracy_score=accuracy_score,
        sentiment_score=sentiment_score,
        citation_rate=citation_rate,
        positioning_hit=positioning_hit,
        brands_mentioned={
            "brands": brands_mentioned,
            "total_count": len(brands_mentioned),
            "positioning_keywords": list(set(all_positioning_keywords)),
            "response_quality": response_data.get("response_quality", "unknown"),
            "query_category": response_data.get("query_category", "unknown")
        },
        analysis_details=response_data,
    )


def get_executor_stats() -> Dict[str, Any]:
    """
    Get global executor statistics (placeholder for monitoring).
    
    Returns:
        Dictionary with executor statistics.
    """
    return {
        "active_executors": 0,
        "total_requests_today": 0,
        "total_cost_today": 0.0,
        "average_response_time": 0.0,
        "success_rate": 0.0,
        "circuit_breaker_status": "closed"
    }
