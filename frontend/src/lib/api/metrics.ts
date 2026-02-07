/**
 * Metrics API client.
 */
import apiClient from './client';

export interface SOVDataPoint {
  date: string;
  avg_sov: number;
  count: number;
}

export interface SOVTrendResponse {
  data: SOVDataPoint[];
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
}

export interface AccuracyDataPoint {
  date: string;
  avg_accuracy: number;
  count: number;
}

export interface AccuracyTrendResponse {
  data: AccuracyDataPoint[];
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
}

export interface ModelComparisonItem {
  model_id: string;
  avg_sov: number;
  avg_accuracy: number;
  count: number;
}

export interface ModelComparisonResponse {
  data: ModelComparisonItem[];
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
}

export interface KeywordPerformanceItem {
  keyword: string;
  avg_sov: number;
  avg_accuracy: number;
  count: number;
}

export interface KeywordPerformanceResponse {
  data: KeywordPerformanceItem[];
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  limit: number;
}

export interface MetricsSummaryResponse {
  total_tasks: number;
  active_tasks: number;
  recent_runs: number;
  avg_sov: number;
  avg_accuracy: number;
  unread_alerts: number;
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
}

export const metricApi = {
  /**
   * Get metrics summary (dashboard overview)
   */
  getSummary: async (): Promise<MetricsSummaryResponse> => {
    const response = await apiClient.get('/metrics/summary');
    return response.data;
  },

  /**
   * Get SOV trend data
   */
  getSOVTrend: async (params?: {
    days?: number;
    keyword?: string;
    model?: string;
  }): Promise<SOVTrendResponse> => {
    const response = await apiClient.get('/metrics/sov-trend', { params });
    return response.data;
  },

  /**
   * Get accuracy trend data
   */
  getAccuracyTrend: async (params?: {
    days?: number;
    keyword?: string;
    model?: string;
  }): Promise<AccuracyTrendResponse> => {
    const response = await apiClient.get('/metrics/accuracy-trend', { params });
    return response.data;
  },

  /**
   * Get model comparison data
   */
  getModelComparison: async (params?: {
    days?: number;
  }): Promise<ModelComparisonResponse> => {
    const response = await apiClient.get('/metrics/model-comparison', { params });
    return response.data;
  },

  /**
   * Get keyword performance data
   */
  getKeywordPerformance: async (params?: {
    days?: number;
    limit?: number;
  }): Promise<KeywordPerformanceResponse> => {
    const response = await apiClient.get('/metrics/keyword-performance', { params });
    return response.data;
  },
};
