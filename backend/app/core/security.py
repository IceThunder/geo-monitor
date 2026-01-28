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
from app.models.entities import TenantConfig
from app.models.schemas import TokenResponse

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


def get_current_tenant_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> str:
    """Get current tenant ID from JWT token.
    
    In development mode, returns a default tenant ID without authentication.
    """
    # Development mode: skip authentication
    if credentials is None:
        return "00000000-0000-0000-0000-000000000001"
    
    token = credentials.credentials
    payload = decode_token(token)
    
    tenant_id: str = payload.get("sub")
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    return tenant_id


def get_current_tenant(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: Session = Depends(get_db)
) -> dict:
    """Get current tenant from JWT token.
    
    In development mode, returns a default tenant without authentication.
    """
    # Development mode: skip authentication
    if credentials is None:
        return {
            "id": str(uuid.uuid4()),
            "tenant_id": "00000000-0000-0000-0000-000000000001",
            "openrouter_api_key_encrypted": None,
            "webhook_url": None,
            "alert_threshold_accuracy": 6,
            "alert_threshold_sentiment": 0.5,
        }
    
    token = credentials.credentials
    payload = decode_token(token)
    
    tenant_id: str = payload.get("sub")
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return tenant


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
