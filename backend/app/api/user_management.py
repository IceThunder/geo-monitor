"""
用户管理API路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from uuid import UUID

from app.core.database import get_db
from app.middleware.auth import get_current_user, require_minimum_role
from app.models.user_entities import User, UserTenant, Tenant, UserInvitation
from app.services.permission_service import PermissionService
from app.schemas.user_schemas import (
    UserResponse, TenantResponse, UserInvite, InviteResponse,
    MessageResponse
)

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("/me/tenants", response_model=List[TenantResponse])
async def get_my_tenants(
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有租户"""
    user, _ = current_user_data
    
    # 获取用户的所有租户关联
    query = select(UserTenant, Tenant).join(
        Tenant, UserTenant.tenant_id == Tenant.id
    ).where(UserTenant.user_id == user.id)
    
    result = db.execute(query)
    tenants = []
    
    for user_tenant, tenant in result:
        tenants.append(TenantResponse(
            id=tenant.id,
            name=tenant.name,
            slug=tenant.slug,
            plan_type=tenant.plan_type,
            status=tenant.status,
            role=user_tenant.role,
            is_primary=user_tenant.is_primary
        ))
    
    return tenants


@router.get("/tenant/members", response_model=List[dict])
async def get_tenant_members(
    current_user_data: tuple[User, UserTenant] = Depends(require_minimum_role("admin")),
    db: Session = Depends(get_db),
):
    """获取当前租户的所有成员"""
    user, user_tenant = current_user_data
    tenant_id = user_tenant.tenant_id
    
    permission_service = PermissionService(db)
    members = permission_service.get_tenant_users_with_roles(tenant_id)
    
    return members


@router.post("/tenant/invite", response_model=InviteResponse)
async def invite_user(
    invite_data: UserInvite,
    current_user_data: tuple[User, UserTenant] = Depends(require_minimum_role("admin")),
    db: Session = Depends(get_db),
):
    """邀请用户加入租户"""
    user, user_tenant = current_user_data
    tenant_id = user_tenant.tenant_id
    
    # 检查邮箱是否已被邀请
    existing_invite = db.query(UserInvitation).filter(
        and_(
            UserInvitation.email == invite_data.email,
            UserInvitation.tenant_id == tenant_id,
            UserInvitation.status == 'pending'
        )
    ).first()
    
    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已有待处理的邀请"
        )
    
    # 检查用户是否已经是租户成员
    existing_user = db.query(User).filter(User.email == invite_data.email).first()
    if existing_user:
        existing_membership = db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == existing_user.id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        if existing_membership:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户已经是租户成员"
            )
    
    # 检查邀请者是否有权限分配该角色
    permission_service = PermissionService(db)
    available_roles = permission_service.get_available_roles_for_user(user.id, tenant_id)
    
    if invite_data.role not in available_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"您无权分配 {invite_data.role} 角色"
        )
    
    # 创建邀请
    invitation = UserInvitation(
        tenant_id=tenant_id,
        email=invite_data.email,
        role=invite_data.role,
        invited_by=user.id,
        token=generate_invitation_token()
    )
    
    db.add(invitation)
    db.commit()

    # Send invitation email
    from app.services.email_service import get_email_service
    email_service = get_email_service()
    import asyncio
    try:
        # Get tenant name
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        tenant_name = tenant.name if tenant else "the team"

        asyncio.create_task(
            email_service.send_invitation_email(
                invite_data.email,
                user.name,
                tenant_name,
                invite_data.role
            )
        )
    except Exception as e:
        # Log but don't fail if email fails
        import logging
        logging.getLogger(__name__).warning(f"Failed to send invitation email: {e}")

    return InviteResponse(
        message="邀请发送成功",
        invite_id=invitation.id
    )


@router.put("/tenant/member/{user_id}/role", response_model=MessageResponse)
async def update_member_role(
    user_id: str,
    new_role: str,
    current_user_data: tuple[User, UserTenant] = Depends(require_minimum_role("admin")),
    db: Session = Depends(get_db),
):
    """更新租户成员角色"""
    user, user_tenant = current_user_data
    tenant_id = user_tenant.tenant_id
    target_user_id = UUID(user_id)
    
    # 检查目标用户是否是租户成员
    target_user_tenant = db.query(UserTenant).filter(
        and_(
            UserTenant.user_id == target_user_id,
            UserTenant.tenant_id == tenant_id
        )
    ).first()
    
    if not target_user_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不是租户成员"
        )
    
    # 检查权限
    permission_service = PermissionService(db)
    
    # 检查是否可以管理该用户
    if not permission_service.can_manage_user(user.id, target_user_id, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您无权管理该用户"
        )
    
    # 检查是否可以分配该角色
    available_roles = permission_service.get_available_roles_for_user(user.id, tenant_id)
    if new_role not in available_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"您无权分配 {new_role} 角色"
        )
    
    # 更新角色
    target_user_tenant.role = new_role
    db.commit()
    
    return MessageResponse(message="用户角色更新成功")


@router.delete("/tenant/member/{user_id}", response_model=MessageResponse)
async def remove_member(
    user_id: str,
    current_user_data: tuple[User, UserTenant] = Depends(require_minimum_role("admin")),
    db: Session = Depends(get_db),
):
    """从租户中移除成员"""
    user, user_tenant = current_user_data
    tenant_id = user_tenant.tenant_id
    target_user_id = UUID(user_id)
    
    # 不能移除自己
    if target_user_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除自己"
        )
    
    # 检查目标用户是否是租户成员
    target_user_tenant = db.query(UserTenant).filter(
        and_(
            UserTenant.user_id == target_user_id,
            UserTenant.tenant_id == tenant_id
        )
    ).first()
    
    if not target_user_tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不是租户成员"
        )
    
    # 检查权限
    permission_service = PermissionService(db)
    if not permission_service.can_manage_user(user.id, target_user_id, tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您无权移除该用户"
        )
    
    # 不能移除租户所有者
    if target_user_tenant.role == 'owner':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能移除租户所有者"
        )
    
    # 移除成员
    db.delete(target_user_tenant)
    db.commit()
    
    return MessageResponse(message="用户移除成功")


@router.get("/tenant/invitations")
async def get_pending_invitations(
    current_user_data: tuple[User, UserTenant] = Depends(require_minimum_role("admin")),
    db: Session = Depends(get_db),
):
    """获取租户的待处理邀请"""
    user, user_tenant = current_user_data
    tenant_id = user_tenant.tenant_id
    
    invitations = db.query(UserInvitation).filter(
        and_(
            UserInvitation.tenant_id == tenant_id,
            UserInvitation.status == 'pending'
        )
    ).all()
    
    return [
        {
            "id": str(invitation.id),
            "email": invitation.email,
            "role": invitation.role,
            "invited_at": invitation.created_at,
            "expires_at": invitation.expires_at
        }
        for invitation in invitations
    ]


@router.delete("/tenant/invitation/{invitation_id}", response_model=MessageResponse)
async def cancel_invitation(
    invitation_id: str,
    current_user_data: tuple[User, UserTenant] = Depends(require_minimum_role("admin")),
    db: Session = Depends(get_db),
):
    """取消邀请"""
    user, user_tenant = current_user_data
    tenant_id = user_tenant.tenant_id
    
    invitation = db.query(UserInvitation).filter(
        and_(
            UserInvitation.id == UUID(invitation_id),
            UserInvitation.tenant_id == tenant_id,
            UserInvitation.status == 'pending'
        )
    ).first()
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邀请不存在"
        )
    
    invitation.status = 'cancelled'
    db.commit()
    
    return MessageResponse(message="邀请已取消")


@router.get("/permissions")
async def get_my_permissions(
    current_user_data: tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的权限列表"""
    user, user_tenant = current_user_data
    
    permission_service = PermissionService(db)
    permissions = permission_service.get_user_permissions(user.id, user_tenant.tenant_id)
    
    return {
        "user_id": str(user.id),
        "tenant_id": str(user_tenant.tenant_id),
        "role": user_tenant.role,
        "permissions": permissions
    }


def generate_invitation_token() -> str:
    """生成邀请token"""
    import secrets
    return secrets.token_urlsafe(32)
