/**
 * Analytics Page
 * 分析报告页面
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import {
  TrendingUp,
  BarChart3,
  PieChart,
  Download,
  Filter,
  Calendar,
  Target,
  Users,
  MessageSquare,
  Loader2,
  AlertCircle
} from 'lucide-react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import apiClient, { handleApiError } from '@/lib/api/client';

// Types
interface MetricsSummary {
  total_tasks: number;
  active_tasks: number;
  recent_runs: number;
  avg_sov: number;
  avg_accuracy: number;
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
}

interface TrendDataPoint {
  date: string;
  avg_sov?: number;
  avg_accuracy?: number;
  count: number;
}

interface ModelComparisonData {
  model_name: string;
  avg_sov: number;
  avg_accuracy: number;
  count: number;
}

interface KeywordPerformanceData {
  keyword: string;
  avg_sov: number;
  avg_accuracy: number;
  count: number;
}

const timeRangeOptions = [
  { label: '最近7天', value: '7' },
  { label: '最近30天', value: '30' },
  { label: '最近90天', value: '90' },
];

export default function AnalyticsPage() {
  // State
  const [timeRange, setTimeRange] = useState('30');
  const [keywordFilter, setKeywordFilter] = useState('');
  const [modelFilter, setModelFilter] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  // Data state
  const [summary, setSummary] = useState<MetricsSummary | null>(null);
  const [sovTrend, setSovTrend] = useState<TrendDataPoint[]>([]);
  const [accuracyTrend, setAccuracyTrend] = useState<TrendDataPoint[]>([]);
  const [modelComparison, setModelComparison] = useState<ModelComparisonData[]>([]);
  const [keywordPerformance, setKeywordPerformance] = useState<KeywordPerformanceData[]>([]);

  // Loading states
  const [loadingSummary, setLoadingSummary] = useState(true);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [loadingModels, setLoadingModels] = useState(true);
  const [loadingKeywords, setLoadingKeywords] = useState(true);

  // Error states
  const [error, setError] = useState<string | null>(null);

  // Fetch summary data
  const fetchSummary = async () => {
    setLoadingSummary(true);
    setError(null);
    try {
      const response = await apiClient.get<MetricsSummary>('/metrics/summary');
      setSummary(response.data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoadingSummary(false);
    }
  };

  // Fetch trend data
  const fetchTrends = async () => {
    setLoadingTrends(true);
    setError(null);
    try {
      const params: Record<string, any> = { days: parseInt(timeRange) };
      if (keywordFilter) params.keyword = keywordFilter;
      if (modelFilter) params.model = modelFilter;

      const [sovResponse, accuracyResponse] = await Promise.all([
        apiClient.get('/metrics/sov-trend', { params }),
        apiClient.get('/metrics/accuracy-trend', { params }),
      ]);

      setSovTrend(sovResponse.data.data);
      setAccuracyTrend(accuracyResponse.data.data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoadingTrends(false);
    }
  };

  // Fetch model comparison data
  const fetchModelComparison = async () => {
    setLoadingModels(true);
    setError(null);
    try {
      const response = await apiClient.get('/metrics/model-comparison', {
        params: { days: parseInt(timeRange) },
      });
      setModelComparison(response.data.data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoadingModels(false);
    }
  };

  // Fetch keyword performance data
  const fetchKeywordPerformance = async () => {
    setLoadingKeywords(true);
    setError(null);
    try {
      const response = await apiClient.get('/metrics/keyword-performance', {
        params: { days: parseInt(timeRange), limit: 20 },
      });
      setKeywordPerformance(response.data.data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoadingKeywords(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchSummary();
    fetchTrends();
    fetchModelComparison();
    fetchKeywordPerformance();
  }, []);

  // Reload when filters change
  useEffect(() => {
    fetchTrends();
    fetchModelComparison();
    fetchKeywordPerformance();
  }, [timeRange]);

  // Apply filters
  const handleApplyFilters = () => {
    fetchTrends();
    setShowFilters(false);
  };

  // Export to CSV
  const handleExport = () => {
    try {
      // Prepare CSV data
      const csvRows: string[] = [];

      // Header
      csvRows.push('Analytics Report');
      csvRows.push(`Generated: ${new Date().toISOString()}`);
      csvRows.push(`Time Range: ${timeRange} days`);
      csvRows.push('');

      // Summary
      if (summary) {
        csvRows.push('Summary');
        csvRows.push('Metric,Value');
        csvRows.push(`Total Tasks,${summary.total_tasks}`);
        csvRows.push(`Active Tasks,${summary.active_tasks}`);
        csvRows.push(`Recent Runs,${summary.recent_runs}`);
        csvRows.push(`Average SOV,${summary.avg_sov.toFixed(2)}`);
        csvRows.push(`Average Accuracy,${summary.avg_accuracy.toFixed(2)}`);
        csvRows.push('');
      }

      // SOV Trend
      if (sovTrend.length > 0) {
        csvRows.push('SOV Trend');
        csvRows.push('Date,Average SOV,Count');
        sovTrend.forEach(row => {
          csvRows.push(`${row.date},${row.avg_sov?.toFixed(2) || 0},${row.count}`);
        });
        csvRows.push('');
      }

      // Model Comparison
      if (modelComparison.length > 0) {
        csvRows.push('Model Comparison');
        csvRows.push('Model,Average SOV,Average Accuracy,Count');
        modelComparison.forEach(row => {
          csvRows.push(`${row.model_name},${row.avg_sov.toFixed(2)},${row.avg_accuracy.toFixed(2)},${row.count}`);
        });
        csvRows.push('');
      }

      // Keyword Performance
      if (keywordPerformance.length > 0) {
        csvRows.push('Keyword Performance');
        csvRows.push('Keyword,Average SOV,Average Accuracy,Count');
        keywordPerformance.forEach(row => {
          csvRows.push(`${row.keyword},${row.avg_sov.toFixed(2)},${row.avg_accuracy.toFixed(2)},${row.count}`);
        });
      }

      // Create blob and download
      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      link.setAttribute('href', url);
      link.setAttribute('download', `analytics-report-${new Date().toISOString().split('T')[0]}.csv`);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Error exporting CSV:', err);
      setError('Failed to export data');
    }
  };

  // Loading skeleton component
  const LoadingSkeleton = () => (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-gray-200 rounded w-1/4"></div>
      <div className="h-64 bg-gray-200 rounded"></div>
    </div>
  );

  // Error alert component
  const ErrorAlert = ({ message }: { message: string }) => (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
      <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
      <div>
        <p className="text-sm font-medium text-red-800">Error</p>
        <p className="text-sm text-red-700">{message}</p>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Page header and controls */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">分析报告</h1>
          <p className="text-gray-600 mt-1">深入分析品牌表现和市场趋势</p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeRangeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            筛选
          </Button>

          <Button
            variant="outline"
            onClick={handleExport}
            disabled={loadingSummary}
          >
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* Filter panel */}
      {showFilters && (
        <Card>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  关键词过滤
                </label>
                <Input
                  placeholder="输入关键词..."
                  value={keywordFilter}
                  onChange={(e) => setKeywordFilter(e.target.value)}
                />
              </div>
              <div>
                <label className="text-sm font-medium text-gray-700 mb-2 block">
                  模型过滤
                </label>
                <Input
                  placeholder="输入模型名称..."
                  value={modelFilter}
                  onChange={(e) => setModelFilter(e.target.value)}
                />
              </div>
              <div className="flex items-end">
                <Button onClick={handleApplyFilters} className="w-full">
                  应用筛选
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error display */}
      {error && <ErrorAlert message={error} />}

      {/* Key metrics overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            {loadingSummary ? (
              <div className="flex items-center justify-center h-24">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">总任务数</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary?.total_tasks || 0}
                  </p>
                  <p className="text-sm text-gray-500">任务总数</p>
                </div>
                <MessageSquare className="h-8 w-8 text-blue-500" />
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            {loadingSummary ? (
              <div className="flex items-center justify-center h-24">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">活跃任务</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary?.active_tasks || 0}
                  </p>
                  <p className="text-sm text-green-600">当前活跃</p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-500" />
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            {loadingSummary ? (
              <div className="flex items-center justify-center h-24">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">平均SOV分数</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary?.avg_sov.toFixed(2) || '0.00'}
                  </p>
                  <p className="text-sm text-gray-500">最近30天</p>
                </div>
                <Target className="h-8 w-8 text-purple-500" />
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            {loadingSummary ? (
              <div className="flex items-center justify-center h-24">
                <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              </div>
            ) : (
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">最近执行次数</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {summary?.recent_runs || 0}
                  </p>
                  <p className="text-sm text-gray-500">最近30天</p>
                </div>
                <Users className="h-8 w-8 text-orange-500" />
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Detailed analysis tabs */}
      <Tabs defaultValue="trends" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
          <TabsTrigger value="competitors">竞品对比</TabsTrigger>
          <TabsTrigger value="keywords">关键词分析</TabsTrigger>
          <TabsTrigger value="channels">渠道分析</TabsTrigger>
        </TabsList>

        {/* Trends Analysis */}
        <TabsContent value="trends" className="space-y-6">
          {loadingTrends ? (
            <LoadingSkeleton />
          ) : (
            <>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <TrendingUp className="h-5 w-5 mr-2" />
                      SOV趋势
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {sovTrend.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={sovTrend}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="date"
                            tickFormatter={(value) => new Date(value).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis />
                          <Tooltip
                            labelFormatter={(value) => new Date(value).toLocaleDateString('zh-CN')}
                            formatter={(value: any) => [value.toFixed(2), 'SOV分数']}
                          />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="avg_sov"
                            stroke="#3b82f6"
                            name="平均SOV"
                            strokeWidth={2}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-80 flex items-center justify-center text-gray-500">
                        暂无数据
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center">
                      <Target className="h-5 w-5 mr-2" />
                      准确性趋势
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {accuracyTrend.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={accuracyTrend}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis
                            dataKey="date"
                            tickFormatter={(value) => new Date(value).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })}
                          />
                          <YAxis />
                          <Tooltip
                            labelFormatter={(value) => new Date(value).toLocaleDateString('zh-CN')}
                            formatter={(value: any) => [value.toFixed(2), '准确性分数']}
                          />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="avg_accuracy"
                            stroke="#10b981"
                            name="平均准确性"
                            strokeWidth={2}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-80 flex items-center justify-center text-gray-500">
                        暂无数据
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>数据概览</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <TrendingUp className="h-5 w-5 text-blue-600" />
                        <p className="font-medium text-blue-900">SOV趋势</p>
                      </div>
                      <p className="text-2xl font-bold text-blue-900">
                        {sovTrend.length > 0 && sovTrend[sovTrend.length - 1]?.avg_sov != null
                          ? sovTrend[sovTrend.length - 1]?.avg_sov?.toFixed(2)
                          : '0.00'}
                      </p>
                      <p className="text-sm text-blue-700">最新平均值</p>
                    </div>

                    <div className="p-4 bg-green-50 rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <Target className="h-5 w-5 text-green-600" />
                        <p className="font-medium text-green-900">准确性趋势</p>
                      </div>
                      <p className="text-2xl font-bold text-green-900">
                        {accuracyTrend.length > 0 && accuracyTrend[accuracyTrend.length - 1]?.avg_accuracy != null
                          ? accuracyTrend[accuracyTrend.length - 1]?.avg_accuracy?.toFixed(2)
                          : '0.00'}
                      </p>
                      <p className="text-sm text-green-700">最新平均值</p>
                    </div>

                    <div className="p-4 bg-purple-50 rounded-lg">
                      <div className="flex items-center space-x-2 mb-2">
                        <BarChart3 className="h-5 w-5 text-purple-600" />
                        <p className="font-medium text-purple-900">数据点</p>
                      </div>
                      <p className="text-2xl font-bold text-purple-900">
                        {sovTrend.length}
                      </p>
                      <p className="text-sm text-purple-700">时间段内</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Model Comparison */}
        <TabsContent value="competitors" className="space-y-6">
          {loadingModels ? (
            <LoadingSkeleton />
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>模型对比分析</CardTitle>
                </CardHeader>
                <CardContent>
                  {modelComparison.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={modelComparison}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="model_name" />
                        <YAxis />
                        <Tooltip formatter={(value: any) => value.toFixed(2)} />
                        <Legend />
                        <Bar dataKey="avg_sov" fill="#3b82f6" name="平均SOV" />
                        <Bar dataKey="avg_accuracy" fill="#10b981" name="平均准确性" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-80 flex items-center justify-center text-gray-500">
                      暂无数据
                    </div>
                  )}
                </CardContent>
              </Card>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>模型性能排名</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {modelComparison
                        .sort((a, b) => b.avg_sov - a.avg_sov)
                        .slice(0, 5)
                        .map((model, index) => (
                          <div
                            key={model.model_name}
                            className={`flex items-center justify-between p-3 rounded-lg ${
                              index === 0 ? 'bg-blue-50' : 'bg-gray-50'
                            }`}
                          >
                            <div className="flex items-center space-x-3">
                              <Badge
                                className={index === 0 ? 'bg-blue-600' : ''}
                                variant={index === 0 ? 'default' : 'secondary'}
                              >
                                {index + 1}
                              </Badge>
                              <span className="font-medium">{model.model_name}</span>
                            </div>
                            <span
                              className={`font-semibold ${
                                index === 0 ? 'text-blue-600' : 'text-gray-600'
                              }`}
                            >
                              {model.avg_sov.toFixed(2)}
                            </span>
                          </div>
                        ))}
                      {modelComparison.length === 0 && (
                        <p className="text-center text-gray-500 py-8">暂无数据</p>
                      )}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>模型统计</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {modelComparison.slice(0, 5).map((model) => (
                        <div key={model.model_name} className="space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="text-sm font-medium text-gray-700">
                              {model.model_name}
                            </span>
                            <span className="text-sm text-gray-600">
                              {model.count} 次执行
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="bg-blue-50 p-2 rounded">
                              <p className="text-gray-600">SOV</p>
                              <p className="font-semibold text-blue-600">
                                {model.avg_sov.toFixed(2)}
                              </p>
                            </div>
                            <div className="bg-green-50 p-2 rounded">
                              <p className="text-gray-600">准确性</p>
                              <p className="font-semibold text-green-600">
                                {model.avg_accuracy.toFixed(2)}
                              </p>
                            </div>
                          </div>
                        </div>
                      ))}
                      {modelComparison.length === 0 && (
                        <p className="text-center text-gray-500 py-8">暂无数据</p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </TabsContent>

        {/* Keyword Analysis */}
        <TabsContent value="keywords" className="space-y-6">
          {loadingKeywords ? (
            <LoadingSkeleton />
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>关键词性能分析</CardTitle>
                </CardHeader>
                <CardContent>
                  {keywordPerformance.length > 0 ? (
                    <ResponsiveContainer width="100%" height={400}>
                      <BarChart data={keywordPerformance.slice(0, 10)}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                          dataKey="keyword"
                          angle={-45}
                          textAnchor="end"
                          height={100}
                        />
                        <YAxis />
                        <Tooltip formatter={(value: any) => value.toFixed(2)} />
                        <Legend />
                        <Bar dataKey="avg_sov" fill="#3b82f6" name="平均SOV" />
                        <Bar dataKey="avg_accuracy" fill="#10b981" name="平均准确性" />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="h-80 flex items-center justify-center text-gray-500">
                      暂无数据
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>关键词详细表现</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-3 px-2">排名</th>
                          <th className="text-left py-3 px-2">关键词</th>
                          <th className="text-right py-3 px-2">执行次数</th>
                          <th className="text-right py-3 px-2">平均SOV</th>
                          <th className="text-right py-3 px-2">平均准确性</th>
                          <th className="text-right py-3 px-2">表现</th>
                        </tr>
                      </thead>
                      <tbody>
                        {keywordPerformance.map((item, index) => (
                          <tr key={index} className="border-b hover:bg-gray-50">
                            <td className="py-3 px-2">
                              <Badge variant="secondary">{index + 1}</Badge>
                            </td>
                            <td className="py-3 px-2 font-medium">{item.keyword}</td>
                            <td className="text-right py-3 px-2">
                              {item.count.toLocaleString()}
                            </td>
                            <td className="text-right py-3 px-2">
                              <span className="font-semibold text-blue-600">
                                {item.avg_sov.toFixed(2)}
                              </span>
                            </td>
                            <td className="text-right py-3 px-2">
                              <span className="font-semibold text-green-600">
                                {item.avg_accuracy.toFixed(2)}
                              </span>
                            </td>
                            <td className="text-right py-3 px-2">
                              <Badge
                                variant={item.avg_sov > 50 ? 'default' : 'secondary'}
                                className={item.avg_sov > 50 ? 'bg-green-600' : ''}
                              >
                                {item.avg_sov > 50 ? '优秀' : '良好'}
                              </Badge>
                            </td>
                          </tr>
                        ))}
                        {keywordPerformance.length === 0 && (
                          <tr>
                            <td colSpan={6} className="text-center py-8 text-gray-500">
                              暂无数据
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        {/* Channel Analysis - Coming Soon */}
        <TabsContent value="channels" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>渠道分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-96 flex flex-col items-center justify-center text-center">
                <PieChart className="h-16 w-16 text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold text-gray-700 mb-2">
                  渠道分析功能开发中
                </h3>
                <p className="text-gray-500 max-w-md">
                  渠道维度的数据分析功能即将上线，将支持微博、微信、抖音、小红书等多个平台的数据对比分析。
                </p>
                <div className="mt-6 p-4 bg-blue-50 rounded-lg max-w-md">
                  <p className="text-sm text-blue-800 font-medium mb-2">即将推出的功能</p>
                  <ul className="text-xs text-blue-700 text-left space-y-1">
                    <li>• 多渠道声量对比</li>
                    <li>• 渠道互动率分析</li>
                    <li>• 渠道情感趋势</li>
                    <li>• 渠道表现排名</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
