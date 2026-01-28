/**
 * Notification Provider
 * 实时通知系统提供者
 */
'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { createWebSocketClient, WebSocketClient, MESSAGE_TYPES, WebSocketMessage } from '@/lib/websocket';
import { Toast, ToastProvider, ToastViewport } from '@/components/ui/toast';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Bell, 
  CheckCircle, 
  AlertTriangle, 
  XCircle, 
  Info,
  X
} from 'lucide-react';

export interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  persistent?: boolean;
  data?: any;
}

interface NotificationContextType {
  notifications: Notification[];
  unreadCount: number;
  isConnected: boolean;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  connect: (token?: string) => Promise<void>;
  disconnect: () => void;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

export function useNotifications() {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotifications must be used within NotificationProvider');
  }
  return context;
}

interface NotificationProviderProps {
  children: React.ReactNode;
  wsUrl?: string;
}

export function NotificationProvider({ 
  children, 
  wsUrl = 'ws://localhost:8000/api/ws' 
}: NotificationProviderProps) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [wsClient, setWsClient] = useState<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
      timestamp: new Date(),
      read: false,
    };

    setNotifications(prev => [newNotification, ...prev]);

    // 自动移除非持久化通知
    if (!notification.persistent) {
      setTimeout(() => {
        removeNotification(newNotification.id);
      }, 5000);
    }
  }, []);

  const markAsRead = useCallback((id: string) => {
    setNotifications(prev => 
      prev.map(notification => 
        notification.id === id 
          ? { ...notification, read: true }
          : notification
      )
    );
  }, []);

  const markAllAsRead = useCallback(() => {
    setNotifications(prev => 
      prev.map(notification => ({ ...notification, read: true }))
    );
  }, []);

  const removeNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(notification => notification.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  const connect = useCallback(async (token?: string) => {
    if (wsClient) {
      wsClient.disconnect();
    }

    const client = createWebSocketClient({
      url: wsUrl,
      token,
    });

    // 设置消息处理器
    client.on(MESSAGE_TYPES.TASK_STATUS_CHANGE, (message: WebSocketMessage) => {
      const { task_id, status, details } = message;
      addNotification({
        type: status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'info',
        title: '任务状态更新',
        message: `任务 ${task_id} 状态变更为: ${status}`,
        data: { task_id, status, details },
      });
    });

    client.on(MESSAGE_TYPES.METRICS_UPDATE, (message: WebSocketMessage) => {
      const { metrics } = message;
      addNotification({
        type: 'info',
        title: '指标更新',
        message: '新的监控指标数据已更新',
        data: metrics,
      });
    });

    client.on(MESSAGE_TYPES.ALERT, (message: WebSocketMessage) => {
      const { alert } = message;
      addNotification({
        type: alert.severity === 'high' || alert.severity === 'critical' ? 'error' : 'warning',
        title: '告警通知',
        message: alert.message || alert.title || '收到新的告警',
        persistent: alert.severity === 'critical',
        data: alert,
      });
    });

    client.on(MESSAGE_TYPES.SYSTEM_MESSAGE, (message: WebSocketMessage) => {
      addNotification({
        type: message.level === 'error' ? 'error' : message.level === 'warning' ? 'warning' : 'info',
        title: '系统消息',
        message: message.message,
      });
    });

    client.on(MESSAGE_TYPES.WELCOME, (message: WebSocketMessage) => {
      addNotification({
        type: 'success',
        title: '连接成功',
        message: '已连接到实时监控系统',
      });
    });

    // 设置连接事件处理器
    client.onConnect(() => {
      setIsConnected(true);
      console.log('WebSocket连接已建立');
    });

    client.onDisconnect(() => {
      setIsConnected(false);
      console.log('WebSocket连接已断开');
    });

    client.onError((error) => {
      console.error('WebSocket连接错误:', error);
      addNotification({
        type: 'error',
        title: '连接错误',
        message: '实时连接出现问题，正在尝试重连...',
      });
    });

    setWsClient(client);

    try {
      await client.connect();
      
      // 订阅相关主题
      client.subscribe([
        'task_updates',
        'metrics_updates', 
        'alerts',
        'system_messages'
      ]);

    } catch (error) {
      console.error('WebSocket连接失败:', error);
      addNotification({
        type: 'error',
        title: '连接失败',
        message: '无法连接到实时监控系统',
      });
    }
  }, [wsUrl, addNotification]);

  const disconnect = useCallback(() => {
    if (wsClient) {
      wsClient.disconnect();
      setWsClient(null);
      setIsConnected(false);
    }
  }, [wsClient]);

  // 计算未读通知数量
  const unreadCount = notifications.filter(n => !n.read).length;

  // 清理函数
  useEffect(() => {
    return () => {
      if (wsClient) {
        wsClient.disconnect();
      }
    };
  }, [wsClient]);

  const contextValue: NotificationContextType = {
    notifications,
    unreadCount,
    isConnected,
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAll,
    connect,
    disconnect,
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      <ToastProvider>
        {children}
        <ToastViewport />
        <NotificationToasts />
      </ToastProvider>
    </NotificationContext.Provider>
  );
}

// Toast通知组件
function NotificationToasts() {
  const { notifications, removeNotification } = useNotifications();

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-4 w-4" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4" />;
      case 'error':
        return <XCircle className="h-4 w-4" />;
      default:
        return <Info className="h-4 w-4" />;
    }
  };

  const getVariant = (type: Notification['type']) => {
    switch (type) {
      case 'error':
        return 'destructive';
      case 'warning':
        return 'warning';
      case 'success':
        return 'success';
      default:
        return 'default';
    }
  };

  return (
    <>
      {notifications
        .filter(n => !n.persistent)
        .slice(0, 3) // 只显示最新的3个非持久化通知
        .map((notification) => (
          <Toast
            key={notification.id}
            variant={getVariant(notification.type)}
            className="flex items-start space-x-3"
          >
            {getIcon(notification.type)}
            <div className="flex-1">
              <div className="font-medium">{notification.title}</div>
              <div className="text-sm opacity-90">{notification.message}</div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={() => removeNotification(notification.id)}
            >
              <X className="h-3 w-3" />
            </Button>
          </Toast>
        ))}
    </>
  );
}

// 通知中心组件
export function NotificationCenter() {
  const { 
    notifications, 
    unreadCount, 
    markAsRead, 
    markAllAsRead, 
    removeNotification,
    clearAll 
  } = useNotifications();

  const [isOpen, setIsOpen] = useState(false);

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return '刚刚';
    if (minutes < 60) return `${minutes}分钟前`;
    if (hours < 24) return `${hours}小时前`;
    return `${days}天前`;
  };

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <Badge 
            className="absolute -top-1 -right-1 h-5 w-5 p-0 text-xs"
            variant="destructive"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </Badge>
        )}
      </Button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">通知中心</h3>
              <div className="flex items-center space-x-2">
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAllAsRead}
                    className="text-xs"
                  >
                    全部已读
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAll}
                  className="text-xs"
                >
                  清空
                </Button>
              </div>
            </div>
          </div>

          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="p-4 text-center text-gray-500">
                暂无通知
              </div>
            ) : (
              notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                    !notification.read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => markAsRead(notification.id)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {notification.type === 'success' && <CheckCircle className="h-4 w-4 text-green-500" />}
                      {notification.type === 'warning' && <AlertTriangle className="h-4 w-4 text-yellow-500" />}
                      {notification.type === 'error' && <XCircle className="h-4 w-4 text-red-500" />}
                      {notification.type === 'info' && <Info className="h-4 w-4 text-blue-500" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {notification.title}
                        </p>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 ml-2"
                          onClick={(e) => {
                            e.stopPropagation();
                            removeNotification(notification.id);
                          }}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {notification.message}
                      </p>
                      <p className="text-xs text-gray-400 mt-2">
                        {formatTime(notification.timestamp)}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
