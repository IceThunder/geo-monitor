"""
用户相关的Pydantic模式
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# 用户注册
class UserRegister(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    tenant_name: Optional[str] = Field(None, max_length=100)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少需要8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


# 用户登录
class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember: bool = False


# 用户信息响应
class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime]

    class Config:
        from_attributes = True


# 租户信息响应
class TenantResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    plan_type: str
    status: str
    role: str  # 用户在该租户中的角色
    is_primary: bool

    class Config:
        from_attributes = True


# 登录响应
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    tenants: List[TenantResponse]


# 注册响应
class RegisterResponse(BaseModel):
    message: str
    user_id: UUID
    tenant_id: UUID


# 邮箱验证
class EmailVerificationRequest(BaseModel):
    token: str


# 忘记密码
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


# 重置密码
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少需要8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


# 更新用户信息
class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = Field(None, max_length=500)


# 修改密码
class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少需要8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


# 切换租户
class TenantSwitch(BaseModel):
    tenant_id: UUID


# 邀请用户
class UserInvite(BaseModel):
    email: EmailStr
    role: str = Field(..., pattern="^(owner|admin|member|viewer)$")


# 邀请响应
class InviteResponse(BaseModel):
    message: str
    invite_id: UUID


# Token刷新
class TokenRefresh(BaseModel):
    refresh_token: str


# JWT Token载荷
class TokenData(BaseModel):
    user_id: UUID
    tenant_id: UUID
    role: str
    exp: datetime


# 当前用户信息（包含租户信息）
class CurrentUser(BaseModel):
    id: UUID
    email: str
    name: str
    avatar_url: Optional[str]
    is_verified: bool
    current_tenant: TenantResponse

    class Config:
        from_attributes = True


# 用户会话信息
class UserSessionResponse(BaseModel):
    id: UUID
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True


# 租户配置更新
class TenantConfigUpdate(BaseModel):
    openrouter_api_key: Optional[str] = None
    webhook_url: Optional[str] = Field(None, max_length=500)
    alert_threshold_accuracy: Optional[int] = Field(None, ge=1, le=10)
    alert_threshold_sentiment: Optional[int] = Field(None, ge=0, le=100)


# 租户配置响应
class TenantConfigResponse(BaseModel):
    openrouter_api_key_set: bool
    webhook_url: Optional[str]
    alert_threshold_accuracy: int
    alert_threshold_sentiment: int

    class Config:
        from_attributes = True


# 通用响应
class MessageResponse(BaseModel):
    message: str


# 错误响应
class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
