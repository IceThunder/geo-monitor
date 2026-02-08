"""
受保护的租户配置API路由（使用JWT认证）
"""
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
import base64

from app.core.database import get_db
from app.models.entities import TenantConfig
from app.models.schemas import (
    TenantConfigResponse,
    TenantConfigUpdate,
)
from app.middleware.auth import get_current_user, require_minimum_role
from app.models.user_entities import User, UserTenant
from app.core.config import settings

router = APIRouter(tags=["Configuration"])


# Simple encoding (not encryption - for development only)
# In production, use proper encryption or external secrets management
def encode_api_key(api_key: str) -> str:
    """Encode an API key (simple base64, not secure for production)."""
    return base64.b64encode(api_key.encode()).decode()


def decode_api_key(encoded_key: str) -> str:
    """Decode an API key."""
    return base64.b64decode(encoded_key.encode()).decode()


@router.get("", response_model=TenantConfigResponse)
async def get_tenant_config(
    current_user_data: Tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current tenant's configuration."""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    result = db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Create default config
        config = TenantConfig(
            tenant_id=tenant_id,
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return TenantConfigResponse(
        openrouter_api_key_set=config.openrouter_api_key_encrypted is not None,
        webhook_url=config.webhook_url,
        alert_threshold_accuracy=config.alert_threshold_accuracy,
        alert_threshold_sentiment=float(config.alert_threshold_sentiment) if config.alert_threshold_sentiment else 0.5,
    )


@router.put("", response_model=TenantConfigResponse)
async def update_tenant_config(
    config_update: TenantConfigUpdate,
    current_user_data: Tuple[User, UserTenant] = Depends(require_minimum_role("admin")),
    db: Session = Depends(get_db),
):
    """Update the current tenant's configuration. Requires admin role or higher."""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    result = db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Create new config
        config = TenantConfig(tenant_id=tenant_id)
        db.add(config)
        db.flush()

    # Update fields
    if config_update.openrouter_api_key is not None:
        config.openrouter_api_key_encrypted = encode_api_key(config_update.openrouter_api_key)

    if config_update.webhook_url is not None:
        config.webhook_url = config_update.webhook_url

    if config_update.alert_threshold_accuracy is not None:
        config.alert_threshold_accuracy = config_update.alert_threshold_accuracy

    if config_update.alert_threshold_sentiment is not None:
        config.alert_threshold_sentiment = config_update.alert_threshold_sentiment

    db.commit()
    db.refresh(config)

    return TenantConfigResponse(
        openrouter_api_key_set=config.openrouter_api_key_encrypted is not None,
        webhook_url=config.webhook_url,
        alert_threshold_accuracy=config.alert_threshold_accuracy,
        alert_threshold_sentiment=float(config.alert_threshold_sentiment) if config.alert_threshold_sentiment else 0.5,
    )


@router.get("/openrouter-key")
async def get_openrouter_key(
    current_user_data: Tuple[User, UserTenant] = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the decoded OpenRouter API key (for internal use only)."""
    user, user_tenant = current_user_data
    tenant_id = str(user_tenant.tenant_id)

    result = db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    config = result.scalar_one_or_none()

    if not config or not config.openrouter_api_key_encrypted:
        # Return system default key if tenant doesn't have one
        return {"api_key": settings.OPENROUTER_API_KEY}

    try:
        api_key = decode_api_key(config.openrouter_api_key_encrypted)
        return {"api_key": api_key}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decode API key",
        )
