'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Play,
  Plus,
  Clock,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Activity,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import apiClient, { handleApiError } from '@/lib/api/client';

// Task response type from backend
interface TaskResponse {
  id: string;
  tenant_id: string;
  name: string;
  description?: string;
  schedule_cron: string;
  is_active: boolean;
  models: string[];
  keywords: string[];
  last_run_status?: 'pending' | 'running' | 'completed' | 'failed';
  last_run_time?: string;
  created_at: string;
  updated_at: string;
}

interface TasksListResponse {
  data: TaskResponse[];
  total: number;
  page: number;
  limit: number;
}

// Simple toast notification
interface Toast {
  message: string;
  type: 'success' | 'error' | 'info';
}

export default function GoogleTasksSimple() {
  const router = useRouter();
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggeringTaskId, setTriggeringTaskId] = useState<string | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);

  // Fetch tasks on mount
  useEffect(() => {
    fetchTasks();
  }, []);

  // Auto-hide toast after 3 seconds
  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get<TasksListResponse>('/tasks', {
        params: {
          page: 1,
          limit: 20,
          is_active: true,
        },
      });
      setTasks(response.data.data);
    } catch (err) {
      const errorMessage = handleApiError(err);
      setError(errorMessage);
      showToast(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerTask = async (taskId: string, taskName: string) => {
    try {
      setTriggeringTaskId(taskId);
      await apiClient.post(`/tasks/${taskId}/trigger`);
      showToast(`任务 "${taskName}" 已成功触发`, 'success');
      // Refresh tasks to get updated status
      await fetchTasks();
    } catch (err) {
      const errorMessage = handleApiError(err);
      showToast(`触发任务失败: ${errorMessage}`, 'error');
    } finally {
      setTriggeringTaskId(null);
    }
  };

  const showToast = (message: string, type: Toast['type']) => {
    setToast({ message, type });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <Play className="h-3 w-3" />;
      case 'completed':
        return <CheckCircle className="h-3 w-3" />;
      case 'pending':
        return <Clock className="h-3 w-3" />;
      case 'failed':
        return <AlertCircle className="h-3 w-3" />;
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

  // Calculate relative time from ISO datetime
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

  // Calculate stats from real data
  const stats = {
    total: tasks.length,
    running: tasks.filter(t => t.last_run_status === 'running').length,
    completed: tasks.filter(t => t.last_run_status === 'completed').length,
    failed: tasks.filter(t => t.last_run_status === 'failed').length,
  };

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toast && (
        <div
          className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg border ${
            toast.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-900'
              : toast.type === 'error'
              ? 'bg-red-50 border-red-200 text-red-900'
              : 'bg-blue-50 border-blue-200 text-blue-900'
          }`}
        >
          {toast.message}
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
                  总任务数
                </p>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : stats.total}
                </p>
              </div>
              <Target className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-600 dark:text-green-400">
                  运行中任务
                </p>
                <p className="text-3xl font-bold text-green-900 dark:text-green-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : stats.running}
                </p>
              </div>
              <Play className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-600 dark:text-purple-400">
                  已完成任务
                </p>
                <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : stats.completed}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-orange-600 dark:text-orange-400">
                  失败任务
                </p>
                <p className="text-3xl font-bold text-orange-900 dark:text-orange-100">
                  {loading ? <Skeleton className="h-9 w-12" /> : stats.failed}
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tasks List */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-semibold">监控任务</CardTitle>
              <CardDescription>管理和监控所有AI模型品牌监控任务</CardDescription>
            </div>
            <Button
              className="bg-blue-600 hover:bg-blue-700"
              onClick={() => router.push('/tasks/create')}
            >
              <Plus className="h-4 w-4 mr-2" />
              新建任务
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Loading State */}
          {loading && (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                  <Skeleton className="h-6 w-48 mb-3" />
                  <Skeleton className="h-4 w-full mb-3" />
                  <div className="flex space-x-4">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-3" />
              <p className="text-gray-600 mb-4">{error}</p>
              <Button onClick={fetchTasks} variant="outline">
                重试
              </Button>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && tasks.length === 0 && (
            <div className="text-center py-8">
              <Target className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 mb-4">暂无任务，创建第一个监控任务</p>
              <Button onClick={() => router.push('/tasks/create')}>
                <Plus className="h-4 w-4 mr-2" />
                新建任务
              </Button>
            </div>
          )}

          {/* Tasks List */}
          {!loading && !error && tasks.length > 0 && (
            <div className="space-y-4">
              {tasks.map((task) => (
                <div key={task.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <Link href={`/tasks/${task.id}`} className="font-semibold text-lg hover:text-blue-600 transition-colors">
                        {task.name}
                      </Link>
                      <Badge className={`${getStatusColor(task.last_run_status || 'pending')} border`}>
                        <div className="flex items-center space-x-1">
                          {getStatusIcon(task.last_run_status || 'pending')}
                          <span className="capitalize">{task.last_run_status || 'pending'}</span>
                        </div>
                      </Badge>
                      {!task.is_active && (
                        <Badge variant="outline" className="text-gray-500">
                          已暂停
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleTriggerTask(task.id, task.name)}
                        disabled={triggeringTaskId === task.id}
                      >
                        {triggeringTaskId === task.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Play className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </div>

                  {task.description && (
                    <p className="text-gray-600 dark:text-gray-400 mb-3">{task.description}</p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">模型数量</p>
                      <p className="text-sm font-semibold">{task.models.length} 个模型</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">关键词数量</p>
                      <p className="text-sm font-semibold">{task.keywords.length} 个关键词</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">上次运行</p>
                      <p className="text-sm">{getRelativeTime(task.last_run_time)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-500 mb-1">执行频率</p>
                      <p className="text-sm">{task.schedule_cron}</p>
                    </div>
                  </div>

                  {/* Keywords Display */}
                  {task.keywords.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      <span className="text-xs text-gray-500">关键词:</span>
                      {task.keywords.slice(0, 5).map((keyword) => (
                        <Badge key={keyword} variant="secondary" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                      {task.keywords.length > 5 && (
                        <Badge variant="outline" className="text-xs">
                          +{task.keywords.length - 5} 更多
                        </Badge>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
