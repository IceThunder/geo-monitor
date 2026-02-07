"""
认证服务模块
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import UUID
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user_entities import (
    User, Tenant, UserTenant, UserSession, 
    EmailVerification, PasswordReset, TenantConfig
)
from app.schemas.user_schemas import UserRegister, UserLogin, TokenData
from app.core.config import settings


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    def generate_token(self, user_id: UUID, tenant_id: UUID, role: str) -> Tuple[str, str]:
        """生成JWT token"""
        # Access token (30分钟)
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token_data = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "role": role,
            "exp": datetime.utcnow() + access_token_expires,
            "type": "access"
        }
        access_token = jwt.encode(access_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Refresh token (7天)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token_data = {
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "exp": datetime.utcnow() + refresh_token_expires,
            "type": "refresh"
        }
        refresh_token = jwt.encode(refresh_token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        return access_token, refresh_token
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """验证JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("user_id")
            tenant_id = payload.get("tenant_id")
            role = payload.get("role", "member")
            exp = payload.get("exp")
            
            if user_id is None or tenant_id is None:
                return None
                
            return TokenData(
                user_id=UUID(user_id),
                tenant_id=UUID(tenant_id),
                role=role,
                exp=datetime.fromtimestamp(exp)
            )
        except JWTError:
            return None
    
    def generate_verification_token(self) -> str:
        """生成验证token"""
        return secrets.token_urlsafe(32)
    
    def create_slug_from_name(self, name: str) -> str:
        """从名称生成slug"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # 确保slug唯一
        base_slug = slug
        counter = 1
        while self.db.query(Tenant).filter(Tenant.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def register_user(self, user_data: UserRegister) -> Tuple[User, Tenant]:
        """用户注册"""
        # 检查邮箱是否已存在
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        hashed_password = self.hash_password(user_data.password)
        user = User(
            email=user_data.email,
            name=user_data.name,
            password_hash=hashed_password,
            is_active=True,
            is_verified=False
        )
        self.db.add(user)
        self.db.flush()  # 获取用户ID
        
        # 创建租户
        tenant_name = user_data.tenant_name or f"{user_data.name}的团队"
        tenant_slug = self.create_slug_from_name(tenant_name)
        tenant = Tenant(
            name=tenant_name,
            slug=tenant_slug,
            plan_type='free',
            status='active'
        )
        self.db.add(tenant)
        self.db.flush()  # 获取租户ID
        
        # 创建用户租户关联（用户为所有者）
        user_tenant = UserTenant(
            user_id=user.id,
            tenant_id=tenant.id,
            role='owner',
            is_primary=True
        )
        self.db.add(user_tenant)
        
        # 创建租户配置
        tenant_config = TenantConfig(
            tenant_id=tenant.id,
            alert_threshold_accuracy=6,
            alert_threshold_sentiment=50
        )
        self.db.add(tenant_config)
        
        # 创建邮箱验证记录
        verification_token = self.generate_verification_token()
        email_verification = EmailVerification(
            user_id=user.id,
            token=verification_token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        self.db.add(email_verification)
        
        self.db.commit()

        # Send verification email
        from app.services.email_service import get_email_service
        email_service = get_email_service()
        import asyncio
        try:
            asyncio.create_task(
                email_service.send_verification_email(
                    user.email,
                    verification_token,
                    user.name
                )
            )
        except Exception as e:
            # Log but don't fail registration if email fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to send verification email: {e}")

        return user, tenant
    
    def login_user(self, login_data: UserLogin, user_agent: str = None, ip_address: str = None) -> Tuple[User, Tenant, str, str]:
        """用户登录"""
        # 验证用户凭据
        user = self.db.query(User).filter(
            and_(User.email == login_data.email, User.is_active == True)
        ).first()
        
        if not user or not self.verify_password(login_data.password, user.password_hash):
            raise ValueError("邮箱或密码错误")
        
        # 获取用户的主租户
        user_tenant = self.db.query(UserTenant).filter(
            and_(UserTenant.user_id == user.id, UserTenant.is_primary == True)
        ).first()
        
        if not user_tenant:
            raise ValueError("用户没有关联的租户")
        
        tenant = user_tenant.tenant
        
        # 生成token
        access_token, refresh_token = self.generate_token(user.id, tenant.id, user_tenant.role)
        
        # 创建会话记录
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = UserSession(
            user_id=user.id,
            tenant_id=tenant.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            user_agent=user_agent,
            ip_address=ip_address
        )
        self.db.add(session)
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        
        self.db.commit()
        
        return user, tenant, access_token, refresh_token
    
    def verify_email(self, token: str) -> User:
        """验证邮箱"""
        verification = self.db.query(EmailVerification).filter(
            and_(
                EmailVerification.token == token,
                EmailVerification.is_used == False,
                EmailVerification.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not verification:
            raise ValueError("验证链接无效或已过期")
        
        # 标记验证为已使用
        verification.is_used = True
        
        # 激活用户
        user = verification.user
        user.is_verified = True
        user.email_verified_at = datetime.utcnow()
        
        self.db.commit()
        
        return user
    
    def request_password_reset(self, email: str) -> str:
        """请求密码重置"""
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("用户不存在")
        
        # 生成重置token
        reset_token = self.generate_verification_token()
        password_reset = PasswordReset(
            user_id=user.id,
            token=reset_token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.db.add(password_reset)
        self.db.commit()

        # Send password reset email
        from app.services.email_service import get_email_service
        email_service = get_email_service()
        import asyncio
        try:
            asyncio.create_task(
                email_service.send_password_reset_email(
                    user.email,
                    reset_token,
                    user.name
                )
            )
        except Exception as e:
            # Log but don't fail if email fails
            import logging
            logging.getLogger(__name__).warning(f"Failed to send password reset email: {e}")

        return reset_token
    
    def reset_password(self, token: str, new_password: str) -> User:
        """重置密码"""
        reset = self.db.query(PasswordReset).filter(
            and_(
                PasswordReset.token == token,
                PasswordReset.is_used == False,
                PasswordReset.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not reset:
            raise ValueError("重置链接无效或已过期")
        
        # 标记重置为已使用
        reset.is_used = True
        
        # 更新密码
        user = reset.user
        user.password_hash = self.hash_password(new_password)
        
        # 清除所有会话
        self.db.query(UserSession).filter(UserSession.user_id == user.id).delete()
        
        self.db.commit()
        
        return user
    
    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """刷新token"""
        token_data = self.verify_token(refresh_token)
        if not token_data:
            raise ValueError("无效的刷新token")
        
        # 验证会话是否存在
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = self.db.query(UserSession).filter(
            and_(
                UserSession.token_hash == token_hash,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()
        
        if not session:
            raise ValueError("会话已过期")
        
        # 获取用户租户信息
        user_tenant = self.db.query(UserTenant).filter(
            and_(
                UserTenant.user_id == token_data.user_id,
                UserTenant.tenant_id == token_data.tenant_id
            )
        ).first()
        
        if not user_tenant:
            raise ValueError("用户租户关联不存在")
        
        # 生成新token
        new_access_token, new_refresh_token = self.generate_token(
            token_data.user_id, token_data.tenant_id, user_tenant.role
        )
        
        # 更新会话
        new_token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
        session.token_hash = new_token_hash
        session.expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        self.db.commit()
        
        return new_access_token, new_refresh_token
    
    def logout_user(self, refresh_token: str):
        """用户登出"""
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        session = self.db.query(UserSession).filter(UserSession.token_hash == token_hash).first()
        
        if session:
            self.db.delete(session)
            self.db.commit()
    
    def get_user_tenants(self, user_id: UUID) -> list:
        """获取用户的所有租户"""
        user_tenants = self.db.query(UserTenant).filter(UserTenant.user_id == user_id).all()
        return user_tenants
    
    def switch_tenant(self, user_id: UUID, tenant_id: UUID) -> Tuple[str, str]:
        """切换租户"""
        user_tenant = self.db.query(UserTenant).filter(
            and_(UserTenant.user_id == user_id, UserTenant.tenant_id == tenant_id)
        ).first()
        
        if not user_tenant:
            raise ValueError("用户不属于该租户")
        
        # 生成新token
        access_token, refresh_token = self.generate_token(user_id, tenant_id, user_tenant.role)
        
        return access_token, refresh_token
