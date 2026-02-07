'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  TrendingUp,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  Play,
  Target,
  Zap,
  MessageSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { metricApi, MetricsSummaryResponse, SOVTrendResponse, KeywordPerformanceResponse } from '@/lib/api/metrics';
import { taskApi } from '@/lib/api/tasks';
import { Task } from '@/lib/api/types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function GoogleDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState('7d');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Data states
  const [summary, setSummary] = useState<MetricsSummaryResponse | null>(null);
  const [sovTrend, setSovTrend] = useState<SOVTrendResponse | null>(null);
  const [keywordPerf, setKeywordPerf] = useState<KeywordPerformanceResponse | null>(null);
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);

  const periodToDays = (period: string): number => {
    switch (period) {
      case '1d': return 1;
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      default: return 7;
    }
  };

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const days = periodToDays(selectedPeriod);

      const [summaryRes, sovRes, kwRes, tasksRes] = await Promise.allSettled([
        metricApi.getSummary(),
        metricApi.getSOVTrend({ days }),
        metricApi.getKeywordPerformance({ days, limit: 10 }),
        taskApi.getTasks({ page: 1, limit: 5 }),
      ]);

      if (summaryRes.status === 'fulfilled') setSummary(summaryRes.value);
      if (sovRes.status === 'fulfilled') setSovTrend(sovRes.value);
      if (kwRes.status === 'fulfilled') setKeywordPerf(kwRes.value);
      if (tasksRes.status === 'fulfilled') setRecentTasks(tasksRes.value.data);
    } catch (err) {
      setError('加载数据失败');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [selectedPeriod]);

  useEffect(() => {
    setLoading(true);
    fetchData();
  }, [fetchData]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    fetchData();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Play className="h-3 w-3" />;
      case 'completed': return <CheckCircle className="h-3 w-3" />;
      case 'pending': return <Clock className="h-3 w-3" />;
      case 'failed': return <AlertTriangle className="h-3 w-3" />;
      default: return <Activity className="h-3 w-3" />;
    }
  };

  const getRelativeTime = (isoDate?: string): string => {
    if (!isoDate) return '从未运行';
    const now = new Date();
    const past = new Date(isoDate);
    const diffMs = now.getTime() - past.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    if (diffHours < 24) return `${diffHours}小时前`;
    return `${diffDays}天前`;
  };

  if (error && !summary) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-3" />
          <p className="text-gray-600 mb-4">{error}</p>
          <Button onClick={handleRefresh} variant="outline">重试</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 页面头部操作栏 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1d">今天</SelectItem>
              <SelectItem value="7d">7天</SelectItem>
              <SelectItem value="30d">30天</SelectItem>
              <SelectItem value="90d">90天</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            刷新
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <Link href="/tasks/create">
            <Button size="sm">
              <Activity className="h-4 w-4 mr-2" />
              新建任务
            </Button>
          </Link>
        </div>
      </div>

      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-400">总任务数</p>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : summary?.total_tasks ?? 0}
                </p>
                <p className="text-sm text-blue-600 dark:text-blue-400 flex items-center mt-1">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  活跃: {summary?.active_tasks ?? 0}
                </p>
              </div>
              <div className="h-12 w-12 bg-blue-600 rounded-xl flex items-center justify-center">
                <Activity className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">近期运行</p>
                <p className="text-3xl font-bold text-green-900 dark:text-green-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : summary?.recent_runs ?? 0}
                </p>
                <p className="text-sm text-green-600 dark:text-green-400 flex items-center mt-1">
                  <Play className="h-4 w-4 mr-1" />
                  过去30天
                </p>
              </div>
              <div className="h-12 w-12 bg-green-600 rounded-xl flex items-center justify-center">
                <Zap className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600 dark:text-purple-400">平均准确率</p>
                <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : (
                    summary?.avg_accuracy ? `${summary.avg_accuracy.toFixed(1)}` : '—'
                  )}
                </p>
                <p className="text-sm text-purple-600 dark:text-purple-400 flex items-center mt-1">
                  <Target className="h-4 w-4 mr-1" />
                  评分 1-10
                </p>
              </div>
              <div className="h-12 w-12 bg-purple-600 rounded-xl flex items-center justify-center">
                <Target className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600 dark:text-orange-400">待处理告警</p>
                <p className="text-3xl font-bold text-orange-900 dark:text-orange-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : summary?.unread_alerts ?? 0}
                </p>
                <p className="text-sm text-orange-600 dark:text-orange-400 flex items-center mt-1">
                  <AlertTriangle className="h-4 w-4 mr-1" />
                  需要关注
                </p>
              </div>
              <div className="h-12 w-12 bg-orange-600 rounded-xl flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-white" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 主要内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧：趋势图表 */}
        <div className="lg:col-span-2 space-y-6">
          {/* SOV趋势图 */}
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-semibold">SOV 趋势</CardTitle>
                  <CardDescription>过去{periodToDays(selectedPeriod)}天的声量占有率变化</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-80 w-full" />
              ) : sovTrend && sovTrend.data.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <LineChart data={sovTrend.data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(val) => val.slice(5)}
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip
                      formatter={(value: number) => [value.toFixed(2), 'SOV']}
                      labelFormatter={(label) => `日期: ${label}`}
                    />
                    <Line
                      type="monotone"
                      dataKey="avg_sov"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                      activeDot={{ r: 5 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-80 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-center">
                    <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">暂无 SOV 趋势数据</p>
                    <p className="text-xs text-gray-400 mt-1">执行监控任务后将展示趋势图</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 关键词性能 */}
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg font-semibold">关键词性能</CardTitle>
                  <CardDescription>热门关键词的 SOV 和准确率</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full" />)}
                </div>
              ) : keywordPerf && keywordPerf.data.length > 0 ? (
                <div className="space-y-4">
                  {keywordPerf.data.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                          <MessageSquare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <p className="font-medium">{item.keyword}</p>
                          <p className="text-sm text-gray-500">{item.count} 次采集</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-6">
                        <div className="text-right">
                          <p className="text-xs text-gray-500">SOV</p>
                          <p className="text-sm font-medium">{item.avg_sov.toFixed(1)}%</p>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-500">准确率</p>
                          <p className="text-sm font-medium">{item.avg_accuracy.toFixed(1)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <MessageSquare className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">暂无关键词性能数据</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* 右侧：任务和告警 */}
        <div className="space-y-6">
          {/* 最近任务 */}
          <Card className="border-0 shadow-sm">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-semibold">最近任务</CardTitle>
              <CardDescription>当前运行和最近的任务</CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="p-4 border border-gray-200 rounded-lg">
                      <Skeleton className="h-5 w-32 mb-2" />
                      <Skeleton className="h-4 w-full mb-2" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                  ))}
                </div>
              ) : recentTasks.length > 0 ? (
                <div className="space-y-4">
                  {recentTasks.map((task) => (
                    <Link key={task.id} href={`/tasks/${task.id}`} className="block">
                      <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-sm truncate">{task.name}</h4>
                          <Badge className={`${getStatusColor(task.last_run_status || 'pending')} text-xs border`}>
                            {getStatusIcon(task.last_run_status || 'pending')}
                            <span className="ml-1 capitalize">{task.last_run_status || 'pending'}</span>
                          </Badge>
                        </div>
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>最后运行: {getRelativeTime(task.last_run_time)}</span>
                          <span>{task.keywords.length} 个关键词</span>
                        </div>
                        {task.keywords.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {task.keywords.slice(0, 3).map((kw) => (
                              <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
                            ))}
                            {task.keywords.length > 3 && (
                              <Badge variant="outline" className="text-xs">+{task.keywords.length - 3}</Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="py-8 text-center">
                  <Target className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-500">暂无任务</p>
                  <Link href="/tasks/create">
                    <Button size="sm" className="mt-3">新建任务</Button>
                  </Link>
                </div>
              )}

              <Link href="/tasks">
                <Button variant="outline" className="w-full mt-4" size="sm">
                  查看所有任务
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
