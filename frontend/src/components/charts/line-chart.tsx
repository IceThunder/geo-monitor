/**
 * Line Chart Component
 * 基于Recharts的折线图组件
 */
import React from 'react';
import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface LineChartDataPoint {
  name: string;
  [key: string]: string | number;
}

export interface LineChartProps {
  data: LineChartDataPoint[];
  lines: {
    dataKey: string;
    name: string;
    color: string;
    strokeWidth?: number;
  }[];
  title?: string;
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
  showTooltip?: boolean;
  className?: string;
  xAxisLabel?: string;
  yAxisLabel?: string;
}

export function LineChart({
  data,
  lines,
  title,
  height = 300,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  className,
  xAxisLabel,
  yAxisLabel,
}: LineChartProps) {
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{`${xAxisLabel || '时间'}: ${label}`}</p>
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
      <RechartsLineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />}
        <XAxis 
          dataKey="name" 
          tick={{ fontSize: 12 }}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={{ stroke: '#e5e7eb' }}
        />
        <YAxis 
          tick={{ fontSize: 12 }}
          axisLine={{ stroke: '#e5e7eb' }}
          tickLine={{ stroke: '#e5e7eb' }}
        />
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
        {lines.map((line) => (
          <Line
            key={line.dataKey}
            type="monotone"
            dataKey={line.dataKey}
            stroke={line.color}
            strokeWidth={line.strokeWidth || 2}
            name={line.name}
            dot={{ fill: line.color, strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6, stroke: line.color, strokeWidth: 2 }}
          />
        ))}
      </RechartsLineChart>
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

// 预设的折线图组件
export function SOVTrendChart({ data, className }: { data: LineChartDataPoint[]; className?: string }) {
  return (
    <LineChart
      data={data}
      lines={[
        { dataKey: 'sov', name: '声量占有率', color: '#3b82f6' },
        { dataKey: 'target', name: '目标值', color: '#ef4444' },
      ]}
      title="声量占有率趋势"
      xAxisLabel="日期"
      yAxisLabel="百分比 (%)"
      className={className}
    />
  );
}

export function SentimentTrendChart({ data, className }: { data: LineChartDataPoint[]; className?: string }) {
  return (
    <LineChart
      data={data}
      lines={[
        { dataKey: 'positive', name: '正面情感', color: '#10b981' },
        { dataKey: 'neutral', name: '中性情感', color: '#6b7280' },
        { dataKey: 'negative', name: '负面情感', color: '#ef4444' },
      ]}
      title="情感趋势分析"
      xAxisLabel="日期"
      yAxisLabel="情感分值"
      className={className}
    />
  );
}
