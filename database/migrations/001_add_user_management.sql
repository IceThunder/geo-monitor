-- Migration 001: Add User Management and Enhanced Features
-- This migration adds user management tables and enhances existing schema
-- Run this after the base schema is in place

-- ============================================================================
-- 1. Add new columns to existing tables
-- ============================================================================

-- Add user tracking to monitor_tasks
ALTER TABLE monitor_tasks 
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS last_run_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS next_run_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS total_runs INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS successful_runs INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS failed_runs INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS total_cost NUMERIC(10, 4) DEFAULT 0 NOT NULL;

-- Enhance tenant_configs
ALTER TABLE tenant_configs 
ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'Default Tenant',
ADD COLUMN IF NOT EXISTS alert_threshold_sov NUMERIC(5, 2) DEFAULT 10.0 NOT NULL CHECK (alert_threshold_sov >= 0),
ADD COLUMN IF NOT EXISTS max_daily_cost NUMERIC(10, 2) DEFAULT 100.00 NOT NULL,
ADD COLUMN IF NOT EXISTS max_monthly_tasks INTEGER DEFAULT 1000 NOT NULL,
ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'UTC' NOT NULL;

-- Enhance task_models
ALTER TABLE task_models 
ADD COLUMN IF NOT EXISTS provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN IF NOT EXISTS max_tokens INTEGER DEFAULT 4000,
ADD COLUMN IF NOT EXISTS temperature NUMERIC(3, 2) DEFAULT 0.1 CHECK (temperature BETWEEN 0 AND 2),
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

-- Enhance task_keywords
ALTER TABLE task_keywords 
ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 10 NOT NULL,
ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN IF NOT EXISTS target_brand VARCHAR(255),
ADD COLUMN IF NOT EXISTS positioning_keywords TEXT[],
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL;

-- Enhance task_runs
ALTER TABLE task_runs 
ADD COLUMN IF NOT EXISTS triggered_by VARCHAR(50) DEFAULT 'scheduler' NOT NULL,
ADD COLUMN IF NOT EXISTS duration_seconds INTEGER,
ADD COLUMN IF NOT EXISTS models_executed INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS keywords_processed INTEGER DEFAULT 0 NOT NULL,
ADD COLUMN IF NOT EXISTS success_rate NUMERIC(5, 2);

-- Update task_status enum to include 'partial'
ALTER TYPE task_status ADD VALUE IF NOT EXISTS 'partial';

-- Enhance model_outputs
ALTER TABLE model_outputs 
ADD COLUMN IF NOT EXISTS provider VARCHAR(50),
ADD COLUMN IF NOT EXISTS prompt_text TEXT,
ADD COLUMN IF NOT EXISTS parsed_response JSONB,
ADD COLUMN IF NOT EXISTS response_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0 NOT NULL;

-- Remove raw_html column if it exists (not used in new design)
ALTER TABLE model_outputs DROP COLUMN IF EXISTS raw_html;

-- Enhance metrics_snapshot
ALTER TABLE metrics_snapshot 
ADD COLUMN IF NOT EXISTS target_brand VARCHAR(255),
ADD COLUMN IF NOT EXISTS positioning_keywords_found TEXT[],
ADD COLUMN IF NOT EXISTS competitive_analysis JSONB DEFAULT '{}' NOT NULL,
ADD COLUMN IF NOT EXISTS quality_score NUMERIC(5, 2),
ADD COLUMN IF NOT EXISTS confidence_score NUMERIC(5, 2);

-- Enhance alert_records
ALTER TABLE alert_records 
ADD COLUMN IF NOT EXISTS run_id UUID REFERENCES task_runs(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'medium' NOT NULL,
ADD COLUMN IF NOT EXISTS affected_keywords TEXT[],
ADD COLUMN IF NOT EXISTS affected_models TEXT[],
ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS resolved_by UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS notification_sent BOOLEAN DEFAULT FALSE NOT NULL;

-- ============================================================================
-- 2. Create new enum types if they don't exist
-- ============================================================================

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
        CREATE TYPE user_role AS ENUM ('owner', 'admin', 'member', 'viewer');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'model_provider') THEN
        CREATE TYPE model_provider AS ENUM ('openai', 'anthropic', 'google', 'meta', 'mistral', 'cohere');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'alert_severity') THEN
        CREATE TYPE alert_severity AS ENUM ('low', 'medium', 'high', 'critical');
    END IF;
END $$;

-- ============================================================================
-- 3. Create new tables
-- ============================================================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255),
    hashed_password TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE NOT NULL,
    supabase_user_id VARCHAR(255) UNIQUE,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Tenant members table
CREATE TABLE IF NOT EXISTS tenant_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role user_role DEFAULT 'member' NOT NULL,
    permissions JSONB DEFAULT '{}' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    invited_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    joined_at TIMESTAMPTZ,
    invited_by UUID REFERENCES users(id),
    UNIQUE (tenant_id, user_id)
);

-- Model performance stats table
CREATE TABLE IF NOT EXISTS model_performance_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE,
    model_id VARCHAR(100) NOT NULL,
    provider VARCHAR(50),
    date DATE NOT NULL,
    total_requests INTEGER DEFAULT 0 NOT NULL,
    successful_requests INTEGER DEFAULT 0 NOT NULL,
    failed_requests INTEGER DEFAULT 0 NOT NULL,
    avg_response_time_ms NUMERIC(8, 2),
    total_tokens INTEGER DEFAULT 0 NOT NULL,
    total_cost NUMERIC(10, 4) DEFAULT 0 NOT NULL,
    avg_accuracy_score NUMERIC(5, 2),
    avg_sentiment_score NUMERIC(5, 2),
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE (tenant_id, model_id, date)
);

-- ============================================================================
-- 4. Add new indexes
-- ============================================================================

-- Users indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_supabase_id ON users(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Tenant members indexes
CREATE INDEX IF NOT EXISTS idx_tenant_members_tenant ON tenant_members(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_user ON tenant_members(user_id);
CREATE INDEX IF NOT EXISTS idx_tenant_members_active ON tenant_members(is_active) WHERE is_active = TRUE;

-- Enhanced monitor tasks indexes
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_created_by ON monitor_tasks(created_by);
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_next_run ON monitor_tasks(next_run_at) WHERE is_active = TRUE;

-- Enhanced task models indexes
CREATE INDEX IF NOT EXISTS idx_task_models_provider ON task_models(provider);
CREATE INDEX IF NOT EXISTS idx_task_models_enabled ON task_models(is_enabled) WHERE is_enabled = TRUE;

-- Enhanced task keywords indexes
CREATE INDEX IF NOT EXISTS idx_task_keywords_brand ON task_keywords(target_brand);
CREATE INDEX IF NOT EXISTS idx_task_keywords_enabled ON task_keywords(is_enabled) WHERE is_enabled = TRUE;

-- Enhanced model outputs indexes
CREATE INDEX IF NOT EXISTS idx_model_outputs_provider ON model_outputs(provider);
CREATE INDEX IF NOT EXISTS idx_model_outputs_status ON model_outputs(status);

-- Enhanced metrics snapshot indexes
CREATE INDEX IF NOT EXISTS idx_metrics_snapshot_brand ON metrics_snapshot(target_brand);

-- Enhanced alert records indexes
CREATE INDEX IF NOT EXISTS idx_alert_records_severity ON alert_records(severity);

-- Model performance stats indexes
CREATE INDEX IF NOT EXISTS idx_model_perf_stats_tenant_date ON model_performance_stats(tenant_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_model_perf_stats_model_date ON model_performance_stats(model_id, date DESC);

-- ============================================================================
-- 5. Add new triggers
-- ============================================================================

-- Updated_at triggers for new tables
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Task statistics update trigger
CREATE OR REPLACE FUNCTION update_task_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE monitor_tasks SET
            total_runs = (
                SELECT COUNT(*) FROM task_runs 
                WHERE task_id = NEW.task_id
            ),
            successful_runs = (
                SELECT COUNT(*) FROM task_runs 
                WHERE task_id = NEW.task_id AND status = 'completed'
            ),
            failed_runs = (
                SELECT COUNT(*) FROM task_runs 
                WHERE task_id = NEW.task_id AND status = 'failed'
            ),
            last_run_at = (
                SELECT MAX(started_at) FROM task_runs 
                WHERE task_id = NEW.task_id
            ),
            total_cost = (
                SELECT COALESCE(SUM(cost_usd), 0) FROM task_runs 
                WHERE task_id = NEW.task_id
            )
        WHERE id = NEW.task_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_task_stats_trigger
    AFTER INSERT OR UPDATE ON task_runs
    FOR EACH ROW EXECUTE FUNCTION update_task_stats();

-- ============================================================================
-- 6. Update existing data (if any)
-- ============================================================================

-- Update provider field in task_models based on model_id
UPDATE task_models SET provider = 
    CASE 
        WHEN model_id LIKE 'openai/%' THEN 'openai'
        WHEN model_id LIKE 'anthropic/%' THEN 'anthropic'
        WHEN model_id LIKE 'google/%' THEN 'google'
        WHEN model_id LIKE 'meta-llama/%' THEN 'meta'
        WHEN model_id LIKE 'mistralai/%' THEN 'mistral'
        WHEN model_id LIKE 'cohere/%' THEN 'cohere'
        ELSE 'openai'
    END
WHERE provider IS NULL;

-- Update provider field in model_outputs based on model_id
UPDATE model_outputs SET provider = 
    CASE 
        WHEN model_id LIKE 'openai/%' THEN 'openai'
        WHEN model_id LIKE 'anthropic/%' THEN 'anthropic'
        WHEN model_id LIKE 'google/%' THEN 'google'
        WHEN model_id LIKE 'meta-llama/%' THEN 'meta'
        WHEN model_id LIKE 'mistralai/%' THEN 'mistral'
        WHEN model_id LIKE 'cohere/%' THEN 'cohere'
        ELSE 'openai'
    END
WHERE provider IS NULL;

-- ============================================================================
-- 7. Create enhanced utility functions
-- ============================================================================

-- Enhanced SOV calculation function
CREATE OR REPLACE FUNCTION calculate_enhanced_sov(
    target_brand TEXT,
    all_brands JSONB,
    total_mentions INTEGER DEFAULT NULL
) RETURNS NUMERIC(5, 2) AS $$
DECLARE
    target_mentions INTEGER := 0;
    total_count INTEGER;
BEGIN
    -- Count mentions of target brand
    SELECT COUNT(*) INTO target_mentions
    FROM jsonb_array_elements_text(all_brands) AS brand
    WHERE LOWER(brand) = LOWER(target_brand);
    
    -- Get total count
    total_count := COALESCE(total_mentions, jsonb_array_length(all_brands));
    
    IF total_count = 0 THEN
        RETURN 0;
    END IF;
    
    RETURN ROUND((target_mentions::NUMERIC / total_count) * 100, 2);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate brand health score
CREATE OR REPLACE FUNCTION calculate_brand_health_score(
    sov_score NUMERIC,
    accuracy_score INTEGER,
    sentiment_score NUMERIC,
    citation_rate NUMERIC,
    positioning_hits INTEGER,
    total_mentions INTEGER
) RETURNS JSONB AS $$
DECLARE
    visibility_score NUMERIC;
    credibility_score NUMERIC;
    perception_score NUMERIC;
    positioning_score NUMERIC;
    overall_score NUMERIC;
    health_status TEXT;
BEGIN
    -- Normalize scores to 0-100 scale
    visibility_score := COALESCE(sov_score, 0);
    credibility_score := (COALESCE(accuracy_score, 5) - 1) * 11.11;
    perception_score := (COALESCE(sentiment_score, 0) + 1) * 50;
    positioning_score := CASE 
        WHEN total_mentions > 0 THEN (positioning_hits::NUMERIC / total_mentions) * 100
        ELSE 0 
    END;
    
    -- Calculate weighted overall score
    overall_score := (
        visibility_score * 0.3 +
        credibility_score * 0.3 +
        perception_score * 0.25 +
        positioning_score * 0.15
    );
    
    -- Determine health status
    health_status := CASE
        WHEN overall_score >= 80 THEN 'Excellent'
        WHEN overall_score >= 65 THEN 'Good'
        WHEN overall_score >= 50 THEN 'Fair'
        WHEN overall_score >= 35 THEN 'Poor'
        ELSE 'Critical'
    END;
    
    RETURN jsonb_build_object(
        'overall_score', ROUND(overall_score, 1),
        'health_status', health_status,
        'component_scores', jsonb_build_object(
            'visibility', ROUND(visibility_score, 1),
            'credibility', ROUND(credibility_score, 1),
            'perception', ROUND(perception_score, 1),
            'positioning', ROUND(positioning_score, 1)
        )
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. Create useful views
-- ============================================================================

-- View for task performance summary
CREATE OR REPLACE VIEW task_performance_summary AS
SELECT 
    mt.id,
    mt.name,
    mt.tenant_id,
    mt.is_active,
    mt.total_runs,
    mt.successful_runs,
    mt.failed_runs,
    CASE 
        WHEN mt.total_runs > 0 THEN ROUND((mt.successful_runs::NUMERIC / mt.total_runs) * 100, 2)
        ELSE 0 
    END as success_rate,
    mt.total_cost,
    mt.last_run_at,
    mt.created_at
FROM monitor_tasks mt;

-- View for recent metrics with brand health
CREATE OR REPLACE VIEW recent_metrics_with_health AS
SELECT 
    ms.*,
    calculate_brand_health_score(
        ms.sov_score,
        ms.accuracy_score,
        ms.sentiment_score,
        ms.citation_rate,
        CASE WHEN ms.positioning_hit THEN 1 ELSE 0 END,
        1
    ) as brand_health
FROM metrics_snapshot ms
WHERE ms.created_at >= NOW() - INTERVAL '30 days';

-- ============================================================================
-- 9. Migration completion
-- ============================================================================

-- Update schema version (if you have a version table)
-- INSERT INTO schema_versions (version, applied_at) VALUES ('1.1.0', NOW());

DO $$
BEGIN
    RAISE NOTICE 'Migration 001 completed successfully!';
    RAISE NOTICE 'Added user management and enhanced features';
    RAISE NOTICE 'Schema is now at version 1.1';
END $$;
