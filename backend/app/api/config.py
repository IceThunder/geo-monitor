"""
Tenant configuration API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import base64

from app.models.database import get_db
from app.models.entities import TenantConfig
from app.models.schemas import (
    TenantConfigResponse,
    TenantConfigUpdate,
)
from app.core.security import get_current_tenant_id
from app.core.config import settings

router = APIRouter(prefix="/config", tags=["Configuration"])


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
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the current tenant's configuration."""
    result = await db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        # Create default config
        config = TenantConfig(
            tenant_id=tenant_id,
        )
        db.add(config)
        await db.commit()
        await db.refresh(config)
    
    return TenantConfigResponse(
        openrouter_api_key_set=config.openrouter_api_key_encrypted is not None,
        webhook_url=config.webhook_url,
        alert_threshold_accuracy=config.alert_threshold_accuracy,
        alert_threshold_sentiment=float(config.alert_threshold_sentiment) if config.alert_threshold_sentiment else 0.5,
    )


@router.put("", response_model=TenantConfigResponse)
async def update_tenant_config(
    config_update: TenantConfigUpdate,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Update the current tenant's configuration."""
    result = await db.execute(
        select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        # Create new config
        config = TenantConfig(tenant_id=tenant_id)
        db.add(config)
        await db.flush()
    
    # Update fields
    if config_update.openrouter_api_key is not None:
        config.openrouter_api_key_encrypted = encode_api_key(config_update.openrouter_api_key)
    
    if config_update.webhook_url is not None:
        config.webhook_url = config_update.webhook_url
    
    if config_update.alert_threshold_accuracy is not None:
        config.alert_threshold_accuracy = config_update.alert_threshold_accuracy
    
    if config_update.alert_threshold_sentiment is not None:
        config.alert_threshold_sentiment = config_update.alert_threshold_sentiment
    
    await db.commit()
    await db.refresh(config)
    
    return TenantConfigResponse(
        openrouter_api_key_set=config.openrouter_api_key_encrypted is not None,
        webhook_url=config.webhook_url,
        alert_threshold_accuracy=config.alert_threshold_accuracy,
        alert_threshold_sentiment=float(config.alert_threshold_sentiment) if config.alert_threshold_sentiment else 0.5,
    )


@router.get("/openrouter-key")
async def get_openrouter_key(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the decoded OpenRouter API key (for internal use only)."""
    result = await db.execute(
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
