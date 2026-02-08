"""
Pytest fixtures for GEO Monitor backend tests.

Sets up an in-memory SQLite test database, overrides FastAPI dependencies,
and provides reusable fixtures for authenticated requests.
"""
import os
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import create_engine, event, text, String
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# ---------------------------------------------------------------------------
# Set environment variables BEFORE any app imports so Settings picks them up.
# The lru_cache on get_settings means the first import wins.
# ---------------------------------------------------------------------------
os.environ["ENVIRONMENT"] = "test"
# Use a file-based SQLite URL for the *app-level* engine that gets created at
# import time in database.py.  This avoids pool_size / StaticPool conflicts.
# Tests use a separate in-memory engine (test_engine) via dependency override.
os.environ["DATABASE_URL"] = "sqlite:///./test_geo_monitor.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"
os.environ["ALGORITHM"] = "HS256"
os.environ["DEBUG"] = "false"

# ---------------------------------------------------------------------------
# Register custom type compilers BEFORE importing app modules, so that
# PostgreSQL-specific types in user_entities.py can be rendered on SQLite.
# ---------------------------------------------------------------------------
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(INET, "sqlite")
def _compile_inet_sqlite(type_, compiler, **kw):
    """Render PostgreSQL INET as TEXT on SQLite."""
    return "TEXT"


# JSONB already falls back to JSON on non-PG, but ensure it compiles
@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):
    """Render PostgreSQL JSONB as TEXT on SQLite."""
    return "TEXT"


from fastapi.testclient import TestClient
from jose import jwt

from app.models.database import Base, get_db
from app.core.config import settings

# ---------------------------------------------------------------------------
# Test database engine (in-memory SQLite, shared via StaticPool)
# ---------------------------------------------------------------------------

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@event.listens_for(test_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key enforcement in SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---------------------------------------------------------------------------
# Table creation
# ---------------------------------------------------------------------------

def _create_all_tables():
    """
    Create all tables in the test database.

    Both model modules are imported so every table is registered with
    Base.metadata.  Custom type compilers (above) allow PostgreSQL-specific
    types to render on SQLite.
    """
    import app.models.entities  # noqa: F401
    import app.models.user_entities  # noqa: F401

    Base.metadata.create_all(bind=test_engine)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once for the entire test session."""
    _create_all_tables()
    yield
    test_engine.dispose()


@pytest.fixture()
def db():
    """
    Provide a database session for each test.

    After each test all rows are deleted to avoid cross-test contamination.
    """
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        _cleanup_tables(session)
        session.close()


def _cleanup_tables(session: Session):
    """Delete data from all tables in dependency order."""
    tables_ordered = [
        "email_verifications",
        "password_resets",
        "user_invitations",
        "user_sessions",
        "model_outputs",
        "metrics_snapshot",
        "task_runs",
        "task_models",
        "task_keywords",
        "monitor_tasks",
        "tenant_members",
        "user_tenants",
        "tenant_config",
        "tenant_configs",
        "users",
        "tenants",
        "alert_records",
        "roles",
        "permissions",
    ]
    for table in tables_ordered:
        try:
            session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            pass
    session.commit()


@pytest.fixture()
def client(db: Session):
    """
    FastAPI TestClient with ``get_db`` overridden to use the test session.

    The app's lifespan (init_db, init_redis, etc.) is patched out so it
    does not connect to a real database or Redis.
    """
    from app.main import app

    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    # Patch lifecycle functions called by the lifespan context manager
    with patch("app.main.init_db"), \
         patch("app.main.close_db"), \
         patch("app.main.init_redis"), \
         patch("app.main.close_redis"):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(db: Session):
    """
    Insert a User, Tenant, UserTenant, and TenantConfig into the test
    database via the ORM models, then return a dict with IDs, email,
    and the plain-text password.

    Using ORM model instances ensures UUID serialisation is consistent
    with what the application code expects.
    """
    import bcrypt as _bcrypt
    from app.models.user_entities import User, Tenant, UserTenant, UserTenantConfig
    from app.models.entities import TenantConfig

    plain_password = "TestPass123"
    password_hash = _bcrypt.hashpw(
        plain_password.encode("utf-8"), _bcrypt.gensalt()
    ).decode("utf-8")

    # --- Tenant (user_entities) ---
    tenant = Tenant(
        name="Test Tenant",
        slug="test-tenant",
        plan_type="free",
        status="active",
    )
    db.add(tenant)
    db.flush()

    # --- TenantConfig (entities.py, FK target for monitor_tasks) ---
    # Explicitly convert to string because the column is String(36), not UUID,
    # and SQLite's DBAPI cannot adapt uuid.UUID objects directly.
    tenant_config = TenantConfig(
        tenant_id=str(tenant.id),
    )
    db.add(tenant_config)
    db.flush()

    # --- UserTenantConfig (user_entities) ---
    user_tenant_config = UserTenantConfig(
        tenant_id=tenant.id,
    )
    db.add(user_tenant_config)
    db.flush()

    # --- User ---
    user = User(
        email="test@example.com",
        name="Test User",
        password_hash=password_hash,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()

    # --- UserTenant ---
    user_tenant = UserTenant(
        user_id=user.id,
        tenant_id=tenant.id,
        role="owner",
        is_primary=True,
    )
    db.add(user_tenant)

    db.commit()

    # Return string representations.  The JWT payload and response
    # assertions work with string IDs.
    return {
        "user_id": str(user.id),
        "tenant_id": str(tenant.id),
        "email": "test@example.com",
        "name": "Test User",
        "password": plain_password,
        "role": "owner",
    }


@pytest.fixture()
def auth_headers(test_user: dict) -> dict:
    """
    Return ``Authorization: Bearer <token>`` headers with a valid JWT
    for the test user.
    """
    payload = {
        "user_id": test_user["user_id"],
        "tenant_id": test_user["tenant_id"],
        "role": test_user["role"],
        "exp": datetime.utcnow() + timedelta(minutes=30),
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"Authorization": f"Bearer {token}"}
