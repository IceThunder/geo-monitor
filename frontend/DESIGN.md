# GEO 监控系统 - 前端设计文档

## 技术选型

| 组件 | 技术栈 | 版本要求 |
|------|--------|----------|
| 框架 | Next.js (App Router) | 14.0+ |
| 语言 | TypeScript | 5.0+ |
| UI 组件库 | Shadcn UI | 0.x |
| 样式 | TailwindCSS | 3.4+ |
| 状态管理 | Zustand | 0.x |
| HTTP 客户端 | Axios / TanStack Query | 7.x / 5.x |
| 图表 | Recharts | 2.x |
| 日期处理 | date-fns | 3.x |
| 表单处理 | React Hook Form + Zod | 7.x + 3.x |
| 图标 | Lucide React | 0.x |

## 页面结构设计

```
frontend/src/app/
├── layout.tsx                    # 根布局（包含全局 Provider）
├── page.tsx                      # Dashboard 首页
├── globals.css                   # 全局样式
├── (auth)/
│   ├── login/
│   │   └── page.tsx              # 登录页
│   └── layout.tsx                # 认证布局
├── (dashboard)/
│   ├── layout.tsx                # 主布局（侧边栏 + Header）
│   ├── tasks/
│   │   ├── page.tsx              # 任务列表页
│   │   ├── [id]/
│   │   │   ├── page.tsx          # 任务详情页
│   │   │   └── edit/page.tsx     # 任务编辑页
│   │   └── new/page.tsx          # 新建任务页
│   ├── metrics/
│   │   ├── page.tsx              # 指标分析页
│   │   └── sov/page.tsx          # SOV 详情页
│   ├── reports/
│   │   ├── page.tsx              # 报表列表页
│   │   └── export/page.tsx       # 报表导出页
│   ├── alerts/
│   │   └── page.tsx              # 告警中心
│   └── settings/
│       └── page.tsx              # 系统设置
└── api/
    └── [...nextauth]/route.ts    # NextAuth API 路由
```

## 组件设计

### 核心组件结构

```
frontend/src/components/
├── ui/                           # 基础 UI 组件 (Shadcn)
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── select.tsx
│   ├── table.tsx
│   ├── dialog.tsx
│   ├── toast.tsx
│   ├── badge.tsx
│   └── ...
├── layout/
│   ├── Sidebar.tsx               # 侧边导航栏
│   ├── Header.tsx                # 顶部导航栏
│   └── Breadcrumb.tsx            # 面包屑导航
├── dashboard/
│   ├── MetricCard.tsx            # 指标卡片
│   ├── TrendChart.tsx            # 趋势图表
│   ├── SOVChart.tsx              # SOV 饼图/柱状图
│   ├── ModelComparison.tsx       # 模型对比图表
│   └── RecentActivity.tsx        # 最近活动列表
├── tasks/
│   ├── TaskList.tsx              # 任务列表
│   ├── TaskCard.tsx              # 任务卡片
│   ├── TaskForm.tsx              # 任务创建/编辑表单
│   ├── KeywordInput.tsx          # 关键词输入组件
│   └── ModelSelector.tsx         # 模型选择器
├── metrics/
│   ├── DataTable.tsx             # 数据表格
│   ├── FilterBar.tsx             # 筛选栏
│   ├── DateRangePicker.tsx       # 日期范围选择器
│   └── ExportButton.tsx          # 导出按钮
└── alerts/
    ├── AlertList.tsx             # 告警列表
    └── AlertItem.tsx             # 单个告警项
```

### 页面功能详情

#### 1. Dashboard 首页

**核心指标卡片：**
- 总监控任务数
- 活跃任务数
- 平均 SOV 分数
- 平均准确性评分
- 今日告警数

**图表组件：**
- SOV 趋势图（近 7/30 天）
- 模型分布饼图
- 品牌声量柱状图

**最近告警列表：**
- 显示最新 5 条未读告警
- 支持快速跳转处理

#### 2. 任务配置页

**任务列表：**
- 支持分页浏览
- 搜索筛选（按名称、关键词）
- 状态筛选（全部/运行中/已暂停）
- 操作按钮（编辑、删除、触发执行）

**创建/编辑任务：**
- 任务名称和描述
- Cron 调度表达式（可视化选择器）
- 关键词管理（支持批量导入 CSV）
- 监控模型选择（多选）
- Prompt 模板选择

#### 3. 指标分析页

**数据筛选：**
- 时间范围选择
- 关键词筛选
- 模型筛选
- 指标类型选择

**数据表格：**
- 关键词
- 模型
- SOV 分数
- 准确性
- 情感分数
- 引用率
- 定位词命中
- 操作（查看详情）

**趋势图表：**
- 支持多指标叠加显示
- 支持多模型对比
- 支持下载 PNG/SVG

#### 4. 报表导出页

**报表类型：**
- SOV 分析报表
- 准确性评估报表
- 品牌对比报表
- 综合分析报表

**导出格式：**
- CSV
- Excel (xlsx)
- PDF

**定时报表：**
- 配置定时发送报表到邮箱
- 配置报表接收人列表

#### 5. 告警中心

**告警列表：**
- 按时间排序
- 按类型筛选
- 按已读/未读筛选
- 批量标记已读

**告警详情：**
- 触发时间
- 任务名称
- 告警类型
- 触发指标值
- 阈值设置
- 处理建议

#### 6. 系统设置

**API 配置：**
- OpenRouter API Key 管理
- Webhook URL 配置

**告警设置：**
- 准确性阈值设置
- 情感分数阈值设置
- 通知渠道配置（邮件/Webhook）

**团队管理：**
- 成员列表
- 角色权限分配

## 状态管理方案

### Zustand Store 设计

```typescript
// frontend/src/lib/stores/

// 1. 任务状态管理
interface TaskStore {
  tasks: Task[]
  currentTask: Task | null
  isLoading: boolean
  error: string | null
  
  fetchTasks: (params?: TaskFilter) => Promise<void>
  fetchTaskById: (id: string) => Promise<void>
  createTask: (data: CreateTaskDTO) => Promise<void>
  updateTask: (id: string, data: UpdateTaskDTO) => Promise<void>
  deleteTask: (id: string) => Promise<void>
  triggerTask: (id: string) => Promise<void>
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  currentTask: null,
  isLoading: false,
  error: null,
  
  fetchTasks: async (params) => {
    set({ isLoading: true })
    try {
      const data = await taskApi.getTasks(params)
      set({ tasks: data.data, isLoading: false })
    } catch (error) {
      set({ error: error.message, isLoading: false })
    }
  },
  // ... 其他方法
}))

// 2. 指标数据状态管理
interface MetricStore {
  sovData: SOVData[]
  accuracyData: AccuracyData[]
  comparisonData: ComparisonData
  isLoading: boolean
  
  fetchSOVTrend: (params: MetricParams) => Promise<void>
  fetchAccuracyTrend: (params: MetricParams) => Promise<void>
  fetchComparison: (params: MetricParams) => Promise<void>
}

export const useMetricStore = create<MetricStore>((set) => ({
  sovData: [],
  accuracyData: [],
  comparisonData: null,
  isLoading: false,
  
  fetchSOVTrend: async (params) => {
    set({ isLoading: true })
    const data = await metricApi.getSOVTrend(params)
    set({ sovData: data, isLoading: false })
  },
  // ... 其他方法
}))

// 3. 告警状态管理
interface AlertStore {
  alerts: Alert[]
  unreadCount: number
  isLoading: boolean
  
  fetchAlerts: (params?: AlertFilter) => Promise<void>
  markAsRead: (id: string) => Promise<void>
  markAllAsRead: () => Promise<void>
}

export const useAlertStore = create<AlertStore>((set) => ({
  alerts: [],
  unreadCount: 0,
  isLoading: false,
  
  fetchAlerts: async (params) => {
    set({ isLoading: true })
    const data = await alertApi.getAlerts(params)
    set({ alerts: data.data, unreadCount: data.unread_count, isLoading: false })
  },
  // ... 其他方法
}))
```

### TanStack Query 数据获取

```typescript
// frontend/src/lib/hooks/useTasks.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

// 查询任务列表
export function useTasks(params?: TaskFilter) {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: () => taskApi.getTasks(params),
    staleTime: 5 * 60 * 1000, // 5分钟内不重新请求
  })
}

// 查询单个任务
export function useTask(id: string) {
  return useQuery({
    queryKey: ['task', id],
    queryFn: () => taskApi.getTaskById(id),
    enabled: !!id,
  })
}

// 创建任务
export function useCreateTask() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateTaskDTO) => taskApi.createTask(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}

// 删除任务
export function useDeleteTask() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: string) => taskApi.deleteTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] })
    },
  })
}
```

## API 对接方案

### Axios 实例配置

```typescript
// frontend/src/lib/api/client.ts
import axios from 'axios'

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 - 添加 JWT Token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器 - 处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 过期，清除本地存储并跳转登录
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

### API 客户端封装

```typescript
// frontend/src/lib/api/tasks.ts
import apiClient from './client'
import { Task, CreateTaskDTO, UpdateTaskDTO, TaskFilter, PaginatedResponse } from './types'

export const taskApi = {
  // 获取任务列表
  getTasks: async (params?: TaskFilter): Promise<PaginatedResponse<Task>> => {
    const response = await apiClient.get('/tasks', { params })
    return response.data
  },
  
  // 获取单个任务
  getTaskById: async (id: string): Promise<Task> => {
    const response = await apiClient.get(`/tasks/${id}`)
    return response.data
  },
  
  // 创建任务
  createTask: async (data: CreateTaskDTO): Promise<Task> => {
    const response = await apiClient.post('/tasks', data)
    return response.data
  },
  
  // 更新任务
  updateTask: async (id: string, data: UpdateTaskDTO): Promise<Task> => {
    const response = await apiClient.put(`/tasks/${id}`, data)
    return response.data
  },
  
  // 删除任务
  deleteTask: async (id: string): Promise<void> => {
    await apiClient.delete(`/tasks/${id}`)
  },
  
  // 手动触发任务
  triggerTask: async (id: string): Promise<{ run_id: string }> => {
    const response = await apiClient.post(`/tasks/${id}/trigger`)
    return response.data
  },
}

// frontend/src/lib/api/metrics.ts
export const metricApi = {
  // 获取 Dashboard 概览
  getDashboardOverview: async (params: DateRangeParams) => {
    const response = await apiClient.get('/dashboard/overview', { params })
    return response.data
  },
  
  // 获取 SOV 趋势
  getSOVTrend: async (params: SOVParams) => {
    const response = await apiClient.get('/metrics/sov', { params })
    return response.data
  },
  
  // 获取准确性趋势
  getAccuracyTrend: async (params: AccuracyParams) => {
    const response = await apiClient.get('/metrics/accuracy', { params })
    return response.data
  },
  
  // 获取模型对比数据
  getModelComparison: async (params: ComparisonParams) => {
    const response = await apiClient.get('/metrics/comparison', { params })
    return response.data
  },
  
  // 导出报表
  exportReport: async (params: ExportParams): Promise<Blob> => {
    const response = await apiClient.get('/reports/export', {
      params,
      responseType: 'blob',
    })
    return response.data
  },
}

// frontend/src/lib/api/alerts.ts
export const alertApi = {
  // 获取告警列表
  getAlerts: async (params?: AlertFilter): Promise<AlertListResponse> => {
    const response = await apiClient.get('/alerts', { params })
    return response.data
  },
  
  // 标记告警已读
  markAsRead: async (id: string): Promise<void> => {
    await apiClient.put(`/alerts/${id}/read`)
  },
  
  // 全部标记已读
  markAllAsRead: async (): Promise<void> => {
    await apiClient.put('/alerts/read-all')
  },
  
  // 测试 Webhook
  testWebhook: async (url: string): Promise<{ success: boolean }> => {
    const response = await apiClient.post('/webhooks/test', { webhook_url: url })
    return response.data
  },
}
```

### 类型定义

```typescript
// frontend/src/lib/api/types.ts

// 任务相关
export interface Task {
  id: string
  name: string
  description?: string
  schedule_cron: string
  is_active: boolean
  models: string[]
  keywords: string[]
  created_at: string
  updated_at: string
  last_run_status?: string
  last_run_time?: string
}

export interface CreateTaskDTO {
  name: string
  description?: string
  schedule_cron: string
  models: string[]
  keywords: string[]
  prompt_template_id?: string
}

export interface UpdateTaskDTO extends Partial<CreateTaskDTO> {
  is_active?: boolean
}

export interface TaskFilter {
  page?: number
  limit?: number
  is_active?: boolean
  search?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
}

// 指标相关
export interface SOVData {
  keyword: string
  model: string
  data: Array<{
    date: string
    sov: number
  }>
}

export interface AccuracyData {
  task_id: string
  data: Array<{
    date: string
    avg_accuracy: number
    min_accuracy: number
    max_accuracy: number
  }>
}

export interface ComparisonData {
  keyword: string
  models: {
    [modelId: string]: {
      sov: number
      accuracy: number
      sentiment: number
    }
  }
}

// 告警相关
export interface Alert {
  id: string
  task_id: string
  task_name: string
  alert_type: string
  alert_message: string
  metric_name: string
  metric_value: number
  threshold_value: number
  is_read: boolean
  created_at: string
}

export interface AlertFilter {
  is_read?: boolean
  limit?: number
  offset?: number
}

export interface AlertListResponse {
  data: Alert[]
  unread_count: number
}

// 通用
export interface DateRangeParams {
  start_date: string
  end_date: string
}
```

## UI 组件实现示例

### Dashboard 页面组件

```tsx
// frontend/src/app/page.tsx
'use client'

import { MetricCard } from '@/components/dashboard/MetricCard'
import { TrendChart } from '@/components/dashboard/TrendChart'
import { SOVChart } from '@/components/dashboard/SOVChart'
import { RecentAlerts } from '@/components/dashboard/RecentAlerts'
import { useDashboard } from '@/lib/hooks/useDashboard'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

export default function DashboardPage() {
  const { data, isLoading, error } = useDashboard()
  
  if (isLoading) {
    return (
      <div className="p-6 space-y-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    )
  }
  
  if (error) {
    return <div className="p-6 text-red-500">加载失败: {error.message}</div>
  }
  
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">监控概览</h1>
      
      {/* 核心指标卡片 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="总任务数"
          value={data.total_tasks}
          trend={data.tasks_trend}
          icon="task"
        />
        <MetricCard
          title="活跃任务"
          value={data.active_tasks}
          trend={data.active_trend}
          icon="active"
        />
        <MetricCard
          title="平均 SOV"
          value={`${data.avg_sov}%`}
          trend={data.sov_trend}
          icon="chart"
        />
        <MetricCard
          title="平均准确性"
          value={data.avg_accuracy.toFixed(1)}
          trend={data.accuracy_trend}
          icon="accuracy"
        />
      </div>
      
      {/* 图表区域 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>SOV 趋势</CardTitle>
          </CardHeader>
          <CardContent>
            <TrendChart data={data.sov_trend_data} />
          </CardContent>
        </Card>
        
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>品牌分布</CardTitle>
          </CardHeader>
          <CardContent>
            <SOVChart data={data.brand_distribution} />
          </CardContent>
        </Card>
      </div>
      
      {/* 最近告警 */}
      <Card>
        <CardHeader>
          <CardTitle>最近告警</CardTitle>
        </CardHeader>
        <CardContent>
          <RecentAlerts alerts={data.recent_alerts} />
        </CardContent>
      </Card>
    </div>
  )
}
```

### 任务配置页面组件

```tsx
// frontend/src/app/tasks/page.tsx
'use client'

import { useTasks } from '@/lib/hooks/useTasks'
import { TaskList } from '@/components/tasks/TaskList'
import { Button } from '@/components/ui/button'
import { Plus } from 'lucide-react'
import Link from 'next/link'

export default function TasksPage() {
  const { data, isLoading, error } = useTasks()
  
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">监控任务</h1>
        <Link href="/tasks/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            新建任务
          </Button>
        </Link>
      </div>
      
      {isLoading && <div className="text-center">加载中...</div>}
      {error && <div className="text-red-500">加载失败</div>}
      
      {data && (
        <TaskList
          tasks={data.data}
          total={data.total}
          page={data.page}
          limit={data.limit}
        />
      )}
    </div>
  )
}
```

## 依赖配置

### package.json

```json
{
  "name": "geo-monitor-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.4",
    "zustand": "^4.4.7",
    "recharts": "^2.10.3",
    "lucide-react": "^0.303.0",
    "date-fns": "^3.2.0",
    "react-hook-form": "^7.49.2",
    "@hookform/resolvers": "^3.3.2",
    "zod": "^3.22.4",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.2.0"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "@types/node": "^20.10.6",
    "@types/react": "^18.2.46",
    "@types/react-dom": "^18.2.18",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.33",
    "eslint": "^8.56.0",
    "eslint-config-next": "14.0.4"
  }
}
```

### TailwindCSS 配置

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

## 部署配置

### Dockerfile

```dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000

CMD ["node", "server.js"]
```

### 环境变量示例 (.env.example)

```
# API 地址
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Supabase 配置
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# NextAuth 配置
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret

# OpenRouter (前端调用需要)
NEXT_PUBLIC_OPENROUTER_SITE_URL=http://localhost:3000
NEXT_PUBLIC_OPENROUTER_APP_NAME=GEO Monitor
```
