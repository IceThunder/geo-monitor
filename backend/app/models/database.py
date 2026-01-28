"""
Database connection and session management.
"""
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, DeclarativeBase
from app.core.config import settings

# Get pool configuration
pool_config = settings.get_pool_config()

# Create sync engine with connection pool settings optimized for Supabase pgbouncer
engine = create_engine(
    settings.get_database_url(),
    echo=settings.DEBUG,
    **pool_config,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)


def close_db():
    """Close database connections."""
    engine.dispose()


# Set statement timeout for pgbouncer compatibility
@event.listens_for(engine, "connect")
def set_session_variables(dbapi_connection, connection_record):
    """Set session variables for better pgbouncer compatibility."""
    cursor = dbapi_connection.cursor()
    # Set statement timeout to prevent long-running queries
    cursor.execute("SET statement_timeout = '30s'")
    cursor.close()
