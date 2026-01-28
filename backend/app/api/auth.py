"""
Authentication API endpoints.
"""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_user_token,
    sync_supabase_user,
    verify_supabase_jwt,
    get_current_user,
    get_current_tenant_id,
    get_current_user_membership,
    Permission,
    Role,
    check_permission
)
from app.models.database import get_db
from app.models.entities import User, TenantConfig, TenantMember
from app.models.schemas import (
    LoginRequest,
    TokenResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    SupabaseAuthRequest,
    TenantMemberResponse,
    TenantMemberInvite,
    TenantMemberUpdate,
    UserPermissions,
    PermissionCheck,
    SuccessResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """用户登录"""
    # 查找用户
    result = db.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # 获取用户的主租户
    membership_result = db.execute(
        select(TenantMember)
        .where(
            TenantMember.user_id == user.id,
            TenantMember.is_active == True
        )
        .order_by(TenantMember.joined_at.desc())
        .limit(1)
    )
    membership = membership_result.scalar_one_or_none()
    
    tenant_id = str(membership.tenant_id) if membership else None
    
    # 创建访问令牌
    token_response = create_user_token(user, tenant_id)
    token_response.user = UserResponse.model_validate(user)
    token_response.tenant_id = tenant_id
    
    return token_response


@router.post("/register", response_model=TokenResponse)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 检查邮箱是否已存在
    result = db.execute(
        select(User).where(User.email == user_data.email)
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
        is_active=True,
        is_verified=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # 创建默认租户配置
    tenant_config = TenantConfig(
        tenant_id=user.id,  # 使用用户ID作为默认租户ID
        alert_threshold_accuracy=6,
        alert_threshold_sentiment=0.5
    )
    db.add(tenant_config)
    
    # 创建租户成员关系
    tenant_member = TenantMember(
        tenant_id=user.id,
        user_id=user.id,
        role=Role.OWNER,
        permissions=Role.get_default_permissions(Role.OWNER),
        is_active=True,
        joined_at=user.created_at
    )
    db.add(tenant_member)
    
    db.commit()
    
    # 创建访问令牌
    token_response = create_user_token(user, str(user.id))
    token_response.user = UserResponse.model_validate(user)
    token_response.tenant_id = str(user.id)
    
    return token_response


@router.post("/supabase", response_model=TokenResponse)
async def supabase_auth(
    auth_data: SupabaseAuthRequest,
    db: Session = Depends(get_db)
):
    """Supabase认证登录"""
    # 验证Supabase JWT
    supabase_payload = verify_supabase_jwt(auth_data.access_token)
    
    # 同步用户到本地数据库
    user = sync_supabase_user(supabase_payload, db)
    
    # 检查用户是否有租户成员关系
    membership_result = db.execute(
        select(TenantMember)
        .where(
            TenantMember.user_id == user.id,
            TenantMember.is_active == True
        )
        .order_by(TenantMember.joined_at.desc())
        .limit(1)
    )
    membership = membership_result.scalar_one_or_none()
    
    # 如果没有租户成员关系，创建默认租户
    if not membership:
        # 创建默认租户配置
        tenant_config = TenantConfig(
            tenant_id=user.id,
            alert_threshold_accuracy=6,
            alert_threshold_sentiment=0.5
        )
        db.add(tenant_config)
        
        # 创建租户成员关系
        membership = TenantMember(
            tenant_id=user.id,
            user_id=user.id,
            role=Role.OWNER,
            permissions=Role.get_default_permissions(Role.OWNER),
            is_active=True,
            joined_at=user.created_at
        )
        db.add(membership)
        db.commit()
    
    tenant_id = str(membership.tenant_id)
    
    # 创建访问令牌
    token_response = create_user_token(user, tenant_id)
    token_response.user = UserResponse.model_validate(user)
    token_response.tenant_id = tenant_id
    
    return token_response


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息"""
    # 更新用户信息
    if user_update.name is not None:
        current_user.name = user_update.name
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.get("/permissions", response_model=UserPermissions)
async def get_user_permissions(
    current_user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership)
):
    """获取当前用户权限"""
    # 获取角色默认权限
    role_permissions = Role.get_default_permissions(membership.role)
    
    # 合并自定义权限
    effective_permissions = {**role_permissions, **membership.permissions}
    
    return UserPermissions(
        user_id=current_user.id,
        tenant_id=membership.tenant_id,
        role=membership.role,
        permissions=membership.permissions,
        effective_permissions=effective_permissions
    )


@router.post("/check-permission", response_model=PermissionCheck)
async def check_user_permission(
    permission: str,
    membership: TenantMember = Depends(get_current_user_membership)
):
    """检查用户是否有特定权限"""
    granted = check_permission(membership, permission)
    
    return PermissionCheck(
        permission=permission,
        granted=granted
    )


# ============================================================================
# Tenant Member Management
# ============================================================================

@router.get("/members", response_model=list[TenantMemberResponse])
async def get_tenant_members(
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db)
):
    """获取租户成员列表"""
    # 检查权限
    if not check_permission(membership, Permission.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view members"
        )
    
    # 查询租户成员
    result = db.execute(
        select(TenantMember)
        .where(TenantMember.tenant_id == tenant_id)
        .order_by(TenantMember.joined_at.desc())
    )
    members = result.scalars().all()
    
    # 加载用户信息
    member_responses = []
    for member in members:
        user_result = db.execute(
            select(User).where(User.id == member.user_id)
        )
        user = user_result.scalar_one()
        
        member_response = TenantMemberResponse.model_validate(member)
        member_response.user = UserResponse.model_validate(user)
        member_responses.append(member_response)
    
    return member_responses


@router.post("/invite", response_model=TenantMemberResponse)
async def invite_member(
    invite_data: TenantMemberInvite,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db)
):
    """邀请新成员加入租户"""
    # 检查权限
    if not check_permission(membership, Permission.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to invite members"
        )
    
    # 查找或创建用户
    user_result = db.execute(
        select(User).where(User.email == invite_data.email)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        # 创建新用户（待激活状态）
        user = User(
            email=invite_data.email,
            is_active=False,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # 检查是否已经是成员
    existing_member_result = db.execute(
        select(TenantMember).where(
            TenantMember.tenant_id == tenant_id,
            TenantMember.user_id == user.id
        )
    )
    existing_member = existing_member_result.scalar_one_or_none()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this tenant"
        )
    
    # 创建租户成员关系
    permissions = invite_data.permissions or Role.get_default_permissions(invite_data.role)
    
    new_member = TenantMember(
        tenant_id=tenant_id,
        user_id=user.id,
        role=invite_data.role,
        permissions=permissions,
        is_active=True
    )
    
    db.add(new_member)
    db.commit()
    db.refresh(new_member)
    
    # 返回成员信息
    member_response = TenantMemberResponse.model_validate(new_member)
    member_response.user = UserResponse.model_validate(user)
    
    return member_response


@router.put("/members/{member_id}", response_model=TenantMemberResponse)
async def update_member(
    member_id: str,
    update_data: TenantMemberUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db)
):
    """更新租户成员"""
    # 检查权限
    if not check_permission(membership, Permission.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update members"
        )
    
    # 查找成员
    member_result = db.execute(
        select(TenantMember).where(
            TenantMember.id == member_id,
            TenantMember.tenant_id == tenant_id
        )
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # 防止用户修改自己的权限
    if member.user_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own permissions"
        )
    
    # 更新成员信息
    if update_data.role is not None:
        member.role = update_data.role
        # 更新角色时重置为默认权限
        member.permissions = Role.get_default_permissions(update_data.role)
    
    if update_data.permissions is not None:
        member.permissions = {**member.permissions, **update_data.permissions}
    
    if update_data.is_active is not None:
        member.is_active = update_data.is_active
    
    db.commit()
    db.refresh(member)
    
    # 加载用户信息
    user_result = db.execute(
        select(User).where(User.id == member.user_id)
    )
    user = user_result.scalar_one()
    
    member_response = TenantMemberResponse.model_validate(member)
    member_response.user = UserResponse.model_validate(user)
    
    return member_response


@router.delete("/members/{member_id}", response_model=SuccessResponse)
async def remove_member(
    member_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    membership: TenantMember = Depends(get_current_user_membership),
    db: Session = Depends(get_db)
):
    """移除租户成员"""
    # 检查权限
    if not check_permission(membership, Permission.MANAGE_USERS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to remove members"
        )
    
    # 查找成员
    member_result = db.execute(
        select(TenantMember).where(
            TenantMember.id == member_id,
            TenantMember.tenant_id == tenant_id
        )
    )
    member = member_result.scalar_one_or_none()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # 防止用户删除自己
    if member.user_id == membership.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the tenant"
        )
    
    # 删除成员
    db.delete(member)
    db.commit()
    
    return SuccessResponse(success=True, message="Member removed successfully")
