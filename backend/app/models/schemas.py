"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid

# ============================================================================
# Task Schemas
# ============================================================================

class TaskModelCreate(BaseModel):
    """任务-模型关联创建模式"""
    model_id: str = Field(..., description="模型ID，如 openai/gpt-4o")
    priority: int = Field(default=10, ge=1, le=100)
    
    model_config = ConfigDict(protected_namespaces=())


class TaskKeywordCreate(BaseModel):
    """任务-关键词关联创建模式"""
    keyword: str = Field(..., min_length=1, max_length=500)
    category: Optional[str] = Field(None, max_length=100)


class TaskCreate(BaseModel):
    """任务创建请求模式"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    schedule_cron: str = Field(default="0 0 * * *", description="Cron 表达式")
    models: List[str] = Field(..., min_length=1, description="监控的模型列表")
    keywords: List[str] = Field(..., min_length=1, description="监控的关键词列表")
    prompt_template_id: Optional[uuid.UUID] = None


class TaskUpdate(BaseModel):
    """任务更新请求模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    schedule_cron: Optional[str] = None
    is_active: Optional[bool] = None
    models: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    prompt_template_id: Optional[uuid.UUID] = None


class TaskResponse(BaseModel):
    """任务响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str
    description: Optional[str]
    schedule_cron: str
    is_active: bool
    prompt_template_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    models: List[str]
    keywords: List[str]
    last_run_status: Optional[str] = None
    last_run_time: Optional[datetime] = None


class TaskListResponse(BaseModel):
    """任务列表响应模式"""
    data: List[TaskResponse]
    total: int
    page: int
    limit: int


class TaskTriggerResponse(BaseModel):
    """任务触发响应模式"""
    run_id: uuid.UUID
    status: str


# ============================================================================
# Metric Schemas
# ============================================================================

class SOVDataPoint(BaseModel):
    """SOV 数据点"""
    date: str
    sov: float


class SOVTrendResponse(BaseModel):
    """SOV 趋势响应"""
    keyword: str
    model: str
    data: List[SOVDataPoint]


class AccuracyDataPoint(BaseModel):
    """准确性数据点"""
    date: str
    avg_accuracy: float
    min_accuracy: float
    max_accuracy: float


class AccuracyTrendResponse(BaseModel):
    """准确性趋势响应"""
    task_id: uuid.UUID
    data: List[AccuracyDataPoint]


class ModelComparisonData(BaseModel):
    """单个模型对比数据"""
    sov: float
    accuracy: float
    sentiment: float


class ModelComparisonResponse(BaseModel):
    """模型对比响应"""
    keyword: str
    models: dict[str, ModelComparisonData]


class DashboardOverviewResponse(BaseModel):
    """Dashboard 概览响应"""
    total_tasks: int
    active_tasks: int
    sov_trend: List[SOVDataPoint]
    accuracy_trend: List[AccuracyDataPoint]
    top_brands: List[dict]
    recent_alerts: List[dict]
    total_cost_usd: float
    total_token_usage: int


# ============================================================================
# Alert Schemas
# ============================================================================

class AlertResponse(BaseModel):
    """告警响应模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    tenant_id: uuid.UUID
    task_id: Optional[uuid.UUID]
    task_name: Optional[str]
    alert_type: str
    alert_message: str
    metric_name: Optional[str]
    metric_value: Optional[float]
    threshold_value: Optional[float]
    is_read: bool
    is_resolved: bool
    created_at: datetime


class AlertListResponse(BaseModel):
    """告警列表响应"""
    data: List[AlertResponse]
    unread_count: int


class MarkAlertReadResponse(BaseModel):
    """标记告警已读响应"""
    success: bool


class WebhookTestRequest(BaseModel):
    """Webhook 测试请求"""
    webhook_url: str = Field(..., description="Webhook URL")


class WebhookTestResponse(BaseModel):
    """Webhook 测试响应"""
    success: bool
    response_time_ms: int
    response_status: Optional[int] = None


# ============================================================================
# Config Schemas
# ============================================================================

class TenantConfigResponse(BaseModel):
    """租户配置响应"""
    openrouter_api_key_set: bool
    webhook_url: Optional[str]
    alert_threshold_accuracy: int
    alert_threshold_sentiment: float


class TenantConfigUpdate(BaseModel):
    """租户配置更新请求"""
    openrouter_api_key: Optional[str] = Field(None, min_length=1)
    webhook_url: Optional[str] = Field(None, max_length=2000)
    alert_threshold_accuracy: int = Field(default=6, ge=1, le=10)
    alert_threshold_sentiment: float = Field(default=0.5, ge=-1, le=1)


# ============================================================================
# Report Schemas
# ============================================================================

class ReportExportRequest(BaseModel):
    """报表导出请求"""
    task_id: Optional[uuid.UUID] = None
    keyword: Optional[str] = None
    format: str = Field(default="csv", pattern="^(csv|xlsx|pdf)$")
    start_date: str = Field(..., pattern="^\\d{4}-\\d{2}-\\d{2}$")
    end_date: str = Field(..., pattern="^\\d{4}-\\d{2}-\\d{2}$")
    metrics: List[str] = Field(default=["sov", "accuracy", "sentiment"])


# ============================================================================
# Auth Schemas
# ============================================================================

class TokenResponse(BaseModel):
    """Token 响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None
    tenant_id: Optional[str] = None


class LoginRequest(BaseModel):
    """登录请求"""
    email: str = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=8, description="密码")


class SupabaseAuthRequest(BaseModel):
    """Supabase认证请求"""
    access_token: str = Field(..., description="Supabase访问令牌")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordResetRequest(BaseModel):
    """密码重置请求"""
    email: str = Field(..., description="用户邮箱")


class PasswordResetConfirm(BaseModel):
    """密码重置确认"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")


class UserResponse(BaseModel):
    """用户响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    email: str
    name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserCreate(BaseModel):
    """用户创建请求"""
    email: str = Field(..., description="用户邮箱")
    name: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=8, description="密码")


class UserUpdate(BaseModel):
    """用户更新请求"""
    name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class TenantMemberResponse(BaseModel):
    """租户成员响应"""
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    permissions: dict
    is_active: bool
    invited_at: datetime
    joined_at: Optional[datetime]
    user: UserResponse


class TenantMemberInvite(BaseModel):
    """邀请租户成员请求"""
    email: str = Field(..., description="邀请用户的邮箱")
    role: str = Field(default="member", description="用户角色")
    permissions: Optional[dict] = Field(default=None, description="自定义权限")


class TenantMemberUpdate(BaseModel):
    """更新租户成员请求"""
    role: Optional[str] = None
    permissions: Optional[dict] = None
    is_active: Optional[bool] = None


class PermissionCheck(BaseModel):
    """权限检查响应"""
    permission: str
    granted: bool


class UserPermissions(BaseModel):
    """用户权限响应"""
    user_id: uuid.UUID
    tenant_id: uuid.UUID
    role: str
    permissions: dict
    effective_permissions: dict


# ============================================================================
# Common Schemas
# ============================================================================

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class DateRangeParams(BaseModel):
    """日期范围参数"""
    start_date: str = Field(..., pattern="^\\d{4}-\\d{2}-\\d{2}$")
    end_date: str = Field(..., pattern="^\\d{4}-\\d{2}-\\d{2}$")


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """成功响应"""
    success: bool
    message: Optional[str] = None
