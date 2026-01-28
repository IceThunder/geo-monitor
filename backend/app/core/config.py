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
    
    # Database
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    
    # Connection Pool
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    
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
        """Get database URL from environment or construct from SUPABASE_URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        if self.SUPABASE_URL and self.SUPABASE_DB_PASSWORD:
            # Supabase URL format: https://project-id.supabase.co
            # Extract project ID and construct DB connection with db. prefix
            from urllib.parse import urlparse
            
            parsed = urlparse(self.SUPABASE_URL)
            hostname = parsed.hostname  # e.g., "mqmzimtckgollewnvlli.supabase.co"
            
            if hostname:
                # Remove .supabase.co to get project ID
                project_id = hostname.replace('.supabase.co', '')
                # Supabase DB host uses db. prefix
                db_host = f"db.{project_id}.supabase.co"
                return f"postgresql://postgres:{self.SUPABASE_DB_PASSWORD}@{db_host}:5432/postgres"
        
        return ""
    
    def get_pool_config(self) -> dict:
        """Get connection pool configuration."""
        return {
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
