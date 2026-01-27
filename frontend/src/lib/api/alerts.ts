/**
 * Alerts API client.
 */
import apiClient from './client';
import { ApiError } from './client';

export interface Alert {
  id: string;
  tenant_id: string;
  task_id?: string;
  task_name?: string;
  alert_type: string;
  alert_message: string;
  metric_name?: string;
  metric_value?: number;
  threshold_value?: number;
  is_read: boolean;
  is_resolved: boolean;
  created_at: string;
}

export interface AlertListResponse {
  data: Alert[];
  unread_count: number;
}

export interface WebhookTestResponse {
  success: boolean;
  response_time_ms: number;
  response_status?: number;
}

export const alertApi = {
  /**
   * Get list of alerts
   */
  getAlerts: async (params?: {
    is_read?: boolean;
    alert_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<AlertListResponse> => {
    const response = await apiClient.get('/alerts', { params });
    return response.data;
  },

  /**
   * Mark an alert as read
   */
  markAsRead: async (id: string): Promise<{ success: boolean }> => {
    const response = await apiClient.put(`/alerts/${id}/read`);
    return response.data;
  },

  /**
   * Mark all alerts as read
   */
  markAllAsRead: async (): Promise<{ success: boolean }> => {
    const response = await apiClient.put('/alerts/read-all');
    return response.data;
  },

  /**
   * Get unread alert count
   */
  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const response = await apiClient.get('/alerts/unread-count');
    return response.data;
  },

  /**
   * Test webhook connectivity
   */
  testWebhook: async (webhookUrl: string): Promise<WebhookTestResponse> => {
    const response = await apiClient.post('/webhooks/test', { webhook_url: webhookUrl });
    return response.data;
  },
};
