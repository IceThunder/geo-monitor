'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Play,
  Trash2,
  Edit,
  Clock,
  CheckCircle,
  AlertCircle,
  Activity,
  Loader2,
  ChevronDown,
  ChevronUp,
  Calendar,
  Cpu,
  Tag,
  DollarSign,
  Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { taskApi, TaskRun, TaskRunsResponse } from '@/lib/api/tasks';
import { Task } from '@/lib/api/types';
import { handleApiError } from '@/lib/api/client';

export default function TaskDetailPage() {
  const params = useParams();
  const router = useRouter();
  const taskId = params.id as string;

  const [task, setTask] = useState<Task | null>(null);
  const [runs, setRuns] = useState<TaskRunsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [runsLoading, setRunsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [triggering, setTriggering] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  useEffect(() => {
    if (toast) {
      const timer = setTimeout(() => setToast(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [toast]);

  const fetchTask = useCallback(async () => {
    try {
      setLoading(true);
      const data = await taskApi.getTaskById(taskId);
      setTask(data);
    } catch (err) {
      setError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  const fetchRuns = useCallback(async () => {
    try {
      setRunsLoading(true);
      const data = await taskApi.getTaskRuns(taskId);
      setRuns(data);
    } catch (err) {
      // Runs loading failure is non-fatal
    } finally {
      setRunsLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    fetchTask();
    fetchRuns();
  }, [fetchTask, fetchRuns]);

  const handleTrigger = async () => {
    try {
      setTriggering(true);
      await taskApi.triggerTask(taskId);
      setToast({ message: '任务已触发执行', type: 'success' });
      // Refresh runs after a short delay
      setTimeout(fetchRuns, 1000);
    } catch (err) {
      setToast({ message: `触发失败: ${handleApiError(err)}`, type: 'error' });
    } finally {
      setTriggering(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('确定要删除此任务吗？此操作不可撤销。')) return;
    try {
      setDeleting(true);
      await taskApi.deleteTask(taskId);
      setToast({ message: '任务已删除', type: 'success' });
      router.push('/tasks');
    } catch (err) {
      setToast({ message: `删除失败: ${handleApiError(err)}`, type: 'error' });
      setDeleting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'partial': return 'bg-orange-100 text-orange-800 border-orange-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running': return <Play className="h-3 w-3" />;
      case 'completed': return <CheckCircle className="h-3 w-3" />;
      case 'pending': return <Clock className="h-3 w-3" />;
      case 'failed': return <AlertCircle className="h-3 w-3" />;
      default: return <Activity className="h-3 w-3" />;
    }
  };

  const formatDate = (iso?: string | null) => {
    if (!iso) return '—';
    return new Date(iso).toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const cronToReadable = (cron: string): string => {
    const parts = cron.split(' ');
    if (parts.length !== 5) return cron;
    const [min, hour, dom, mon, dow] = parts;
    if (min === '0' && hour === '0' && dom === '*' && mon === '*' && dow === '*') return '每天 00:00';
    if (min === '0' && dom === '*' && mon === '*' && dow === '*') return `每天 ${hour}:00`;
    if (dom === '*' && mon === '*' && dow === '*') return `每天 ${hour}:${min.padStart(2, '0')}`;
    return cron;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-3" />
          <p className="text-gray-600 mb-4">{error || '任务不存在'}</p>
          <Link href="/tasks">
            <Button variant="outline">返回任务列表</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg border ${
          toast.type === 'success' ? 'bg-green-50 border-green-200 text-green-900'
            : 'bg-red-50 border-red-200 text-red-900'
        }`}>
          {toast.message}
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/tasks">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              返回
            </Button>
          </Link>
          <div>
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold">{task.name}</h1>
              <Badge className={`${getStatusColor(task.last_run_status || 'pending')} border`}>
                {getStatusIcon(task.last_run_status || 'pending')}
                <span className="ml-1 capitalize">{task.last_run_status || 'pending'}</span>
              </Badge>
              {!task.is_active && (
                <Badge variant="outline" className="text-gray-500">已暂停</Badge>
              )}
            </div>
            {task.description && (
              <p className="text-gray-500 mt-1">{task.description}</p>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleTrigger}
            disabled={triggering || !task.is_active}
          >
            {triggering ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
            触发执行
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            onClick={handleDelete}
            disabled={deleting}
          >
            {deleting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Trash2 className="h-4 w-4 mr-2" />}
            删除
          </Button>
        </div>
      </div>

      {/* Basic Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-0 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Calendar className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-xs text-gray-500">执行频率</p>
                <p className="font-medium">{cronToReadable(task.schedule_cron)}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Cpu className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-xs text-gray-500">监控模型</p>
                <p className="font-medium">{task.models.length} 个</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Tag className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-xs text-gray-500">关键词</p>
                <p className="font-medium">{task.keywords.length} 个</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center space-x-3">
              <Clock className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-xs text-gray-500">最后运行</p>
                <p className="font-medium text-sm">{formatDate(task.last_run_time)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Models and Keywords */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">监控模型</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {task.models.map((model) => (
                <Badge key={model} variant="secondary">{model}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">监控关键词</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {task.keywords.map((kw) => (
                <Badge key={kw} variant="outline">{kw}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Execution History */}
      <Card className="border-0 shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">执行历史</CardTitle>
              <CardDescription>任务的执行记录和指标详情</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={fetchRuns} disabled={runsLoading}>
              <Activity className="h-4 w-4 mr-2" />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {runsLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : runs && runs.data.length > 0 ? (
            <div className="space-y-3">
              {runs.data.map((run) => (
                <div key={run.id} className="border border-gray-200 dark:border-gray-700 rounded-lg">
                  {/* Run header */}
                  <div
                    className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                    onClick={() => setExpandedRunId(expandedRunId === run.id ? null : run.id)}
                  >
                    <div className="flex items-center space-x-4">
                      <Badge className={`${getStatusColor(run.status)} border`}>
                        {getStatusIcon(run.status)}
                        <span className="ml-1 capitalize">{run.status}</span>
                      </Badge>
                      <div>
                        <p className="text-sm font-medium">{formatDate(run.started_at)}</p>
                        {run.completed_at && (
                          <p className="text-xs text-gray-500">
                            完成: {formatDate(run.completed_at)}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-right">
                        <div className="flex items-center text-xs text-gray-500">
                          <Zap className="h-3 w-3 mr-1" />
                          {run.token_usage.toLocaleString()} tokens
                        </div>
                        <div className="flex items-center text-xs text-gray-500">
                          <DollarSign className="h-3 w-3 mr-1" />
                          ${run.cost_usd.toFixed(4)}
                        </div>
                      </div>
                      <div className="text-xs text-gray-400">
                        {run.metrics.length} 指标
                      </div>
                      {expandedRunId === run.id ? (
                        <ChevronUp className="h-4 w-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-gray-400" />
                      )}
                    </div>
                  </div>

                  {/* Error message */}
                  {run.error_message && (
                    <div className="px-4 pb-2">
                      <p className="text-sm text-red-600 bg-red-50 p-2 rounded">{run.error_message}</p>
                    </div>
                  )}

                  {/* Expanded metrics */}
                  {expandedRunId === run.id && run.metrics.length > 0 && (
                    <div className="border-t border-gray-200 dark:border-gray-700 p-4">
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="text-left text-gray-500 text-xs">
                              <th className="pb-2 pr-4">模型</th>
                              <th className="pb-2 pr-4">关键词</th>
                              <th className="pb-2 pr-4">SOV</th>
                              <th className="pb-2 pr-4">准确率</th>
                              <th className="pb-2 pr-4">情感</th>
                              <th className="pb-2 pr-4">引用率</th>
                              <th className="pb-2">定位命中</th>
                            </tr>
                          </thead>
                          <tbody>
                            {run.metrics.map((m) => (
                              <tr key={m.id} className="border-t border-gray-100 dark:border-gray-800">
                                <td className="py-2 pr-4 font-medium">{m.model_id.split('/').pop()}</td>
                                <td className="py-2 pr-4 max-w-[150px] truncate">{m.keyword}</td>
                                <td className="py-2 pr-4">{m.sov_score !== null ? `${Number(m.sov_score).toFixed(1)}%` : '—'}</td>
                                <td className="py-2 pr-4">{m.accuracy_score ?? '—'}</td>
                                <td className="py-2 pr-4">{m.sentiment_score !== null ? Number(m.sentiment_score).toFixed(2) : '—'}</td>
                                <td className="py-2 pr-4">{m.citation_rate !== null ? `${Number(m.citation_rate).toFixed(1)}%` : '—'}</td>
                                <td className="py-2">
                                  {m.positioning_hit ? (
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                  ) : (
                                    <span className="text-gray-400">—</span>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {expandedRunId === run.id && run.metrics.length === 0 && (
                    <div className="border-t border-gray-200 p-4 text-center text-sm text-gray-500">
                      此次执行无指标数据
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center">
              <Clock className="h-12 w-12 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-500">暂无执行记录</p>
              <p className="text-xs text-gray-400 mt-1">点击"触发执行"开始首次监控</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
