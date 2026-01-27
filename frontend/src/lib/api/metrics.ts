/**
 * Metrics API client.
 */
import apiClient from './client';
import { DateRangeParams } from './types';

export interface SOVDataPoint {
  date: string;
  sov: number;
}

export interface SOVTrendResponse {
  keyword: string;
  model: string;
  data: SOVDataPoint[];
}

export interface AccuracyDataPoint {
  date: string;
  avg_accuracy: number;
  min_accuracy: number;
  max_accuracy: number;
}

export interface AccuracyTrendResponse {
  task_id?: string;
  data: AccuracyDataPoint[];
}

export interface ModelComparisonData {
  sov: number;
  accuracy: number;
  sentiment: number;
}

export interface ModelComparisonResponse {
  keyword: string;
  models: Record<string, ModelComparisonData>;
}

export interface DashboardOverviewResponse {
  total_tasks: number;
  active_tasks: number;
  sov_trend: SOVDataPoint[];
  accuracy_trend: AccuracyDataPoint[];
  top_brands: Array<{ brand: string; count: number }>;
  recent_alerts: Array<{ id: string; message: string; type: string }>;
  total_cost_usd: number;
  total_token_usage: number;
}

export interface ReportExportParams {
  task_id?: string;
  keyword?: string;
  format: 'csv' | 'xlsx' | 'pdf';
  start_date: string;
  end_date: string;
  metrics: string[];
}

export const metricApi = {
  /**
   * Get dashboard overview data
   */
  getDashboardOverview: async (params: DateRangeParams): Promise<DashboardOverviewResponse> => {
    const response = await apiClient.get('/dashboard/overview', { params });
    return response.data;
  },

  /**
   * Get SOV trend data
   */
  getSOVTrend: async (params: {
    keyword: string;
    model?: string;
    period?: string;
  }): Promise<SOVTrendResponse> => {
    const response = await apiClient.get('/metrics/sov', { params });
    return response.data;
  },

  /**
   * Get accuracy trend data
   */
  getAccuracyTrend: async (params: {
    task_id?: string;
    period?: string;
  }): Promise<AccuracyTrendResponse> => {
    const response = await apiClient.get('/metrics/accuracy', { params });
    return response.data;
  },

  /**
   * Get model comparison data
   */
  getModelComparison: async (params: {
    keyword: string;
    period?: string;
  }): Promise<ModelComparisonResponse> => {
    const response = await apiClient.get('/metrics/comparison', { params });
    return response.data;
  },

  /**
   * Export report
   */
  exportReport: async (params: ReportExportParams): Promise<Blob> => {
    const response = await apiClient.get('/reports/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
};
