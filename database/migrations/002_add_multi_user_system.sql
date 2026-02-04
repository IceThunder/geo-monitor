-- 多用户系统数据库迁移
-- 创建用户、租户和权限相关表

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verified_at TIMESTAMP,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建租户表
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(50) UNIQUE NOT NULL,
    plan_type VARCHAR(20) DEFAULT 'free', -- free, pro, enterprise
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, cancelled
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建用户租户关联表
CREATE TABLE IF NOT EXISTS user_tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- owner, admin, member, viewer
    is_primary BOOLEAN DEFAULT false,
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, tenant_id)
);

-- 创建用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    user_agent TEXT,
    ip_address INET,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建邮箱验证表
CREATE TABLE IF NOT EXISTS email_verifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建密码重置表
CREATE TABLE IF NOT EXISTS password_resets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建角色表
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建权限表
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL, -- tasks, metrics, alerts, config
    action VARCHAR(20) NOT NULL,   -- create, read, update, delete
    description TEXT
);

-- 创建用户邀请表
CREATE TABLE IF NOT EXISTS user_invitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    token VARCHAR(255) UNIQUE NOT NULL,
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    expires_at TIMESTAMP NOT NULL,
    is_accepted BOOLEAN DEFAULT false,
    accepted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 修改现有表，添加tenant_id字段
ALTER TABLE monitor_tasks ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE task_runs ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE metrics_snapshots ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;
ALTER TABLE alert_records ADD COLUMN IF NOT EXISTS tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE;

-- 如果tenant_config表不存在，创建它
CREATE TABLE IF NOT EXISTS tenant_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID UNIQUE REFERENCES tenants(id) ON DELETE CASCADE,
    openrouter_api_key_encrypted TEXT,
    webhook_url VARCHAR(500),
    alert_threshold_accuracy INTEGER DEFAULT 6,
    alert_threshold_sentiment DECIMAL(3,2) DEFAULT 0.5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants(slug);
CREATE INDEX IF NOT EXISTS idx_user_tenants_user_id ON user_tenants(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tenants_tenant_id ON user_tenants(tenant_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_email_verifications_token ON email_verifications(token);
CREATE INDEX IF NOT EXISTS idx_password_resets_token ON password_resets(token);
CREATE INDEX IF NOT EXISTS idx_user_invitations_token ON user_invitations(token);
CREATE INDEX IF NOT EXISTS idx_user_invitations_email ON user_invitations(email);

-- 为现有表添加tenant_id索引
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_tenant_id ON monitor_tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_task_runs_tenant_id ON task_runs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_metrics_snapshots_tenant_id ON metrics_snapshots(tenant_id);
CREATE INDEX IF NOT EXISTS idx_alert_records_tenant_id ON alert_records(tenant_id);

-- 插入默认角色
INSERT INTO roles (name, display_name, description, permissions) VALUES
('super_admin', '系统超级管理员', '拥有所有权限的系统管理员', '["*:*"]'),
('tenant_owner', '租户所有者', '租户的拥有者，拥有租户内所有权限', '["users:*", "tasks:*", "metrics:*", "alerts:*", "config:*"]'),
('tenant_admin', '租户管理员', '租户管理员，可以管理用户和配置', '["users:read", "users:update", "tasks:*", "metrics:*", "alerts:*", "config:*"]'),
('tenant_member', '租户成员', '租户普通成员，可以创建和管理任务', '["tasks:*", "metrics:read", "alerts:read", "alerts:update"]'),
('tenant_viewer', '租户查看者', '只能查看数据的用户', '["tasks:read", "metrics:read", "alerts:read"]')
ON CONFLICT (name) DO NOTHING;

-- 插入默认权限
INSERT INTO permissions (name, resource, action, description) VALUES
('users:create', 'users', 'create', '创建用户'),
('users:read', 'users', 'read', '查看用户'),
('users:update', 'users', 'update', '更新用户'),
('users:delete', 'users', 'delete', '删除用户'),
('tasks:create', 'tasks', 'create', '创建任务'),
('tasks:read', 'tasks', 'read', '查看任务'),
('tasks:update', 'tasks', 'update', '更新任务'),
('tasks:delete', 'tasks', 'delete', '删除任务'),
('metrics:read', 'metrics', 'read', '查看指标'),
('alerts:create', 'alerts', 'create', '创建告警'),
('alerts:read', 'alerts', 'read', '查看告警'),
('alerts:update', 'alerts', 'update', '更新告警'),
('alerts:delete', 'alerts', 'delete', '删除告警'),
('config:read', 'config', 'read', '查看配置'),
('config:update', 'config', 'update', '更新配置')
ON CONFLICT (name) DO NOTHING;

-- 启用行级安全策略 (RLS)
ALTER TABLE monitor_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_config ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略 (这些策略将在应用层通过JWT中的tenant_id来执行)
-- 注意：实际的RLS策略需要根据具体的认证机制来实现
-- 这里先创建基本的策略框架

-- 清理过期的会话和验证token的函数
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    -- 清理过期的用户会话
    DELETE FROM user_sessions WHERE expires_at < NOW();
    
    -- 清理过期的邮箱验证token
    DELETE FROM email_verifications WHERE expires_at < NOW();
    
    -- 清理过期的密码重置token
    DELETE FROM password_resets WHERE expires_at < NOW();
    
    -- 清理过期的用户邀请
    DELETE FROM user_invitations WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- 创建定时清理任务 (需要pg_cron扩展)
-- SELECT cron.schedule('cleanup-tokens', '0 2 * * *', 'SELECT cleanup_expired_tokens();');
