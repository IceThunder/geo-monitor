'use client';

import React, { useState } from 'react';
import {
  Play,
  Pause,
  Plus,
  Clock,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Activity,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

// 模拟任务数据
const mockTasks = [
  {
    id: '1',
    name: '品牌声量监控',
    description: '监控品牌在各大AI模型中的提及情况',
    status: 'running' as const,
    progress: 75,
    accuracy: 94.2,
    lastRun: '5分钟前',
    nextRun: '15分钟后',
  },
  {
    id: '2',
    name: '竞品分析任务',
    description: '分析竞争对手在AI模型中的表现',
    status: 'completed' as const,
    progress: 100,
    accuracy: 91.8,
    lastRun: '1小时前',
    nextRun: '23小时后',
  },
  {
    id: '3',
    name: '情感分析监控',
    description: '监控品牌相关内容的情感倾向',
    status: 'pending' as const,
    progress: 0,
    accuracy: 0,
    lastRun: '从未运行',
    nextRun: '待定',
  },
  {
    id: '4',
    name: '错误测试任务',
    description: '用于测试错误处理的任务',
    status: 'failed' as const,
    progress: 25,
    accuracy: 0,
    lastRun: '2小时前',
    nextRun: '重试中',
  },
];

export default function GoogleTasksSimple() {
  const [tasks] = useState(mockTasks);

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

  // 统计数据
  const stats = {
    total: tasks.length,
    running: tasks.filter(t => t.status === 'running').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
    avgAccuracy: tasks.reduce((sum, t) => sum + t.accuracy, 0) / tasks.length,
  };

  return (
    <div className="space-y-6">
      {/* 页面头部统计 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
                  总任务数
                </p>
                <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                  {stats.total}
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
                  {stats.running}
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
                  {stats.completed}
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
                  平均准确率
                </p>
                <p className="text-3xl font-bold text-orange-900 dark:text-orange-100">
                  {stats.avgAccuracy.toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 任务列表 */}
      <Card className="border-0 shadow-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl font-semibold">监控任务</CardTitle>
              <CardDescription>管理和监控所有AI模型品牌监控任务</CardDescription>
            </div>
            <Button className="bg-blue-600 hover:bg-blue-700">
              <Plus className="h-4 w-4 mr-2" />
              新建任务
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {tasks.map((task) => (
              <div key={task.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-3">
                    <h3 className="font-semibold text-lg">{task.name}</h3>
                    <Badge className={`${getStatusColor(task.status)} border`}>
                      <div className="flex items-center space-x-1">
                        {getStatusIcon(task.status)}
                        <span className="capitalize">{task.status}</span>
                      </div>
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button variant="outline" size="sm">
                      <Play className="h-4 w-4" />
                    </Button>
                    <Button variant="outline" size="sm">
                      <Pause className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                <p className="text-gray-600 dark:text-gray-400 mb-3">{task.description}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">进度</p>
                    <div className="flex items-center space-x-2">
                      <Progress value={task.progress} className="flex-1" />
                      <span className="text-sm font-medium">{task.progress}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">准确率</p>
                    <p className="text-sm font-semibold">{task.accuracy}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">上次运行</p>
                    <p className="text-sm">{task.lastRun}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">下次运行</p>
                    <p className="text-sm">{task.nextRun}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
