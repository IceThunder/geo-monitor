"""
Database connection and session management.
"""
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Get pool configuration
pool_config = settings.get_pool_config()

# Create sync engine with connection pool settings optimized for Supabase pgbouncer
engine = create_engine(
    settings.get_database_url(),
    echo=settings.DEBUG,
    **pool_config,
)

# Create async engine for worker
def get_async_database_url() -> str:
    """Convert database URL to async format."""
    db_url = settings.get_database_url()
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://")
    elif db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "sqlite+aiosqlite://")
    return db_url

async_engine = create_async_engine(
    get_async_database_url(),
    echo=settings.DEBUG,
    **pool_config,
)

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
async_session_factory = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


async def init_async_db():
    """Initialize database tables asynchronously."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def close_db():
    """Close database connections."""
    engine.dispose()


async def close_async_db():
    """Close async database connections."""
    await async_engine.dispose()


# Set session variables based on database type
@event.listens_for(engine, "connect")
def set_session_variables(dbapi_connection, connection_record):
    """Set session variables based on database type."""
    if settings.get_database_url().startswith("postgresql"):
        # PostgreSQL/Supabase specific settings
        cursor = dbapi_connection.cursor()
        cursor.execute("SET statement_timeout = '30s'")
        cursor.close()
    # SQLite doesn't need special session variables
