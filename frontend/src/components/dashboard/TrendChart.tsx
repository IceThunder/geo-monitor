'use client';

import { useEffect, useRef } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { format, parseISO } from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface TrendChartProps {
  title: string;
  data: Array<{
    date: string;
    value: number;
  }>;
  yAxisLabel?: string;
  dataKey?: string;
  color?: string;
  className?: string;
}

export function TrendChart({
  title,
  data,
  yAxisLabel,
  dataKey = 'value',
  color = '#3b82f6',
  className,
}: TrendChartProps) {
  const chartData = data.map((item) => ({
    ...item,
    [dataKey]: item.value,
  }));

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tickFormatter={(value) =>
                  format(parseISO(value), 'MM/dd', { locale: zhCN })
                }
                className="text-xs"
              />
              <YAxis
                tickFormatter={(value) => value.toFixed(1)}
                className="text-xs"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
                labelFormatter={(value) =>
                  format(parseISO(value as string), 'yyyy-MM-dd', {
                    locale: zhCN,
                  })
                }
                formatter={(value: number) => [
                  value.toFixed(2),
                  yAxisLabel || dataKey,
                ]}
              />
              <Line
                type="monotone"
                dataKey={dataKey}
                stroke={color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
