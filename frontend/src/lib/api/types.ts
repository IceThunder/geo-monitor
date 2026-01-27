/**
 * Common API types.
 */

// Pagination
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

// Date range
export interface DateRangeParams {
  start_date: string;
  end_date: string;
}

// Task types
export interface Task {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  schedule_cron: string;
  is_active: boolean;
  prompt_template_id?: string;
  created_at: string;
  updated_at: string;
  models: string[];
  keywords: string[];
  last_run_status?: string;
  last_run_time?: string;
}

export interface CreateTaskDTO {
  name: string;
  description?: string;
  schedule_cron: string;
  models: string[];
  keywords: string[];
  prompt_template_id?: string;
}

export interface UpdateTaskDTO {
  name?: string;
  description?: string;
  schedule_cron?: string;
  is_active?: boolean;
  models?: string[];
  keywords?: string[];
  prompt_template_id?: string;
}

export interface TaskFilter {
  page?: number;
  limit?: number;
  is_active?: boolean;
  search?: string;
}

// Alert types
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

// Config types
export interface TenantConfig {
  openrouter_api_key_set: boolean;
  webhook_url?: string;
  alert_threshold_accuracy: number;
  alert_threshold_sentiment: number;
}
