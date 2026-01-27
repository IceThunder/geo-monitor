/**
 * Tasks Page - Task Management
 */
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { TaskList } from '@/components/tasks/TaskList';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Input } from '@/components/ui/input';
import { taskApi, Task, CreateTaskDTO, UpdateTaskDTO } from '@/lib/api';
import { Plus, Search, Filter } from 'lucide-react';

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0 });

  async function fetchTasks() {
    try {
      setLoading(true);
      const response = await taskApi.getTasks({
        page: pagination.page,
        limit: pagination.limit,
        search: searchQuery || undefined,
        is_active: filterActive,
      });
      setTasks(response.data);
      setPagination(prev => ({ ...prev, total: response.total }));
    } catch (err) {
      setError('加载任务列表失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchTasks();
  }, [pagination.page, filterActive]);

  useEffect(() => {
    // Debounced search
    const timer = setTimeout(() => {
      if (pagination.page === 1) {
        fetchTasks();
      } else {
        setPagination(prev => ({ ...prev, page: 1 }));
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  async function handleEditTask(task: Task) {
    // Navigate to edit page
    window.location.href = `/tasks/${task.id}/edit`;
  }

  async function handleDeleteTask(task: Task) {
    if (confirm(`确定要删除任务 "${task.name}" 吗？`)) {
      try {
        await taskApi.deleteTask(task.id);
        fetchTasks();
      } catch (err) {
        alert('删除失败');
        console.error(err);
      }
    }
  }

  async function handleTriggerTask(task: Task) {
    try {
      await taskApi.triggerTask(task.id);
      alert('任务已触发执行');
    } catch (err) {
      alert('触发失败');
      console.error(err);
    }
  }

  async function handleToggleActive(task: Task) {
    try {
      await taskApi.updateTask(task.id, { is_active: !task.is_active });
      fetchTasks();
    } catch (err) {
      alert('操作失败');
      console.error(err);
    }
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">监控任务</h1>
        <Link href="/tasks/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            新建任务
          </Button>
        </Link>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="搜索任务名称..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant={filterActive === undefined ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterActive(undefined)}
          >
            全部
          </Button>
          <Button
            variant={filterActive === true ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterActive(true)}
          >
            运行中
          </Button>
          <Button
            variant={filterActive === false ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterActive(false)}
          >
            已暂停
          </Button>
        </div>
      </div>

      {/* Task List */}
      {loading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
      ) : (
        <TaskList
          tasks={tasks}
          onEdit={handleEditTask}
          onDelete={handleDeleteTask}
          onTrigger={handleTriggerTask}
          onToggleActive={handleToggleActive}
        />
      )}

      {/* Pagination */}
      {pagination.total > pagination.limit && (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
            disabled={pagination.page === 1}
          >
            上一页
          </Button>
          <span className="text-sm text-muted-foreground">
            第 {pagination.page} 页 / 共 {Math.ceil(pagination.total / pagination.limit)} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
            disabled={pagination.page >= Math.ceil(pagination.total / pagination.limit)}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  );
}
