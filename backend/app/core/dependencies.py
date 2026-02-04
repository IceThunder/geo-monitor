"""
全局依赖项和中间件配置
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, Tuple

from app.core.database import get_db
from app.middleware.auth import get_current_user, get_optional_user
from app.models.user_entities import User, UserTenant


async def get_current_user_dependency(
    current_user_data: Tuple[User, UserTenant] = Depends(get_current_user)
) -> Tuple[User, UserTenant]:
    """获取当前用户的全局依赖项"""
    return current_user_data


async def get_optional_user_dependency(
    current_user_data: Optional[Tuple[User, UserTenant]] = Depends(get_optional_user)
) -> Optional[Tuple[User, UserTenant]]:
    """获取可选用户的全局依赖项"""
    return current_user_data


def get_current_tenant_id(
    current_user_data: Tuple[User, UserTenant] = Depends(get_current_user)
) -> str:
    """获取当前租户ID"""
    user, user_tenant = current_user_data
    return str(user_tenant.tenant_id)


def get_current_user_id(
    current_user_data: Tuple[User, UserTenant] = Depends(get_current_user)
) -> str:
    """获取当前用户ID"""
    user, user_tenant = current_user_data
    return str(user.id)


def require_verified_user(
    current_user_data: Tuple[User, UserTenant] = Depends(get_current_user)
) -> Tuple[User, UserTenant]:
    """要求用户邮箱已验证"""
    user, user_tenant = current_user_data
    
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="请先验证您的邮箱地址"
        )
    
    return current_user_data


def require_active_user(
    current_user_data: Tuple[User, UserTenant] = Depends(get_current_user)
) -> Tuple[User, UserTenant]:
    """要求用户账户为活跃状态"""
    user, user_tenant = current_user_data
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    
    return current_user_data


def require_role(required_role: str):
    """要求特定角色的依赖项工厂"""
    def dependency(
        current_user_data: Tuple[User, UserTenant] = Depends(get_current_user)
    ) -> Tuple[User, UserTenant]:
        user, user_tenant = current_user_data
        
        if user_tenant.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要 {required_role} 角色权限"
            )
        
        return current_user_data
    
    return dependency


def require_owner():
    """要求所有者角色"""
    return require_role("owner")


def require_admin():
    """要求管理员角色"""
    return require_role("admin")


def require_member():
    """要求成员角色"""
    return require_role("member")
