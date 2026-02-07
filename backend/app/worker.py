"""
Background worker for task execution.

This worker handles:
1. Scheduled cron tasks via APScheduler
2. Manually triggered tasks via Redis queue
"""
import asyncio
import signal
import sys
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

import redis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.core.config import settings
from app.models.database import async_session_factory, init_async_db, close_async_db
from app.models.entities import MonitorTask, TaskRun
from app.services.executor import execute_task_run
from app.services.scheduler import get_redis

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskWorker:
    """Background worker for executing tasks."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.redis_client: Optional[redis.Redis] = None
        self.running = False
        self.queue_consumer_task: Optional[asyncio.Task] = None
        self.sync_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize worker resources."""
        logger.info("Initializing worker...")

        # Initialize database
        try:
            await init_async_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        # Initialize Redis
        try:
            self.redis_client = get_redis()
            if self.redis_client:
                # Test Redis connection
                self.redis_client.ping()
                logger.info("Redis connected")
            else:
                logger.warning("Redis not configured - running in dev mode")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e} - running without queue")
            self.redis_client = None

        # Start APScheduler
        self.scheduler.start()
        logger.info("APScheduler started")

        # Load initial scheduled tasks
        await self.sync_scheduled_tasks()

    async def sync_scheduled_tasks(self):
        """Sync scheduled tasks from database to APScheduler."""
        logger.info("Syncing scheduled tasks...")

        async with async_session_factory() as session:
            # Get all active tasks with cron schedules
            result = await session.execute(
                select(MonitorTask).where(
                    MonitorTask.is_active == True,
                    MonitorTask.schedule_cron.isnot(None)
                )
            )
            tasks = result.scalars().all()

            # Remove all existing jobs
            for job in self.scheduler.get_jobs():
                job.remove()

            # Add jobs for each active task
            for task in tasks:
                try:
                    # Parse cron expression
                    trigger = CronTrigger.from_crontab(task.schedule_cron)

                    # Add job to scheduler
                    self.scheduler.add_job(
                        self.execute_scheduled_task,
                        trigger=trigger,
                        args=[task.id],
                        id=str(task.id),
                        name=f"Task: {task.name}",
                        replace_existing=True,
                    )

                    logger.info(
                        f"Scheduled task '{task.name}' (ID: {task.id}) "
                        f"with cron: {task.schedule_cron}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to schedule task '{task.name}' (ID: {task.id}): {e}"
                    )

            logger.info(f"Synced {len(tasks)} scheduled tasks")

    async def execute_scheduled_task(self, task_id: UUID):
        """Execute a scheduled task by creating a task run."""
        logger.info(f"Executing scheduled task: {task_id}")

        try:
            async with async_session_factory() as session:
                # Create task run
                task_run = TaskRun(
                    task_id=task_id,
                    status="pending",
                )
                session.add(task_run)
                await session.commit()
                await session.refresh(task_run)

                run_id = task_run.id
                logger.info(f"Created task run {run_id} for task {task_id}")

            # Execute the task run
            await execute_task_run(run_id)

        except Exception as e:
            logger.error(f"Error executing scheduled task {task_id}: {e}")

    async def consume_redis_queue(self):
        """Consume tasks from Redis queue."""
        logger.info("Starting Redis queue consumer...")

        while self.running:
            try:
                if not self.redis_client:
                    # No Redis - sleep and continue
                    await asyncio.sleep(5)
                    continue

                # BRPOP with 5 second timeout
                result = self.redis_client.brpop("task_queue", timeout=5)

                if result:
                    _, run_id_str = result
                    run_id = UUID(run_id_str)

                    logger.info(f"Processing task run from queue: {run_id}")

                    try:
                        await execute_task_run(run_id)
                    except Exception as e:
                        logger.error(f"Error executing task run {run_id}: {e}")

            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                await asyncio.sleep(10)  # Wait before retry

            except Exception as e:
                logger.error(f"Error in queue consumer: {e}")
                await asyncio.sleep(5)

    async def periodic_sync(self):
        """Periodically sync scheduled tasks (every 60 seconds)."""
        logger.info("Starting periodic task sync...")

        while self.running:
            try:
                await asyncio.sleep(60)
                await self.sync_scheduled_tasks()

            except Exception as e:
                logger.error(f"Error in periodic sync: {e}")

    async def start(self):
        """Start the worker."""
        logger.info("Starting task worker...")
        self.running = True

        # Initialize resources
        await self.initialize()

        # Start queue consumer
        self.queue_consumer_task = asyncio.create_task(self.consume_redis_queue())

        # Start periodic sync
        self.sync_task = asyncio.create_task(self.periodic_sync())

        logger.info("Worker started successfully")

        # Wait for tasks
        await asyncio.gather(
            self.queue_consumer_task,
            self.sync_task,
            return_exceptions=True
        )

    async def shutdown(self):
        """Gracefully shutdown the worker."""
        logger.info("Shutting down worker...")
        self.running = False

        # Stop scheduler
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

        # Cancel background tasks
        if self.queue_consumer_task:
            self.queue_consumer_task.cancel()
            try:
                await self.queue_consumer_task
            except asyncio.CancelledError:
                pass

        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass

        # Close Redis
        if self.redis_client:
            try:
                self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

        # Close database
        try:
            await close_async_db()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

        logger.info("Worker shutdown complete")


# Global worker instance
worker: Optional[TaskWorker] = None


def signal_handler(sig, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {sig}, initiating shutdown...")
    if worker:
        asyncio.create_task(worker.shutdown())


async def main():
    """Main entry point for the worker."""
    global worker

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create and start worker
    worker = TaskWorker()

    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
