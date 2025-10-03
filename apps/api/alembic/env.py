from __future__ import annotations

import os
import sys
from sqlalchemy import engine_from_config, pool, create_engine, event
from sqlalchemy.engine import make_url
from alembic import context

# Ensure `src` package is importable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from src.config import settings  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Override sqlalchemy.url from app settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# target_metadata is used for 'autogenerate' support.
target_metadata = None


def _engine_from_settings():
    url = make_url(settings.DATABASE_URL)
    schema = None
    if "schema" in url.query:
        q = dict(url.query)
        schema = q.pop("schema")
        url = url.set(query=q)

    eng = create_engine(url, pool_pre_ping=True, future=True)

    if schema:
        import re
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
            raise ValueError(f"Invalid schema name in DATABASE_URL: {schema!r}")

        @event.listens_for(eng, "connect")
        def set_search_path(dbapi_connection, connection_record):  # type: ignore[no-redef]
            with dbapi_connection.cursor() as cur:
                cur.execute(f"SET search_path TO {schema}")
    return eng


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
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
    """Run migrations in 'online' mode."""

    connectable = _engine_from_settings()

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
