'use client';

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  BarChart3,
  PieChart,
  LineChart,
  Calendar,
  Filter,
  Download,
  RefreshCw,
  Eye,
  Play,
  Pause,
  Settings,
  MoreHorizontal,
  ArrowUpRight,
  ArrowDownRight,
  Zap,
  Target,
  Globe,
  MessageSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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

// 模拟数据
const mockData = {
  overview: {
    totalTasks: 24,
    activeTasks: 18,
    completedToday: 12,
    alertsCount: 3,
    avgAccuracy: 94.2,
    sovTrend: 8.5,
  },
  recentTasks: [
    {
      id: '1',
      name: '品牌声量监控',
      status: 'running',
      progress: 75,
      lastRun: '2分钟前',
      accuracy: 96.5,
      keywords: ['品牌A', '竞品B'],
    },
    {
      id: '2',
      name: '竞品分析任务',
      status: 'completed',
      progress: 100,
      lastRun: '1小时前',
      accuracy: 92.8,
      keywords: ['竞品A', '市场份额'],
    },
    {
      id: '3',
      name: '情感分析监控',
      status: 'pending',
      progress: 0,
      lastRun: '待执行',
      accuracy: 0,
      keywords: ['用户评价', '满意度'],
    },
  ],
  alerts: [
    {
      id: '1',
      type: 'warning',
      title: '准确率下降',
      message: '品牌声量监控任务准确率低于95%',
      time: '5分钟前',
    },
    {
      id: '2',
      type: 'info',
      title: '新数据可用',
      message: '竞品分析报告已生成',
      time: '1小时前',
    },
    {
      id: '3',
      type: 'success',
      title: '任务完成',
      message: '情感分析任务执行成功',
      time: '2小时前',
    },
  ],
  chartData: {
    sovTrend: [
      { date: '01-24', value: 85.2, target: 90 },
      { date: '01-25', value: 87.1, target: 90 },
      { date: '01-26', value: 89.3, target: 90 },
      { date: '01-27', value: 91.5, target: 90 },
      { date: '01-28', value: 93.7, target: 90 },
      { date: '01-29', value: 94.2, target: 90 },
    ],
    sentimentDistribution: [
      { name: '正面', value: 65, color: '#10b981' },
      { name: '中性', value: 25, color: '#6b7280' },
      { name: '负面', value: 10, color: '#ef4444' },
    ],
    keywordPerformance: [
      { keyword: '品牌A', mentions: 1250, sentiment: 0.85 },
      { keyword: '产品B', mentions: 980, sentiment: 0.72 },
      { keyword: '服务C', mentions: 750, sentiment: 0.91 },
      { keyword: '竞品D', mentions: 650, sentiment: 0.45 },
    ],
  },
};

export default function GoogleDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState('7d');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  const handleRefresh = async () => {
    setIsRefreshing(true);
    // 模拟刷新延迟
    setTimeout(() => setIsRefreshing(false), 2000);
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
        return <AlertTriangle className="h-3 w-3" />;
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

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
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              导出
            </Button>
            <Button variant="outline" size="sm">
              <Calendar className="h-4 w-4 mr-2" />
              计划
            </Button>
            <Button size="sm">
              <Activity className="h-4 w-4 mr-2" />
              新建任务
            </Button>
          </div>
        </div>

        {/* 关键指标卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
                    总任务数
                  </p>
                  <p className="text-3xl font-bold text-blue-900 dark:text-blue-100">
                    {mockData.overview.totalTasks}
                  </p>
                  <p className="text-sm text-blue-600 dark:text-blue-400 flex items-center mt-1">
                    <TrendingUp className="h-4 w-4 mr-1" />
                    +12% 较上周
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
                  <p className="text-sm font-medium text-green-600 dark:text-green-400">
                    运行中任务
                  </p>
                  <p className="text-3xl font-bold text-green-900 dark:text-green-100">
                    {mockData.overview.activeTasks}
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400 flex items-center mt-1">
                    <Play className="h-4 w-4 mr-1" />
                    实时监控中
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
                  <p className="text-sm font-medium text-purple-600 dark:text-purple-400">
                    平均准确率
                  </p>
                  <p className="text-3xl font-bold text-purple-900 dark:text-purple-100">
                    {mockData.overview.avgAccuracy}%
                  </p>
                  <p className="text-sm text-purple-600 dark:text-purple-400 flex items-center mt-1">
                    <Target className="h-4 w-4 mr-1" />
                    目标: 95%
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
                  <p className="text-sm font-medium text-orange-600 dark:text-orange-400">
                    待处理告警
                  </p>
                  <p className="text-3xl font-bold text-orange-900 dark:text-orange-100">
                    {mockData.overview.alertsCount}
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
                    <CardTitle className="text-lg font-semibold">声量占有率趋势</CardTitle>
                    <CardDescription>过去7天的SOV变化情况</CardDescription>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge variant="outline" className="text-green-600 border-green-200">
                      <ArrowUpRight className="h-3 w-3 mr-1" />
                      +{mockData.overview.sovTrend}%
                    </Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Eye className="h-4 w-4 mr-2" />
                          查看详情
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="h-4 w-4 mr-2" />
                          导出数据
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem>
                          <Settings className="h-4 w-4 mr-2" />
                          配置图表
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-80 flex items-center justify-center bg-gray-50 dark:bg-gray-800 rounded-lg">
                  <div className="text-center">
                    <LineChart className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">SOV趋势图表</p>
                    <p className="text-xs text-gray-400 mt-1">
                      当前值: {mockData.overview.avgAccuracy}% | 目标: 95%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 关键词性能表格 */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-semibold">关键词性能</CardTitle>
                    <CardDescription>热门关键词的提及次数和情感分析</CardDescription>
                  </div>
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    筛选
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockData.chartData.keywordPerformance.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
                          <MessageSquare className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <p className="font-medium">{item.keyword}</p>
                          <p className="text-sm text-gray-500">{item.mentions} 次提及</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4">
                        <div className="text-right">
                          <p className="text-sm font-medium">情感分值</p>
                          <p className={`text-sm ${item.sentiment > 0.7 ? 'text-green-600' : item.sentiment > 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                            {(item.sentiment * 100).toFixed(1)}%
                          </p>
                        </div>
                        <Progress value={item.sentiment * 100} className="w-20" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 右侧：任务状态和告警 */}
          <div className="space-y-6">
            {/* 最近任务 */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg font-semibold">最近任务</CardTitle>
                <CardDescription>当前运行和最近完成的任务</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockData.recentTasks.map((task) => (
                    <div key={task.id} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium text-sm">{task.name}</h4>
                        <Badge className={`${getStatusColor(task.status)} text-xs`}>
                          {getStatusIcon(task.status)}
                          <span className="ml-1 capitalize">{task.status}</span>
                        </Badge>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="flex justify-between text-xs text-gray-500">
                          <span>进度</span>
                          <span>{task.progress}%</span>
                        </div>
                        <Progress value={task.progress} className="h-2" />
                        
                        <div className="flex justify-between text-xs">
                          <span className="text-gray-500">最后运行: {task.lastRun}</span>
                          {task.accuracy > 0 && (
                            <span className={`font-medium ${task.accuracy > 95 ? 'text-green-600' : task.accuracy > 90 ? 'text-yellow-600' : 'text-red-600'}`}>
                              准确率: {task.accuracy}%
                            </span>
                          )}
                        </div>
                        
                        <div className="flex flex-wrap gap-1 mt-2">
                          {task.keywords.map((keyword, idx) => (
                            <Badge key={idx} variant="secondary" className="text-xs">
                              {keyword}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                
                <Button variant="outline" className="w-full mt-4" size="sm">
                  查看所有任务
                </Button>
              </CardContent>
            </Card>

            {/* 系统告警 */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg font-semibold">系统告警</CardTitle>
                    <CardDescription>需要关注的系统通知</CardDescription>
                  </div>
                  <Badge variant="outline" className="text-orange-600 border-orange-200">
                    {mockData.overview.alertsCount} 条
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockData.alerts.map((alert) => (
                    <div key={alert.id} className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <div className={`h-2 w-2 rounded-full mt-2 flex-shrink-0 ${
                        alert.type === 'warning' ? 'bg-orange-500' :
                        alert.type === 'success' ? 'bg-green-500' : 'bg-blue-500'
                      }`} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{alert.title}</p>
                        <p className="text-xs text-gray-500 mt-1">{alert.message}</p>
                        <p className="text-xs text-gray-400 mt-1">{alert.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
                
                <Button variant="outline" className="w-full mt-4" size="sm">
                  查看所有告警
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
  );
}
