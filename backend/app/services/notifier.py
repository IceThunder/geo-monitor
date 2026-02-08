"""
Alert notification service.
"""
import asyncio
import json
import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy import select

from app.core.config import settings
from app.models.entities import AlertRecord, TenantConfig, MetricsSnapshot, TaskRun

logger = logging.getLogger(__name__)


async def send_webhook_notification(
    webhook_url: str,
    alert_data: Dict[str, Any],
) -> tuple[bool, int, Optional[int]]:
    """
    Send a webhook notification.
    
    Args:
        webhook_url: The webhook URL to send to.
        alert_data: The alert data to send.
        
    Returns:
        Tuple of (success, response_time_ms, response_status).
    """
    start_time = datetime.utcnow()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                webhook_url,
                json=alert_data,
                headers={"Content-Type": "application/json"},
            )
            
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return response.status_code < 400, response_time, response.status_code
            
    except Exception as e:
        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        return False, response_time, None


async def test_webhook(webhook_url: str) -> tuple[bool, int, Optional[int]]:
    """
    Test webhook connectivity.
    
    Args:
        webhook_url: The webhook URL to test.
        
    Returns:
        Tuple of (success, response_time_ms, response_status).
    """
    test_data = {
        "type": "test",
        "message": "GEO Monitor webhook test successful",
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    return await send_webhook_notification(webhook_url, test_data)


async def create_and_send_alert(
    tenant_id: str,
    task_id: str,
    alert_type: str,
    alert_message: str,
    metric_name: Optional[str] = None,
    metric_value: Optional[Decimal] = None,
    threshold_value: Optional[Decimal] = None,
) -> AlertRecord:
    """
    Create an alert record and send notification.
    
    Args:
        tenant_id: The tenant ID.
        task_id: The task ID.
        alert_type: Type of alert (e.g., "accuracy_low", "sov_drop").
        alert_message: Human-readable alert message.
        metric_name: Name of the metric that triggered the alert.
        metric_value: Current value of the metric.
        threshold_value: Threshold that was crossed.
        
    Returns:
        Created AlertRecord.
    """
    from app.models.database import async_session_factory
    
    async with async_session_factory() as session:
        # Create alert record
        alert = AlertRecord(
            tenant_id=tenant_id,
            task_id=task_id,
            alert_type=alert_type,
            alert_message=alert_message,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold_value=threshold_value,
        )
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        
        # Get tenant config for webhook
        result = await session.execute(
            select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
        )
        config = result.scalar_one_or_none()
        
        # Send webhook if configured
        if config and config.webhook_url and settings.WEBHOOK_ENABLED:
            alert_data = {
                "type": "alert",
                "alert_id": str(alert.id),
                "tenant_id": tenant_id,
                "task_id": task_id,
                "alert_type": alert_type,
                "message": alert_message,
                "metric": {
                    "name": metric_name,
                    "value": float(metric_value) if metric_value else None,
                    "threshold": float(threshold_value) if threshold_value else None,
                },
                "timestamp": alert.created_at.isoformat(),
            }
            
            success, response_time, status = await send_webhook_notification(
                config.webhook_url,
                alert_data,
            )
            
            logger.info(f"Webhook notification sent: success={success}, time={response_time}ms")

        # Send WebSocket notification
        try:
            from app.services.websocket import WebSocketService
            await WebSocketService.notify_alert(
                tenant_id=tenant_id,
                alert={
                    "id": str(alert.id),
                    "type": alert_type,
                    "message": alert_message,
                    "metric_name": metric_name,
                    "metric_value": float(metric_value) if metric_value else None,
                    "threshold_value": float(threshold_value) if threshold_value else None,
                    "severity": "high" if alert_type in ("accuracy_low", "sov_low") else "medium",
                }
            )
        except Exception as ws_err:
            logger.warning(f"Failed to send WebSocket alert notification: {ws_err}")

        return alert


async def check_and_alert(
    tenant_id: str,
    task_id: str,
    metrics: MetricsSnapshot,
    config: TenantConfig,
) -> list[AlertRecord]:
    """
    Check metrics against thresholds and create alerts if needed.
    
    Args:
        tenant_id: The tenant ID.
        task_id: The task ID.
        metrics: The metrics snapshot to check.
        config: The tenant configuration with thresholds.
        
    Returns:
        List of created alerts.
    """
    alerts = []
    
    # Check accuracy threshold
    if metrics.accuracy_score is not None:
        if metrics.accuracy_score < config.alert_threshold_accuracy:
            alert = await create_and_send_alert(
                tenant_id=tenant_id,
                task_id=task_id,
                alert_type="accuracy_low",
                alert_message=f"Accuracy score {metrics.accuracy_score} below threshold {config.alert_threshold_accuracy}",
                metric_name="accuracy_score",
                metric_value=Decimal(str(metrics.accuracy_score)),
                threshold_value=Decimal(str(config.alert_threshold_accuracy)),
            )
            alerts.append(alert)
    
    # Check sentiment threshold
    if metrics.sentiment_score is not None:
        sentiment_threshold = float(config.alert_threshold_sentiment)
        if metrics.sentiment_score < sentiment_threshold:
            alert = await create_and_send_alert(
                tenant_id=tenant_id,
                task_id=task_id,
                alert_type="sentiment_low",
                alert_message=f"Sentiment score {metrics.sentiment_score:.2f} below threshold {sentiment_threshold:.2f}",
                metric_name="sentiment_score",
                metric_value=metrics.sentiment_score,
                threshold_value=Decimal(str(sentiment_threshold)),
            )
            alerts.append(alert)
    
    # Check SOV threshold (default 20%, configurable via ALERT_SOV_THRESHOLD env)
    if metrics.sov_score is not None:
        sov_threshold = getattr(settings, 'ALERT_SOV_THRESHOLD', 20.0)
        if float(metrics.sov_score) < sov_threshold:
            alert = await create_and_send_alert(
                tenant_id=tenant_id,
                task_id=task_id,
                alert_type="sov_low",
                alert_message=f"SOV score {metrics.sov_score:.2f}% below threshold {sov_threshold}%",
                metric_name="sov_score",
                metric_value=metrics.sov_score,
                threshold_value=Decimal(str(sov_threshold)),
            )
            alerts.append(alert)
    
    return alerts


async def process_alerts_for_run(run_id: str):
    """
    Process all alerts for a completed task run.
    
    Args:
        run_id: The task run ID.
    """
    from app.models.database import async_session_factory
    from app.models.entities import TaskRun, MonitorTask
    
    async with async_session_factory() as session:
        # Get the task run
        result = await session.execute(
            select(TaskRun).where(TaskRun.id == run_id)
        )
        task_run = result.scalar_one_or_none()
        
        if not task_run:
            return
        
        # Get the task and tenant config
        result = await session.execute(
            select(MonitorTask).where(MonitorTask.id == task_run.task_id)
        )
        task = result.scalar_one_or_none()
        
        if not task:
            return
        
        result = await session.execute(
            select(TenantConfig).where(TenantConfig.tenant_id == task.tenant_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            return
        
        # Get all metrics for this run
        result = await session.execute(
            select(MetricsSnapshot).where(MetricsSnapshot.run_id == run_id)
        )
        metrics_list = result.scalars().all()
        
        # Check each metric
        for metrics in metrics_list:
            await check_and_alert(
                tenant_id=str(task.tenant_id),
                task_id=str(task.id),
                metrics=metrics,
                config=config,
            )
