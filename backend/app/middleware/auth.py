"""
JWT认证中间件
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Tuple
from uuid import UUID

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.models.user_entities import User, UserTenant, Tenant
from app.schemas.user_schemas import TokenData


security = HTTPBearer(auto_error=False)


class AuthMiddleware:
    """JWT认证中间件类"""
    
    def __init__(self):
        pass
    
    async def get_current_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Tuple[User, UserTenant]:
        """获取当前认证用户"""
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少认证token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
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
    
    async def get_optional_user(
        self,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> Optional[Tuple[User, UserTenant]]:
        """获取可选的当前用户（不强制要求认证）"""
        if not credentials:
            return None
        
        try:
            return await self.get_current_user(credentials, db)
        except HTTPException:
            return None
    
    def require_roles(self, *allowed_roles: str):
        """要求特定角色的装饰器"""
        def decorator(func):
            async def wrapper(
                current_user_data: Tuple[User, UserTenant] = Depends(self.get_current_user),
                *args, **kwargs
            ):
                user, user_tenant = current_user_data
                
                if user_tenant.role not in allowed_roles:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"需要以下角色之一: {', '.join(allowed_roles)}"
                    )
                
                return await func(current_user_data, *args, **kwargs)
            return wrapper
        return decorator
    
    def require_permissions(self, *required_permissions: str):
        """要求特定权限的装饰器"""
        def decorator(func):
            async def wrapper(
                current_user_data: Tuple[User, UserTenant] = Depends(self.get_current_user),
                db: Session = Depends(get_db),
                *args, **kwargs
            ):
                user, user_tenant = current_user_data
                
                # 检查用户是否有所需权限
                has_permission = self._check_user_permissions(
                    db, user_tenant, required_permissions
                )
                
                if not has_permission:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"缺少必要权限: {', '.join(required_permissions)}"
                    )
                
                return await func(current_user_data, db, *args, **kwargs)
            return wrapper
        return decorator
    
    def require_verified_email(self):
        """要求邮箱已验证的装饰器"""
        def decorator(func):
            async def wrapper(
                current_user_data: Tuple[User, UserTenant] = Depends(self.get_current_user),
                *args, **kwargs
            ):
                user, user_tenant = current_user_data
                
                if not user.is_verified:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="请先验证您的邮箱地址"
                    )
                
                return await func(current_user_data, *args, **kwargs)
            return wrapper
        return decorator
    
    def require_active_tenant(self):
        """要求租户状态为活跃的装饰器"""
        def decorator(func):
            async def wrapper(
                current_user_data: Tuple[User, UserTenant] = Depends(self.get_current_user),
                db: Session = Depends(get_db),
                *args, **kwargs
            ):
                user, user_tenant = current_user_data
                
                tenant = db.query(Tenant).filter(Tenant.id == user_tenant.tenant_id).first()
                if not tenant or tenant.status != 'active':
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="租户账户已被暂停或取消"
                    )
                
                return await func(current_user_data, db, *args, **kwargs)
            return wrapper
        return decorator
    
    def _check_user_permissions(
        self, 
        db: Session, 
        user_tenant: UserTenant, 
        required_permissions: Tuple[str, ...]
    ) -> bool:
        """检查用户是否有所需权限"""
        from app.models.user_entities import Role, Permission
        
        # 根据角色获取权限
        role_permissions = db.query(Permission).join(
            Role.permissions
        ).filter(Role.name == user_tenant.role).all()
        
        user_permission_names = {perm.name for perm in role_permissions}
        
        # 检查是否有所有必需的权限
        return all(perm in user_permission_names for perm in required_permissions)


# 创建全局认证中间件实例
auth_middleware = AuthMiddleware()

# 便捷的依赖注入函数
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Tuple[User, UserTenant]:
    """获取当前认证用户的便捷函数"""
    return await auth_middleware.get_current_user(credentials, db)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Tuple[User, UserTenant]]:
    """获取可选当前用户的便捷函数"""
    return await auth_middleware.get_optional_user(credentials, db)


def require_roles(*roles: str):
    """要求特定角色的便捷装饰器"""
    return auth_middleware.require_roles(*roles)


def require_permissions(*permissions: str):
    """要求特定权限的便捷装饰器"""
    return auth_middleware.require_permissions(*permissions)


def require_verified_email():
    """要求邮箱已验证的便捷装饰器"""
    return auth_middleware.require_verified_email()


def require_active_tenant():
    """要求租户状态为活跃的便捷装饰器"""
    return auth_middleware.require_active_tenant()


# 角色层级定义
ROLE_HIERARCHY = {
    'owner': 4,
    'admin': 3,
    'member': 2,
    'viewer': 1
}


def has_higher_or_equal_role(user_role: str, required_role: str) -> bool:
    """检查用户角色是否高于或等于所需角色"""
    user_level = ROLE_HIERARCHY.get(user_role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    return user_level >= required_level


def require_minimum_role(min_role: str):
    """要求最低角色级别的装饰器"""
    def decorator(func):
        async def wrapper(
            current_user_data: Tuple[User, UserTenant] = Depends(get_current_user),
            *args, **kwargs
        ):
            user, user_tenant = current_user_data
            
            if not has_higher_or_equal_role(user_tenant.role, min_role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"需要至少 {min_role} 角色权限"
                )
            
            return await func(current_user_data, *args, **kwargs)
        return wrapper
    return decorator
