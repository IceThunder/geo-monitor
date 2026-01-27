"""
Services package initialization.
"""
from app.services.scheduler import (
    get_redis,
    init_redis,
    close_redis,
    trigger_task_run,
    TaskScheduler,
    schedule_task,
)
from app.services.executor import (
    ModelExecutor,
    execute_task_run,
    calculate_metrics,
)
from app.services.calculator import (
    calculate_sov,
    calculate_accuracy_score,
    analyze_sentiment,
    calculate_citation_rate,
    check_positioning_hit,
    calculate_overall_metrics,
    get_grade,
)
from app.services.notifier import (
    send_webhook_notification,
    test_webhook,
    create_and_send_alert,
    check_and_alert,
    process_alerts_for_run,
)

__all__ = [
    # Scheduler
    "get_redis",
    "init_redis",
    "close_redis",
    "trigger_task_run",
    "TaskScheduler",
    "schedule_task",
    # Executor
    "ModelExecutor",
    "execute_task_run",
    "calculate_metrics",
    # Calculator
    "calculate_sov",
    "calculate_accuracy_score",
    "analyze_sentiment",
    "calculate_citation_rate",
    "check_positioning_hit",
    "calculate_overall_metrics",
    "get_grade",
    # Notifier
    "send_webhook_notification",
    "test_webhook",
    "create_and_send_alert",
    "check_and_alert",
    "process_alerts_for_run",
]
