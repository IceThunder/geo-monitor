"""
认证相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user_entities import User, UserTenant
from app.schemas.user_schemas import (
    UserRegister, UserLogin, LoginResponse, RegisterResponse,
    EmailVerificationRequest, ForgotPasswordRequest, ResetPasswordRequest,
    UserUpdate, PasswordChange, TenantSwitch, UserInvite, InviteResponse,
    TokenRefresh, CurrentUser, MessageResponse, UserResponse, TenantResponse
)

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple[User, UserTenant]:
    """获取当前用户"""
    auth_service = AuthService(db)
    token_data = auth_service.verify_token(credentials.credentials)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户信息
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用"
        )
    
    # 获取用户租户关联
    user_tenant = db.query(UserTenant).filter(
        UserTenant.user_id == token_data.user_id,
        UserTenant.tenant_id == token_data.tenant_id
    ).first()
    
    if not user_tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户不属于该租户"
        )
    
    return user, user_tenant


@router.post("/register", response_model=RegisterResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        auth_service = AuthService(db)
        user, tenant = auth_service.register_user(user_data)
        
        return RegisterResponse(
            message="注册成功，请检查邮箱验证链接",
            user_id=user.id,
            tenant_id=tenant.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        auth_service = AuthService(db)
        user_agent = request.headers.get("user-agent")
        ip_address = request.client.host if request.client else None
        
        user, tenant, access_token, refresh_token = auth_service.login_user(
            login_data, user_agent, ip_address
        )
        
        # 获取用户的所有租户
        user_tenants = auth_service.get_user_tenants(user.id)
        tenants = []
        for ut in user_tenants:
            tenants.append(TenantResponse(
                id=ut.tenant.id,
                name=ut.tenant.name,
                slug=ut.tenant.slug,
                plan_type=ut.tenant.plan_type,
                status=ut.tenant.status,
                role=ut.role,
                is_primary=ut.is_primary
            ))
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,  # 30分钟
            user=UserResponse.from_orm(user),
            tenants=tenants
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=CurrentUser)
async def get_current_user_info(
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user)
):
    """获取当前用户信息"""
    user, user_tenant = current_user_data
    
    return CurrentUser(
        id=user.id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        is_verified=user.is_verified,
        current_tenant=TenantResponse(
            id=user_tenant.tenant.id,
            name=user_tenant.tenant.name,
            slug=user_tenant.tenant.slug,
            plan_type=user_tenant.tenant.plan_type,
            status=user_tenant.tenant.status,
            role=user_tenant.role,
            is_primary=user_tenant.is_primary
        )
    )


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user, _ = current_user_data
    
    if user_update.name is not None:
        user.name = user_update.name
    if user_update.avatar_url is not None:
        user.avatar_url = user_update.avatar_url
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.put("/me/password", response_model=MessageResponse)
async def change_password(
    password_change: PasswordChange,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    user, _ = current_user_data
    auth_service = AuthService(db)
    
    # 验证当前密码
    if not auth_service.verify_password(password_change.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    user.password_hash = auth_service.hash_password(password_change.new_password)
    db.commit()
    
    return MessageResponse(message="密码修改成功")


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """验证邮箱"""
    try:
        auth_service = AuthService(db)
        user = auth_service.verify_email(token)
        
        # 获取用户的主租户
        user_tenant = db.query(UserTenant).filter(
            UserTenant.user_id == user.id,
            UserTenant.is_primary == True
        ).first()
        
        if not user_tenant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户租户关联不存在"
            )
        
        # 生成登录token
        access_token, refresh_token = auth_service.generate_token(
            user.id, user_tenant.tenant_id, user_tenant.role
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800,
            user=UserResponse.from_orm(user),
            tenants=[TenantResponse(
                id=user_tenant.tenant.id,
                name=user_tenant.tenant.name,
                slug=user_tenant.tenant.slug,
                plan_type=user_tenant.tenant.plan_type,
                status=user_tenant.tenant.status,
                role=user_tenant.role,
                is_primary=user_tenant.is_primary
            )]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """忘记密码"""
    try:
        auth_service = AuthService(db)
        auth_service.request_password_reset(request.email)
        
        return MessageResponse(message="密码重置链接已发送到您的邮箱")
    except ValueError as e:
        # 为了安全，即使用户不存在也返回成功消息
        return MessageResponse(message="密码重置链接已发送到您的邮箱")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """重置密码"""
    try:
        auth_service = AuthService(db)
        auth_service.reset_password(request.token, request.new_password)
        
        return MessageResponse(message="密码重置成功")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: TokenRefresh,
    db: Session = Depends(get_db)
):
    """刷新token"""
    try:
        auth_service = AuthService(db)
        access_token, refresh_token = auth_service.refresh_token(request.refresh_token)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: TokenRefresh,
    db: Session = Depends(get_db)
):
    """用户登出"""
    auth_service = AuthService(db)
    auth_service.logout_user(request.refresh_token)
    
    return MessageResponse(message="登出成功")


@router.post("/switch-tenant", response_model=dict)
async def switch_tenant(
    request: TenantSwitch,
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换租户"""
    user, _ = current_user_data
    
    try:
        auth_service = AuthService(db)
        access_token, refresh_token = auth_service.switch_tenant(user.id, request.tenant_id)
        
        # 获取新租户信息
        user_tenant = db.query(UserTenant).filter(
            UserTenant.user_id == user.id,
            UserTenant.tenant_id == request.tenant_id
        ).first()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "tenant": TenantResponse(
                id=user_tenant.tenant.id,
                name=user_tenant.tenant.name,
                slug=user_tenant.tenant.slug,
                plan_type=user_tenant.tenant.plan_type,
                status=user_tenant.tenant.status,
                role=user_tenant.role,
                is_primary=user_tenant.is_primary
            )
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
