"""
Configuration management using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Database (all optional, derived from SUPABASE_URL if not set)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # Redis
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
    
    # OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    
    # JWT
    SECRET_KEY: str = "default-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 20
    RATE_LIMIT_MAX_RETRIES: int = 3
    RATE_LIMIT_BASE_DELAY: float = 1.0
    
    # Token & Cost Limits
    MAX_TOKEN_PER_REQUEST: int = 4000
    MAX_COST_PER_REQUEST: float = 1.00
    
    # Webhook
    WEBHOOK_ENABLED: bool = True
    ALERT_EMAIL_ENABLED: bool = False
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    def get_database_url(self) -> str:
        """Get database URL, deriving from SUPABASE_URL if not set."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.SUPABASE_URL:
            # Convert Supabase URL to postgres connection string
            host = self.SUPABASE_URL.replace("https://", "").replace("http://", "")
            return f"postgresql://postgres:password@{host}:5432/postgres"
        return ""


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
