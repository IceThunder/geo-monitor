"""
Models package initialization.
"""
from app.models.database import Base, get_db, init_db, close_db
from app.models.entities import (
    MonitorTask,
    TaskModel,
    TaskKeyword,
    TaskRun,
    ModelOutput,
    MetricsSnapshot,
    TenantConfig,
    AlertRecord,
)
from app.models.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    TaskTriggerResponse,
    SOVTrendResponse,
    AccuracyTrendResponse,
    ModelComparisonResponse,
    DashboardOverviewResponse,
    AlertResponse,
    AlertListResponse,
    TenantConfigResponse,
    TenantConfigUpdate,
)

__all__ = [
    # Database
    "Base",
    "get_db",
    "init_db",
    "close_db",
    # Entities
    "MonitorTask",
    "TaskModel",
    "TaskKeyword",
    "TaskRun",
    "ModelOutput",
    "MetricsSnapshot",
    "TenantConfig",
    "AlertRecord",
    # Schemas
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "TaskListResponse",
    "TaskTriggerResponse",
    "SOVTrendResponse",
    "AccuracyTrendResponse",
    "ModelComparisonResponse",
    "DashboardOverviewResponse",
    "AlertResponse",
    "AlertListResponse",
    "TenantConfigResponse",
    "TenantConfigUpdate",
]
