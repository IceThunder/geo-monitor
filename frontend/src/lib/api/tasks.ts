/**
 * Tasks API client.
 */
import apiClient from './client';
import { Task, CreateTaskDTO, UpdateTaskDTO, TaskFilter, PaginatedResponse } from './types';

export interface MetricSnapshot {
  id: string;
  model_id: string;
  keyword: string;
  sov_score: number | null;
  accuracy_score: number | null;
  sentiment_score: number | null;
  citation_rate: number | null;
  positioning_hit: boolean;
}

export interface TaskRun {
  id: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  token_usage: number;
  cost_usd: number;
  metrics: MetricSnapshot[];
}

export interface TaskRunsResponse {
  data: TaskRun[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface SearchResult {
  tasks: Task[];
  keywords: Array<{ keyword: string; task_id: string; task_name: string }>;
}

export const taskApi = {
  /**
   * Get list of tasks
   */
  getTasks: async (params?: TaskFilter): Promise<PaginatedResponse<Task>> => {
    const response = await apiClient.get('/tasks', { params });
    return response.data;
  },

  /**
   * Get a single task by ID
   */
  getTaskById: async (id: string): Promise<Task> => {
    const response = await apiClient.get(`/tasks/${id}`);
    return response.data;
  },

  /**
   * Create a new task
   */
  createTask: async (data: CreateTaskDTO): Promise<Task> => {
    const response = await apiClient.post('/tasks', data);
    return response.data;
  },

  /**
   * Update an existing task
   */
  updateTask: async (id: string, data: UpdateTaskDTO): Promise<Task> => {
    const response = await apiClient.put(`/tasks/${id}`, data);
    return response.data;
  },

  /**
   * Delete a task
   */
  deleteTask: async (id: string): Promise<void> => {
    await apiClient.delete(`/tasks/${id}`);
  },

  /**
   * Manually trigger a task execution
   */
  triggerTask: async (id: string): Promise<{ run_id: string; status: string }> => {
    const response = await apiClient.post(`/tasks/${id}/trigger`);
    return response.data;
  },

  /**
   * Get task execution history
   */
  getTaskRuns: async (taskId: string, page?: number, limit?: number): Promise<TaskRunsResponse> => {
    const response = await apiClient.get(`/tasks/${taskId}/runs`, {
      params: { page: page || 1, limit: limit || 20 },
    });
    return response.data;
  },

  /**
   * Global search across tasks and keywords
   */
  searchGlobal: async (query: string): Promise<SearchResult> => {
    const response = await apiClient.get('/search', { params: { q: query } });
    return response.data;
  },
};
