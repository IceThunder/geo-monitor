/**
 * Bar Chart Component
 * 基于Recharts的柱状图组件
 */
import React from 'react';
import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface BarChartDataPoint {
  name: string;
  [key: string]: string | number;
}

export interface BarChartProps {
  data: BarChartDataPoint[];
  bars: {
    dataKey: string;
    name: string;
    color: string;
  }[];
  title?: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  className?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
  layout?: 'horizontal' | 'vertical';
}

export function BarChart({
  data,
  bars,
  title,
  height = 300,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  className,
  xAxisLabel,
  yAxisLabel,
  layout = 'vertical',
}: BarChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{`${xAxisLabel || '类别'}: ${label}`}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {`${entry.name}: ${entry.value}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const content = (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart 
        data={data} 
        layout={layout}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
        <XAxis 
          type={layout === 'vertical' ? 'category' : 'number'}
          dataKey={layout === 'vertical' ? 'name' : undefined}
          tick={{ fontSize: 12 }}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={{ stroke: '#e5e7eb' }}
        />
        <YAxis 
          type={layout === 'vertical' ? 'number' : 'category'}
          dataKey={layout === 'horizontal' ? 'name' : undefined}
          tick={{ fontSize: 12 }}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={{ stroke: '#e5e7eb' }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
        {bars.map((bar) => (
          <Bar
            key={bar.dataKey}
            dataKey={bar.dataKey}
            fill={bar.color}
            name={bar.name}
            radius={[2, 2, 0, 0]}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  );

  if (title) {
    return (
      <Card className={cn('w-full', className)}>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          {content}
        </CardContent>
      </Card>
    );
  }

  return <div className={cn('w-full', className)}>{content}</div>;
}

// 预设的柱状图组件
export function KeywordPerformanceChart({ data, className }: { data: BarChartDataPoint[]; className?: string }) {
  return (
    <BarChart
      data={data}
      bars={[
        { dataKey: 'mentions', name: '提及次数', color: '#3b82f6' },
        { dataKey: 'sentiment', name: '情感分值', color: '#10b981' },
      ]}
      title="关键词表现分析"
      xAxisLabel="关键词"
      yAxisLabel="数值"
      layout="vertical"
      className={className}
    />
  );
}

export function CompetitorComparisonChart({ data, className }: { data: BarChartDataPoint[]; className?: string }) {
  return (
    <BarChart
      data={data}
      bars={[
        { dataKey: 'ourBrand', name: '我们的品牌', color: '#3b82f6' },
        { dataKey: 'competitor1', name: '竞品A', color: '#ef4444' },
        { dataKey: 'competitor2', name: '竞品B', color: '#f59e0b' },
      ]}
      title="竞品对比分析"
      xAxisLabel="指标"
      yAxisLabel="分值"
      layout="vertical"
      className={className}
    />
  );
}
