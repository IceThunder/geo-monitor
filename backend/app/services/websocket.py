"""
WebSocket服务
处理实时连接和消息推送
"""
import json
import uuid
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 存储活跃连接: {connection_id: {websocket, tenant_id, user_id}}
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        # 按租户分组连接: {tenant_id: [connection_ids]}
        self.tenant_connections: Dict[str, List[str]] = {}
        # 按用户分组连接: {user_id: [connection_ids]}
        self.user_connections: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> str:
        """建立WebSocket连接"""
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        
        # 解析用户信息
        tenant_id = "default"
        user_id = "anonymous"
        
        if token:
            try:
                payload = decode_token(token)
                tenant_id = payload.get("sub", "default")
                user_id = payload.get("user_id", "anonymous")
            except Exception as e:
                logger.warning(f"Token解析失败: {e}")
        
        # 存储连接信息
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "tenant_id": tenant_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow()
        }
        
        # 按租户分组
        if tenant_id not in self.tenant_connections:
            self.tenant_connections[tenant_id] = []
        self.tenant_connections[tenant_id].append(connection_id)
        
        # 按用户分组
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        logger.info(f"WebSocket连接建立: {connection_id}, 租户: {tenant_id}, 用户: {user_id}")
        
        # 发送连接确认消息
        await self.send_personal_message(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return connection_id
    
    def disconnect(self, connection_id: str):
        """断开WebSocket连接"""
        if connection_id not in self.active_connections:
            return
        
        connection_info = self.active_connections[connection_id]
        tenant_id = connection_info["tenant_id"]
        user_id = connection_info["user_id"]
        
        # 从活跃连接中移除
        del self.active_connections[connection_id]
        
        # 从租户分组中移除
        if tenant_id in self.tenant_connections:
            self.tenant_connections[tenant_id].remove(connection_id)
            if not self.tenant_connections[tenant_id]:
                del self.tenant_connections[tenant_id]
        
        # 从用户分组中移除
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        logger.info(f"WebSocket连接断开: {connection_id}")
    
    async def send_personal_message(self, connection_id: str, message: dict):
        """发送个人消息"""
        if connection_id not in self.active_connections:
            return False
        
        try:
            websocket = self.active_connections[connection_id]["websocket"]
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
            return True
        except Exception as e:
            logger.error(f"发送个人消息失败: {e}")
            self.disconnect(connection_id)
            return False
    
    async def send_to_tenant(self, tenant_id: str, message: dict):
        """向租户的所有连接发送消息"""
        if tenant_id not in self.tenant_connections:
            return 0
        
        sent_count = 0
        connection_ids = self.tenant_connections[tenant_id].copy()
        
        for connection_id in connection_ids:
            if await self.send_personal_message(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_to_user(self, user_id: str, message: dict):
        """向用户的所有连接发送消息"""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        connection_ids = self.user_connections[user_id].copy()
        
        for connection_id in connection_ids:
            if await self.send_personal_message(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        sent_count = 0
        connection_ids = list(self.active_connections.keys())
        
        for connection_id in connection_ids:
            if await self.send_personal_message(connection_id, message):
                sent_count += 1
        
        return sent_count
    
    def get_connection_stats(self) -> dict:
        """获取连接统计信息"""
        return {
            "total_connections": len(self.active_connections),
            "tenant_count": len(self.tenant_connections),
            "user_count": len(self.user_connections),
            "connections_by_tenant": {
                tenant_id: len(connections) 
                for tenant_id, connections in self.tenant_connections.items()
            }
        }

# 全局连接管理器实例
manager = ConnectionManager()

class WebSocketService:
    """WebSocket业务服务"""
    
    @staticmethod
    async def notify_task_status_change(tenant_id: str, task_id: str, status: str, details: dict = None):
        """通知任务状态变更"""
        message = {
            "type": "task_status_change",
            "task_id": task_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sent_count = await manager.send_to_tenant(tenant_id, message)
        logger.info(f"任务状态变更通知已发送: {task_id} -> {status}, 发送给 {sent_count} 个连接")
    
    @staticmethod
    async def notify_new_metrics(tenant_id: str, metrics: dict):
        """通知新的指标数据"""
        message = {
            "type": "metrics_update",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sent_count = await manager.send_to_tenant(tenant_id, message)
        logger.info(f"指标更新通知已发送给 {sent_count} 个连接")
    
    @staticmethod
    async def notify_alert(tenant_id: str, alert: dict):
        """发送告警通知"""
        message = {
            "type": "alert",
            "alert": alert,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sent_count = await manager.send_to_tenant(tenant_id, message)
        logger.info(f"告警通知已发送: {alert.get('title', 'Unknown')}, 发送给 {sent_count} 个连接")
    
    @staticmethod
    async def notify_system_message(message_text: str, level: str = "info"):
        """发送系统消息"""
        message = {
            "type": "system_message",
            "message": message_text,
            "level": level,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        sent_count = await manager.broadcast(message)
        logger.info(f"系统消息已广播给 {sent_count} 个连接")

# WebSocket端点处理函数
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """WebSocket端点处理函数"""
    connection_id = None
    
    try:
        # 建立连接
        connection_id = await manager.connect(websocket, token)
        
        # 发送欢迎消息
        await manager.send_personal_message(connection_id, {
            "type": "welcome",
            "message": "欢迎连接到GEO监控系统",
            "connection_id": connection_id
        })
        
        # 监听消息
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理心跳消息
                if message.get("type") == "ping":
                    await manager.send_personal_message(connection_id, {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                # 处理订阅消息
                if message.get("type") == "subscribe":
                    topics = message.get("topics", [])
                    await manager.send_personal_message(connection_id, {
                        "type": "subscription_confirmed",
                        "topics": topics,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    continue
                
                # 其他消息类型的处理
                logger.info(f"收到WebSocket消息: {message}")
                
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "消息格式错误",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"处理WebSocket消息时出错: {e}")
                await manager.send_personal_message(connection_id, {
                    "type": "error",
                    "message": "服务器内部错误",
                    "timestamp": datetime.utcnow().isoformat()
                })
    
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    
    finally:
        # 清理连接
        if connection_id:
            manager.disconnect(connection_id)
