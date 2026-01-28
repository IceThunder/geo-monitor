"""
API routes package initialization.
"""
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.metrics import router as metrics_router
from app.api.alerts import router as alerts_router
from app.api.config import router as config_router

__all__ = [
    "auth_router",
    "tasks_router",
    "metrics_router", 
    "alerts_router",
    "config_router",
]
