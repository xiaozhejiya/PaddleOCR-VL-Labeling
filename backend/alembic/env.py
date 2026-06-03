from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.core.config import get_settings, is_missing_or_placeholder
from app.db.base import Base
import app.db.models.core  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_database_url(*, require_migrator: bool) -> str:
    settings = get_settings()
    if not is_missing_or_placeholder(settings.migrator_database_url):
        return settings.migrator_database_url
    if require_migrator:
        raise RuntimeError("MIGRATOR_DATABASE_URL is required for online Alembic.")
    if not is_missing_or_placeholder(settings.database_url):
        return settings.database_url
    raise RuntimeError(
        "MIGRATOR_DATABASE_URL or DATABASE_URL is not configured for Alembic.",
    )


def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(require_migrator=False),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    external_connection = config.attributes.get("connection")
    if external_connection is not None:
        context.configure(
            connection=external_connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    connectable = create_engine(
        get_database_url(require_migrator=True),
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
