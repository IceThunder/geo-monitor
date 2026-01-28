"""
API routes package initialization.
"""
from app.api.auth import router as auth_router
from app.api.tasks import router as tasks_router
from app.api.metrics import router as metrics_router
from app.api.alerts import router as alerts_router
from app.api.config import router as config_router

# 暂时禁用WebSocket以确保部署成功
try:
    from app.api.websocket import router as websocket_router
    WEBSOCKET_AVAILABLE = True
except ImportError:
    websocket_router = None
    WEBSOCKET_AVAILABLE = False

__all__ = [
    "auth_router",
    "tasks_router",
    "metrics_router", 
    "alerts_router",
    "config_router",
]

if WEBSOCKET_AVAILABLE:
    __all__.append("websocket_router")
