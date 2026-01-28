/**
 * Task Status Badge Component
 * 用于显示任务状态的徽章组件
 */
import React from 'react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { 
  Clock, 
  Play, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Pause
} from 'lucide-react';

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'partial' | 'paused';

interface TaskStatusBadgeProps {
  status: TaskStatus;
  className?: string;
  showIcon?: boolean;
}

export function TaskStatusBadge({ 
  status, 
  className,
  showIcon = true 
}: TaskStatusBadgeProps) {
  const getStatusConfig = (status: TaskStatus) => {
    switch (status) {
      case 'pending':
        return {
          label: '等待中',
          variant: 'secondary' as const,
          color: 'bg-gray-100 text-gray-700 border-gray-200',
          icon: Clock
        };
      case 'running':
        return {
          label: '运行中',
          variant: 'default' as const,
          color: 'bg-blue-100 text-blue-700 border-blue-200',
          icon: Play
        };
      case 'completed':
        return {
          label: '已完成',
          variant: 'default' as const,
          color: 'bg-green-100 text-green-700 border-green-200',
          icon: CheckCircle
        };
      case 'failed':
        return {
          label: '失败',
          variant: 'destructive' as const,
          color: 'bg-red-100 text-red-700 border-red-200',
          icon: XCircle
        };
      case 'partial':
        return {
          label: '部分完成',
          variant: 'secondary' as const,
          color: 'bg-yellow-100 text-yellow-700 border-yellow-200',
          icon: AlertTriangle
        };
      case 'paused':
        return {
          label: '已暂停',
          variant: 'secondary' as const,
          color: 'bg-gray-100 text-gray-700 border-gray-200',
          icon: Pause
        };
      default:
        return {
          label: '未知',
          variant: 'secondary' as const,
          color: 'bg-gray-100 text-gray-700 border-gray-200',
          icon: AlertTriangle
        };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <Badge 
      className={cn(
        'inline-flex items-center gap-1 px-2 py-1 text-xs font-medium border',
        config.color,
        className
      )}
    >
      {showIcon && <Icon className="h-3 w-3" />}
      {config.label}
    </Badge>
  );
}

// 预设的状态徽章组件
export function PendingBadge(props: Omit<TaskStatusBadgeProps, 'status'>) {
  return <TaskStatusBadge status="pending" {...props} />;
}

export function RunningBadge(props: Omit<TaskStatusBadgeProps, 'status'>) {
  return <TaskStatusBadge status="running" {...props} />;
}

export function CompletedBadge(props: Omit<TaskStatusBadgeProps, 'status'>) {
  return <TaskStatusBadge status="completed" {...props} />;
}

export function FailedBadge(props: Omit<TaskStatusBadgeProps, 'status'>) {
  return <TaskStatusBadge status="failed" {...props} />;
}

export function PartialBadge(props: Omit<TaskStatusBadgeProps, 'status'>) {
  return <TaskStatusBadge status="partial" {...props} />;
}

export function PausedBadge(props: Omit<TaskStatusBadgeProps, 'status'>) {
  return <TaskStatusBadge status="paused" {...props} />;
}
