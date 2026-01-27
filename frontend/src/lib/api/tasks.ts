/**
 * Tasks API client.
 */
import apiClient from './client';
import { Task, CreateTaskDTO, UpdateTaskDTO, TaskFilter, PaginatedResponse } from './types';

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
};
