"""
JWT Authentication and security utilities.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid

from app.core.config import settings
from app.models.database import get_db
from app.models.entities import TenantConfig, TenantMember
from app.models.user_entities import User
from app.models.schemas import TokenResponse, UserResponse

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Standard JWT Bearer scheme (for production)
security = HTTPBearer()


class OptionalBearer:
    """Custom security scheme that skips authentication in development mode."""
    
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        """Return credentials if present, None if in development mode."""
        # Development mode: skip authentication
        if settings.ENVIRONMENT == "development":
            return None
        
        # Production mode: require authentication
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authenticated",
            )
        
        return HTTPBearer()(request)


# Optional bearer that skips in development
optional_security = OptionalBearer()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token.
    
    In development mode, returns a default user without authentication.
    """
    # Development mode: skip authentication
    if credentials is None:
        # Return a mock user for development
        return User(
            id=uuid.uuid4(),
            email="dev@example.com",
            name="Development User",
            is_active=True,
            is_verified=True
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Query user from database
    result = db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_tenant_id(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> str:
    """Get current tenant ID for the user.
    
    In development mode, returns a default tenant ID.
    """
    # Development mode: return default tenant
    if settings.ENVIRONMENT == "development":
        return "00000000-0000-0000-0000-000000000001"
    
    # Get user's primary tenant (first active membership)
    result = db.execute(
        select(TenantMember)
        .where(
            TenantMember.user_id == user.id,
            TenantMember.is_active == True
        )
        .order_by(TenantMember.joined_at.desc())
        .limit(1)
    )
    membership = result.scalar_one_or_none()
    
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active tenant membership",
        )
    
    return str(membership.tenant_id)


def get_current_tenant(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
) -> TenantConfig:
    """Get current tenant configuration.
    
    In development mode, returns a default tenant configuration.
    """
    # Development mode: return mock tenant
    if settings.ENVIRONMENT == "development":
        return TenantConfig(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            openrouter_api_key_encrypted=None,
            webhook_url=None,
            alert_threshold_accuracy=6,
            alert_threshold_sentiment=0.5,
        )
    
    # Query tenant config
    result = db.execute(
        select(TenantConfig).where(
            TenantConfig.tenant_id == tenant_id
        )
    )
    tenant = result.scalar_one_or_none()
    
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant configuration not found",
        )
    
    return tenant


def get_current_user_membership(
    user: User = Depends(get_current_user),
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
) -> TenantMember:
    """Get current user's tenant membership."""
    # Development mode: return mock membership
    if settings.ENVIRONMENT == "development":
        return TenantMember(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(tenant_id),
            user_id=user.id,
            role="owner",
            permissions={"read": True, "write": True, "admin": True},
            is_active=True
        )
    
    result = db.execute(
        select(TenantMember).where(
            TenantMember.user_id == user.id,
            TenantMember.tenant_id == tenant_id,
            TenantMember.is_active == True
        )
    )
    membership = result.scalar_one_or_none()
    
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this tenant",
        )
    
    return membership


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_user_token(user: User, tenant_id: Optional[str] = None) -> TokenResponse:
    """Create access token for user."""
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "name": user.name,
    }
    
    if tenant_id:
        token_data["tenant_id"] = tenant_id
    
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================================================
# Permission Management
# ============================================================================

class Permission:
    """Permission constants."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    MANAGE_BILLING = "manage_billing"


class Role:
    """Role constants with default permissions."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"
    
    @classmethod
    def get_default_permissions(cls, role: str) -> dict:
        """Get default permissions for a role."""
        permissions_map = {
            cls.OWNER: {
                Permission.READ: True,
                Permission.WRITE: True,
                Permission.DELETE: True,
                Permission.ADMIN: True,
                Permission.MANAGE_USERS: True,
                Permission.MANAGE_BILLING: True,
            },
            cls.ADMIN: {
                Permission.READ: True,
                Permission.WRITE: True,
                Permission.DELETE: True,
                Permission.ADMIN: True,
                Permission.MANAGE_USERS: True,
                Permission.MANAGE_BILLING: False,
            },
            cls.MEMBER: {
                Permission.READ: True,
                Permission.WRITE: True,
                Permission.DELETE: False,
                Permission.ADMIN: False,
                Permission.MANAGE_USERS: False,
                Permission.MANAGE_BILLING: False,
            },
            cls.VIEWER: {
                Permission.READ: True,
                Permission.WRITE: False,
                Permission.DELETE: False,
                Permission.ADMIN: False,
                Permission.MANAGE_USERS: False,
                Permission.MANAGE_BILLING: False,
            },
        }
        return permissions_map.get(role, {})


def check_permission(membership: TenantMember, permission: str) -> bool:
    """Check if user has specific permission."""
    # Get role-based permissions
    role_permissions = Role.get_default_permissions(membership.role)
    
    # Merge with custom permissions
    user_permissions = {**role_permissions, **membership.permissions}
    
    return user_permissions.get(permission, False)


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get membership from dependency injection
            membership = kwargs.get('current_membership')
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed: no membership context"
                )
            
            if not check_permission(membership, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {permission} required"
                )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_permissions(*permissions: str):
    """Decorator to require multiple permissions (AND logic)."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            membership = kwargs.get('current_membership')
            if not membership:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Permission check failed: no membership context"
                )
            
            for permission in permissions:
                if not check_permission(membership, permission):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Insufficient permissions: {permission} required"
                    )
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Supabase Integration
# ============================================================================

def verify_supabase_jwt(token: str) -> dict:
    """Verify Supabase JWT token."""
    try:
        # In production, you would verify against Supabase's public key
        # For now, we'll use our own verification
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,  # In production, use Supabase JWT secret
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Supabase token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def sync_supabase_user(supabase_user_data: dict, db: Session) -> User:
    """Sync user from Supabase to local database."""
    supabase_user_id = supabase_user_data.get("sub")
    email = supabase_user_data.get("email")
    name = supabase_user_data.get("user_metadata", {}).get("full_name")
    
    if not supabase_user_id or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Supabase user data"
        )
    
    # Check if user exists
    result = db.execute(
        select(User).where(
            (User.supabase_user_id == supabase_user_id) |
            (User.email == email)
        )
    )
    user = result.scalar_one_or_none()
    
    if user:
        # Update existing user
        user.supabase_user_id = supabase_user_id
        user.email = email
        user.name = name or user.name
        user.is_verified = True
        user.updated_at = datetime.utcnow()
    else:
        # Create new user
        user = User(
            email=email,
            name=name,
            supabase_user_id=supabase_user_id,
            is_active=True,
            is_verified=True
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    return user
