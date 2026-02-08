"""
Alembic environment configuration for GEO Monitor.

This module configures Alembic to use the application's database URL
and SQLAlchemy metadata for autogenerate support.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import application settings and models
# ---------------------------------------------------------------------------

# Import settings to get the database URL
from app.core.config import settings

# Import Base which holds the metadata
from app.models.database import Base

# Import ALL model modules so their tables are registered on Base.metadata.
# Without these imports, autogenerate will not detect any tables.
import app.models.entities        # noqa: F401  — MonitorTask, TaskRun, MetricsSnapshot, etc.
import app.models.user_entities   # noqa: F401  — User, Tenant, UserTenant, Session, etc.

# target_metadata is used by autogenerate to compare the database state
# against the models defined in code.
target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from application settings
# ---------------------------------------------------------------------------

# Set the database URL from the application config so we don't have to
# duplicate it in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.get_database_url())


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
