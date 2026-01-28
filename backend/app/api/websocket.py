"""
WebSocket API端点
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
from app.services.websocket import websocket_endpoint, manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.websocket("/ws")
async def websocket_connect(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    WebSocket连接端点
    
    参数:
    - token: 可选的JWT认证令牌
    """
    await websocket_endpoint(websocket, token)

@router.get("/ws/stats")
async def get_websocket_stats():
    """
    获取WebSocket连接统计信息
    """
    return manager.get_connection_stats()

@router.post("/ws/broadcast")
async def broadcast_message(message: dict):
    """
    广播消息到所有连接
    """
    sent_count = await manager.broadcast(message)
    return {"message": "消息已广播", "sent_count": sent_count}

@router.post("/ws/tenant/{tenant_id}/notify")
async def notify_tenant(tenant_id: str, message: dict):
    """
    向指定租户发送通知
    """
    sent_count = await manager.send_to_tenant(tenant_id, message)
    return {"message": f"消息已发送给租户 {tenant_id}", "sent_count": sent_count}
