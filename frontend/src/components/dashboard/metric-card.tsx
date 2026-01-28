/**
 * Metric Card Component
 * 用于显示监控指标的卡片组件
 */
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  change?: number;
  changeType?: 'increase' | 'decrease' | 'neutral';
  trend?: 'up' | 'down' | 'stable';
  status?: 'success' | 'warning' | 'error' | 'info';
  description?: string;
  className?: string;
}

export function MetricCard({
  title,
  value,
  unit,
  change,
  changeType = 'neutral',
  trend = 'stable',
  status = 'info',
  description,
  className
}: MetricCardProps) {
  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-4 w-4" />;
      case 'down':
        return <TrendingDown className="h-4 w-4" />;
      default:
        return <Minus className="h-4 w-4" />;
    }
  };

  const getTrendColor = () => {
    switch (changeType) {
      case 'increase':
        return 'text-green-600';
      case 'decrease':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'border-green-200 bg-green-50';
      case 'warning':
        return 'border-yellow-200 bg-yellow-50';
      case 'error':
        return 'border-red-200 bg-red-50';
      default:
        return 'border-blue-200 bg-blue-50';
    }
  };

  return (
    <Card className={cn('transition-all hover:shadow-md', getStatusColor(), className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-700">
          {title}
        </CardTitle>
        {status && (
          <Badge 
            variant={status === 'error' ? 'destructive' : 'secondary'}
            className="text-xs"
          >
            {status}
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline space-x-2">
          <div className="text-2xl font-bold text-gray-900">
            {value}
          </div>
          {unit && (
            <div className="text-sm text-gray-500">
              {unit}
            </div>
          )}
        </div>
        
        {change !== undefined && (
          <div className={cn('flex items-center space-x-1 text-sm mt-2', getTrendColor())}>
            {getTrendIcon()}
            <span>
              {change > 0 ? '+' : ''}{change}%
            </span>
            <span className="text-gray-500">vs 上期</span>
          </div>
        )}
        
        {description && (
          <p className="text-xs text-gray-600 mt-2">
            {description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

// 预设的指标卡片组件
export function SOVCard({ value, change, ...props }: Omit<MetricCardProps, 'title' | 'unit'>) {
  return (
    <MetricCard
      title="声量占有率 (SOV)"
      value={value}
      unit="%"
      change={change}
      {...props}
    />
  );
}

export function AccuracyCard({ value, change, ...props }: Omit<MetricCardProps, 'title' | 'unit'>) {
  return (
    <MetricCard
      title="准确性评分"
      value={value}
      unit="/10"
      change={change}
      {...props}
    />
  );
}

export function SentimentCard({ value, change, ...props }: Omit<MetricCardProps, 'title' | 'unit'>) {
  return (
    <MetricCard
      title="情感倾向"
      value={value}
      change={change}
      {...props}
    />
  );
}

export function CitationCard({ value, change, ...props }: Omit<MetricCardProps, 'title' | 'unit'>) {
  return (
    <MetricCard
      title="引用率"
      value={value}
      unit="%"
      change={change}
      {...props}
    />
  );
}
