"""
全局搜索API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, or_

from app.core.database import get_db
from app.models.entities import MonitorTask, TaskKeyword
from app.middleware.auth import get_current_user
from app.models.user_entities import User, UserTenant

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("")
async def search_global(
    q: str = Query(..., min_length=1, max_length=200),
    type: str = Query(default="all", regex="^(all|tasks|keywords)$"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """全局搜索：搜索任务名称、描述和关键词"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)
    search_pattern = f"%{q}%"

    tasks_result = []
    keywords_result = []

    # Search tasks
    if type in ("all", "tasks"):
        task_query = (
            select(MonitorTask)
            .where(
                MonitorTask.tenant_id == tenant_id,
                or_(
                    MonitorTask.name.ilike(search_pattern),
                    MonitorTask.description.ilike(search_pattern),
                ),
            )
            .options(
                selectinload(MonitorTask.models),
                selectinload(MonitorTask.keywords),
            )
            .limit(limit)
        )
        result = db.execute(task_query)
        tasks = result.scalars().all()

        tasks_result = [
            {
                "id": str(t.id),
                "name": t.name,
                "description": t.description,
                "is_active": t.is_active,
                "models": [m.model_id for m in t.models],
                "keywords": [k.keyword for k in t.keywords],
            }
            for t in tasks
        ]

    # Search keywords
    if type in ("all", "keywords"):
        kw_query = (
            select(TaskKeyword, MonitorTask.name.label("task_name"))
            .join(MonitorTask, TaskKeyword.task_id == MonitorTask.id)
            .where(
                MonitorTask.tenant_id == tenant_id,
                TaskKeyword.keyword.ilike(search_pattern),
            )
            .limit(limit)
        )
        result = db.execute(kw_query)
        kw_rows = result.all()

        keywords_result = [
            {
                "keyword": row.TaskKeyword.keyword,
                "task_id": str(row.TaskKeyword.task_id),
                "task_name": row.task_name,
            }
            for row in kw_rows
        ]

    return {
        "tasks": tasks_result,
        "keywords": keywords_result,
        "query": q,
    }
