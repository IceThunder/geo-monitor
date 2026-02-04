"""
受保护的任务管理API路由（使用JWT认证）
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, delete, update, func
from sqlalchemy.orm import selectinload
import uuid

from app.core.database import get_db
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

router = APIRouter(prefix="/tasks", tags=["Protected Tasks"])


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前租户的所有监控任务列表"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    # 构建查询
    query = select(MonitorTask).where(MonitorTask.tenant_id == tenant_id)
    
    if is_active is not None:
        query = query.where(MonitorTask.is_active == is_active)
    
    if search:
        query = query.where(MonitorTask.name.ilike(f"%{search}%"))
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 获取分页结果
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    query = query.options(
        selectinload(MonitorTask.models),
        selectinload(MonitorTask.keywords)
    )
    
    result = db.execute(query)
    tasks = result.scalars().all()
    
    return TaskListResponse(
        items=[TaskResponse.from_orm(task) for task in tasks],
        total=total,
        page=page,
        limit=limit,
        pages=(total + limit - 1) // limit
    )


@router.post("", response_model=TaskResponse)
@require_minimum_role("member")
async def create_task(
    task_data: TaskCreate,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建新的监控任务"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    # 验证cron表达式
    if not _validate_cron_expression(task_data.schedule):
        raise ValidationException("无效的cron表达式")
    
    # 验证模型
    if not _validate_models(task_data.models):
        raise ValidationException("无效的模型配置")
    
    # 创建任务
    task = MonitorTask(
        tenant_id=tenant_id,
        name=task_data.name,
        description=task_data.description,
        schedule=task_data.schedule,
        target_brand=task_data.target_brand,
        positioning_keywords=task_data.positioning_keywords or [],
        is_active=task_data.is_active,
        created_by=str(user.id)
    )
    
    db.add(task)
    db.flush()  # 获取任务ID
    
    # 添加模型
    for model_data in task_data.models:
        task_model = TaskModel(
            task_id=task.id,
            model_name=model_data.name,
            provider=model_data.provider,
            config=model_data.config or {}
        )
        db.add(task_model)
    
    # 添加关键词
    for keyword in task_data.keywords:
        task_keyword = TaskKeyword(
            task_id=task.id,
            keyword=keyword
        )
        db.add(task_keyword)
    
    db.commit()
    db.refresh(task)
    
    return TaskResponse.from_orm(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取指定任务的详细信息"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    query = select(MonitorTask).where(
        MonitorTask.id == task_id,
        MonitorTask.tenant_id == tenant_id
    ).options(
        selectinload(MonitorTask.models),
        selectinload(MonitorTask.keywords)
    )
    
    result = db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("任务不存在")
    
    return TaskResponse.from_orm(task)


@router.put("/{task_id}", response_model=TaskResponse)
@require_minimum_role("member")
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新指定任务"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    # 获取任务
    query = select(MonitorTask).where(
        MonitorTask.id == task_id,
        MonitorTask.tenant_id == tenant_id
    )
    result = db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("任务不存在")
    
    # 验证cron表达式（如果提供）
    if task_data.schedule and not _validate_cron_expression(task_data.schedule):
        raise ValidationException("无效的cron表达式")
    
    # 验证模型（如果提供）
    if task_data.models and not _validate_models(task_data.models):
        raise ValidationException("无效的模型配置")
    
    # 更新任务字段
    update_data = task_data.dict(exclude_unset=True)
    if update_data:
        for field, value in update_data.items():
            if field not in ['models', 'keywords']:  # 这些字段需要特殊处理
                setattr(task, field, value)
        
        task.updated_at = datetime.utcnow()
    
    # 更新模型（如果提供）
    if task_data.models is not None:
        # 删除现有模型
        db.execute(delete(TaskModel).where(TaskModel.task_id == task_id))
        
        # 添加新模型
        for model_data in task_data.models:
            task_model = TaskModel(
                task_id=task.id,
                model_name=model_data.name,
                provider=model_data.provider,
                config=model_data.config or {}
            )
            db.add(task_model)
    
    # 更新关键词（如果提供）
    if task_data.keywords is not None:
        # 删除现有关键词
        db.execute(delete(TaskKeyword).where(TaskKeyword.task_id == task_id))
        
        # 添加新关键词
        for keyword in task_data.keywords:
            task_keyword = TaskKeyword(
                task_id=task.id,
                keyword=keyword
            )
            db.add(task_keyword)
    
    db.commit()
    db.refresh(task)
    
    return TaskResponse.from_orm(task)


@router.delete("/{task_id}")
@require_minimum_role("admin")
async def delete_task(
    task_id: str,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除指定任务"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    # 检查任务是否存在
    query = select(MonitorTask).where(
        MonitorTask.id == task_id,
        MonitorTask.tenant_id == tenant_id
    )
    result = db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("任务不存在")
    
    # 删除任务（级联删除相关数据）
    db.delete(task)
    db.commit()
    
    return {"message": "任务删除成功"}


@router.post("/{task_id}/trigger", response_model=TaskTriggerResponse)
@require_minimum_role("member")
async def trigger_task(
    task_id: str,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """手动触发任务执行"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    # 检查任务是否存在
    query = select(MonitorTask).where(
        MonitorTask.id == task_id,
        MonitorTask.tenant_id == tenant_id
    )
    result = db.execute(query)
    task = result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("任务不存在")
    
    if not task.is_active:
        raise ValidationException("任务未激活，无法执行")
    
    # 触发任务执行
    try:
        run_id = await trigger_task_run(task_id)
        return TaskTriggerResponse(
            message="任务触发成功",
            run_id=run_id,
            task_id=task_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务触发失败: {str(e)}"
        )


@router.get("/{task_id}/runs")
async def get_task_runs(
    task_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取任务的执行历史"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    
    # 检查任务是否存在
    task_query = select(MonitorTask).where(
        MonitorTask.id == task_id,
        MonitorTask.tenant_id == tenant_id
    )
    task_result = db.execute(task_query)
    task = task_result.scalar_one_or_none()
    
    if not task:
        raise NotFoundException("任务不存在")
    
    # 获取执行历史
    query = select(TaskRun).where(TaskRun.task_id == task_id)
    
    # 获取总数
    count_query = select(func.count()).select_from(query.subquery())
    total_result = db.execute(count_query)
    total = total_result.scalar() or 0
    
    # 获取分页结果
    offset = (page - 1) * limit
    query = query.order_by(TaskRun.created_at.desc()).offset(offset).limit(limit)
    
    result = db.execute(query)
    runs = result.scalars().all()
    
    return {
        "items": [
            {
                "id": str(run.id),
                "status": run.status,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "error_message": run.error_message,
                "metrics": run.metrics
            }
            for run in runs
        ],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


def _validate_cron_expression(cron_expr: str) -> bool:
    """验证cron表达式"""
    try:
        croniter(cron_expr)
        return True
    except (ValueError, TypeError):
        return False


def _validate_models(models: List) -> bool:
    """验证模型配置"""
    if not models:
        return False
    
    valid_providers = ['openrouter', 'openai', 'anthropic']
    
    for model in models:
        if not hasattr(model, 'name') or not model.name:
            return False
        if not hasattr(model, 'provider') or model.provider not in valid_providers:
            return False
    
    return True
