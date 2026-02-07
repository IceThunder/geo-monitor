"""
受保护的指标API路由（使用JWT认证）
"""
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_, desc

from app.core.database import get_db
from app.models.entities import TaskRun, MetricsSnapshot, MonitorTask, AlertRecord
from app.middleware.auth import get_current_user
from app.models.user_entities import User, UserTenant

router = APIRouter(prefix="/metrics", tags=["Protected Metrics"])


@router.get("/sov-trend")
async def get_sov_trend(
    days: int = Query(default=30, ge=1, le=365),
    keyword: Optional[str] = None,
    model: Optional[str] = None,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取SOV趋势数据"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    # 计算日期范围
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 构建基础查询
    query = select(
        func.date(TaskRun.completed_at).label('date'),
        func.avg(MetricsSnapshot.sov_score).label('avg_sov'),
        func.count(MetricsSnapshot.id).label('count')
    ).select_from(
        TaskRun.__table__.join(MetricsSnapshot.__table__)
        .join(MonitorTask.__table__)
    ).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.status == 'completed',
            TaskRun.completed_at >= start_date,
            TaskRun.completed_at <= end_date
        )
    )

    # 添加过滤条件
    if keyword:
        query = query.where(MetricsSnapshot.keyword == keyword)

    if model:
        query = query.where(MetricsSnapshot.model_id == model)

    # 按日期分组
    query = query.group_by(func.date(TaskRun.completed_at))
    query = query.order_by(func.date(TaskRun.completed_at))

    result = db.execute(query)
    data = result.fetchall()

    return {
        "data": [
            {
                "date": row.date.isoformat() if row.date else None,
                "avg_sov": float(row.avg_sov) if row.avg_sov else 0,
                "count": row.count
            }
            for row in data
        ],
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }


@router.get("/accuracy-trend")
async def get_accuracy_trend(
    days: int = Query(default=30, ge=1, le=365),
    keyword: Optional[str] = None,
    model: Optional[str] = None,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取准确性趋势数据"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    # 计算日期范围
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 构建基础查询
    query = select(
        func.date(TaskRun.completed_at).label('date'),
        func.avg(MetricsSnapshot.accuracy_score).label('avg_accuracy'),
        func.count(MetricsSnapshot.id).label('count')
    ).select_from(
        TaskRun.__table__.join(MetricsSnapshot.__table__)
        .join(MonitorTask.__table__)
    ).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.status == 'completed',
            TaskRun.completed_at >= start_date,
            TaskRun.completed_at <= end_date
        )
    )

    # 添加过滤条件
    if keyword:
        query = query.where(MetricsSnapshot.keyword == keyword)

    if model:
        query = query.where(MetricsSnapshot.model_id == model)

    # 按日期分组
    query = query.group_by(func.date(TaskRun.completed_at))
    query = query.order_by(func.date(TaskRun.completed_at))

    result = db.execute(query)
    data = result.fetchall()

    return {
        "data": [
            {
                "date": row.date.isoformat() if row.date else None,
                "avg_accuracy": float(row.avg_accuracy) if row.avg_accuracy else 0,
                "count": row.count
            }
            for row in data
        ],
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }


@router.get("/summary")
async def get_metrics_summary(
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取指标摘要"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    # 获取最近30天的数据
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    # 总任务数
    total_tasks_query = select(func.count(MonitorTask.id)).where(
        MonitorTask.tenant_id == tenant_id
    )
    total_tasks = db.execute(total_tasks_query).scalar() or 0

    # 活跃任务数
    active_tasks_query = select(func.count(MonitorTask.id)).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            MonitorTask.is_active == True
        )
    )
    active_tasks = db.execute(active_tasks_query).scalar() or 0

    # 最近30天执行次数
    recent_runs_query = select(func.count(TaskRun.id)).select_from(
        TaskRun.__table__.join(MonitorTask.__table__)
    ).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.completed_at >= start_date,
            TaskRun.status == 'completed'
        )
    )
    recent_runs = db.execute(recent_runs_query).scalar() or 0

    # 平均SOV分数
    avg_sov_query = select(func.avg(MetricsSnapshot.sov_score)).select_from(
        MetricsSnapshot.__table__.join(TaskRun.__table__)
        .join(MonitorTask.__table__)
    ).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.completed_at >= start_date,
            TaskRun.status == 'completed'
        )
    )
    avg_sov = db.execute(avg_sov_query).scalar() or 0

    # 平均准确性分数
    avg_accuracy_query = select(func.avg(MetricsSnapshot.accuracy_score)).select_from(
        MetricsSnapshot.__table__.join(TaskRun.__table__)
        .join(MonitorTask.__table__)
    ).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.completed_at >= start_date,
            TaskRun.status == 'completed'
        )
    )
    avg_accuracy = db.execute(avg_accuracy_query).scalar() or 0

    # 未读告警数量
    unread_alerts_query = select(func.count(AlertRecord.id)).where(
        and_(
            AlertRecord.tenant_id == tenant_id,
            AlertRecord.is_read == False
        )
    )
    unread_alerts = db.execute(unread_alerts_query).scalar() or 0

    return {
        "total_tasks": total_tasks,
        "active_tasks": active_tasks,
        "recent_runs": recent_runs,
        "avg_sov": float(avg_sov) if avg_sov else 0,
        "avg_accuracy": float(avg_accuracy) if avg_accuracy else 0,
        "unread_alerts": unread_alerts,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": 30
        }
    }


@router.get("/model-comparison")
async def get_model_comparison(
    days: int = Query(default=30, ge=1, le=365),
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取模型对比数据"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    # 计算日期范围
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 按模型统计
    query = select(
        MetricsSnapshot.model_id,
        func.avg(MetricsSnapshot.sov_score).label('avg_sov'),
        func.avg(MetricsSnapshot.accuracy_score).label('avg_accuracy'),
        func.count(MetricsSnapshot.id).label('count')
    ).select_from(
        MetricsSnapshot.__table__.join(TaskRun.__table__)
        .join(MonitorTask.__table__)
    ).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.status == 'completed',
            TaskRun.completed_at >= start_date,
            TaskRun.completed_at <= end_date
        )
    ).group_by(MetricsSnapshot.model_id)

    result = db.execute(query)
    data = result.fetchall()

    return {
        "data": [
            {
                "model_id": row.model_id,
                "avg_sov": float(row.avg_sov) if row.avg_sov else 0,
                "avg_accuracy": float(row.avg_accuracy) if row.avg_accuracy else 0,
                "count": row.count
            }
            for row in data
        ],
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        }
    }


@router.get("/keyword-performance")
async def get_keyword_performance(
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=20, ge=1, le=100),
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取关键词性能数据"""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    # 计算日期范围
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # 按关键词统计
    query = select(
        MetricsSnapshot.keyword,
        func.avg(MetricsSnapshot.sov_score).label('avg_sov'),
        func.avg(MetricsSnapshot.accuracy_score).label('avg_accuracy'),
        func.count(MetricsSnapshot.id).label('count')
    ).select_from(
        MetricsSnapshot.__table__.join(TaskRun.__table__)
        .join(MonitorTask.__table__)
    ).where(
        and_(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.status == 'completed',
            TaskRun.completed_at >= start_date,
            TaskRun.completed_at <= end_date
        )
    ).group_by(MetricsSnapshot.keyword).order_by(
        desc(func.avg(MetricsSnapshot.sov_score))
    ).limit(limit)

    result = db.execute(query)
    data = result.fetchall()

    return {
        "data": [
            {
                "keyword": row.keyword,
                "avg_sov": float(row.avg_sov) if row.avg_sov else 0,
                "avg_accuracy": float(row.avg_accuracy) if row.avg_accuracy else 0,
                "count": row.count
            }
            for row in data
        ],
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "days": days
        },
        "limit": limit
    }
