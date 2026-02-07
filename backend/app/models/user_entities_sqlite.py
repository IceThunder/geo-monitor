"""
用户相关的数据模型（SQLite兼容版本）
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, UniqueConstraint, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.database_sqlite import Base


# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', String, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String, ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    user_tenants = relationship("UserTenant", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    password_resets = relationship("PasswordReset", back_populates="user", cascade="all, delete-orphan")
    sent_invitations = relationship("UserInvitation", back_populates="inviter", cascade="all, delete-orphan")


class Tenant(Base):
    """租户表"""
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    plan_type = Column(String(20), default='free', nullable=False)  # free, pro, enterprise
    status = Column(String(20), default='active', nullable=False)  # active, suspended, cancelled
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    user_tenants = relationship("UserTenant", back_populates="tenant", cascade="all, delete-orphan")
    config = relationship("UserTenantConfig", back_populates="tenant", uselist=False, cascade="all, delete-orphan")
    invitations = relationship("UserInvitation", back_populates="tenant", cascade="all, delete-orphan")


class UserTenant(Base):
    """用户租户关联表"""
    __tablename__ = "user_tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(String, ForeignKey('tenants.id'), nullable=False)
    role = Column(String(20), default='member', nullable=False)  # owner, admin, member, viewer
    is_primary = Column(Boolean, default=False, nullable=False)
    joined_at = Column(DateTime, default=func.now(), nullable=False)

    # 唯一约束
    __table_args__ = (UniqueConstraint('user_id', 'tenant_id', name='uq_user_tenant'),)

    # 关系
    user = relationship("User", back_populates="user_tenants")
    tenant = relationship("Tenant", back_populates="user_tenants")


class UserSession(Base):
    """用户会话表"""
    __tablename__ = "user_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    tenant_id = Column(String, ForeignKey('tenants.id'), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # 支持IPv6
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 关系
    user = relationship("User", back_populates="sessions")


class EmailVerification(Base):
    """邮箱验证表"""
    __tablename__ = "email_verifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 关系
    user = relationship("User", back_populates="email_verifications")


class PasswordReset(Base):
    """密码重置表"""
    __tablename__ = "password_resets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 关系
    user = relationship("User", back_populates="password_resets")


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 关系
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 关系
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")


class UserInvitation(Base):
    """用户邀请表"""
    __tablename__ = "user_invitations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey('tenants.id'), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # owner, admin, member, viewer
    token = Column(String(255), nullable=False, unique=True, index=True)
    invited_by = Column(String, ForeignKey('users.id'), nullable=False)
    status = Column(String(20), default='pending', nullable=False)  # pending, accepted, expired, cancelled
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # 关系
    tenant = relationship("Tenant", back_populates="invitations")
    inviter = relationship("User", back_populates="sent_invitations")


class UserTenantConfig(Base):
    """租户配置表（认证模块）"""
    __tablename__ = "tenant_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey('tenants.id'), unique=True, nullable=False)
    openrouter_api_key = Column(Text, nullable=True)  # 加密存储
    webhook_url = Column(String(500), nullable=True)
    alert_threshold_accuracy = Column(Integer, default=6, nullable=False)  # 1-10
    alert_threshold_sentiment = Column(Integer, default=50, nullable=False)  # 0-100
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # 关系
    tenant = relationship("Tenant", back_populates="config")
