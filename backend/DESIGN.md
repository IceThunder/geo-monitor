# GEO 监控系统 - 后端设计文档

## 技术选型

| 组件 | 技术栈 | 版本要求 |
|------|--------|----------|
| 运行时 | Python | 3.11+ |
| Web框架 | FastAPI | 0.109+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据验证 | Pydantic | 2.5+ |
| 数据库 | PostgreSQL (Supabase) | 15+ |
| 消息队列 | Redis (Upstash) | 7.0+ |
| LLM网关 | OpenRouter | - |
| 任务调度 | APScheduler / pg_cron | - |

## 数据库 Schema

### 核心表结构

#### 1. monitor_tasks - 监控任务表
```sql
CREATE TABLE monitor_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule_cron TEXT DEFAULT '0 0 * * *',
    is_active BOOLEAN DEFAULT true,
    prompt_template_id UUID,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_monitor_tasks_tenant ON monitor_tasks(tenant_id);
CREATE INDEX idx_monitor_tasks_active ON monitor_tasks(is_active);
```

#### 2. task_models - 任务-模型关联表
```sql
CREATE TABLE task_models (
    task_id UUID REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    priority INT DEFAULT 10,
    PRIMARY KEY (task_id, model_id)
);

-- 索引
CREATE INDEX idx_task_models_task ON task_models(task_id);
CREATE INDEX idx_task_models_priority ON task_models(priority);
```

#### 3. task_keywords - 任务-关键词关联表
```sql
CREATE TABLE task_keywords (
    task_id UUID REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    keyword VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    PRIMARY KEY (task_id, keyword)
);

-- 索引
CREATE INDEX idx_task_keywords_task ON task_keywords(task_id);
CREATE INDEX idx_task_keywords_category ON task_keywords(category);
```

#### 4. task_runs - 任务运行记录表
```sql
CREATE TABLE task_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    token_usage INT DEFAULT 0,
    cost_usd NUMERIC(10, 4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_task_runs_task ON task_runs(task_id);
CREATE INDEX idx_task_runs_status ON task_runs(status);
CREATE INDEX idx_task_runs_created ON task_runs(created_at);
```

#### 5. model_outputs - 模型输出原始数据
```sql
CREATE TABLE model_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES task_runs(id) ON DELETE CASCADE,
    keyword VARCHAR(500) NOT NULL,
    model_id VARCHAR(100) NOT NULL,
    raw_response JSONB,
    raw_html TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    error_message TEXT,
    token_usage INT DEFAULT 0,
    cost_usd NUMERIC(10, 4) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_model_outputs_run ON model_outputs(run_id);
CREATE INDEX idx_model_outputs_keyword ON model_outputs(keyword);
CREATE INDEX idx_model_outputs_model ON model_outputs(model_id);
```

#### 6. metrics_snapshot - 指标快照表
```sql
CREATE TABLE metrics_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES task_runs(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    keyword VARCHAR(500) NOT NULL,
    sov_score NUMERIC(5, 2),
    accuracy_score INT,
    sentiment_score NUMERIC(5, 2),
    citation_rate NUMERIC(5, 2),
    positioning_hit BOOLEAN DEFAULT false,
    brands_mentioned JSONB DEFAULT '[]',
    analysis_details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE (run_id, model_id, keyword)
);

-- 索引
CREATE INDEX idx_metrics_snapshot_run ON metrics_snapshot(run_id);
CREATE INDEX idx_metrics_snapshot_keyword ON metrics_snapshot(keyword);
CREATE INDEX idx_metrics_snapshot_model ON metrics_snapshot(model_id);
CREATE INDEX idx_metrics_snapshot_created ON metrics_snapshot(created_at);
```

#### 7. tenant_configs - 租户配置表
```sql
CREATE TABLE tenant_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE,
    openrouter_api_key_encrypted TEXT,
    webhook_url TEXT,
    alert_threshold_accuracy INT DEFAULT 6,
    alert_threshold_sentiment NUMERIC(5, 2) DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_tenant_configs_tenant ON tenant_configs(tenant_id);
```

#### 8. alert_records - 告警记录表
```sql
CREATE TABLE alert_records (
    id UUID PRIMARY KEY(),
    tenant_id DEFAULT gen_random_uuid UUID NOT NULL,
    task_id UUID REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    alert_message TEXT,
    metric_name VARCHAR(100),
    metric_value NUMERIC(10, 4),
    threshold_value NUMERIC(10, 4),
    is_read BOOLEAN DEFAULT false,
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 索引
CREATE INDEX idx_alert_records_tenant ON alert_records(tenant_id);
CREATE INDEX idx_alert_records_task ON alert_records(task_id);
CREATE INDEX idx_alert_records_unread ON alert_records(is_read) WHERE is_read = false;
CREATE INDEX idx_alert_records_created ON alert_records(created_at);
```

## API 接口设计

### 认证与授权

所有 API 需要在 Header 中携带 JWT Token：
```
Authorization: Bearer <jwt_token>
```

### 任务管理 API

#### 1. 创建监控任务
```
POST /api/v1/tasks
Request Body:
{
    "name": "CRM品牌监控",
    "description": "监控企业级CRM品牌声量",
    "schedule_cron": "0 9 * * *",
    "models": ["openai/gpt-4o", "anthropic/claude-3-5-sonnet"],
    "keywords": ["企业级CRM", "CRM系统", "客户关系管理"],
    "prompt_template_id": null
}
Response: 201 Created
{
    "id": "uuid",
    "name": "CRM品牌监控",
    "status": "active",
    "created_at": "2024-01-27T10:00:00Z"
}
```

#### 2. 获取任务列表
```
GET /api/v1/tasks?page=1&limit=20&is_active=true
Response: 200 OK
{
    "data": [...],
    "total": 100,
    "page": 1,
    "limit": 20
}
```

#### 3. 获取任务详情
```
GET /api/v1/tasks/{task_id}
Response: 200 OK
{
    "id": "uuid",
    "name": "CRM品牌监控",
    "schedule_cron": "0 9 * * *",
    "models": [...],
    "keywords": [...],
    "runs": [...]
}
```

#### 4. 更新任务
```
PUT /api/v1/tasks/{task_id}
Request Body:
{
    "name": "CRM品牌监控V2",
    "schedule_cron": "0 10 * * *",
    "models": ["openai/gpt-4o"],
    "keywords": ["企业级CRM", "CRM软件"]
}
Response: 200 OK
```

#### 5. 删除任务
```
DELETE /api/v1/tasks/{task_id}
Response: 204 No Content
```

#### 6. 手动触发任务
```
POST /api/v1/tasks/{task_id}/trigger
Response: 202 Accepted
{
    "run_id": "uuid",
    "status": "pending"
}
```

### 指标数据 API

#### 1. Dashboard 概览数据
```
GET /api/v1/dashboard/overview?start_date=2024-01-01&end_date=2024-01-27
Response: 200 OK
{
    "total_tasks": 10,
    "active_tasks": 8,
    "sov_trend": [...],
    "accuracy_trend": [...],
    "top_brands": [...],
    "recent_alerts": [...]
}
```

#### 2. SOV 趋势数据
```
GET /api/v1/metrics/sov?keyword=企业级CRM&model=openai/gpt-4o&period=7d
Response: 200 OK
{
    "keyword": "企业级CRM",
    "model": "openai/gpt-4o",
    "data": [
        {"date": "2024-01-21", "sov": 35.5},
        {"date": "2024-01-22", "sov": 38.2}
    ]
}
```

#### 3. 准确性评分数据
```
GET /api/v1/metrics/accuracy?task_id=uuid&period=30d
Response: 200 OK
{
    "task_id": "uuid",
    "data": [
        {"date": "2024-01-01", "avg_accuracy": 8.5, "min_accuracy": 6.0},
        {"date": "2024-01-02", "avg_accuracy": 8.7, "min_accuracy": 6.5}
    ]
}
```

#### 4. 模型对比数据
```
GET /api/v1/metrics/comparison?keyword=CRM系统&period=7d
Response: 200 OK
{
    "keyword": "CRM系统",
    "models": {
        "openai/gpt-4o": {"sov": 35.2, "accuracy": 8.5},
        "anthropic/claude-3-5-sonnet": {"sov": 32.1, "accuracy": 8.8}
    }
}
```

### 告警管理 API

#### 1. 获取告警列表
```
GET /api/v1/alerts?is_read=false&limit=50
Response: 200 OK
{
    "data": [...],
    "unread_count": 5
}
```

#### 2. 标记告警已读
```
PUT /api/v1/alerts/{alert_id}/read
Response: 200 OK
```

#### 3. 测试 Webhook
```
POST /api/v1/webhooks/test
Request Body:
{
    "webhook_url": "https://example.com/webhook"
}
Response: 200 OK
{
    "success": true,
    "response_time_ms": 150
}
```

### 租户配置 API

#### 1. 获取租户配置
```
GET /api/v1/config
Response: 200 OK
{
    "openrouter_api_key_set": true,
    "webhook_url": "https://...",
    "alert_threshold_accuracy": 6,
    "alert_threshold_sentiment": 0.5
}
```

#### 2. 更新租户配置
```
PUT /api/v1/config
Request Body:
{
    "openrouter_api_key": "sk-...",
    "webhook_url": "https://...",
    "alert_threshold_accuracy": 7,
    "alert_threshold_sentiment": 0.6
}
Response: 200 OK
```

### 报表导出 API

#### 1. 导出报表
```
POST /api/v1/reports/export
Request Body:
{
    "task_id": "uuid",
    "format": "csv",
    "start_date": "2024-01-01",
    "end_date": "2024-01-27",
    "metrics": ["sov", "accuracy", "sentiment"]
}
Response: 200 OK
Content-Type: text/csv
<csv_content>
```

## 任务调度流程

### 调度流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   pg_cron       │────▶│   Task Manager  │────▶│   Redis Queue   │
│  (定时触发)      │     │   (API Service) │     │   (任务缓冲)     │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Result        │◀────│   Model Executor │◀────│   Redis Queue   │
│   Analyzer      │     │   (Worker)      │     │   (任务消费)     │
└────────┬────────┘     └─────────────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Supabase DB   │
│   (数据持久化)   │
└─────────────────┘
```

### 调度流程详解

1. **定时触发**：pg_cron 根据 Cron 表达式定时执行调度任务
2. **任务生成**：Task Manager 查询待执行的监控任务，生成任务消息
3. **队列缓冲**：任务消息推入 Redis 队列
4. **任务消费**：Model Executor 从队列中抢占任务
5. **模型调用**：Executor 调用 OpenRouter API，执行监控查询
6. **结果解析**：Result Analyzer 解析模型返回的 JSON 数据
7. **指标计算**：计算 SOV、准确性、情感等指标
8. **数据持久化**：将结果写入 Supabase 数据库
9. **告警检查**：检查指标是否触发告警阈值，发送通知

## 核心算法逻辑

### SOV (声量份额) 计算

```python
def calculate_sov(brand_mentions: List[str], total_models: int) -> float:
    """
    SOV = (品牌提及次数 / 查询模型总数) × 100%
    """
    if total_models == 0:
        return 0.0
    return (len(brand_mentions) / total_models) * 100
```

### 准确性评分算法

```python
def calculate_accuracy_score(response: str, fact_sheet: Dict) -> int:
    """
    准确性评分 (1-10分)：
    1. 使用 GPT-4o 作为 Evaluator Model
    2. 将回答与品牌 Fact Sheet 比对
    3. 检测幻觉内容（错误的价格、功能、特性）
    4. 返回 1-10 的评分
    """
    prompt = f"""
    你是一个品牌准确性审计员。请对比以下品牌回答与事实表，评估准确性。

    品牌事实表:
    {json.dumps(fact_sheet, ensure_ascii=False, indent=2)}

    模型回答:
    {response}

    请评估以下方面（每个方面1-5分，总分转换为10分制）：
    1. 产品功能描述准确性
    2. 价格信息准确性
    3. 核心特性描述准确性
    4. 公司背景信息准确性

    只返回 1-10 的数字评分，无需解释。
    """
    # 调用评估模型获取分数
```

### 定位词命中检测

```python
def check_positioning_hit(response: str, brand: str, positioning_keywords: List[str], window_size: int = 50) -> bool:
    """
    检测品牌名称与定位词是否在同一回答中共现
    使用滑动窗口算法
    """
    tokens = response.split()
    brand_tokens = brand.lower().split()
    
    for i, token in enumerate(tokens):
        token_lower = token.lower()
        if any(bt in token_lower for bt in brand_tokens):
            # 检查窗口内的定位词
            start = max(0, i - window_size)
            end = min(len(tokens), i + window_size)
            window_text = ' '.join(tokens[start:end]).lower()
            if any(pk.lower() in window_text for pk in positioning_keywords):
                return True
    return False
```

### 情感分析

```python
def analyze_sentiment(text: str) -> float:
    """
    情感分析，返回 -1 到 1 的分数
    -1: 负面, 0: 中性, 1: 正面
    """
    # 使用预训练的情感分析模型或调用 LLM
```

### 引用率计算

```python
def calculate_citation_rate(answers_with_links: int, total_mentions: int) -> float:
    """
    CR = (包含品牌链接的回答数 / 品牌总提及数) × 100%
    """
    if total_mentions == 0:
        return 0.0
    return (answers_with_links / total_mentions) * 100
```

## 异常处理与重试机制

### 指数退避重试

```python
import time
import asyncio

async def call_with_retry(func, max_retries: int = 3, base_delay: float = 1.0):
    """
    带指数退避的重试机制
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = base_delay * (2 ** attempt)
            # 添加随机抖动
            delay += random.uniform(0, 0.5)
            
            await asyncio.sleep(delay)
```

### 熔断机制

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.last_failure_time = None
        self.is_open = False
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
    
    def record_success(self):
        self.failure_count = 0
        self.is_open = False
    
    def allow_request(self) -> bool:
        if not self.is_open:
            return True
        if time.time() - self.last_failure_time > self.recovery_time:
            self.is_open = False
            return True
        return False
```

## 速率限制

### Redis 计数器实现 RPM 限制

```python
import redis
from datetime import datetime

class RateLimiter:
    def __init__(self, redis_client, max_requests: int = 20, window_seconds: int = 60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
    
    def check_rate_limit(self, key: str) -> bool:
        """
        使用 Redis INCR 实现滑动窗口限流
        """
        now = datetime.utcnow().timestamp()
        window_start = now - self.window_seconds
        
        # 删除过期的时间窗口
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # 当前窗口的请求数
        current_count = self.redis.zcard(key)
        
        if current_count >= self.max_requests:
            return False
        
        # 添加新请求
        self.redis.zadd(key, {str(now): now})
        self.redis.expire(key, self.window_seconds)
        
        return True
```

## 项目结构

```
backend/
├── app/
│   ├── main.py                    # FastAPI 应用入口
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py            # SQLAlchemy 数据库连接
│   │   ├── entities.py            # 数据库实体定义
│   │   └── schemas.py             # Pydantic 模式定义
│   ├── api/
│   │   ├── __init__.py
│   │   ├── tasks.py               # 任务管理 API
│   │   ├── metrics.py             # 指标数据 API
│   │   ├── alerts.py              # 告警管理 API
│   │   └── config.py              # 租户配置 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── scheduler.py           # 任务调度服务
│   │   ├── executor.py            # 模型执行服务
│   │   ├── analyzer.py            # 结果分析服务
│   │   ├── calculator.py          # 指标计算服务
│   │   └── notifier.py            # 告警通知服务
│   └── core/
│       ├── __init__.py
│       ├── config.py              # 配置管理
│       ├── security.py            # JWT 认证
│       └── exceptions.py          # 异常处理
├── requirements.txt
├── Dockerfile
├── .env.example
└── .gitignore
```

## 依赖列表

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0
redis==5.0.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiofiles==23.2.1
httpx==0.26.0
apscheduler==3.10.4
python-dotenv==1.0.0
```

## 部署配置

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 环境变量示例 (.env.example)

```
# 数据库配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://user:password@host:5432/db

# Redis 配置
UPSTASH_REDIS_REST_URL=https://your-db.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-redis-token

# OpenRouter 配置
OPENROUTER_API_KEY=sk-or-v1-xxx

# 应用配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# JWT 配置
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Webhook 配置
WEBHOOK_ENABLED=true
```
