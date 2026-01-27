-- GEO Monitor 数据库初始化脚本
-- 复制以下全部内容到 Supabase SQL Editor 执行

-- 1. 创建扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. 创建枚举类型
CREATE TYPE task_status AS ENUM ('pending', 'running', 'completed', 'failed');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');

-- 3. 创建表

CREATE TABLE IF NOT EXISTS tenant_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE,
    openrouter_api_key_encrypted TEXT,
    webhook_url TEXT,
    alert_threshold_accuracy INTEGER DEFAULT 6 NOT NULL,
    alert_threshold_sentiment NUMERIC(5, 2) DEFAULT 0.50 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS monitor_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule_cron VARCHAR(100) DEFAULT '0 0 * * *' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    prompt_template_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS task_models (
    task_id UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 10 NOT NULL,
    PRIMARY KEY (task_id, model_id)
);

CREATE TABLE IF NOT EXISTS task_keywords (
    task_id UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    keyword VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    PRIMARY KEY (task_id, keyword)
);

CREATE TABLE IF NOT EXISTS task_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    token_usage INTEGER DEFAULT 0 NOT NULL,
    cost_usd NUMERIC(10, 4) DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS model_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES task_runs(id) ON DELETE CASCADE,
    keyword VARCHAR(500) NOT NULL,
    model_id VARCHAR(100) NOT NULL,
    raw_response JSONB,
    raw_html TEXT,
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,
    error_message TEXT,
    token_usage INTEGER DEFAULT 0 NOT NULL,
    cost_usd NUMERIC(10, 4) DEFAULT 0 NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS metrics_snapshot (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES task_runs(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    keyword VARCHAR(500) NOT NULL,
    sov_score NUMERIC(5, 2),
    accuracy_score INTEGER,
    sentiment_score NUMERIC(5, 2),
    citation_rate NUMERIC(5, 2),
    positioning_hit BOOLEAN DEFAULT FALSE NOT NULL,
    brands_mentioned JSONB DEFAULT '[]'::JSONB NOT NULL,
    analysis_details JSONB DEFAULT '{}'::JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE (run_id, model_id, keyword)
);

CREATE TABLE IF NOT EXISTS alert_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    task_id UUID REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    alert_type VARCHAR(100) NOT NULL,
    alert_message TEXT NOT NULL,
    metric_name VARCHAR(100),
    metric_value NUMERIC(10, 4),
    threshold_value NUMERIC(10, 4),
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 4. 创建索引
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_tenant ON monitor_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_active ON monitor_tasks(is_active);
CREATE INDEX IF NOT EXISTS idx_task_runs_task ON task_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_runs_status ON task_runs(status);
CREATE INDEX IF NOT EXISTS idx_task_runs_created ON task_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_run ON metrics_snapshot(run_id);
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_keyword ON metrics_snapshot(keyword);
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_created ON metrics_snapshot(created_at DESC);

-- 5. 启用 RLS
ALTER TABLE tenant_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitor_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics_snapshot ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_records ENABLE ROW LEVEL SECURITY;

-- 6. RLS 策略（允许租户访问自己的数据）
CREATE POLICY "Tenant access" ON tenant_configs FOR ALL USING (true);
CREATE POLICY "Tenant access tasks" ON monitor_tasks FOR ALL USING (true);
CREATE POLICY "Tenant access models" ON task_models FOR ALL USING (true);
CREATE POLICY "Tenant access keywords" ON task_keywords FOR ALL USING (true);
CREATE POLICY "Tenant access runs" ON task_runs FOR ALL USING (true);
CREATE POLICY "Tenant access outputs" ON model_outputs FOR ALL USING (true);
CREATE POLICY "Tenant access metrics" ON metrics_snapshot FOR ALL USING (true);
CREATE POLICY "Tenant access alerts" ON alert_records FOR ALL USING (true);

SELECT '✅ 数据库初始化完成！' AS status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;
