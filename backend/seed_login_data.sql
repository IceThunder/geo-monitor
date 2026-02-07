-- ============================================================
-- GEO Monitor 测试登录数据 Seed Script
-- 密码统一: Test@123456
-- 可直接在 Supabase SQL Editor 或 psql 中执行
-- ============================================================

-- 1. 默认租户
INSERT INTO tenants (id, name, slug, plan_type, status, created_at, updated_at)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'GEO Monitor 测试团队',
    'geo-test',
    'free',
    'active',
    NOW(),
    NOW()
)
ON CONFLICT (slug) DO NOTHING;

-- 2. 用户（密码: Test@123456）
-- bcrypt hash: $2b$12$tSmpQME3bhIOL.KkFmsroegKv3.iHLOEIHo4WKRDcj2hJPsVnN30W

-- 管理员 (owner)
INSERT INTO users (id, email, name, password_hash, is_active, is_verified, email_verified_at, created_at, updated_at)
VALUES (
    'b0000000-0000-0000-0000-000000000001',
    'admin@example.com',
    '管理员',
    '$2b$12$tSmpQME3bhIOL.KkFmsroegKv3.iHLOEIHo4WKRDcj2hJPsVnN30W',
    true,
    true,
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 测试用户 (member)
INSERT INTO users (id, email, name, password_hash, is_active, is_verified, email_verified_at, created_at, updated_at)
VALUES (
    'b0000000-0000-0000-0000-000000000002',
    'test@example.com',
    '测试用户',
    '$2b$12$tSmpQME3bhIOL.KkFmsroegKv3.iHLOEIHo4WKRDcj2hJPsVnN30W',
    true,
    true,
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 普通成员 (viewer)
INSERT INTO users (id, email, name, password_hash, is_active, is_verified, email_verified_at, created_at, updated_at)
VALUES (
    'b0000000-0000-0000-0000-000000000003',
    'member@example.com',
    '普通成员',
    '$2b$12$tSmpQME3bhIOL.KkFmsroegKv3.iHLOEIHo4WKRDcj2hJPsVnN30W',
    true,
    true,
    NOW(),
    NOW(),
    NOW()
)
ON CONFLICT (email) DO NOTHING;

-- 3. 用户-租户关联
-- admin → owner
INSERT INTO user_tenants (id, user_id, tenant_id, role, is_primary, joined_at)
VALUES (
    'c0000000-0000-0000-0000-000000000001',
    'b0000000-0000-0000-0000-000000000001',
    'a0000000-0000-0000-0000-000000000001',
    'owner',
    true,
    NOW()
)
ON CONFLICT ON CONSTRAINT uq_user_tenant DO NOTHING;

-- test → member
INSERT INTO user_tenants (id, user_id, tenant_id, role, is_primary, joined_at)
VALUES (
    'c0000000-0000-0000-0000-000000000002',
    'b0000000-0000-0000-0000-000000000002',
    'a0000000-0000-0000-0000-000000000001',
    'member',
    true,
    NOW()
)
ON CONFLICT ON CONSTRAINT uq_user_tenant DO NOTHING;

-- member → viewer
INSERT INTO user_tenants (id, user_id, tenant_id, role, is_primary, joined_at)
VALUES (
    'c0000000-0000-0000-0000-000000000003',
    'b0000000-0000-0000-0000-000000000003',
    'a0000000-0000-0000-0000-000000000001',
    'viewer',
    true,
    NOW()
)
ON CONFLICT ON CONSTRAINT uq_user_tenant DO NOTHING;
