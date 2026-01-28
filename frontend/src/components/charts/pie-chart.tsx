/**
 * Pie Chart Component
 * 基于Recharts的饼图组件
 */
import React from 'react';
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface PieChartDataPoint {
  name: string;
  value: number;
  color?: string;
}

export interface PieChartProps {
  data: PieChartDataPoint[];
  title?: string;
  height?: number;
  showLegend?: boolean;
  showTooltip?: boolean;
  className?: string;
  colors?: string[];
  innerRadius?: number;
  outerRadius?: number;
  showLabels?: boolean;
}

const DEFAULT_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', 
  '#06b6d4', '#84cc16', '#f97316', '#ec4899', '#6b7280'
];

export function PieChart({
  data,
  title,
  height = 300,
  showLegend = true,
  showTooltip = true,
  className,
  colors = DEFAULT_COLORS,
  innerRadius = 0,
  outerRadius = 80,
  showLabels = true,
}: PieChartProps) {
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0];
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{data.name}</p>
          <p className="text-sm" style={{ color: data.color }}>
            {`数值: ${data.value}`}
          </p>
          <p className="text-sm text-gray-600">
            {`占比: ${((data.value / data.payload.total) * 100).toFixed(1)}%`}
          </p>
        </div>
      );
    }
    return null;
  };

  const renderLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }: any) => {
    if (percent < 0.05) return null; // 不显示小于5%的标签
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize={12}
        fontWeight="bold"
      >
        {`${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  // 计算总值用于百分比计算
  const dataWithTotal = data.map(item => ({
    ...item,
    total: data.reduce((sum, d) => sum + d.value, 0)
  }));

  const content = (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsPieChart>
        <Pie
          data={dataWithTotal}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={showLabels ? renderLabel : false}
          outerRadius={outerRadius}
          innerRadius={innerRadius}
          fill="#8884d8"
          dataKey="value"
        >
          {dataWithTotal.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.color || colors[index % colors.length]} 
            />
          ))}
        </Pie>
        {showTooltip && <Tooltip content={<CustomTooltip />} />}
        {showLegend && <Legend />}
      </RechartsPieChart>
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

// 预设的饼图组件
export function SentimentDistributionChart({ data, className }: { data: PieChartDataPoint[]; className?: string }) {
  return (
    <PieChart
      data={data}
      title="情感分布"
      colors={['#10b981', '#6b7280', '#ef4444']}
      className={className}
    />
  );
}

export function ChannelDistributionChart({ data, className }: { data: PieChartDataPoint[]; className?: string }) {
  return (
    <PieChart
      data={data}
      title="渠道分布"
      colors={['#3b82f6', '#f59e0b', '#10b981', '#ef4444', '#8b5cf6']}
      className={className}
    />
  );
}

export function DonutChart({ data, title, className }: { data: PieChartDataPoint[]; title?: string; className?: string }) {
  return (
    <PieChart
      data={data}
      title={title}
      innerRadius={40}
      outerRadius={80}
      className={className}
    />
  );
}
