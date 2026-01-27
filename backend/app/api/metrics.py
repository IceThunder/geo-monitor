"""
Metrics API routes for data retrieval and analysis.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
import uuid

from app.models.database import get_db
from app.models.entities import MonitorTask, MetricsSnapshot, TaskRun, TaskKeyword
from app.models.schemas import (
    SOVTrendResponse,
    AccuracyTrendResponse,
    ModelComparisonResponse,
    DashboardOverviewResponse,
)
from app.core.security import get_current_tenant_id

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/sov")
async def get_sov_trend(
    keyword: str = Query(..., description="关键词"),
    model: Optional[str] = Query(None, description="模型ID"),
    period: str = Query(default="7d", pattern="^(7d|30d|90d)$"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get SOV trend data for a keyword."""
    # Calculate date range
    days = int(period.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = (
        select(MetricsSnapshot)
        .join(TaskRun, MetricsSnapshot.run_id == TaskRun.id)
        .join(MonitorTask, TaskRun.task_id == MonitorTask.id)
        .where(
            MonitorTask.tenant_id == tenant_id,
            MetricsSnapshot.keyword == keyword,
            MetricsSnapshot.created_at >= start_date,
        )
    )
    
    if model:
        query = query.where(MetricsSnapshot.model_id == model)
    
    query = query.order_by(MetricsSnapshot.created_at.asc())
    
    result = await db.execute(query)
    snapshots = result.scalars().all()
    
    # Group by date and calculate daily average
    daily_data = {}
    for snapshot in snapshots:
        date_key = snapshot.created_at.strftime("%Y-%m-%d")
        if date_key not in daily_data:
            daily_data[date_key] = []
        if snapshot.sov_score is not None:
            daily_data[date_key].append(float(snapshot.sov_score))
    
    data = [
        {"date": date, "sov": sum(values) / len(values) if values else 0}
        for date, values in sorted(daily_data.items())
    ]
    
    return SOVTrendResponse(keyword=keyword, model=model or "all", data=data)


@router.get("/accuracy")
async def get_accuracy_trend(
    task_id: Optional[uuid.UUID] = Query(None, description="任务ID"),
    period: str = Query(default="30d", pattern="^(7d|30d|90d|365d)$"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get accuracy trend data."""
    days = int(period.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = (
        select(MetricsSnapshot)
        .join(TaskRun, MetricsSnapshot.run_id == TaskRun.id)
        .join(MonitorTask, TaskRun.task_id == MonitorTask.id)
        .where(
            MonitorTask.tenant_id == tenant_id,
            MetricsSnapshot.created_at >= start_date,
            MetricsSnapshot.accuracy_score.isnot(None),
        )
    )
    
    if task_id:
        query = query.where(TaskRun.task_id == task_id)
    
    query = query.order_by(MetricsSnapshot.created_at.asc())
    
    result = await db.execute(query)
    snapshots = result.scalars().all()
    
    # Group by date
    daily_data = {}
    for snapshot in snapshots:
        date_key = snapshot.created_at.strftime("%Y-%m-%d")
        if date_key not in daily_data:
            daily_data[date_key] = {"values": [], "min": 10, "max": 0}
        
        accuracy = float(snapshot.accuracy_score)
        daily_data[date_key]["values"].append(accuracy)
        daily_data[date_key]["min"] = min(daily_data[date_key]["min"], accuracy)
        daily_data[date_key]["max"] = max(daily_data[date_key]["max"], accuracy)
    
    data = [
        {
            "date": date,
            "avg_accuracy": sum(info["values"]) / len(info["values"]),
            "min_accuracy": info["min"],
            "max_accuracy": info["max"],
        }
        for date, info in sorted(daily_data.items())
    ]
    
    return AccuracyTrendResponse(task_id=task_id, data=data)


@router.get("/comparison")
async def get_model_comparison(
    keyword: str = Query(..., description="关键词"),
    period: str = Query(default="7d", pattern="^(7d|30d)$"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get model comparison data for a keyword."""
    days = int(period.replace("d", ""))
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get metrics grouped by model
    query = (
        select(
            MetricsSnapshot.model_id,
            func.avg(MetricsSnapshot.sov_score).label("avg_sov"),
            func.avg(MetricsSnapshot.accuracy_score).label("avg_accuracy"),
            func.avg(MetricsSnapshot.sentiment_score).label("avg_sentiment"),
        )
        .join(TaskRun, MetricsSnapshot.run_id == TaskRun.id)
        .join(MonitorTask, TaskRun.task_id == MonitorTask.id)
        .where(
            MonitorTask.tenant_id == tenant_id,
            MetricsSnapshot.keyword == keyword,
            MetricsSnapshot.created_at >= start_date,
        )
        .group_by(MetricsSnapshot.model_id)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    models = {}
    for row in rows:
        models[row.model_id] = {
            "sov": float(row.avg_sov) if row.avg_sov else 0,
            "accuracy": float(row.avg_accuracy) if row.avg_accuracy else 0,
            "sentiment": float(row.avg_sentiment) if row.avg_sentiment else 0,
        }
    
    return ModelComparisonResponse(keyword=keyword, models=models)


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    start_date: str = Query(..., pattern="^\\d{4}-\\d{2}-\\d{2}$"),
    end_date: str = Query(..., pattern="^\\d{4}-\\d{2}-\\d{2}$"),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard overview data."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
    
    # Count tasks
    tasks_result = await db.execute(
        select(
            func.count().filter(MonitorTask.is_active == True).label("active"),
            func.count().label("total"),
        ).where(MonitorTask.tenant_id == tenant_id)
    )
    tasks_counts = tasks_result.one()
    active_tasks = tasks_counts.active or 0
    total_tasks = tasks_counts.total or 0
    
    # Get SOV trend for top keywords
    sov_result = await db.execute(
        select(
            MetricsSnapshot.keyword,
            func.avg(MetricsSnapshot.sov_score).label("avg_sov"),
        )
        .join(TaskRun, MetricsSnapshot.run_id == TaskRun.id)
        .join(MonitorTask, TaskRun.task_id == MonitorTask.id)
        .where(
            MonitorTask.tenant_id == tenant_id,
            MetricsSnapshot.created_at >= start,
            MetricsSnapshot.created_at < end,
        )
        .group_by(MetricsSnapshot.keyword)
        .order_by(func.avg(MetricsSnapshot.sov_score).desc())
        .limit(10)
    )
    sov_trend = [
        {"keyword": row.keyword, "sov": float(row.avg_sov) if row.avg_sov else 0}
        for row in sov_result.all()
    ]
    
    # Get accuracy trend
    accuracy_result = await db.execute(
        select(
            func.date_trunc("day", MetricsSnapshot.created_at).label("date"),
            func.avg(MetricsSnapshot.accuracy_score).label("avg_accuracy"),
        )
        .join(TaskRun, MetricsSnapshot.run_id == TaskRun.id)
        .join(MonitorTask, TaskRun.task_id == MonitorTask.id)
        .where(
            MonitorTask.tenant_id == tenant_id,
            MetricsSnapshot.created_at >= start,
            MetricsSnapshot.created_at < end,
            MetricsSnapshot.accuracy_score.isnot(None),
        )
        .group_by(func.date_trunc("day", MetricsSnapshot.created_at))
        .order_by("date")
    )
    accuracy_trend = [
        {"date": str(row.date.date()), "avg_accuracy": float(row.avg_accuracy) if row.avg_accuracy else 0}
        for row in accuracy_result.all()
    ]
    
    # Get top brands mentioned
    brands_result = await db.execute(
        select(
            func.jsonb_array_elements_text(MetricsSnapshot.brands_mentioned).label("brand"),
            func.count().label("count"),
        )
        .join(TaskRun, MetricsSnapshot.run_id == TaskRun.id)
        .join(MonitorTask, TaskRun.task_id == MonitorTask.id)
        .where(
            MonitorTask.tenant_id == tenant_id,
            MetricsSnapshot.created_at >= start,
            MetricsSnapshot.created_at < end,
        )
        .group_by("brand")
        .order_by(func.count().desc())
        .limit(10)
    )
    top_brands = [
        {"brand": row.brand, "count": row.count}
        for row in brands_result.all()
    ]
    
    # Get recent alerts (placeholder - would need AlertRecord model)
    recent_alerts = []
    
    # Get total cost and token usage
    cost_result = await db.execute(
        select(
            func.sum(TaskRun.cost_usd).label("total_cost"),
            func.sum(TaskRun.token_usage).label("total_tokens"),
        )
        .join(MonitorTask, TaskRun.task_id == MonitorTask.id)
        .where(
            MonitorTask.tenant_id == tenant_id,
            TaskRun.created_at >= start,
            TaskRun.created_at < end,
        )
    )
    cost_data = cost_result.one()
    total_cost_usd = float(cost_data.total_cost) if cost_data.total_cost else 0
    total_token_usage = cost_data.total_tokens or 0
    
    return DashboardOverviewResponse(
        total_tasks=total_tasks,
        active_tasks=active_tasks,
        sov_trend=[],
        accuracy_trend=accuracy_trend,
        top_brands=top_brands,
        recent_alerts=recent_alerts,
        total_cost_usd=total_cost_usd,
        total_token_usage=total_token_usage,
    )
