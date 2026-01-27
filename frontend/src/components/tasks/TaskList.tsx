/**
 * Task List Component
 */
'use client';

import { Task } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '@/components/ui/table';
import { 
  Play, 
  Pause, 
  Edit, 
  Trash2, 
  MoreVertical,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { formatDateTime, getStatusColor, cn } from '@/lib/utils';
import { useState } from 'react';

interface TaskListProps {
  tasks: Task[];
  onEdit?: (task: Task) => void;
  onDelete?: (task: Task) => void;
  onTrigger?: (task: Task) => void;
  onToggleActive?: (task: Task) => void;
}

export function TaskList({
  tasks,
  onEdit,
  onDelete,
  onTrigger,
  onToggleActive,
}: TaskListProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>监控任务列表</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>任务名称</TableHead>
              <TableHead>关键词</TableHead>
              <TableHead>监控模型</TableHead>
              <TableHead>调度周期</TableHead>
              <TableHead>状态</TableHead>
              <TableHead>最近运行</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {tasks.map((task) => (
              <TableRow key={task.id}>
                <TableCell>
                  <div>
                    <div className="font-medium">{task.name}</div>
                    {task.description && (
                      <div className="text-sm text-muted-foreground truncate max-w-xs">
                        {task.description}
                      </div>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {task.keywords.slice(0, 2).map((keyword) => (
                      <Badge key={keyword} variant="secondary" className="text-xs">
                        {keyword}
                      </Badge>
                    ))}
                    {task.keywords.length > 2 && (
                      <Badge variant="secondary" className="text-xs">
                        +{task.keywords.length - 2}
                      </Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {task.models.slice(0, 2).map((model) => (
                      <Badge key={model} variant="outline" className="text-xs">
                        {model.split('/').pop()}
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
                  <span className="font-mono text-sm">{task.schedule_cron}</span>
                </TableCell>
                <TableCell>
                  <Badge className={cn(getStatusColor(task.is_active ? 'active' : 'inactive'))}>
                    {task.is_active ? '运行中' : '已暂停'}
                  </Badge>
                </TableCell>
                <TableCell>
                  {task.last_run_time ? (
                    <div className="text-sm">
                      <div>{formatDateTime(task.last_run_time)}</div>
                      {task.last_run_status && (
                        <Badge 
                          variant="ghost" 
                          className={cn(
                            'mt-1',
                            task.last_run_status === 'completed' && 'text-green-600',
                            task.last_run_status === 'failed' && 'text-red-600',
                            task.last_run_status === 'running' && 'text-blue-600'
                          )}
                        >
                          {task.last_run_status === 'completed' && <CheckCircle className="h-3 w-3 mr-1" />}
                          {task.last_run_status === 'failed' && <XCircle className="h-3 w-3 mr-1" />}
                          {task.last_run_status === 'running' && <Clock className="h-3 w-3 mr-1" />}
                          {task.last_run_status}
                        </Badge>
                      )}
                    </div>
                  ) : (
                    <span className="text-muted-foreground">从未运行</span>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onTrigger?.(task)}
                      title="手动触发"
                    >
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onToggleActive?.(task)}
                      title={task.is_active ? '暂停任务' : '启动任务'}
                    >
                      {task.is_active ? (
                        <Pause className="h-4 w-4" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onEdit?.(task)}
                      title="编辑"
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => onDelete?.(task)}
                      title="删除"
                      className="text-red-500 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        
        {tasks.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            暂无监控任务，请创建新任务
          </div>
        )}
      </CardContent>
    </Card>
  );
}
