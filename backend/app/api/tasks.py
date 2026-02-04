"""
Task management API routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
import uuid

from app.models.database import get_db
from app.models.entities import MonitorTask, TaskModel, TaskKeyword, TaskRun
from app.models.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskTriggerResponse,
)
from app.middleware.auth import get_current_user, require_minimum_role
from app.models.user_entities import User, UserTenant
from app.core.exceptions import NotFoundException, ValidationException
from croniter import croniter
import re
from datetime import datetime
from app.services.scheduler import trigger_task_run

router = APIRouter(tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all monitor tasks for the current tenant."""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    # Build query
    query = select(MonitorTask).where(MonitorTask.tenant_id == tenant_id)
    
    if is_active is not None:
        query = query.where(MonitorTask.is_active == is_active)
    
    if search:
        query = query.where(MonitorTask.name.ilike(f"%{search}%"))
    
    # Get total count
    count_query = select(uuid.func.count()).select_from(query.subquery())
    total_result = db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.offset((page - 1) * limit).limit(limit).order_by(MonitorTask.created_at.desc())
    result = db.execute(query)
    tasks = result.scalars().all()
    
    # Build response
    data = []
    for task in tasks:
        # Get related models and keywords
        models_result = db.execute(
            select(TaskModel.model_id).where(TaskModel.task_id == task.id)
        )
        keywords_result = db.execute(
            select(TaskKeyword.keyword).where(TaskKeyword.task_id == task.id)
        )
        
        # Get last run info
        last_run_result = db.execute(
            select(TaskRun)
            .where(TaskRun.task_id == task.id)
            .order_by(TaskRun.created_at.desc())
            .limit(1)
        )
        last_run = last_run_result.scalar_one_or_none()
        
        data.append(TaskResponse(
            id=task.id,
            tenant_id=task.tenant_id,
            name=task.name,
            description=task.description,
            schedule_cron=task.schedule_cron,
            is_active=task.is_active,
            prompt_template_id=task.prompt_template_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            models=[m.model_id for m in models_result.scalars().all()],
            keywords=[k.keyword for k in keywords_result.scalars().all()],
            last_run_status=last_run.status if last_run else None,
            last_run_time=last_run.started_at if last_run else None,
        ))
    
    return TaskListResponse(data=data, total=total, page=page, limit=limit)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db),
):
    """Get a specific task by ID."""
    # Check read permission
    if not check_permission(membership, Permission.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view task"
        )
    result = db.execute(
        select(MonitorTask)
        .options(
            selectinload(MonitorTask.models),
            selectinload(MonitorTask.keywords),
        )
        .where(MonitorTask.id == task_id, MonitorTask.tenant_id == tenant_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    # Get last run info
    last_run_result = db.execute(
        select(TaskRun)
        .where(TaskRun.task_id == task.id)
        .order_by(TaskRun.created_at.desc())
        .limit(1)
    )
    last_run = last_run_result.scalar_one_or_none()
    
    return TaskResponse(
        id=task.id,
        tenant_id=task.tenant_id,
        name=task.name,
        description=task.description,
        schedule_cron=task.schedule_cron,
        is_active=task.is_active,
        prompt_template_id=task.prompt_template_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        models=[m.model_id for m in task.models],
        keywords=[k.keyword for k in task.keywords],
        last_run_status=last_run.status if last_run else None,
        last_run_time=last_run.started_at if last_run else None,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db),
):
    """Create a new monitor task."""
    # Check write permission
    if not check_permission(membership, Permission.WRITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create tasks"
        )
    
    # Validate cron expression
    if not _validate_cron_expression(task_data.schedule_cron):
        raise ValidationException("Invalid cron expression")
    
    # Validate models
    if not _validate_models(task_data.models):
        raise ValidationException("Invalid model IDs provided")
    
    # Validate keywords
    if not _validate_keywords(task_data.keywords):
        raise ValidationException("Invalid keywords provided")
    # Create task
    task = MonitorTask(
        tenant_id=tenant_id,
        name=task_data.name,
        description=task_data.description,
        schedule_cron=task_data.schedule_cron,
        prompt_template_id=task_data.prompt_template_id,
    )
    db.add(task)
    db.flush()
    
    # Add models
    for model_id in task_data.models:
        db.add(TaskModel(task_id=task.id, model_id=model_id))
    
    # Add keywords
    for keyword in task_data.keywords:
        db.add(TaskKeyword(task_id=task.id, keyword=keyword))
    
    db.commit()
    db.refresh(task)
    
    return TaskResponse(
        id=task.id,
        tenant_id=task.tenant_id,
        name=task.name,
        description=task.description,
        schedule_cron=task.schedule_cron,
        is_active=task.is_active,
        prompt_template_id=task.prompt_template_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        models=task_data.models,
        keywords=task_data.keywords,
    )


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: uuid.UUID,
    task_data: TaskUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db),
):
    """Update an existing task."""
    # Check write permission
    if not check_permission(membership, Permission.WRITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update tasks"
        )
    
    # Validate cron expression if provided
    if task_data.schedule_cron and not _validate_cron_expression(task_data.schedule_cron):
        raise ValidationException("Invalid cron expression")
    
    # Validate models if provided
    if task_data.models and not _validate_models(task_data.models):
        raise ValidationException("Invalid model IDs provided")
    
    # Validate keywords if provided
    if task_data.keywords and not _validate_keywords(task_data.keywords):
        raise ValidationException("Invalid keywords provided")
    # Get task
    result = db.execute(
        select(MonitorTask)
        .where(MonitorTask.id == task_id, MonitorTask.tenant_id == tenant_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    # Update fields
    if task_data.name is not None:
        task.name = task_data.name
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.schedule_cron is not None:
        task.schedule_cron = task_data.schedule_cron
    if task_data.is_active is not None:
        task.is_active = task_data.is_active
    if task_data.prompt_template_id is not None:
        task.prompt_template_id = task_data.prompt_template_id
    
    # Update models if provided
    if task_data.models is not None:
        db.execute(
            delete(TaskModel).where(TaskModel.task_id == task_id)
        )
        for model_id in task_data.models:
            db.add(TaskModel(task_id=task.id, model_id=model_id))
    
    # Update keywords if provided
    if task_data.keywords is not None:
        db.execute(
            delete(TaskKeyword).where(TaskKeyword.task_id == task_id)
        )
        for keyword in task_data.keywords:
            db.add(TaskKeyword(task_id=task.id, keyword=keyword))
    
    db.commit()
    db.refresh(task)
    
    # Get updated models and keywords
    models_result = db.execute(
        select(TaskModel.model_id).where(TaskModel.task_id == task.id)
    )
    keywords_result = db.execute(
        select(TaskKeyword.keyword).where(TaskKeyword.task_id == task.id)
    )
    
    return TaskResponse(
        id=task.id,
        tenant_id=task.tenant_id,
        name=task.name,
        description=task.description,
        schedule_cron=task.schedule_cron,
        is_active=task.is_active,
        prompt_template_id=task.prompt_template_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
        models=[m.model_id for m in models_result.scalars().all()],
        keywords=[k.keyword for k in keywords_result.scalars().all()],
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db),
):
    """Delete a task and all associated data."""
    # Check delete permission
    if not check_permission(membership, Permission.DELETE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete tasks"
        )
    result = db.execute(
        select(MonitorTask)
        .where(MonitorTask.id == task_id, MonitorTask.tenant_id == tenant_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    db.delete(task)
    db.commit()


@router.post("/{task_id}/trigger", response_model=TaskTriggerResponse)
def trigger_task(
    task_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db),
):
    """Manually trigger a task execution."""
    # Check write permission
    if not check_permission(membership, Permission.WRITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to trigger tasks"
        )
    result = db.execute(
        select(MonitorTask)
        .where(MonitorTask.id == task_id, MonitorTask.tenant_id == tenant_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    # Create a new task run
    task_run = TaskRun(
        task_id=task.id,
        status="pending",
    )
    db.add(task_run)
    db.commit()
    db.refresh(task_run)
    
    # Trigger async execution
    import asyncio
    asyncio.create_task(trigger_task_run(task_run.id))
    
    return TaskTriggerResponse(run_id=task_run.id, status="pending")


# ============================================================================
# Validation Functions
# ============================================================================

def _validate_cron_expression(cron_expr: str) -> bool:
    """Validate cron expression format."""
    try:
        croniter(cron_expr)
        return True
    except (ValueError, TypeError):
        return False


def _validate_models(models: list[str]) -> bool:
    """Validate model IDs."""
    if not models:
        return False
    
    # Define supported model patterns
    supported_patterns = [
        r'^openai/gpt-.*',
        r'^anthropic/claude-.*',
        r'^google/gemini-.*',
        r'^meta-llama/.*',
        r'^mistralai/.*',
        r'^cohere/.*',
    ]
    
    for model_id in models:
        if not isinstance(model_id, str) or not model_id.strip():
            return False
        
        # Check if model matches any supported pattern
        if not any(re.match(pattern, model_id) for pattern in supported_patterns):
            return False
    
    return True


def _validate_keywords(keywords: list[str]) -> bool:
    """Validate keywords."""
    if not keywords:
        return False
    
    for keyword in keywords:
        if not isinstance(keyword, str) or not keyword.strip():
            return False
        
        # Check keyword length
        if len(keyword.strip()) < 2 or len(keyword.strip()) > 500:
            return False
        
        # Check for invalid characters (basic validation)
        if re.search(r'[<>"\\]', keyword):
            return False
    
    return True


@router.get("/models", response_model=dict)
def get_supported_models(
    membership: TenantMember = Depends(get_current_user_membership)
):
    """Get list of supported AI models."""
    # Check read permission
    if not check_permission(membership, Permission.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view models"
        )
    
    models = {
        "openai": [
            {"id": "openai/gpt-4o", "name": "GPT-4o", "provider": "OpenAI"},
            {"id": "openai/gpt-4o-mini", "name": "GPT-4o Mini", "provider": "OpenAI"},
            {"id": "openai/gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "OpenAI"},
            {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "provider": "OpenAI"},
        ],
        "anthropic": [
            {"id": "anthropic/claude-3.5-sonnet", "name": "Claude 3.5 Sonnet", "provider": "Anthropic"},
            {"id": "anthropic/claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic"},
            {"id": "anthropic/claude-3-haiku", "name": "Claude 3 Haiku", "provider": "Anthropic"},
        ],
        "google": [
            {"id": "google/gemini-1.5-pro", "name": "Gemini 1.5 Pro", "provider": "Google"},
            {"id": "google/gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "Google"},
        ],
        "meta": [
            {"id": "meta-llama/llama-3.1-70b-instruct", "name": "Llama 3.1 70B", "provider": "Meta"},
            {"id": "meta-llama/llama-3.1-8b-instruct", "name": "Llama 3.1 8B", "provider": "Meta"},
        ],
        "mistral": [
            {"id": "mistralai/mistral-large", "name": "Mistral Large", "provider": "Mistral AI"},
            {"id": "mistralai/mistral-medium", "name": "Mistral Medium", "provider": "Mistral AI"},
        ],
        "cohere": [
            {"id": "cohere/command-r-plus", "name": "Command R+", "provider": "Cohere"},
            {"id": "cohere/command-r", "name": "Command R", "provider": "Cohere"},
        ]
    }
    
    return {"models": models}


@router.get("/validate-cron", response_model=dict)
def validate_cron(
    expression: str = Query(..., description="Cron expression to validate"),
    membership: TenantMember = Depends(get_current_user_membership)
):
    """Validate a cron expression and return next execution times."""
    # Check read permission
    if not check_permission(membership, Permission.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    try:
        cron = croniter(expression)
        next_runs = []
        
        # Get next 5 execution times
        for _ in range(5):
            next_runs.append(cron.get_next(datetime).isoformat())
        
        return {
            "valid": True,
            "next_runs": next_runs,
            "description": _describe_cron_expression(expression)
        }
    except (ValueError, TypeError) as e:
        return {
            "valid": False,
            "error": str(e),
            "next_runs": [],
            "description": None
        }


def _describe_cron_expression(cron_expr: str) -> str:
    """Generate human-readable description of cron expression."""
    common_expressions = {
        "0 0 * * *": "Daily at midnight",
        "0 9 * * *": "Daily at 9:00 AM",
        "0 */6 * * *": "Every 6 hours",
        "0 0 * * 0": "Weekly on Sunday at midnight",
        "0 0 1 * *": "Monthly on the 1st at midnight",
        "*/30 * * * *": "Every 30 minutes",
        "0 */2 * * *": "Every 2 hours",
        "0 8-18 * * 1-5": "Hourly from 8 AM to 6 PM, Monday to Friday"
    }
    
    return common_expressions.get(cron_expr, "Custom schedule")


@router.get("/{task_id}/runs", response_model=dict)
def get_task_runs(
    task_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status: Optional[str] = Query(default=None, description="Filter by status"),
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db)
):
    """Get execution history for a specific task."""
    # Check read permission
    if not check_permission(membership, Permission.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view task runs"
        )
    
    # Verify task exists and belongs to tenant
    task_result = db.execute(
        select(MonitorTask).where(
            MonitorTask.id == task_id,
            MonitorTask.tenant_id == tenant_id
        )
    )
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    # Build query for task runs
    query = select(TaskRun).where(TaskRun.task_id == task_id)
    
    if status:
        query = query.where(TaskRun.status == status)
    
    # Get total count
    count_result = db.execute(
        select(uuid.func.count()).select_from(query.subquery())
    )
    total = count_result.scalar() or 0
    
    # Get paginated results
    query = query.offset((page - 1) * limit).limit(limit).order_by(TaskRun.created_at.desc())
    result = db.execute(query)
    runs = result.scalars().all()
    
    return {
        "data": [
            {
                "id": run.id,
                "status": run.status,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                "error_message": run.error_message,
                "token_usage": run.token_usage,
                "cost_usd": float(run.cost_usd) if run.cost_usd else 0.0,
                "created_at": run.created_at.isoformat()
            }
            for run in runs
        ],
        "total": total,
        "page": page,
        "limit": limit
    }
