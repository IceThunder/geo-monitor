# GEO 监控系统技术白皮书

## 面向大模型时代的品牌声量与准确性实时监控平台

# 执行摘要

本白皮书定义了 “GEO 监控系统” 的技术架构与实施细节。随着搜索行为从 “寻找链接” 向 “获取答案” 迁移，该系统旨在帮助企业量化并优化其在 ChatGPT、Claude、Gemini 等主流模型中的表现。

### 核心目标

* **实时监控：** 自动化追踪品牌在多模型中的 SOV（声量份额）、引用率与准确性。
* **多租户支持：** 为不同企业团队提供隔离的数据环境与 OpenRouter API 配置。
* **量化决策：** 提供可视化仪表盘，辅助内容团队验证 “定位词” 与 “知识库” 优化效果。

### 交付范围

* **后端服务：** 基于 Python/Go 的任务调度器与 REST API 网关。
* **前端控制台：** 包含监控配置、数据可视化与告警中心的管理界面。
* **非目标：** 本系统不涉及内容自动生成或 SEO 排名抓取，仅专注于生成式引擎的输出审计。

# 需求说明 (PRD)

系统设计需满足以下功能与非功能指标，确保在高并发与多模型环境下稳定运行。

| 模块     | 需求描述                                                   | 验收标准                                                     | 优先级 |
| ---------- | ------------------------------------------------------------ | -------------------------------------------------------------- | -------- |
| 监控管理 | 支持关键词、品牌词及竞品词的增删改查；配置 Cron 调度策略。 | 单租户支持>100 个关键词；调度误差<10 秒。                    | P0     |
| 模型路由 | 集成 OpenRouter API，支持模型优先级配置与自动降级。        | 支持 GPT-4o, Claude-3.5, Gemini 1.5 Pro 等主流模型无缝切换。 | P0     |
| 指标计算 | 自动计算 SOV、情感得分、准确性、引用率。                   | 计算延迟<1 分钟；准确率（与人工标定对比）>90%。              | P0     |
| 告警通知 | 当指标（如情感分）跌破阈值时触发 Webhook/Email。           | 通知延迟<5 分钟；支持自定义告警规则。                        | P1     |

# 系统架构设计

系统采用微服务架构，以 API Gateway 为入口，通过消息队列解耦任务调度与模型执行，确保高可用性。

暂时无法在AnyGen文档外展示此内容

**关键组件说明：**

* **Task Manager：** 负责监控任务的生命周期管理，解析 Cron 表达式并生产任务消息。
* **Model Executor：** 无状态 Worker 节点，负责调用 OpenRouter 接口，处理速率限制（Rate Limiting）与重试逻辑。
* **Result Analyzer：** 核心计算引擎，执行 NLP 分析、实体提取、情感判断与指标打分。

# 数据架构与详细设计

为支撑多租户隔离与高并发写入，本系统采用 **Supabase (PostgreSQL)** 作为核心数据底座，深度利用其 RLS (Row Level Security) 特性保障数据安全，并通过 `pg_cron` 实现数据库原生的轻量级任务调度。

## 数据表关联性校验与优化建议 (v1.1)

针对 v1.0 版本的 ERD 校验发现，使用数组字段存储核心关系限制了查询灵活性，且 Metrics 聚合粒度不足以支撑多模型对比分析。以下是 v1.1 的关键优化结论与重构方案：

### 关系型结构重构

* **拆分数组字段：** 原 `target_models` 与 `keywords` 拆分为独立关联表（Task-Model, Task-Keyword），支持单任务关联多模型与多关键词的灵活配置与索引优化。
* **粒度细化：** `metrics_snapshot` 从 “Run” 级调整为 “Run + Model” 级，确保能独立记录 GPT-4 与 Claude 在同一次任务中的不同表现（准确性、SOV）。

### 安全与一致性

* **RLS 优化：** 摒弃子查询，改用 `auth.jwt()` 直接获取 Tenant ID，大幅降低鉴权开销。
* **级联策略：** 任务删除时，配置 `ON DELETE CASCADE` 自动清理关联的运行记录与指标快照，防止脏数据残留。

## DDL 关键调整示例

以下是优化后的 Schema 定义，集成了关系表设计与增强的 RLS 策略。

```SQL
-- 1. 监控任务表 (瘦身版)
create table monitor_tasks (
  id uuid primary key default gen_random_uuid(),
  tenant_id uuid not null, 
  schedule_cron text default '0 0 * * *',
  is_active boolean default true,
  created_at timestamptz default now()
);

-- 2. 任务 - 模型关联表 (新增)
create table task_models (
  task_id uuid references monitor_tasks(id) on delete cascade,
  model_id text not null, -- e.g. 'openai/gpt-4o'
  priority int default 10,
  primary key (task_id, model_id)
);

-- 3. 任务 - 关键词关联表 (新增)
create table task_keywords (
  task_id uuid references monitor_tasks(id) on delete cascade,
  keyword text not null,
  primary key (task_id, keyword)
);

-- 4. 指标快照 (增加 model_id 维度)
create table metrics_snapshot (
  id uuid primary key default gen_random_uuid(),
  run_id uuid references task_runs(id) on delete cascade,
  model_id text not null, -- 记录具体产生数据的模型
  sov_score numeric(5,2),
  accuracy_score int,
  unique (run_id, model_id) -- 复合唯一约束
);

-- 5. RLS 策略示例 (高性能)
alter table monitor_tasks enable row level security;

create policy "Tenant Isolation" on monitor_tasks
using (tenant_id = current_setting('app.jwt_tenant_id', true)::uuid);
```

# 接口设计

API 遵循 RESTful 规范，使用 JWT 进行身份验证。所有写操作需验证 Tenant ID 以确保多租户安全。

```JSON
{
  "keyword": "企业级 CRM",
  "models": ["openai/gpt-4", "anthropic/claude-3-opus"],
  "schedule": "0 0 * * *", // 每天零点执行
  "prompts": {
    "template_id": "default_comparison",
    "custom_vars": {"category": "SaaS"}
  }
}
```

## 主要端点列表

| 方法 | 路径                           | 描述                                |
| ------ | -------------------------------- | ------------------------------------- |
| GET  | /api/v1/dashboard/metrics      | 获取指定时间范围的 SOV 与趋势数据。 |
| POST | /api/v1/credentials/openrouter | 绑定租户的 OpenRouter API Key。     |
| GET  | /api/v1/reports/export         | 导出 PDF/CSV 格式的分析报表。       |
| POST | /api/v1/webhooks/test          | 测试告警 Webhook 连通性。           |

# 关键模块与指标算法

本系统基于[GEO 方法论](https://a16z.com/geo-over-seo/)实现以下核心指标的自动化计算，确保数据具有业务指导意义。

### AI SOV (声量份额)

**定义：** 品牌在特定品类查询结果中出现的频率。

$$
SOV = \frac{\text{Brand Mentions}}{\text{Total Models Queried}} \times 100\%
$$

### 引用率 (Citation Rate)

**定义：** AI 回答中包含指向品牌官网链接的比例。

$$
CR = \frac{\text{Answers with Link}}{\text{Total Mentions}}
$$

## 解析器逻辑 (Parser Logic)

1. **定位词命中 (Positioning Hit)：** 计算品牌核心卖点（如 “高性价比”、“企业级”）与品牌名称在同一回答中出现的概率。算法采用滑动窗口（Window Size=50 tokens）检测共现。
2. **准确性得分 (Accuracy Score)：** 调用 Evaluator Model（如 GPT-4o）将模型回答与预存的 “品牌 Fact Sheet” 进行比对，按 1-10 分打分，重点检测幻觉（如错误的价格或功能）。
3. **实体提取：** 使用轻量级 NER 模型提取回答中的竞争对手品牌，计算相对 SOV。

# Prompt 与评估策略

为了标准化输出并便于程序解析，系统强制要求模型以 JSON 格式返回评估结果（Function Calling 模式）。

```JSON
You are a Brand Auditor. Analyze the following user query about [Category].
User Query: "${query}"

Output Requirements:
1. List all brands mentioned.
2. For each brand, identify the sentiment (Positive/Neutral/Negative).
3. Check if a URL link is provided for the brand.

Response Format (JSON only):
{
  "brands": [
    {
      "name": "BrandA",
      "sentiment": "Positive",
      "has_link": true,
      "positioning_keywords_hit": ["fast", "reliable"],
      "accuracy_score": 9  // 1-10 based on provided fact sheet
    }
  ]
}
```

# 端到端工作流

系统从任务配置到最终生成报告的端到端数据流如下：

* **步骤 1 - 任务配置 (Configuration)：** 用户登录控制台，定义监控任务。输入监控关键词（如 “企业级 CRM”），选择对比模型（如 GPT-4, Claude-3），并设置调度频率（如 “每天 09:00”）。数据被加密存储至 PostgreSQL。
* **步骤 2 - 调度触发 (Scheduling)：** 数据库内置的 pg\_cron 服务根据 Cron 表达式定时触发。它通过 Webhook 调用 Task Manager 服务，Task Manager 生成具体的任务指令并推入 Redis 消息队列。
* **步骤 3 - 模型执行 (Execution)：** Model Executor 工作节点从 Redis 队列中抢占任务。它将用户关键词封装进标准 Prompt 模板，并发调用 OpenRouter API。如果遇到 API 限流 (HTTP 429)，Worker 会自动执行指数退避重试。
* **步骤 4 - 结果分析 (Analysis)：** 大模型返回 JSON 格式的评估数据。Result Analyzer 接收响应，校验 JSON 格式，计算 SOV、准确性得分及情感倾向，并将结构化结果写入数据库。
* **步骤 5 - 告警与反馈 (Reporting)：** 系统检查新生成的指标是否低于用户设定的阈值（如 “准确性 < 6 分”）。如果触发条件，系统通过 Webhook 或邮件发送实时告警，并更新仪表盘数据。

# 前端界面设计

控制台采用左侧导航布局，核心页面如下：

* **概览 (Dashboard)：** 展示全局 SOV 趋势图、最新告警、模型 Token 消耗成本。
* **任务配置 (Task Config)：** 向导式创建监控任务，支持 CSV 批量导入关键词与品牌词库。
* **分析报表 (Reports)：** 详细的品牌对比分析，支持按模型（GPT vs Claude）维度切分数据。
* **设置 (Settings)：** API Key 管理（OpenRouter）、成员权限分配、Webhook 通知渠道配置。

# 在线服务优先架构 (Cloud-Native)

为降低运维成本并提升交付速度，本系统采用 “在线服务优先” 策略，利用免费层（Free Tier）资源构建高可用架构。核心原则：**不仅服务于代码，更服务于数据流。**

## 架构选型与服务矩阵

| 层级                | 选型服务       | 免费层额度 (参考)   | 架构角色                                                            |
| --------------------- | ---------------- | --------------------- | --------------------------------------------------------------------- |
| **数据层**    | Supabase       | 500MB DB / 5GB 带宽 | Postgres 数据库、Auth 认证、pg\_cron 调度、Storage (原始 HTML 存储) |
| **后端/计算** | Railway / Edge | \$5.00/月 (Railway) | Python Worker (执行耗时爬虫与分析任务), FastAPI 网关                |
| **消息队列**  | Upstash Redis  | 10,000 req/day      | 任务队列缓冲、速率限制 (Rate Limiting) 计数器                       |
| **大模型**    | OpenRouter     | 按量付费            | 统一模型网关，聚合 GPT-4, Claude, Gemini 等接口                     |
| **可观测性**  | Grafana Cloud  | 10k metrics series  | 系统监控仪表盘、日志聚合                                            |

# 第三方免费服务注册清单

本系统采用 “Free Tier First” 策略，以下基础服务需在部署前完成注册并获取密钥。

| 服务/组件                           | 免费额度          | 核心 ENV 变量                                        | 准备事项                                                              |
| ------------------------------------- | ------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------- |
| **Supabase**(PostgreSQL)      | 500MB DB 5GB 带宽 | `SUPABASE_URLSUPABASE_SERVICE_ROLE_KEY`          | 注册后创建 Project，记录 DB Password，并在 SQL Editor 启用 pg\_cron。 |
| **Upstash**(Redis)            | 10,000 req/day    | `UPSTASH_REDIS_REST_URLUPSTASH_REDIS_REST_TOKEN` | 创建 Global Redis 数据库，选择靠近应用服务器的 Region。               |
| **OpenRouter**(LLM Gateway)   | 按量付费 (无门槛) | `OPENROUTER_API_KEY`                             | 建议预充值 \$5 用于测试。创建 Key 时建议设置 Credit Limit。           |
| **Railway**(Hosting)          | \$5 Trial Credit  | `RAILWAY_TOKEN`                                  | 关联 GitHub 账号。建议安装 Railway CLI 用于本地调试与部署。           |
| **Grafana Cloud**(Monitoring) | 10k Metrics       | `GRAFANA_USER_IDGRAFANA_API_KEY`                 | 配置 Prometheus 抓取端点或使用 OpenTelemetry 推送 Logs。              |

## 部署指南：从零到上线

1. **初始化 Supabase：** 创建项目，在 SQL Editor 中执行上述 DDL 脚本。启用 `Database Webhooks` 用于告警触发。
2. **配置 Upstash Redis：** 创建 Global Database，获取 `UPSTASH_REDIS_REST_URL` 与 Token，用于 Python Worker 的任务队列。
3. **​部署后端 (Railway)：​**连接 GitHub 仓库，设置环境变量： - `SUPABASE_URL` & `SUPABASE_KEY`- `OPENROUTER_API_KEY` (系统级兜底 Key) - `REDIS_URL`
4. **前端托管 (Vercel)：** 导入 Next.js/React 项目，配置 `NEXT_PUBLIC_SUPABASE_URL`。利用 Vercel Analytics 监控用户访问。
5. **启动调度：** 在 Supabase 中执行 SQL 开启 Cron：`select cron.schedule('*/30 * * * *', $$call_worker_endpoint$$);`

## 运维与成本控制手册

### 熔断与限流策略

为防止 API 费用超支与被封禁：

* **Token 熔断：** 单次任务消耗超过 \$1.00 立即终止并告警。
* **速率平滑：** 利用 Upstash 实现漏桶算法，限制 OpenRouter 调用不超过 20 RPM (Requests Per Minute)。
* **退避重试：** 遇到 429 错误时，执行指数退避 (Exponential Backoff)，最大重试 3 次。

### 数据生命周期 (Cost Optimization)

针对 Supabase 500MB 限制的优化：

* **冷热分离：** `model_outputs` 表中的 `raw_response` (大文本) 在 7 天后自动迁移至 Supabase Storage (更便宜) 或直接归档。
* **指标留存：** `metrics_snapshot` (纯数字) 永久保留，便于生成年度趋势报告。

# 安全与合规

* **密钥加密：** 用户提供的 OpenRouter Key 使用 AES-256 加密存储，仅在 Worker 执行内存中临时解密。
* **数据隔离：** 数据库层面启用 Row-Level Security (RLS)，强制检查 Tenant ID，防止越权访问。
* **审计日志：** 所有配置变更、任务创建与数据导出操作均记录 Audit Log，保留 6 个月以备合规审查。

# 测试计划

| 测试类型  | 内容                                         | 工具           |
| ----------- | ---------------------------------------------- | ---------------- |
| 单元测试  | 解析器逻辑、指标计算公式、Cron 调度算法      | PyTest / Jest  |
| 集成测试  | 任务全流程、API 网关鉴权、DB 事务一致性      | Postman / Hurl |
| Mock 测试 | 模拟 OpenRouter 响应，测试异常处理与重试机制 | WireMock       |

# 性能与扩展性

设计目标为支持单租户每日 10,000 次查询，系统需具备水平扩展能力。

* **队列削峰：** 使用 Redis List 缓冲大量并发监控任务，Worker 按速率限制（Rate Limit）消费，避免触发上游 API 封锁。
* **冷热分离：** 超过 3 个月的历史原始 HTML 响应迁移至 S3/Object Storage，仅保留计算后的指标数据在数据库中。

# 里程碑与规划

**Phase 1: MVP (Month 1-2)**
完成核心监控功能，OpenRouter 对接，基础 SOV 仪表盘上线。

**Phase 2: Beta (Month 3-4)**
增加告警系统，多用户权限管理，CSV/PDF 报表导出，定位词命中率分析。

**Phase 3: GA (Month 5+)**
API 开放平台，移动端 App 支持，Agent2Agent 自动化优化协议集成。

