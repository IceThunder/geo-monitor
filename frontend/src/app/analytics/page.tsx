/**
 * Analytics Page
 * 分析报告页面
 */
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
// 暂时注释掉图表组件导入，避免404错误
// import { 
//   SOVTrendChart,
//   SentimentTrendChart,
//   KeywordPerformanceChart,
//   CompetitorComparisonChart,
//   SentimentDistributionChart,
//   ChannelDistributionChart,
//   DonutChart
// } from '@/components/charts';
import { 
  TrendingUp, 
  BarChart3, 
  PieChart, 
  Download,
  Filter,
  Calendar,
  Target,
  Users,
  MessageSquare
} from 'lucide-react';

// 扩展的模拟数据
const extendedSOVData = [
  { name: '1月', sov: 18.2, target: 20, competitor1: 15.8, competitor2: 12.5 },
  { name: '2月', sov: 19.8, target: 20, competitor1: 16.2, competitor2: 13.1 },
  { name: '3月', sov: 21.5, target: 20, competitor1: 15.9, competitor2: 12.8 },
  { name: '4月', sov: 20.1, target: 20, competitor1: 17.3, competitor2: 14.2 },
  { name: '5月', sov: 22.8, target: 20, competitor1: 16.8, competitor2: 13.5 },
  { name: '6月', sov: 23.5, target: 20, competitor1: 17.1, competitor2: 14.0 },
];

const competitorData = [
  { name: '声量占有率', ourBrand: 23.5, competitor1: 17.1, competitor2: 14.0 },
  { name: '情感分值', ourBrand: 0.75, competitor1: 0.68, competitor2: 0.62 },
  { name: '互动率', ourBrand: 4.2, competitor1: 3.8, competitor2: 3.1 },
  { name: '转化率', ourBrand: 2.8, competitor1: 2.1, competitor2: 1.9 },
];

const detailedKeywordData = [
  { name: '品牌A', mentions: 1250, sentiment: 0.8, growth: 15.2 },
  { name: '产品B', mentions: 980, sentiment: 0.75, growth: 8.7 },
  { name: '服务C', mentions: 750, sentiment: 0.65, growth: -2.1 },
  { name: '活动D', mentions: 620, sentiment: 0.7, growth: 22.5 },
  { name: '新品E', mentions: 450, sentiment: 0.82, growth: 45.8 },
];

const channelPerformanceData = [
  { name: '微博', mentions: 2850, engagement: 4.2, sentiment: 0.72 },
  { name: '微信', mentions: 2280, engagement: 6.8, sentiment: 0.78 },
  { name: '抖音', mentions: 1620, engagement: 8.5, sentiment: 0.75 },
  { name: '小红书', mentions: 980, engagement: 5.9, sentiment: 0.81 },
  { name: '知乎', mentions: 650, engagement: 3.2, sentiment: 0.69 },
];

const timeRangeOptions = [
  { label: '最近7天', value: '7d' },
  { label: '最近30天', value: '30d' },
  { label: '最近90天', value: '90d' },
  { label: '最近6个月', value: '6m' },
  { label: '最近1年', value: '1y' },
];

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('30d');
  const [selectedMetric, setSelectedMetric] = useState('sov');

  const handleExport = () => {
    console.log('导出报告...');
    // TODO: 实现报告导出功能
  };

  const handleFilter = () => {
    console.log('应用筛选...');
    // TODO: 实现筛选功能
  };

  return (
    <div className="space-y-6">
      {/* 页面标题和控制 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">分析报告</h1>
          <p className="text-gray-600 mt-1">深入分析品牌表现和市场趋势</p>
        </div>
        <div className="flex items-center space-x-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeRangeOptions.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          <Button variant="outline" onClick={handleFilter}>
            <Filter className="h-4 w-4 mr-2" />
            筛选
          </Button>
          
          <Button variant="outline" onClick={handleExport}>
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        </div>
      </div>

      {/* 关键指标概览 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">总提及量</p>
                <p className="text-2xl font-bold text-gray-900">8,750</p>
                <p className="text-sm text-green-600">+12.5% vs 上期</p>
              </div>
              <MessageSquare className="h-8 w-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">声量占有率</p>
                <p className="text-2xl font-bold text-gray-900">23.5%</p>
                <p className="text-sm text-green-600">+2.3% vs 上期</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">平均情感分值</p>
                <p className="text-2xl font-bold text-gray-900">0.75</p>
                <p className="text-sm text-green-600">+0.12 vs 上期</p>
              </div>
              <Target className="h-8 w-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">活跃用户</p>
                <p className="text-2xl font-bold text-gray-900">2,340</p>
                <p className="text-sm text-red-600">-1.8% vs 上期</p>
              </div>
              <Users className="h-8 w-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 详细分析标签页 */}
      <Tabs defaultValue="trends" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
          <TabsTrigger value="competitors">竞品对比</TabsTrigger>
          <TabsTrigger value="keywords">关键词分析</TabsTrigger>
          <TabsTrigger value="channels">渠道分析</TabsTrigger>
        </TabsList>

        {/* 趋势分析 */}
        <TabsContent value="trends" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <TrendingUp className="h-5 w-5 mr-2" />
                  声量趋势对比
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500">声量趋势图表</p>
                    <p className="text-sm text-gray-400">图表组件开发中...</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <PieChart className="h-5 w-5 mr-2" />
                  情感趋势分析
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <PieChart className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                    <p className="text-gray-500">情感趋势图表</p>
                    <p className="text-sm text-gray-400">图表组件开发中...</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>情感分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <PieChart className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">情感分布图表</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>渠道分布</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <BarChart3 className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">渠道分布图表</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>关键洞察</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-start space-x-2">
                      <TrendingUp className="h-4 w-4 text-green-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-green-800">声量增长</p>
                        <p className="text-xs text-green-700">本月声量较上月增长12.5%，主要来自新品发布活动</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-start space-x-2">
                      <Target className="h-4 w-4 text-blue-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-blue-800">情感改善</p>
                        <p className="text-xs text-blue-700">正面情感占比提升至75%，用户满意度持续上升</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                    <div className="flex items-start space-x-2">
                      <MessageSquare className="h-4 w-4 text-yellow-600 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-yellow-800">关注重点</p>
                        <p className="text-xs text-yellow-700">服务C的情感分值下降，需要重点关注</p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 竞品对比 */}
        <TabsContent value="competitors" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>竞品对比分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500">竞品对比图表</p>
                  <p className="text-sm text-gray-400">图表组件开发中...</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>竞品表现排名</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Badge className="bg-blue-600">1</Badge>
                      <span className="font-medium">我们的品牌</span>
                    </div>
                    <span className="text-blue-600 font-semibold">23.5%</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Badge variant="secondary">2</Badge>
                      <span className="font-medium">竞品A</span>
                    </div>
                    <span className="text-gray-600 font-semibold">17.1%</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Badge variant="secondary">3</Badge>
                      <span className="font-medium">竞品B</span>
                    </div>
                    <span className="text-gray-600 font-semibold">14.0%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>优势分析</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">声量占有率</span>
                    <span className="text-sm font-medium text-green-600">领先 6.4%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">情感分值</span>
                    <span className="text-sm font-medium text-green-600">领先 0.07</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">互动率</span>
                    <span className="text-sm font-medium text-green-600">领先 0.4%</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">转化率</span>
                    <span className="text-sm font-medium text-green-600">领先 0.7%</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 关键词分析 */}
        <TabsContent value="keywords" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>关键词性能分析</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 bg-gray-50 rounded-lg flex items-center justify-center">
                <div className="text-center">
                  <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-500">关键词性能图表</p>
                  <p className="text-sm text-gray-400">图表组件开发中...</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle>关键词详细表现</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">关键词</th>
                      <th className="text-right py-2">提及量</th>
                      <th className="text-right py-2">情感分值</th>
                      <th className="text-right py-2">增长率</th>
                      <th className="text-right py-2">趋势</th>
                    </tr>
                  </thead>
                  <tbody>
                    {detailedKeywordData.map((item, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2 font-medium">{item.name}</td>
                        <td className="text-right py-2">{item.mentions.toLocaleString()}</td>
                        <td className="text-right py-2">{item.sentiment.toFixed(2)}</td>
                        <td className={`text-right py-2 ${item.growth > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {item.growth > 0 ? '+' : ''}{item.growth}%
                        </td>
                        <td className="text-right py-2">
                          {item.growth > 0 ? (
                            <TrendingUp className="h-4 w-4 text-green-600 inline" />
                          ) : (
                            <TrendingUp className="h-4 w-4 text-red-600 inline transform rotate-180" />
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 渠道分析 */}
        <TabsContent value="channels" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>渠道表现对比</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">渠道</th>
                      <th className="text-right py-2">提及量</th>
                      <th className="text-right py-2">互动率</th>
                      <th className="text-right py-2">情感分值</th>
                      <th className="text-right py-2">表现</th>
                    </tr>
                  </thead>
                  <tbody>
                    {channelPerformanceData.map((item, index) => (
                      <tr key={index} className="border-b">
                        <td className="py-2 font-medium">{item.name}</td>
                        <td className="text-right py-2">{item.mentions.toLocaleString()}</td>
                        <td className="text-right py-2">{item.engagement}%</td>
                        <td className="text-right py-2">{item.sentiment.toFixed(2)}</td>
                        <td className="text-right py-2">
                          <Badge 
                            variant={item.engagement > 5 ? 'default' : 'secondary'}
                            className={item.engagement > 5 ? 'bg-green-600' : ''}
                          >
                            {item.engagement > 5 ? '优秀' : '良好'}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
