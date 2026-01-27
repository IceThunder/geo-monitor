-- GEO Monitor Database Initialization Script
-- PostgreSQL (Supabase) Database Schema
-- Version: 1.1

-- ============================================================================
-- 1. Enable required extensions
-- ============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pg_cron for scheduling (Supabase Pro plan)
-- CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- ============================================================================
-- 2. Create Enum Types
-- ============================================================================

CREATE TYPE task_status AS ENUM ('pending', 'running', 'completed', 'failed');
CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');

-- ============================================================================
-- 3. Create Tables
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 3.1 Tenant Configuration Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE tenant_configs IS '租户配置表，存储 API Key、告警阈值等';
COMMENT ON COLUMN tenant_configs.tenant_id IS '租户唯一标识';
COMMENT ON COLUMN tenant_configs.openrouter_api_key_encrypted IS '加密后的 OpenRouter API Key';
COMMENT ON COLUMN tenant_configs.alert_threshold_accuracy IS '准确性告警阈值 (1-10)';

-- ----------------------------------------------------------------------------
-- 3.2 Monitor Tasks Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS monitor_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    schedule_cron VARCHAR(100) DEFAULT '0 0 * * *' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    prompt_template_id UUID,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

COMMENT ON TABLE monitor_tasks IS '监控任务表';
COMMENT ON COLUMN monitor_tasks.schedule_cron IS 'Cron 调度表达式';
COMMENT ON COLUMN monitor_tasks.prompt_template_id IS 'Prompt 模板 ID';

-- ----------------------------------------------------------------------------
-- 3.3 Task-Model Association Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_models (
    task_id UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    priority INTEGER DEFAULT 10 NOT NULL CHECK (priority BETWEEN 1 AND 100),
    PRIMARY KEY (task_id, model_id)
);

COMMENT ON TABLE task_models IS '任务-模型关联表，支持多模型监控';
COMMENT ON COLUMN task_models.model_id IS '模型 ID，如 openai/gpt-4o';
COMMENT ON COLUMN task_models.priority IS '优先级，数字越小优先级越高';

-- ----------------------------------------------------------------------------
-- 3.4 Task-Keyword Association Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS task_keywords (
    task_id UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    keyword VARCHAR(500) NOT NULL,
    category VARCHAR(100),
    PRIMARY KEY (task_id, keyword)
);

COMMENT ON TABLE task_keywords IS '任务-关键词关联表';
COMMENT ON COLUMN task_keywords.category IS '关键词分类';

-- ----------------------------------------------------------------------------
-- 3.5 Task Runs Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE task_runs IS '任务运行记录表';
COMMENT ON COLUMN task_runs.status IS '运行状态：pending, running, completed, failed';

-- ----------------------------------------------------------------------------
-- 3.6 Model Outputs Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE model_outputs IS '模型输出原始数据表';
COMMENT ON COLUMN model_outputs.raw_response IS '模型返回的 JSON 响应';
COMMENT ON COLUMN model_outputs.raw_html IS '原始 HTML 响应';

-- ----------------------------------------------------------------------------
-- 3.7 Metrics Snapshot Table
-- ----------------------------------------------------------------------------
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

COMMENT ON TABLE metrics_snapshot IS '指标快照表';
COMMENT ON COLUMN metrics_snapshot.sov_score IS '声量份额 (0-100)';
COMMENT ON COLUMN metrics_snapshot.accuracy_score IS '准确性评分 (1-10)';
COMMENT ON COLUMN metrics_snapshot.sentiment_score IS '情感分数 (-1 到 1)';
COMMENT ON COLUMN metrics_snapshot.citation_rate IS '引用率 (0-100)';
COMMENT ON COLUMN metrics_snapshot.positioning_hit IS '定位词是否命中';

-- ----------------------------------------------------------------------------
-- 3.8 Alert Records Table
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alert_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE,
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

COMMENT ON TABLE alert_records IS '告警记录表';
COMMENT ON COLUMN alert_records.alert_type IS '告警类型：accuracy_low, sentiment_low, sov_low';

-- ============================================================================
-- 4. Create Indexes
-- ============================================================================

-- Tenant configs indexes
CREATE INDEX IF NOT EXISTS idx_tenant_configs_tenant ON tenant_configs(tenant_id);

-- Monitor tasks indexes
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_tenant ON monitor_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_active ON monitor_tasks(is_active);
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_created ON monitor_tasks(created_at DESC);

-- Task models indexes
CREATE INDEX IF NOT EXISTS idx_task_models_task ON task_models(task_id);
CREATE INDEX IF NOT EXISTS idx_task_models_priority ON task_models(priority);

-- Task keywords indexes
CREATE INDEX IF NOT EXISTS idx_task_keywords_task ON task_keywords(task_id);
CREATE INDEX IF NOT EXISTS idx_task_keywords_category ON task_keywords(category);

-- Task runs indexes
CREATE INDEX IF NOT EXISTS idx_task_runs_task ON task_runs(task_id);
CREATE INDEX IF NOT EXISTS idx_task_runs_status ON task_runs(status);
CREATE INDEX IF NOT EXISTS idx_task_runs_created ON task_runs(created_at DESC);

-- Model outputs indexes
CREATE INDEX IF NOT EXISTS idx_model_outputs_run ON model_outputs(run_id);
CREATE INDEX IF NOT EXISTS idx_model_outputs_keyword ON model_outputs(keyword);
CREATE INDEX IF NOT EXISTS idx_model_outputs_model ON model_outputs(model_id);
CREATE INDEX IF NOT EXISTS idx_model_outputs_created ON model_outputs(created_at DESC);

-- Metrics snapshot indexes
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_run ON metrics_snapshot(run_id);
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_keyword ON metrics_snapshot(keyword);
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_model ON metrics_snapshot(model_id);
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_created ON metrics_snapshot(created_at DESC);

-- Alert records indexes
CREATE INDEX IF NOT EXISTS idx_alert_records_tenant ON alert_records(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_records_task ON alert_records(task_id);
CREATE INDEX IF NOT EXISTS idx_alert_records_unread ON alert_records(is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_alert_records_created ON alert_records(created_at DESC);

-- ============================================================================
-- 5. Create Row Level Security (RLS) Policies
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE tenant_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE monitor_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_keywords ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_outputs ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics_snapshot ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_records ENABLE ROW LEVEL SECURITY;

-- Tenant configs: Tenant can only access their own config
CREATE POLICY "Tenant can view own config" ON tenant_configs
    FOR SELECT USING (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

CREATE POLICY "Tenant can update own config" ON tenant_configs
    FOR UPDATE USING (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

-- Monitor tasks: Tenant can only access their own tasks
CREATE POLICY "Tenant can view own tasks" ON monitor_tasks
    FOR SELECT USING (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

CREATE POLICY "Tenant can create tasks" ON monitor_tasks
    FOR INSERT WITH CHECK (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

CREATE POLICY "Tenant can update own tasks" ON monitor_tasks
    FOR UPDATE USING (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

CREATE POLICY "Tenant can delete own tasks" ON monitor_tasks
    FOR DELETE USING (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

-- Task models, keywords: Cascade from tasks
CREATE POLICY "Tenant can view own task models" ON task_models
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM monitor_tasks
            WHERE monitor_tasks.id = task_models.task_id
            AND monitor_tasks.tenant_id = current_setting('app.jwt_tenant_id', true)::UUID
        )
    );

CREATE POLICY "Tenant can view own task keywords" ON task_keywords
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM monitor_tasks
            WHERE monitor_tasks.id = task_keywords.task_id
            AND monitor_tasks.tenant_id = current_setting('app.jwt_tenant_id', true)::UUID
        )
    );

-- Task runs: Cascade from tasks
CREATE POLICY "Tenant can view own task runs" ON task_runs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM monitor_tasks
            WHERE monitor_tasks.id = task_runs.task_id
            AND monitor_tasks.tenant_id = current_setting('app.jwt_tenant_id', true)::UUID
        )
    );

-- Model outputs: Cascade from runs
CREATE POLICY "Tenant can view own model outputs" ON model_outputs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM task_runs
            WHERE task_runs.id = model_outputs.run_id
            AND EXISTS (
                SELECT 1 FROM monitor_tasks
                WHERE monitor_tasks.id = task_runs.task_id
                AND monitor_tasks.tenant_id = current_setting('app.jwt_tenant_id', true)::UUID
            )
        )
    );

-- Metrics snapshot: Cascade from runs
CREATE POLICY "Tenant can view own metrics" ON metrics_snapshot
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM task_runs
            WHERE task_runs.id = metrics_snapshot.run_id
            AND EXISTS (
                SELECT 1 FROM monitor_tasks
                WHERE monitor_tasks.id = task_runs.task_id
                AND monitor_tasks.tenant_id = current_setting('app.jwt_tenant_id', true)::UUID
            )
        )
    );

-- Alert records: Tenant can only access their own alerts
CREATE POLICY "Tenant can view own alerts" ON alert_records
    FOR SELECT USING (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

CREATE POLICY "Tenant can update own alerts" ON alert_records
    FOR UPDATE USING (tenant_id = current_setting('app.jwt_tenant_id', true)::UUID);

-- ============================================================================
-- 6. Create Triggers for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_tenant_configs_updated_at
    BEFORE UPDATE ON tenant_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_monitor_tasks_updated_at
    BEFORE UPDATE ON monitor_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 7. Initialize Sample Data (Optional - for testing)
-- ============================================================================

-- Insert sample tenant config
INSERT INTO tenant_configs (tenant_id, alert_threshold_accuracy, alert_threshold_sentiment)
VALUES 
    ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 6, 0.50),
    ('b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a22', 7, 0.60)
ON CONFLICT (tenant_id) DO NOTHING;

-- Insert sample task (commented out - uncomment for testing)
-- INSERT INTO monitor_tasks (tenant_id, name, description, schedule_cron, is_active)
-- VALUES 
--     ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'CRM品牌监控', '监控企业级CRM品牌声量', '0 9 * * *', true),
--     ('a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11', 'ERP竞品分析', '监控ERP领域主要竞争对手', '0 10 * * *', true)
-- ON CONFLICT DO NOTHING;

-- ============================================================================
-- 8. Setup pg_cron for scheduling (Optional - requires Pro plan)
-- ============================================================================

-- Enable pg_cron
-- CREATE EXTENSION IF NOT EXISTS "pg_cron";

-- Schedule task checker to run every minute
-- SELECT cron.schedule('geo-monitor-scheduler', '* * * * *', $$
--     SELECT webhook('http://localhost:8000/api/v1/internal/scheduler/check', 'POST', '{"key": "value"}'::jsonb)
-- $$);

-- ============================================================================
-- 9. Utility Functions
-- ============================================================================

-- Function to calculate SOV
CREATE OR REPLACE FUNCTION calculate_sov(
    brand_mentions INTEGER,
    total_models INTEGER
) RETURNS NUMERIC(5, 2) AS $$
BEGIN
    IF total_models = 0 OR brand_mentions IS NULL THEN
        RETURN 0;
    END IF;
    RETURN ROUND((brand_mentions::NUMERIC / total_models) * 100, 2);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate citation rate
CREATE OR REPLACE FUNCTION calculate_citation_rate(
    answers_with_links INTEGER,
    total_mentions INTEGER
) RETURNS NUMERIC(5, 2) AS $$
BEGIN
    IF total_mentions = 0 OR answers_with_links IS NULL THEN
        RETURN 0;
    END IF;
    RETURN ROUND((answers_with_links::NUMERIC / total_mentions) * 100, 2);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 10. Comments Summary
-- ============================================================================

COMMENT ON TABLE tenant_configs IS '租户配置表 - 存储各租户的 API Key、告警阈值等配置';
COMMENT ON TABLE monitor_tasks IS '监控任务表 - 存储任务配置信息';
COMMENT ON TABLE task_models IS '任务-模型关联表 - 一个任务可监控多个模型';
COMMENT ON TABLE task_keywords IS '任务-关键词关联表 - 一个任务可监控多个关键词';
COMMENT ON TABLE task_runs IS '任务运行记录表 - 记录每次任务执行的状态和信息';
COMMENT ON TABLE model_outputs IS '模型输出表 - 存储各模型对各关键词的原始输出';
COMMENT ON TABLE metrics_snapshot IS '指标快照表 - 存储计算后的各类指标数据';
COMMENT ON TABLE alert_records IS '告警记录表 - 存储触发的告警信息';

-- ============================================================================
-- Done
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE 'GEO Monitor database schema created successfully!';
    RAISE NOTICE 'Tables created: tenant_configs, monitor_tasks, task_models, task_keywords, task_runs, model_outputs, metrics_snapshot, alert_records';
    RAISE NOTICE 'RLS policies enabled for multi-tenant security';
    RAISE NOTICE 'Indexes created for optimal query performance';
END $$;
