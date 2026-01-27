"""
Task management API routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
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
from app.core.security import get_current_tenant_id
from app.core.exceptions import NotFoundException, ValidationException
from app.services.scheduler import trigger_task_run

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """List all monitor tasks for the current tenant."""
    # Build query
    query = select(MonitorTask).where(MonitorTask.tenant_id == tenant_id)
    
    if is_active is not None:
        query = query.where(MonitorTask.is_active == is_active)
    
    if search:
        query = query.where(MonitorTask.name.ilike(f"%{search}%"))
    
    # Get total count
    count_query = select(uuid.func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.offset((page - 1) * limit).limit(limit).order_by(MonitorTask.created_at.desc())
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    # Build response
    data = []
    for task in tasks:
        # Get related models and keywords
        models_result = await db.execute(
            select(TaskModel.model_id).where(TaskModel.task_id == task.id)
        )
        keywords_result = await db.execute(
            select(TaskKeyword.keyword).where(TaskKeyword.task_id == task.id)
        )
        
        # Get last run info
        last_run_result = await db.execute(
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
async def get_task(
    task_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific task by ID."""
    result = await db.execute(
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
    last_run_result = await db.execute(
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
async def create_task(
    task_data: TaskCreate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new monitor task."""
    # Create task
    task = MonitorTask(
        tenant_id=tenant_id,
        name=task_data.name,
        description=task_data.description,
        schedule_cron=task_data.schedule_cron,
        prompt_template_id=task_data.prompt_template_id,
    )
    db.add(task)
    await db.flush()
    
    # Add models
    for model_id in task_data.models:
        db.add(TaskModel(task_id=task.id, model_id=model_id))
    
    # Add keywords
    for keyword in task_data.keywords:
        db.add(TaskKeyword(task_id=task.id, keyword=keyword))
    
    await db.commit()
    await db.refresh(task)
    
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
async def update_task(
    task_id: uuid.UUID,
    task_data: TaskUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing task."""
    # Get task
    result = await db.execute(
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
        await db.execute(
            delete(TaskModel).where(TaskModel.task_id == task_id)
        )
        for model_id in task_data.models:
            db.add(TaskModel(task_id=task.id, model_id=model_id))
    
    # Update keywords if provided
    if task_data.keywords is not None:
        await db.execute(
            delete(TaskKeyword).where(TaskKeyword.task_id == task_id)
        )
        for keyword in task_data.keywords:
            db.add(TaskKeyword(task_id=task.id, keyword=keyword))
    
    await db.commit()
    await db.refresh(task)
    
    # Get updated models and keywords
    models_result = await db.execute(
        select(TaskModel.model_id).where(TaskModel.task_id == task.id)
    )
    keywords_result = await db.execute(
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
async def delete_task(
    task_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task and all associated data."""
    result = await db.execute(
        select(MonitorTask)
        .where(MonitorTask.id == task_id, MonitorTask.tenant_id == tenant_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("Task", str(task_id))
    
    await db.delete(task)
    await db.commit()


@router.post("/{task_id}/trigger", response_model=TaskTriggerResponse)
async def trigger_task(
    task_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a task execution."""
    result = await db.execute(
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
    await db.commit()
    await db.refresh(task_run)
    
    # Trigger async execution
    await trigger_task_run(task_run.id)
    
    return TaskTriggerResponse(run_id=task_run.id, status="pending")
