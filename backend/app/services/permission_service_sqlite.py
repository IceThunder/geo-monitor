"""
权限管理服务（SQLite兼容版本）
"""
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from typing import List, Dict, Optional
from uuid import UUID

from app.models.simple_user_models import (
    Role, Permission, UserTenant, User, Tenant
)


class PermissionService:
    """权限管理服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_permissions(self, user_id: str, tenant_id: str) -> List[str]:
        """获取用户在指定租户中的权限列表"""
        # 获取用户在租户中的角色
        user_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        if not user_tenant:
            return []
        
        # 获取角色对应的权限
        role = self.db.query(Role).filter(Role.name == user_tenant.role).first()
        if not role:
            return []
        
        return [perm.name for perm in role.permissions]
    
    def has_permission(self, user_id: str, tenant_id: str, permission_name: str) -> bool:
        """检查用户是否有指定权限"""
        permissions = self.get_user_permissions(user_id, tenant_id)
        return permission_name in permissions
    
    def has_any_permission(self, user_id: str, tenant_id: str, permission_names: List[str]) -> bool:
        """检查用户是否有任意一个指定权限"""
        permissions = self.get_user_permissions(user_id, tenant_id)
        return any(perm in permissions for perm in permission_names)
    
    def has_all_permissions(self, user_id: str, tenant_id: str, permission_names: List[str]) -> bool:
        """检查用户是否有所有指定权限"""
        permissions = self.get_user_permissions(user_id, tenant_id)
        return all(perm in permissions for perm in permission_names)
    
    def get_role_permissions(self, role_name: str) -> List[str]:
        """获取角色的权限列表"""
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not role:
            return []
        
        return [perm.name for perm in role.permissions]
    
    def create_role(self, name: str, description: str, permissions: List[str]) -> Role:
        """创建新角色"""
        # 检查角色是否已存在
        existing_role = self.db.query(Role).filter(Role.name == name).first()
        if existing_role:
            raise ValueError(f"角色 {name} 已存在")
        
        # 创建角色
        role = Role(name=name, description=description)
        self.db.add(role)
        self.db.flush()
        
        # 添加权限
        for perm_name in permissions:
            permission = self.db.query(Permission).filter(Permission.name == perm_name).first()
            if permission:
                role.permissions.append(permission)
        
        self.db.commit()
        return role
    
    def update_role_permissions(self, role_name: str, permissions: List[str]) -> Role:
        """更新角色权限"""
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError(f"角色 {role_name} 不存在")
        
        # 清除现有权限
        role.permissions.clear()
        
        # 添加新权限
        for perm_name in permissions:
            permission = self.db.query(Permission).filter(Permission.name == perm_name).first()
            if permission:
                role.permissions.append(permission)
        
        self.db.commit()
        return role
    
    def assign_user_role(self, user_id: str, tenant_id: str, role_name: str) -> UserTenant:
        """为用户分配角色"""
        # 检查角色是否存在
        role = self.db.query(Role).filter(Role.name == role_name).first()
        if not role:
            raise ValueError(f"角色 {role_name} 不存在")
        
        # 获取用户租户关联
        user_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        if not user_tenant:
            raise ValueError("用户不属于该租户")
        
        # 更新角色
        user_tenant.role = role_name
        self.db.commit()
        
        return user_tenant
    
    def get_tenant_users_with_roles(self, tenant_id: str) -> List[Dict]:
        """获取租户中所有用户及其角色"""
        query = select(User, UserTenant).join(
            UserTenant, User.id == UserTenant.user_id
        ).where(UserTenant.tenant_id == tenant_id)
        
        result = self.db.execute(query)
        users_data = []
        
        for user, user_tenant in result:
            users_data.append({
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user_tenant.role,
                "is_primary": user_tenant.is_primary,
                "joined_at": user_tenant.joined_at,
                "permissions": self.get_user_permissions(user.id, tenant_id)
            })
        
        return users_data
    
    def can_manage_user(self, manager_user_id: str, target_user_id: str, tenant_id: str) -> bool:
        """检查管理员是否可以管理目标用户"""
        # 获取管理员角色
        manager_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == manager_user_id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        # 获取目标用户角色
        target_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == target_user_id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        if not manager_tenant or not target_tenant:
            return False
        
        # 角色层级检查
        role_hierarchy = {
            'owner': 4,
            'admin': 3,
            'member': 2,
            'viewer': 1
        }
        
        manager_level = role_hierarchy.get(manager_tenant.role, 0)
        target_level = role_hierarchy.get(target_tenant.role, 0)
        
        # 管理员级别必须高于目标用户，且不能管理同级别用户（除非是owner）
        if manager_tenant.role == 'owner':
            return True
        
        return manager_level > target_level
    
    def get_available_roles_for_user(self, user_id: str, tenant_id: str) -> List[str]:
        """获取用户可以分配的角色列表"""
        user_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == user_id,
                UserTenant.tenant_id == tenant_id
            )
        ).first()
        
        if not user_tenant:
            return []
        
        # 根据用户角色返回可分配的角色
        if user_tenant.role == 'owner':
            return ['owner', 'admin', 'member', 'viewer']
        elif user_tenant.role == 'admin':
            return ['member', 'viewer']
        else:
            return []
    
    def initialize_default_permissions(self):
        """初始化默认权限和角色"""
        # 定义默认权限
        default_permissions = [
            ('tasks.read', '查看任务'),
            ('tasks.create', '创建任务'),
            ('tasks.update', '更新任务'),
            ('tasks.delete', '删除任务'),
            ('tasks.execute', '执行任务'),
            ('metrics.read', '查看指标'),
            ('alerts.read', '查看告警'),
            ('alerts.manage', '管理告警'),
            ('config.read', '查看配置'),
            ('config.update', '更新配置'),
            ('users.read', '查看用户'),
            ('users.invite', '邀请用户'),
            ('users.manage', '管理用户'),
            ('tenant.read', '查看租户信息'),
            ('tenant.update', '更新租户信息'),
            ('tenant.delete', '删除租户'),
        ]
        
        # 创建权限
        for perm_name, perm_desc in default_permissions:
            existing_perm = self.db.query(Permission).filter(Permission.name == perm_name).first()
            if not existing_perm:
                permission = Permission(name=perm_name, description=perm_desc)
                self.db.add(permission)
        
        self.db.commit()
        
        # 定义默认角色及其权限
        default_roles = {
            'owner': {
                'description': '租户所有者，拥有所有权限',
                'permissions': [perm[0] for perm in default_permissions]
            },
            'admin': {
                'description': '管理员，拥有大部分管理权限',
                'permissions': [
                    'tasks.read', 'tasks.create', 'tasks.update', 'tasks.delete', 'tasks.execute',
                    'metrics.read', 'alerts.read', 'alerts.manage',
                    'config.read', 'config.update',
                    'users.read', 'users.invite', 'users.manage',
                    'tenant.read'
                ]
            },
            'member': {
                'description': '普通成员，可以管理任务和查看数据',
                'permissions': [
                    'tasks.read', 'tasks.create', 'tasks.update', 'tasks.execute',
                    'metrics.read', 'alerts.read',
                    'config.read'
                ]
            },
            'viewer': {
                'description': '只读用户，只能查看数据',
                'permissions': [
                    'tasks.read', 'metrics.read', 'alerts.read', 'config.read'
                ]
            }
        }
        
        # 创建角色
        for role_name, role_data in default_roles.items():
            existing_role = self.db.query(Role).filter(Role.name == role_name).first()
            if not existing_role:
                role = Role(name=role_name, description=role_data['description'])
                self.db.add(role)
                self.db.flush()
                
                # 添加权限
                for perm_name in role_data['permissions']:
                    permission = self.db.query(Permission).filter(Permission.name == perm_name).first()
                    if permission:
                        role.permissions.append(permission)
        
        self.db.commit()
