-- ============================================================
-- GEO Monitor — 完整数据库建表 SQL (PostgreSQL / Supabase)
-- 生成自: backend/app/models/user_entities.py + entities.py
-- 日期: 2026-02-07
-- ============================================================

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. 用户与认证系统 (user_entities.py)
-- ============================================================

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    name            VARCHAR(100) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(500),
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,
    email_verified_at TIMESTAMPTZ,
    last_login_at   TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- 租户表
CREATE TABLE IF NOT EXISTS tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(50) NOT NULL UNIQUE,
    plan_type       VARCHAR(20) DEFAULT 'free',        -- free, pro, enterprise
    status          VARCHAR(20) DEFAULT 'active',      -- active, suspended, cancelled
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);

-- 用户-租户关联表
CREATE TABLE IF NOT EXISTS user_tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role            VARCHAR(20) DEFAULT 'member',      -- owner, admin, member, viewer
    is_primary      BOOLEAN DEFAULT FALSE,
    joined_at       TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_user_tenant UNIQUE (user_id, tenant_id)
);

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    user_agent      TEXT,
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);

-- 邮箱验证表
CREATE TABLE IF NOT EXISTS email_verifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           VARCHAR(255) NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    is_used         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_email_verifications_token ON email_verifications(token);

-- 密码重置表
CREATE TABLE IF NOT EXISTS password_resets (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token           VARCHAR(255) NOT NULL UNIQUE,
    expires_at      TIMESTAMPTZ NOT NULL,
    is_used         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);

-- 角色表
CREATE TABLE IF NOT EXISTS roles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(50) NOT NULL UNIQUE,
    display_name    VARCHAR(100) NOT NULL,
    description     TEXT,
    permissions     JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(100) NOT NULL UNIQUE,
    resource        VARCHAR(50) NOT NULL,              -- tasks, metrics, alerts, config
    action          VARCHAR(20) NOT NULL,              -- create, read, update, delete
    description     TEXT
);

-- 用户邀请表
CREATE TABLE IF NOT EXISTS user_invitations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,
    role            VARCHAR(20) DEFAULT 'member',
    token           VARCHAR(255) NOT NULL UNIQUE,
    invited_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    is_accepted     BOOLEAN DEFAULT FALSE,
    accepted_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_user_invitations_email ON user_invitations(email);
CREATE INDEX IF NOT EXISTS idx_user_invitations_token ON user_invitations(token);

-- 租户配置表 (user_entities.py 版本，表名: tenant_config)
CREATE TABLE IF NOT EXISTS tenant_config (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
    openrouter_api_key_encrypted TEXT,
    webhook_url     VARCHAR(500),
    alert_threshold_accuracy  INTEGER DEFAULT 6,
    alert_threshold_sentiment INTEGER DEFAULT 50,      -- 0-100 scale
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 2. 业务系统 (entities.py)
-- ============================================================

-- 租户配置表 (entities.py 版本，表名: tenant_configs)
-- 注意：这是业务模块的配置表，monitor_tasks 外键指向此表
CREATE TABLE IF NOT EXISTS tenant_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL UNIQUE,
    openrouter_api_key_encrypted TEXT,
    webhook_url     TEXT,
    alert_threshold_accuracy  INTEGER DEFAULT 6,
    alert_threshold_sentiment NUMERIC(5, 2) DEFAULT 0.5,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 监控任务表
CREATE TABLE IF NOT EXISTS monitor_tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    schedule_cron   VARCHAR(100) DEFAULT '0 0 * * *',
    is_active       BOOLEAN DEFAULT TRUE,
    prompt_template_id UUID,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 任务-模型关联表 (复合主键)
CREATE TABLE IF NOT EXISTS task_models (
    task_id         UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    model_id        VARCHAR(100) NOT NULL,
    priority        INTEGER DEFAULT 10,
    PRIMARY KEY (task_id, model_id)
);

-- 任务-关键词关联表 (复合主键)
CREATE TABLE IF NOT EXISTS task_keywords (
    task_id         UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    keyword         VARCHAR(500) NOT NULL,
    category        VARCHAR(100),
    PRIMARY KEY (task_id, keyword)
);

-- 任务运行记录表
CREATE TABLE IF NOT EXISTS task_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id         UUID NOT NULL REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    status          VARCHAR(50) DEFAULT 'pending',     -- pending, running, completed, failed
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    token_usage     INTEGER DEFAULT 0,
    cost_usd        NUMERIC(10, 4) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 模型输出原始数据表
CREATE TABLE IF NOT EXISTS model_outputs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID NOT NULL REFERENCES task_runs(id) ON DELETE CASCADE,
    keyword         VARCHAR(500) NOT NULL,
    model_id        VARCHAR(100) NOT NULL,
    raw_response    JSON,
    raw_html        TEXT,
    status          VARCHAR(50) DEFAULT 'pending',
    error_message   TEXT,
    token_usage     INTEGER DEFAULT 0,
    cost_usd        NUMERIC(10, 4) DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 指标快照表
CREATE TABLE IF NOT EXISTS metrics_snapshot (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID NOT NULL REFERENCES task_runs(id) ON DELETE CASCADE,
    model_id        VARCHAR(100) NOT NULL,
    keyword         VARCHAR(500) NOT NULL,
    sov_score       NUMERIC(5, 2),
    accuracy_score  INTEGER,
    sentiment_score NUMERIC(5, 2),
    citation_rate   NUMERIC(5, 2),
    positioning_hit BOOLEAN DEFAULT FALSE,
    brands_mentioned JSON DEFAULT '[]'::json,
    analysis_details JSON DEFAULT '{}'::json,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 租户成员关联表 (legacy)
CREATE TABLE IF NOT EXISTS tenant_members (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenant_configs(tenant_id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role            VARCHAR(50) DEFAULT 'member',
    permissions     JSON DEFAULT '{}'::json,
    is_active       BOOLEAN DEFAULT TRUE,
    invited_at      TIMESTAMPTZ DEFAULT NOW(),
    joined_at       TIMESTAMPTZ
);

-- 告警记录表
CREATE TABLE IF NOT EXISTS alert_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL,
    task_id         UUID REFERENCES monitor_tasks(id) ON DELETE CASCADE,
    alert_type      VARCHAR(100) NOT NULL,
    alert_message   TEXT NOT NULL,
    metric_name     VARCHAR(100),
    metric_value    NUMERIC(10, 4),
    threshold_value NUMERIC(10, 4),
    is_read         BOOLEAN DEFAULT FALSE,
    is_resolved     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 3. 种子数据 — 测试登录账号 (密码: Test@123456)
-- ============================================================

-- 默认租户
INSERT INTO tenants (id, name, slug, plan_type, status)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'GEO Monitor 测试团队',
    'geo-test',
    'free',
    'active'
)
ON CONFLICT (slug) DO NOTHING;

-- 管理员 (owner)
INSERT INTO users (id, email, name, password_hash, is_active, is_verified, email_verified_at)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'admin@example.com',
    '管理员',
    '$2b$12$tSmpQME3bhIOL.KkFmsroegKv3.iHLOEIHo4WKRDcj2hJPsVnN30W',
    true, true, NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 测试用户 (member)
INSERT INTO users (id, email, name, password_hash, is_active, is_verified, email_verified_at)
VALUES (
    'b0000000-0000-0000-0000-000000000002',
    'test@example.com',
    '测试用户',
    '$2b$12$tSmpQME3bhIOL.KkFmsroegKv3.iHLOEIHo4WKRDcj2hJPsVnN30W',
    true, true, NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 普通成员 (viewer)
INSERT INTO users (id, email, name, password_hash, is_active, is_verified, email_verified_at)
VALUES (
    'b0000000-0000-0000-0000-000000000003',
    'member@example.com',
    '普通成员',
    '$2b$12$tSmpQME3bhIOL.KkFmsroegKv3.iHLOEIHo4WKRDcj2hJPsVnN30W',
    true, true, NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 用户-租户关联
INSERT INTO user_tenants (id, user_id, tenant_id, role, is_primary)
VALUES
    ('c0000000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'owner', true),
    ('c0000000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'member', true),
    ('c0000000-0000-0000-0000-000000000003', 'b0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'viewer', true)
ON CONFLICT ON CONSTRAINT uq_user_tenant DO NOTHING;

-- 为测试租户创建 tenant_configs 记录 (业务模块需要)
INSERT INTO tenant_configs (id, tenant_id)
VALUES (
    'd0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001'
)
ON CONFLICT (tenant_id) DO NOTHING;
