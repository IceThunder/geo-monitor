# GEO Monitor Frontend

基于 Next.js 14 和 TypeScript 构建的现代化前端应用，专为品牌声量监控系统设计。

## 技术栈

- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **样式**: TailwindCSS
- **UI组件**: Radix UI + 自定义组件库
- **状态管理**: Zustand
- **数据获取**: TanStack Query
- **图表**: Recharts
- **图标**: Lucide React
- **表单**: React Hook Form + Zod

## 项目结构

```
src/
├── app/                    # Next.js App Router页面
│   ├── dashboard/         # 仪表板页面
│   └── tasks/            # 任务管理页面
├── components/            # 组件库
│   ├── ui/               # 基础UI组件
│   ├── dashboard/        # 仪表板专用组件
│   ├── tasks/           # 任务管理组件
│   └── layout/          # 布局组件
└── lib/                  # 工具函数和配置
```

## UI组件库

### 基础组件
- **Button** - 按钮组件，支持多种变体和尺寸
- **Input** - 输入框组件
- **Textarea** - 多行文本输入
- **Select** - 下拉选择器
- **Card** - 卡片容器
- **Badge** - 徽章标签
- **Table** - 数据表格
- **Dialog** - 对话框/模态框
- **Alert** - 警告提示
- **Tabs** - 标签页
- **Form** - 表单组件
- **Toast** - 消息通知
- **Separator** - 分隔线
- **Label** - 标签

### 业务组件
- **MetricCard** - 指标卡片，显示关键业务指标
- **TaskStatusBadge** - 任务状态徽章
- **TaskTable** - 任务列表表格
- **MainLayout** - 主布局组件

## 核心页面

### 仪表板 (`/dashboard`)
- 关键指标概览（SOV、准确性、情感倾向、引用率）
- 多标签页界面（概览、任务管理、分析报告、告警中心）
- 实时数据展示和趋势分析
- 最近活动和告警信息

### 任务创建 (`/tasks/create`)
- 完整的任务配置表单
- 模型选择和参数配置
- 关键词和定位词管理
- 调度设置和成本预估
- 实时表单验证

### 主布局
- 响应式侧边栏导航
- 顶部搜索和通知
- 用户信息和退出功能
- 移动端适配

## 特性

### 设计系统
- 基于 Radix UI 的无障碍组件
- 一致的设计语言和交互模式
- 深色/浅色主题支持
- 响应式设计

### 用户体验
- 流畅的页面切换动画
- 实时数据更新
- 智能表单验证
- 直观的状态反馈

### 开发体验
- 完整的 TypeScript 类型定义
- 组件化架构
- 可复用的业务组件
- 清晰的文件组织结构

## 快速开始

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 启动生产服务器
npm start
```

## 组件使用示例

### 指标卡片
```tsx
import { SOVCard } from '@/components/dashboard/metric-card';

<SOVCard 
  value={23.5}
  change={2.3}
  changeType="increase"
  status="info"
  description="相比上周提升2.3%"
/>
```

### 任务状态徽章
```tsx
import { TaskStatusBadge } from '@/components/dashboard/task-status-badge';

<TaskStatusBadge status="running" showIcon />
```

### 任务表格
```tsx
import { TaskTable } from '@/components/tasks/task-table';

<TaskTable 
  tasks={tasks}
  onTaskAction={handleTaskAction}
  loading={false}
/>
```

## 下一步计划

- [ ] 数据可视化组件集成
- [ ] 更多图表类型支持
- [ ] 主题定制功能
- [ ] 国际化支持
- [ ] 性能优化
- [ ] 单元测试覆盖

## 贡献指南

1. 遵循现有的代码风格和组件设计模式
2. 新组件需要包含完整的 TypeScript 类型定义
3. 确保组件的可访问性和响应式设计
4. 提供清晰的组件文档和使用示例
