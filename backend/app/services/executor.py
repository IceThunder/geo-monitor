"""
Model execution service - calls OpenRouter API.
"""
import asyncio
import uuid
import json
import httpx
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from app.core.config import settings
from app.models.entities import TaskRun, ModelOutput, MetricsSnapshot, MonitorTask, TaskKeyword
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


class ModelExecutor:
    """
    Executor for calling LLM models via OpenRouter.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.max_retries = settings.RATE_LIMIT_MAX_RETRIES
        self.base_delay = settings.RATE_LIMIT_BASE_DELAY
        self.max_cost = settings.MAX_COST_PER_REQUEST
    
    async def execute(
        self,
        keyword: str,
        model_id: str,
        run_id: uuid.UUID,
        task_id: uuid.UUID,
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
        
        # Execute with retry
        for attempt in range(self.max_retries):
            try:
                response = await self._call_api(prompt, model_id)
                
                # Parse the response
                content = response["choices"][0]["message"]["content"]
                usage = response.get("usage", {})
                
                # Update output
                output.raw_response = json.loads(content) if content else {}
                output.token_usage = usage.get("total_tokens", 0)
                # Calculate cost (simplified - real implementation would use model pricing)
                output.cost_usd = self._calculate_cost(model_id, usage)
                output.status = "completed"
                break
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    output.status = "failed"
                    output.error_message = str(e)
                else:
                    delay = self.base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        return output
    
    def _build_prompt(self, keyword: str) -> str:
        """
        Build the prompt for brand monitoring.
        
        Args:
            keyword: The keyword to query.
            
        Returns:
            The formatted prompt.
        """
        return f"""You are a Brand Auditor. Analyze the following user query about brands.

User Query: "{keyword}"

Output Requirements:
1. List all brands mentioned in the response.
2. For each brand, identify the sentiment (Positive/Neutral/Negative).
3. Check if a URL link is provided for the brand.
4. Identify if positioning keywords (high-quality, enterprise, reliable) are present.

Response Format (JSON only):
{{
  "brands": [
    {{
      "name": "BrandA",
      "sentiment": "Positive",
      "has_link": true,
      "positioning_keywords_hit": ["fast", "reliable"],
      "accuracy_score": 9
    }}
  ]
}}"""
    
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
    Execute all model calls for a task run.
    
    Args:
        run_id: The ID of the task run to execute.
    """
    from app.models.database import async_session_factory
    
    async with async_session_factory() as session:
        # Get the task run
        result = await session.execute(
            select(TaskRun).where(TaskRun.id == run_id)
        )
        task_run = result.scalar_one_or_none()
        
        if not task_run:
            print(f"Task run {run_id} not found")
            return
        
        # Get the task
        result = await session.execute(
            select(MonitorTask).where(MonitorTask.id == task_run.task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task or not task.is_active:
            print(f"Task {task_run.task_id} not found or inactive")
            task_run.status = "failed"
            task_run.error_message = "Task not found or inactive"
            await session.commit()
            return
        
        # Update run status
        task_run.status = "running"
        task_run.started_at = datetime.utcnow()
        await session.commit()
        
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
        models = [row[0] for row in result.all()]
        
        # Initialize executor
        executor = ModelExecutor(settings.OPENROUTER_API_KEY)
        
        # Execute for each keyword and model combination
        total_tokens = 0
        total_cost = Decimal("0")
        
        for keyword in keywords:
            for model_id in models:
                try:
                    output = await executor.execute(
                        keyword=keyword,
                        model_id=model_id,
                        run_id=run_id,
                        task_id=task.id,
                    )
                    session.add(output)
                    total_tokens += output.token_usage
                    total_cost += output.cost_usd
                    
                    # Create metrics snapshot if successful
                    if output.status == "completed" and output.raw_response:
                        metrics = await calculate_metrics(
                            output.raw_response,
                            keyword,
                            model_id,
                            run_id,
                        )
                        session.add(metrics)
                    
                except Exception as e:
                    print(f"Error executing {keyword} on {model_id}: {e}")
        
        # Update run with totals
        task_run.token_usage = total_tokens
        task_run.cost_usd = total_cost
        task_run.status = "completed"
        task_run.completed_at = datetime.utcnow()
        
        await session.commit()


async def calculate_metrics(
    response_data: Dict[str, Any],
    keyword: str,
    model_id: str,
    run_id: uuid.UUID,
) -> MetricsSnapshot:
    """
    Calculate metrics from model response.
    
    Args:
        response_data: Parsed JSON response from the model.
        keyword: The keyword queried.
        model_id: The model used.
        run_id: The task run ID.
        
    Returns:
        MetricsSnapshot record.
    """
    brands_data = response_data.get("brands", [])
    
    # Extract brand information
    brands_mentioned = [b.get("name") for b in brands_data if b.get("name")]
    
    # Calculate metrics
    sov_score = calculate_sov(brands_mentioned, 1)  # Single model
    
    accuracy_scores = [
        b.get("accuracy_score", 5) for b in brands_data 
        if b.get("accuracy_score")
    ]
    accuracy_score = int(sum(accuracy_scores) / len(accuracy_scores)) if accuracy_scores else None
    
    sentiments = [
        {"Positive": 1, "Neutral": 0, "Negative": -1}.get(b.get("sentiment"), 0)
        for b in brands_data
        if b.get("sentiment")
    ]
    sentiment_score = sum(sentiments) / len(sentiments) if sentiments else 0
    
    links_count = sum(1 for b in brands_data if b.get("has_link"))
    citation_rate = calculate_citation_rate(links_count, len(brands_mentioned)) if brands_mentioned else 0
    
    positioning_hit = any(
        b.get("positioning_keywords_hit") 
        for b in brands_data 
        if b.get("positioning_keywords_hit")
    )
    
    return MetricsSnapshot(
        run_id=run_id,
        model_id=model_id,
        keyword=keyword,
        sov_score=sov_score,
        accuracy_score=accuracy_score,
        sentiment_score=sentiment_score,
        citation_rate=citation_rate,
        positioning_hit=positioning_hit,
        brands_mentioned=brands_mentioned,
        analysis_details=response_data,
    )
