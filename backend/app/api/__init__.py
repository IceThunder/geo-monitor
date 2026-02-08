"""
API routes package initialization.

Note: Legacy routers (tasks, auth, config) have been superseded by protected_* routers
registered directly in main.py. Only alerts and metrics (old) are
still loaded here for backwards compatibility.
"""
from app.api.metrics import router as metrics_router
from app.api.alerts import router as alerts_router

# 暂时禁用WebSocket以确保部署成功
try:
    from app.api.websocket import router as websocket_router
    WEBSOCKET_AVAILABLE = True
except ImportError:
    websocket_router = None
    WEBSOCKET_AVAILABLE = False

__all__ = [
    "metrics_router",
    "alerts_router",
]

if WEBSOCKET_AVAILABLE:
    __all__.append("websocket_router")
