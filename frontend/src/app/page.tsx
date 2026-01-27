/**
 * Dashboard Page - Main Overview
 */
'use client';

import { useState, useEffect } from 'react';
import { MetricCard } from '@/components/dashboard/MetricCard';
import { TrendChart } from '@/components/dashboard/TrendChart';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { metricApi, DashboardOverviewResponse } from '@/lib/api/metrics';
import { 
  ListTodo, 
  CheckCircle, 
  TrendingUp, 
  AlertTriangle,
  Activity,
  DollarSign,
} from 'lucide-react';
import { formatCurrency, getRelativeTime } from '@/lib/utils';

export default function DashboardPage() {
  const [data, setData] = useState<DashboardOverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        const endDate = new Date().toISOString().split('T')[0];
        const startDate = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
          .toISOString()
          .split('T')[0];
        
        const response = await metricApi.getDashboardOverview({
          start_date: startDate,
          end_date: endDate,
        });
        
        setData(response);
      } catch (err) {
        setError('加载数据失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 animate-fade-in">
      <h1 className="text-3xl font-bold">监控概览</h1>
      
      {/* Core Metrics Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="总任务数"
          value={data?.total_tasks || 0}
          description="监控任务总数"
          icon={ListTodo}
        />
        <MetricCard
          title="活跃任务"
          value={data?.active_tasks || 0}
          description="当前运行中的任务"
          icon={CheckCircle}
        />
        <MetricCard
          title="今日成本"
          value={formatCurrency(data?.total_cost_usd || 0)}
          description="API 调用消耗"
          icon={DollarSign}
        />
        <MetricCard
          title="Token 使用"
          value={(data?.total_token_usage || 0).toLocaleString()}
          description="模型调用 token"
          icon={Activity}
        />
      </div>
      
      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <TrendChart
          title="准确性趋势 (近7天)"
          data={(data?.accuracy_trend || []).map(d => ({
            date: d.date,
            value: d.avg_accuracy,
          }))}
          yAxisLabel="准确性分数"
          dataKey="value"
          color="#22c55e"
          className="col-span-4"
        />
        
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>Top 品牌声量</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(data?.top_brands || []).slice(0, 5).map((brand, index) => (
                <div key={brand.brand} className="flex items-center gap-3">
                  <span className="text-sm font-medium w-6">{index + 1}</span>
                  <div className="flex-1">
                    <div className="flex justify-between text-sm mb-1">
                      <span>{brand.brand}</span>
                      <span className="text-muted-foreground">{brand.count} 次</span>
                    </div>
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full"
                        style={{ 
                          width: `${(brand.count / (data?.top_brands?.[0]?.count || 1)) * 100}%` 
                        }}
                      />
                    </div>
                  </div>
                </div>
              ))}
              
              {(!data?.top_brands || data.top_brands.length === 0) && (
                <p className="text-center text-muted-foreground py-4">
                  暂无数据
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Recent Alerts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-500" />
            最近告警
          </CardTitle>
        </CardHeader>
        <CardContent>
          {(data?.recent_alerts && data.recent_alerts.length > 0) ? (
            <div className="space-y-3">
              {data.recent_alerts.map((alert) => (
                <div 
                  key={alert.id} 
                  className="flex items-start gap-3 p-3 rounded-lg bg-yellow-50 border border-yellow-200"
                >
                  <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-800">
                      {alert.type}
                    </p>
                    <p className="text-sm text-yellow-700">
                      {alert.message}
                    </p>
                  </div>
                  <Badge variant="outline" className="text-yellow-700 border-yellow-300">
                    {getRelativeTime(new Date().toISOString())}
                  </Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <CheckCircle className="h-12 w-12 mx-auto text-green-500 mb-2" />
              <p>暂无告警</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
