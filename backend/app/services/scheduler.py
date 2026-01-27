"""
Task scheduler service.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Optional
import redis.asyncio as redis

from app.core.config import settings
from app.models.entities import TaskRun, MonitorTask, TaskModel, TaskKeyword

# Redis client
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(
            host=settings.UPSTASH_REDIS_REST_URL.replace("https://", "").split("/")[0],
            port=443,
            ssl=True,
            decode_responses=True,
        )
    return redis_client


async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    redis_client = await get_redis()


async def close_redis():
    """Close Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def trigger_task_run(run_id: uuid.UUID):
    """
    Trigger a task run by adding it to the Redis queue.
    
    Args:
        run_id: The ID of the task run to execute.
    """
    r = await get_redis()
    await r.lpush("task_queue", str(run_id))
    print(f"Task run {run_id} queued for execution")


async def enqueue_scheduled_tasks():
    """
    Find and enqueue tasks that are due for execution.
    This would be called by a cron job or scheduler.
    """
    # This is a simplified version - in production, you'd want to:
    # 1. Query tasks that are active and due for execution
    # 2. Create task run records
    # 3. Enqueue them for execution
    pass


class TaskScheduler:
    """
    Simple task scheduler that checks for due tasks.
    In production, you'd use pg_cron or a proper scheduler.
    """
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.running = False
    
    async def start(self):
        """Start the scheduler."""
        self.running = True
        while self.running:
            try:
                await self._check_and_schedule_tasks()
            except Exception as e:
                print(f"Scheduler error: {e}")
            await asyncio.sleep(self.check_interval)
    
    async def stop(self):
        """Stop the scheduler."""
        self.running = False
    
    async def _check_and_schedule_tasks(self):
        """
        Check for tasks that need to be executed.
        
        This is a placeholder - in production, you'd:
        1. Use cron parsing to determine which tasks are due
        2. Create TaskRun records
        3. Call trigger_task_run() for each
        """
        # Placeholder: Check every 60 seconds for simplicity
        # Real implementation would parse cron expressions
        pass


# Convenience function for triggering tasks
async def schedule_task(task_id: uuid.UUID) -> uuid.UUID:
    """
    Schedule a task for immediate execution.
    
    Args:
        task_id: The ID of the task to run.
        
    Returns:
        The ID of the created TaskRun.
    """
    from app.models.database import async_session_factory
    
    async with async_session_factory() as session:
        # Create a new task run
        task_run = TaskRun(
            task_id=task_id,
            status="pending",
        )
        session.add(task_run)
        await session.commit()
        await session.refresh(task_run)
        
        # Enqueue for execution
        await trigger_task_run(task_run.id)
        
        return task_run.id
