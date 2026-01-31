"""
SQLAlchemy database entities/models.
"""
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, Integer, Numeric, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.database import Base
from app.core.config import settings

# Use appropriate UUID type based on database
def get_uuid_column():
    """Get UUID column type based on database URL."""
    if settings.get_database_url().startswith("postgresql"):
        return PostgresUUID(as_uuid=True)
    else:
        # For SQLite, use String to store UUID as text
        return String(36)

# ============================================================================
# Monitor Tasks
# ============================================================================

class MonitorTask(Base):
    """监控任务表"""
    __tablename__ = "monitor_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("tenant_configs.tenant_id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schedule_cron: Mapped[str] = mapped_column(String(100), default="0 0 * * *")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    prompt_template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        get_uuid_column(), 
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    models: Mapped[List["TaskModel"]] = relationship(
        "TaskModel", 
        back_populates="task", 
        cascade="all, delete-orphan"
    )
    keywords: Mapped[List["TaskKeyword"]] = relationship(
        "TaskKeyword", 
        back_populates="task", 
        cascade="all, delete-orphan"
    )
    runs: Mapped[List["TaskRun"]] = relationship(
        "TaskRun", 
        back_populates="task", 
        cascade="all, delete-orphan"
    )
    tenant: Mapped["TenantConfig"] = relationship("TenantConfig", back_populates="tasks")


class TaskModel(Base):
    """任务-模型关联表"""
    __tablename__ = "task_models"
    
    task_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("monitor_tasks.id", ondelete="CASCADE"),
        primary_key=True
    )
    model_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    priority: Mapped[int] = mapped_column(Integer, default=10)
    
    # Relationships
    task: Mapped["MonitorTask"] = relationship("MonitorTask", back_populates="models")


class TaskKeyword(Base):
    """任务-关键词关联表"""
    __tablename__ = "task_keywords"
    
    task_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("monitor_tasks.id", ondelete="CASCADE"),
        primary_key=True
    )
    keyword: Mapped[str] = mapped_column(String(500), primary_key=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Relationships
    task: Mapped["MonitorTask"] = relationship("MonitorTask", back_populates="keywords")


# ============================================================================
# Task Execution
# ============================================================================

class TaskRun(Base):
    """任务运行记录表"""
    __tablename__ = "task_runs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("monitor_tasks.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), 
        default="pending"
    )  # pending, running, completed, failed
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Numeric] = mapped_column(
        Numeric(10, 4), 
        default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    
    # Relationships
    task: Mapped["MonitorTask"] = relationship("MonitorTask", back_populates="runs")
    outputs: Mapped[List["ModelOutput"]] = relationship(
        "ModelOutput", 
        back_populates="run", 
        cascade="all, delete-orphan"
    )
    metrics: Mapped[List["MetricsSnapshot"]] = relationship(
        "MetricsSnapshot", 
        back_populates="run", 
        cascade="all, delete-orphan"
    )


class ModelOutput(Base):
    """模型输出原始数据"""
    __tablename__ = "model_outputs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("task_runs.id", ondelete="CASCADE"),
        nullable=False
    )
    keyword: Mapped[str] = mapped_column(String(500), nullable=False)
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_usage: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[Numeric] = mapped_column(
        Numeric(10, 4), 
        default=0
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    
    # Relationships
    run: Mapped["TaskRun"] = relationship("TaskRun", back_populates="outputs")


class MetricsSnapshot(Base):
    """指标快照表"""
    __tablename__ = "metrics_snapshot"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("task_runs.id", ondelete="CASCADE"),
        nullable=False
    )
    model_id: Mapped[str] = mapped_column(String(100), nullable=False)
    keyword: Mapped[str] = mapped_column(String(500), nullable=False)
    sov_score: Mapped[Optional[Numeric]] = mapped_column(
        Numeric(5, 2), 
        nullable=True
    )
    accuracy_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sentiment_score: Mapped[Optional[Numeric]] = mapped_column(
        Numeric(5, 2), 
        nullable=True
    )
    citation_rate: Mapped[Optional[Numeric]] = mapped_column(
        Numeric(5, 2), 
        nullable=True
    )
    positioning_hit: Mapped[bool] = mapped_column(Boolean, default=False)
    brands_mentioned: Mapped[dict] = mapped_column(JSON, default=list)
    analysis_details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    
    # Relationships
    run: Mapped["TaskRun"] = relationship("TaskRun", back_populates="metrics")
    
    # Unique constraint
    __table_args__ = (
        {},
    )


# ============================================================================
# User Management
# ============================================================================

class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    supabase_user_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    tenant_memberships: Mapped[List["TenantMember"]] = relationship(
        "TenantMember", 
        back_populates="user"
    )


class TenantMember(Base):
    """租户成员关联表"""
    __tablename__ = "tenant_members"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("tenant_configs.tenant_id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(
        String(50), 
        default="member"
    )  # owner, admin, member, viewer
    permissions: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    joined_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tenant_memberships")
    tenant: Mapped["TenantConfig"] = relationship("TenantConfig", back_populates="members")
    
    # Unique constraint
    __table_args__ = (
        {},
    )


# ============================================================================
# Tenant Configuration
# ============================================================================

class TenantConfig(Base):
    """租户配置表"""
    __tablename__ = "tenant_configs"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        unique=True, 
        nullable=False
    )
    openrouter_api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True
    )
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    alert_threshold_accuracy: Mapped[int] = mapped_column(Integer, default=6)
    alert_threshold_sentiment: Mapped[Numeric] = mapped_column(
        Numeric(5, 2), 
        default=0.5
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    tasks: Mapped[List["MonitorTask"]] = relationship(
        "MonitorTask", 
        back_populates="tenant"
    )
    members: Mapped[List["TenantMember"]] = relationship(
        "TenantMember", 
        back_populates="tenant"
    )


# ============================================================================
# Alert Records
# ============================================================================

class AlertRecord(Base):
    """告警记录表"""
    __tablename__ = "alert_records"
    
    id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        primary_key=True, 
        default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        nullable=False
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        get_uuid_column(), 
        ForeignKey("monitor_tasks.id", ondelete="CASCADE"),
        nullable=True
    )
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    metric_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metric_value: Mapped[Optional[Numeric]] = mapped_column(
        Numeric(10, 4), 
        nullable=True
    )
    threshold_value: Mapped[Optional[Numeric]] = mapped_column(
        Numeric(10, 4), 
        nullable=True
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        default=datetime.utcnow
    )
