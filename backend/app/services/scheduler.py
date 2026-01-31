"""
Task scheduler service - Synchronous version.
"""
import uuid
from datetime import datetime
from typing import Optional
import redis

from app.core.config import settings
from app.models.entities import TaskRun, MonitorTask, TaskModel, TaskKeyword
from app.models.database import SessionLocal

# Redis client
redis_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Get Redis client."""
    global redis_client
    if redis_client is None and hasattr(settings, 'UPSTASH_REDIS_REST_URL') and settings.UPSTASH_REDIS_REST_URL:
        # Parse URL: https://handy-thrush-8862.upstash.io -> handy-thrush-8862.upstash.io:443
        url = settings.UPSTASH_REDIS_REST_URL
        host = url.replace("https://", "").replace("http://", "").split("/")[0]
        redis_client = redis.Redis(
            host=host,
            port=443,
            ssl=True,
            decode_responses=True,
        )
    return redis_client


def init_redis():
    """Initialize Redis connection."""
    global redis_client
    if hasattr(settings, 'UPSTASH_REDIS_REST_URL') and settings.UPSTASH_REDIS_REST_URL:
        redis_client = get_redis()
    else:
        # Skip Redis in development mode
        redis_client = None


def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        redis_client.close()
        redis_client = None


def trigger_task_run(run_id: uuid.UUID):
    """Trigger a task run by adding it to the Redis queue."""
    r = get_redis()
    if r:
        r.lpush("task_queue", str(run_id))
    else:
        # In development mode without Redis, just log the task
        print(f"Task run triggered (no Redis): {run_id}")
    print(f"Task run {run_id} queued for execution")


def schedule_task(task_id: uuid.UUID) -> uuid.UUID:
    """
    Schedule a task for immediate execution.
    
    Args:
        task_id: The ID of the task to run.
        
    Returns:
        The ID of the created TaskRun.
    """
    session = SessionLocal()
    try:
        # Create a new task run
        task_run = TaskRun(
            task_id=task_id,
            status="pending",
        )
        session.add(task_run)
        session.commit()
        session.refresh(task_run)
        
        # Enqueue for execution
        trigger_task_run(task_run.id)
        
        return task_run.id
    finally:
        session.close()
