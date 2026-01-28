/**
 * Task Table Component
 * 用于显示监控任务列表的表格组件
 */
import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TaskStatusBadge, type TaskStatus } from '@/components/dashboard/task-status-badge';
import { cn } from '@/lib/utils';
import { 
  Play, 
  Pause, 
  Settings, 
  MoreHorizontal,
  Calendar,
  Target
} from 'lucide-react';

export interface Task {
  id: string;
  name: string;
  description?: string;
  status: TaskStatus;
  schedule: string;
  isActive: boolean;
  lastRun?: string;
  nextRun?: string;
  successRate?: number;
  totalCost?: number;
  models: string[];
  keywords: string[];
  createdAt: string;
}

interface TaskTableProps {
  tasks: Task[];
  onTaskAction?: (taskId: string, action: 'start' | 'pause' | 'edit' | 'delete') => void;
  loading?: boolean;
  className?: string;
}

export function TaskTable({ 
  tasks, 
  onTaskAction,
  loading = false,
  className 
}: TaskTableProps) {
  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return '-';
    return `¥${amount.toFixed(2)}`;
  };

  const getSuccessRateColor = (rate?: number) => {
    if (!rate) return 'text-gray-500';
    if (rate >= 90) return 'text-green-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className={cn('rounded-md border', className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[200px]">任务名称</TableHead>
            <TableHead>状态</TableHead>
            <TableHead>调度</TableHead>
            <TableHead>模型</TableHead>
            <TableHead>关键词</TableHead>
            <TableHead>成功率</TableHead>
            <TableHead>成本</TableHead>
            <TableHead>最后运行</TableHead>
            <TableHead>下次运行</TableHead>
            <TableHead className="text-right">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {loading ? (
            // 加载状态
            Array.from({ length: 3 }).map((_, index) => (
              <TableRow key={index}>
                <TableCell colSpan={10}>
                  <div className="flex items-center space-x-2">
                    <div className="h-4 w-4 bg-gray-200 rounded animate-pulse" />
                    <div className="h-4 w-32 bg-gray-200 rounded animate-pulse" />
                  </div>
                </TableCell>
              </TableRow>
            ))
          ) : tasks.length === 0 ? (
            // 空状态
            <TableRow>
              <TableCell colSpan={10} className="text-center py-8 text-gray-500">
                暂无监控任务
              </TableCell>
            </TableRow>
          ) : (
            // 任务列表
            tasks.map((task) => (
              <TableRow key={task.id} className="hover:bg-gray-50">
                <TableCell className="font-medium">
                  <div>
                    <div className="font-semibold text-gray-900">{task.name}</div>
                    {task.description && (
                      <div className="text-sm text-gray-500 truncate max-w-[180px]">
                        {task.description}
                      </div>
                    )}
                  </div>
                </TableCell>
                
                <TableCell>
                  <div className="flex items-center space-x-2">
                    <TaskStatusBadge status={task.status} />
                    {!task.isActive && (
                      <Badge variant="secondary" className="text-xs">
                        已禁用
                      </Badge>
                    )}
                  </div>
                </TableCell>
                
                <TableCell>
                  <div className="flex items-center space-x-1 text-sm text-gray-600">
                    <Calendar className="h-3 w-3" />
                    <span>{task.schedule}</span>
                  </div>
                </TableCell>
                
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {task.models.slice(0, 2).map((model) => (
                      <Badge key={model} variant="outline" className="text-xs">
                        {model}
                      </Badge>
                    ))}
                    {task.models.length > 2 && (
                      <Badge variant="outline" className="text-xs">
                        +{task.models.length - 2}
                      </Badge>
                    )}
                  </div>
                </TableCell>
                
                <TableCell>
                  <div className="flex items-center space-x-1 text-sm">
                    <Target className="h-3 w-3 text-gray-400" />
                    <span className="text-gray-600">{task.keywords.length} 个</span>
                  </div>
                </TableCell>
                
                <TableCell>
                  <span className={cn('font-medium', getSuccessRateColor(task.successRate))}>
                    {task.successRate ? `${task.successRate}%` : '-'}
                  </span>
                </TableCell>
                
                <TableCell>
                  <span className="text-gray-900 font-medium">
                    {formatCurrency(task.totalCost)}
                  </span>
                </TableCell>
                
                <TableCell>
                  <span className="text-sm text-gray-600">
                    {formatDate(task.lastRun)}
                  </span>
                </TableCell>
                
                <TableCell>
                  <span className="text-sm text-gray-600">
                    {formatDate(task.nextRun)}
                  </span>
                </TableCell>
                
                <TableCell className="text-right">
                  <div className="flex items-center justify-end space-x-1">
                    {task.status === 'running' ? (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onTaskAction?.(task.id, 'pause')}
                        className="h-8 w-8 p-0"
                      >
                        <Pause className="h-4 w-4" />
                      </Button>
                    ) : (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onTaskAction?.(task.id, 'start')}
                        className="h-8 w-8 p-0"
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                    )}
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onTaskAction?.(task.id, 'edit')}
                      className="h-8 w-8 p-0"
                    >
                      <Settings className="h-4 w-4" />
                    </Button>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
