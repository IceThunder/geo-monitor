'use client';

import React, { useState, useEffect } from 'react';
import { GoogleLayout } from '@/components/layout/google-layout';
import {
  Play,
  Pause,
  Square,
  MoreVertical,
  Plus,
  Search,
  Filter,
  Download,
  Calendar,
  Clock,
  Target,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Settings,
  Edit,
  Trash2,
  Copy,
  Eye,
  BarChart3,
  Activity,
  Zap,
  Globe,
  MessageSquare,
  Users,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

// 任务数据类型
interface Task {
  id: string;
  name: string;
  description: string;
  status: 'running' | 'completed' | 'pending' | 'failed' | 'paused';
  progress: number;
  lastRun: string;
  nextRun: string;
  keywords: string[];
  accuracy: number;
  model: string;
  schedule: string;
  createdAt: string;
  owner: {
    name: string;
    avatar: string;
  };
  metrics: {
    totalRuns: number;
    successRate: number;
    avgAccuracy: number;
    dataPoints: number;
  };
}

// 模拟数据
const mockTasks: Task[] = [
  {
    id: '1',
    name: '品牌声量监控',
    description: '实时监控品牌在各大平台的声量变化和用户讨论',
    status: 'running',
    progress: 75,
    lastRun: '2分钟前',
    nextRun: '58分钟后',
    keywords: ['品牌A', '产品线B', '服务C'],
    accuracy: 96.5,
    model: 'GPT-4',
    schedule: '每小时',
    createdAt: '2024-01-15',
    owner: {
      name: '张三',
      avatar: '',
    },
    metrics: {
      totalRuns: 1247,
      successRate: 98.2,
      avgAccuracy: 95.8,
      dataPoints: 15420,
    },
  },
  {
    id: '2',
    name: '竞品分析任务',
    description: '深度分析竞争对手的市场策略和用户反馈',
    status: 'completed',
    progress: 100,
    lastRun: '1小时前',
    nextRun: '23小时后',
    keywords: ['竞品A', '市场份额', '用户评价'],
    accuracy: 92.8,
    model: 'Claude-3',
    schedule: '每日',
    createdAt: '2024-01-10',
    owner: {
      name: '李四',
      avatar: '',
    },
    metrics: {
      totalRuns: 45,
      successRate: 95.6,
      avgAccuracy: 93.2,
      dataPoints: 8750,
    },
  },
  {
    id: '3',
    name: '情感分析监控',
    description: '分析用户对产品和服务的情感倾向变化',
    status: 'pending',
    progress: 0,
    lastRun: '从未运行',
    nextRun: '等待中',
    keywords: ['用户评价', '满意度', '体验反馈'],
    accuracy: 0,
    model: 'GPT-3.5',
    schedule: '每6小时',
    createdAt: '2024-01-28',
    owner: {
      name: '王五',
      avatar: '',
    },
    metrics: {
      totalRuns: 0,
      successRate: 0,
      avgAccuracy: 0,
      dataPoints: 0,
    },
  },
  {
    id: '4',
    name: '社交媒体监控',
    description: '监控社交媒体平台上的品牌提及和讨论热度',
    status: 'paused',
    progress: 45,
    lastRun: '3小时前',
    nextRun: '已暂停',
    keywords: ['社交媒体', '品牌提及', '热度分析'],
    accuracy: 89.3,
    model: 'GPT-4',
    schedule: '每30分钟',
    createdAt: '2024-01-20',
    owner: {
      name: '赵六',
      avatar: '',
    },
    metrics: {
      totalRuns: 892,
      successRate: 91.4,
      avgAccuracy: 88.7,
      dataPoints: 12350,
    },
  },
  {
    id: '5',
    name: '新闻舆情分析',
    description: '分析新闻媒体对品牌的报道情况和舆论导向',
    status: 'failed',
    progress: 25,
    lastRun: '6小时前',
    nextRun: '重试中',
    keywords: ['新闻报道', '舆情分析', '媒体监控'],
    accuracy: 78.9,
    model: 'Claude-3',
    schedule: '每2小时',
    createdAt: '2024-01-25',
    owner: {
      name: '孙七',
      avatar: '',
    },
    metrics: {
      totalRuns: 156,
      successRate: 87.2,
      avgAccuracy: 82.1,
      dataPoints: 4280,
    },
  },
];

export default function GoogleTasks() {
  const [tasks, setTasks] = useState<Task[]>(mockTasks);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('lastRun');
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);

  // 获取状态样式
  const getStatusStyle = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'paused':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  // 获取状态图标
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
      case 'paused':
        return <Pause className="h-3 w-3" />;
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

  // 获取状态中文名
  const getStatusText = (status: string) => {
    switch (status) {
      case 'running':
        return '运行中';
      case 'completed':
        return '已完成';
      case 'pending':
        return '等待中';
      case 'failed':
        return '失败';
      case 'paused':
        return '已暂停';
      default:
        return '未知';
    }
  };

  // 筛选和排序任务
  const filteredTasks = tasks
    .filter(task => {
      const matchesSearch = task.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          task.keywords.some(keyword => keyword.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return a.name.localeCompare(b.name);
        case 'status':
          return a.status.localeCompare(b.status);
        case 'accuracy':
          return b.accuracy - a.accuracy;
        case 'lastRun':
        default:
          return new Date(b.lastRun).getTime() - new Date(a.lastRun).getTime();
      }
    });

  // 统计数据
  const stats = {
    total: tasks.length,
    running: tasks.filter(t => t.status === 'running').length,
    completed: tasks.filter(t => t.status === 'completed').length,
    failed: tasks.filter(t => t.status === 'failed').length,
    avgAccuracy: tasks.reduce((sum, t) => sum + t.accuracy, 0) / tasks.length,
  };

  return (
    <GoogleLayout>
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
                <Activity className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-green-600 dark:text-green-400">
                    运行中
                  </p>
                  <p className="text-3xl font-bold text-green-900 dark:text-green-100">
                    {stats.running}
                  </p>
                </div>
                <Zap className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-sm bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-purple-600 dark:text-purple-400">
                    平均准确率
                  </p>
                  <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
                    {stats.avgAccuracy.toFixed(1)}%
                  </p>
                </div>
                <Target className="h-8 w-8 text-purple-600" />
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
                    {stats.failed}
                  </p>
                </div>
                <AlertCircle className="h-8 w-8 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* 操作栏 */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex flex-1 items-center space-x-4">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="搜索任务名称或关键词..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="running">运行中</SelectItem>
                <SelectItem value="completed">已完成</SelectItem>
                <SelectItem value="pending">等待中</SelectItem>
                <SelectItem value="failed">失败</SelectItem>
                <SelectItem value="paused">已暂停</SelectItem>
              </SelectContent>
            </Select>

            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="lastRun">最后运行</SelectItem>
                <SelectItem value="name">任务名称</SelectItem>
                <SelectItem value="status">状态</SelectItem>
                <SelectItem value="accuracy">准确率</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              导出
            </Button>
            <Button size="sm">
              <Plus className="h-4 w-4 mr-2" />
              新建任务
            </Button>
          </div>
        </div>

        {/* 任务列表 */}
        <div className="grid grid-cols-1 gap-4">
          {filteredTasks.map((task) => (
            <Card key={task.id} className="border-0 shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  {/* 左侧：任务信息 */}
                  <div className="flex-1 space-y-4">
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-semibold">{task.name}</h3>
                          <Badge className={`${getStatusStyle(task.status)} text-xs`}>
                            {getStatusIcon(task.status)}
                            <span className="ml-1">{getStatusText(task.status)}</span>
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {task.description}
                        </p>
                      </div>
                      
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem>
                            <Eye className="h-4 w-4 mr-2" />
                            查看详情
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Edit className="h-4 w-4 mr-2" />
                            编辑任务
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Copy className="h-4 w-4 mr-2" />
                            复制任务
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem>
                            <BarChart3 className="h-4 w-4 mr-2" />
                            查看报告
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Settings className="h-4 w-4 mr-2" />
                            任务设置
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600">
                            <Trash2 className="h-4 w-4 mr-2" />
                            删除任务
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>

                    {/* 进度条 */}
                    {task.status === 'running' && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>执行进度</span>
                          <span>{task.progress}%</span>
                        </div>
                        <Progress value={task.progress} className="h-2" />
                      </div>
                    )}

                    {/* 关键词标签 */}
                    <div className="flex flex-wrap gap-2">
                      {task.keywords.map((keyword, index) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                    </div>

                    {/* 任务详情 */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">模型</p>
                        <p className="font-medium">{task.model}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">调度</p>
                        <p className="font-medium">{task.schedule}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">准确率</p>
                        <p className={`font-medium ${
                          task.accuracy > 95 ? 'text-green-600' : 
                          task.accuracy > 90 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {task.accuracy > 0 ? `${task.accuracy}%` : '-'}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 dark:text-gray-400">负责人</p>
                        <div className="flex items-center space-x-2">
                          <Avatar className="h-6 w-6">
                            <AvatarImage src={task.owner.avatar} />
                            <AvatarFallback className="text-xs">
                              {task.owner.name.charAt(0)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-medium">{task.owner.name}</span>
                        </div>
                      </div>
                    </div>

                    {/* 运行信息 */}
                    <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 pt-2 border-t">
                      <div className="flex items-center space-x-4">
                        <span>最后运行: {task.lastRun}</span>
                        <span>下次运行: {task.nextRun}</span>
                      </div>
                      <div className="flex items-center space-x-4">
                        <span>总运行: {task.metrics.totalRuns}次</span>
                        <span>成功率: {task.metrics.successRate}%</span>
                        <span>数据点: {task.metrics.dataPoints.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 空状态 */}
        {filteredTasks.length === 0 && (
          <Card className="border-0 shadow-sm">
            <CardContent className="p-12 text-center">
              <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">没有找到匹配的任务</h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                尝试调整搜索条件或创建新的监控任务
              </p>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                创建第一个任务
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </GoogleLayout>
  );
}
