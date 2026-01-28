/**
 * Dashboard Page
 * 仪表板主页面
 */
'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MetricCard, SOVCard, AccuracyCard, SentimentCard, CitationCard } from '@/components/dashboard/metric-card';
import { TaskTable, type Task } from '@/components/tasks/task-table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  TrendingUp, 
  AlertTriangle, 
  Plus,
  RefreshCw,
  Filter,
  Download
} from 'lucide-react';

// 模拟数据
const mockMetrics = {
  sov: { value: 23.5, change: 2.3, changeType: 'increase' as const },
  accuracy: { value: 8.2, change: -0.5, changeType: 'decrease' as const },
  sentiment: { value: 0.65, change: 0.12, changeType: 'increase' as const },
  citation: { value: 45.8, change: 5.2, changeType: 'increase' as const }
};

const mockTasks: Task[] = [
  {
    id: '1',
    name: '品牌声量监控',
    description: '监控品牌在各大平台的声量表现',
    status: 'running',
    schedule: '0 */6 * * *',
    isActive: true,
    lastRun: '2024-01-28T10:00:00Z',
    nextRun: '2024-01-28T16:00:00Z',
    successRate: 95,
    totalCost: 12.50,
    models: ['gpt-4', 'claude-3'],
    keywords: ['品牌A', '产品B', '服务C'],
    createdAt: '2024-01-20T08:00:00Z'
  },
  {
    id: '2',
    name: '竞品分析',
    description: '分析竞争对手的市场表现',
    status: 'completed',
    schedule: '0 0 * * *',
    isActive: true,
    lastRun: '2024-01-28T00:00:00Z',
    nextRun: '2024-01-29T00:00:00Z',
    successRate: 88,
    totalCost: 8.75,
    models: ['gpt-3.5-turbo'],
    keywords: ['竞品X', '竞品Y'],
    createdAt: '2024-01-15T10:00:00Z'
  }
];

export default function DashboardPage() {
  const handleTaskAction = (taskId: string, action: string) => {
    console.log(`Task ${taskId} action: ${action}`);
    // TODO: 实现任务操作逻辑
  };

  const handleRefresh = () => {
    console.log('Refreshing dashboard...');
    // TODO: 实现刷新逻辑
  };

  return (
    <div className="space-y-6">
      {/* 页面标题和操作 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">仪表板</h1>
          <p className="text-gray-600 mt-1">监控您的品牌表现和任务状态</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={handleRefresh}>
            <RefreshCw className="h-4 w-4 mr-2" />
            刷新
          </Button>
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            筛选
          </Button>
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            新建任务
          </Button>
        </div>
      </div>

      {/* 关键指标卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <SOVCard 
          value={mockMetrics.sov.value}
          change={mockMetrics.sov.change}
          changeType={mockMetrics.sov.changeType}
          status="info"
          description="相比上周提升2.3%"
        />
        <AccuracyCard 
          value={mockMetrics.accuracy.value}
          change={mockMetrics.accuracy.change}
          changeType={mockMetrics.accuracy.changeType}
          status="warning"
          description="准确性略有下降"
        />
        <SentimentCard 
          value={mockMetrics.sentiment.value}
          change={mockMetrics.sentiment.change}
          changeType={mockMetrics.sentiment.changeType}
          status="success"
          description="情感倾向持续改善"
        />
        <CitationCard 
          value={mockMetrics.citation.value}
          change={mockMetrics.citation.change}
          changeType={mockMetrics.citation.changeType}
          status="success"
          description="引用率显著提升"
        />
      </div>

      {/* 主要内容区域 */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList>
          <TabsTrigger value="overview">概览</TabsTrigger>
          <TabsTrigger value="tasks">任务管理</TabsTrigger>
          <TabsTrigger value="analytics">分析报告</TabsTrigger>
          <TabsTrigger value="alerts">告警中心</TabsTrigger>
        </TabsList>

        {/* 概览标签页 */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 趋势图表 */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  声量趋势
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                  <div className="text-center text-gray-500">
                    <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                    <p>趋势图表组件</p>
                    <p className="text-sm">将在数据可视化阶段实现</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 最近活动 */}
            <Card>
              <CardHeader>
                <CardTitle>最近活动</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full mt-2"></div>
                    <div>
                      <p className="text-sm font-medium">品牌声量监控任务完成</p>
                      <p className="text-xs text-gray-500">2分钟前</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <div>
                      <p className="text-sm font-medium">新增关键词监控</p>
                      <p className="text-xs text-gray-500">15分钟前</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2"></div>
                    <div>
                      <p className="text-sm font-medium">准确性评分下降提醒</p>
                      <p className="text-xs text-gray-500">1小时前</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 任务管理标签页 */}
        <TabsContent value="tasks" className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">监控任务</h2>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary">
                {mockTasks.length} 个任务
              </Badge>
              <Badge variant="default">
                {mockTasks.filter(t => t.status === 'running').length} 个运行中
              </Badge>
            </div>
          </div>
          
          <TaskTable 
            tasks={mockTasks}
            onTaskAction={handleTaskAction}
          />
        </TabsContent>

        {/* 分析报告标签页 */}
        <TabsContent value="analytics" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>分析报告</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64 flex items-center justify-center bg-gray-50 rounded-lg">
                <div className="text-center text-gray-500">
                  <BarChart3 className="h-12 w-12 mx-auto mb-2" />
                  <p>分析报告组件</p>
                  <p className="text-sm">将在数据可视化阶段实现</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 告警中心标签页 */}
        <TabsContent value="alerts" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <AlertTriangle className="h-5 w-5 mr-2" />
                告警中心
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border border-yellow-200 bg-yellow-50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-yellow-800">准确性评分下降</h4>
                      <p className="text-sm text-yellow-700 mt-1">
                        品牌声量监控任务的准确性评分从8.7降至8.2，建议检查关键词配置
                      </p>
                      <p className="text-xs text-yellow-600 mt-2">1小时前</p>
                    </div>
                  </div>
                </div>
                
                <div className="p-4 border border-green-200 bg-green-50 rounded-lg">
                  <div className="flex items-start space-x-3">
                    <div className="w-5 h-5 bg-green-500 rounded-full mt-0.5 flex items-center justify-center">
                      <div className="w-2 h-2 bg-white rounded-full"></div>
                    </div>
                    <div>
                      <h4 className="font-medium text-green-800">SOV指标提升</h4>
                      <p className="text-sm text-green-700 mt-1">
                        声量占有率从21.2%提升至23.5%，表现良好
                      </p>
                      <p className="text-xs text-green-600 mt-2">3小时前</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
