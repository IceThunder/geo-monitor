"""
Alert management API routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
import uuid

from app.models.database import get_db
from app.models.entities import AlertRecord, MonitorTask
from app.models.schemas import (
    AlertResponse,
    AlertListResponse,
    MarkAlertReadResponse,
    WebhookTestRequest,
    WebhookTestResponse,
)
from app.core.security import get_current_tenant_id
from app.services.notifier import test_webhook

router = APIRouter(tags=["Alerts"])


@router.get("", response_model=AlertListResponse)
def list_alerts(
    is_read: Optional[bool] = Query(None, description="是否已读"),
    alert_type: Optional[str] = Query(None, description="告警类型"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """List alerts for the current tenant."""
    # Build query
    query = select(AlertRecord).where(AlertRecord.tenant_id == tenant_id)
    
    if is_read is not None:
        query = query.where(AlertRecord.is_read == is_read)
    
    if alert_type:
        query = query.where(AlertRecord.alert_type == alert_type)
    
    # Get unread count
    unread_query = (
        select(func.count())
        .select_from(AlertRecord)
        .where(AlertRecord.tenant_id == tenant_id, AlertRecord.is_read == False)
    )
    unread_result = db.execute(unread_query)
    unread_count = unread_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(AlertRecord.created_at.desc()).offset(offset).limit(limit)
    result = db.execute(query)
    alerts = result.scalars().all()
    
    # Get task names for each alert
    data = []
    for alert in alerts:
        task_name = None
        if alert.task_id:
            task_result = db.execute(
                select(MonitorTask.name).where(MonitorTask.id == alert.task_id)
            )
            task_name = task_result.scalar_one_or_none()
        
        data.append(AlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            task_id=alert.task_id,
            task_name=task_name,
            alert_type=alert.alert_type,
            alert_message=alert.alert_message,
            metric_name=alert.metric_name,
            metric_value=float(alert.metric_value) if alert.metric_value else None,
            threshold_value=float(alert.threshold_value) if alert.threshold_value else None,
            is_read=alert.is_read,
            is_resolved=alert.is_resolved,
            created_at=alert.created_at,
        ))
    
    return AlertListResponse(data=data, unread_count=unread_count)


@router.put("/{alert_id}/read", response_model=MarkAlertReadResponse)
def mark_alert_read(
    alert_id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Mark an alert as read."""
    result = db.execute(
        select(AlertRecord).where(
            AlertRecord.id == alert_id,
            AlertRecord.tenant_id == tenant_id,
        )
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        return MarkAlertReadResponse(success=False)
    
    alert.is_read = True
    db.commit()
    
    return MarkAlertReadResponse(success=True)


@router.put("/read-all", response_model=MarkAlertReadResponse)
def mark_all_alerts_read(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Mark all alerts as read."""
    db.execute(
        update(AlertRecord)
        .where(AlertRecord.tenant_id == tenant_id, AlertRecord.is_read == False)
        .values(is_read=True)
    )
    db.commit()
    
    return MarkAlertReadResponse(success=True)


@router.get("/unread-count")
def get_unread_count(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db),
):
    """Get the count of unread alerts."""
    result = db.execute(
        select(func.count())
        .select_from(AlertRecord)
        .where(AlertRecord.tenant_id == tenant_id, AlertRecord.is_read == False)
    )
    count = result.scalar() or 0
    
    return {"unread_count": count}


@router.post("/webhooks/test", response_model=WebhookTestResponse)
async def test_webhook_endpoint(
    request: WebhookTestRequest,
):
    """Test webhook connectivity."""
    success, response_time, response_status = await test_webhook(request.webhook_url)
    
    return WebhookTestResponse(
        success=success,
        response_time_ms=response_time,
        response_status=response_status,
    )
