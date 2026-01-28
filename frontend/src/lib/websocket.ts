/**
 * WebSocket客户端服务
 * 处理与后端的实时通信
 */

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

export interface WebSocketConfig {
  url: string;
  token?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export type MessageHandler = (message: WebSocketMessage) => void;
export type ConnectionHandler = () => void;
export type ErrorHandler = (error: Event) => void;

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private connectionHandlers: ConnectionHandler[] = [];
  private disconnectionHandlers: ConnectionHandler[] = [];
  private errorHandlers: ErrorHandler[] = [];
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;
  private isManualClose = false;

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      ...config,
    };
  }

  /**
   * 连接WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('连接正在进行中'));
        return;
      }

      this.isConnecting = true;
      this.isManualClose = false;

      try {
        const url = this.config.token 
          ? `${this.config.url}?token=${this.config.token}`
          : this.config.url;
        
        this.ws = new WebSocket(url);

        this.ws.onopen = () => {
          console.log('WebSocket连接已建立');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.connectionHandlers.forEach(handler => handler());
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('解析WebSocket消息失败:', error);
          }
        };

        this.ws.onclose = () => {
          console.log('WebSocket连接已关闭');
          this.isConnecting = false;
          this.disconnectionHandlers.forEach(handler => handler());
          
          if (!this.isManualClose) {
            this.scheduleReconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket错误:', error);
          this.isConnecting = false;
          this.errorHandlers.forEach(handler => handler(error));
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * 断开WebSocket连接
   */
  disconnect(): void {
    this.isManualClose = true;
    
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 发送消息
   */
  send(message: WebSocketMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket未连接，无法发送消息');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('发送WebSocket消息失败:', error);
      return false;
    }
  }

  /**
   * 订阅消息类型
   */
  on(messageType: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * 取消订阅消息类型
   */
  off(messageType: string, handler?: MessageHandler): void {
    if (!this.messageHandlers.has(messageType)) {
      return;
    }

    if (handler) {
      const handlers = this.messageHandlers.get(messageType)!;
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    } else {
      this.messageHandlers.delete(messageType);
    }
  }

  /**
   * 监听连接事件
   */
  onConnect(handler: ConnectionHandler): void {
    this.connectionHandlers.push(handler);
  }

  /**
   * 监听断开连接事件
   */
  onDisconnect(handler: ConnectionHandler): void {
    this.disconnectionHandlers.push(handler);
  }

  /**
   * 监听错误事件
   */
  onError(handler: ErrorHandler): void {
    this.errorHandlers.push(handler);
  }

  /**
   * 获取连接状态
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * 发送心跳
   */
  ping(): void {
    this.send({ type: 'ping' });
  }

  /**
   * 订阅主题
   */
  subscribe(topics: string[]): void {
    this.send({
      type: 'subscribe',
      topics,
    });
  }

  /**
   * 处理接收到的消息
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('处理WebSocket消息时出错:', error);
        }
      });
    }

    // 处理通用消息
    if (message.type === 'pong') {
      console.log('收到心跳响应');
    }
  }

  /**
   * 安排重连
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.config.maxReconnectAttempts!) {
      console.error('达到最大重连次数，停止重连');
      return;
    }

    this.reconnectAttempts++;
    const delay = this.config.reconnectInterval! * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`${delay}ms后尝试第${this.reconnectAttempts}次重连`);
    
    this.reconnectTimer = setTimeout(() => {
      this.connect().catch(error => {
        console.error('重连失败:', error);
      });
    }, delay);
  }
}

// 创建全局WebSocket客户端实例
let wsClient: WebSocketClient | null = null;

export function createWebSocketClient(config: WebSocketConfig): WebSocketClient {
  if (wsClient) {
    wsClient.disconnect();
  }
  
  wsClient = new WebSocketClient(config);
  return wsClient;
}

export function getWebSocketClient(): WebSocketClient | null {
  return wsClient;
}

// 预定义的消息类型
export const MESSAGE_TYPES = {
  TASK_STATUS_CHANGE: 'task_status_change',
  METRICS_UPDATE: 'metrics_update',
  ALERT: 'alert',
  SYSTEM_MESSAGE: 'system_message',
  CONNECTION_ESTABLISHED: 'connection_established',
  WELCOME: 'welcome',
  PING: 'ping',
  PONG: 'pong',
  SUBSCRIBE: 'subscribe',
  SUBSCRIPTION_CONFIRMED: 'subscription_confirmed',
} as const;
