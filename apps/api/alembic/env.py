from __future__ import annotations

import os
import re
import sys
from typing import Optional, Tuple

from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from alembic import context

# Ensure `src` package is importable
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from src.config import settings  # noqa: E402

# Alembic Config object gives access to .ini values.
config = context.config

# Override sqlalchemy.url from app settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# target_metadata is used for 'autogenerate' support (not used; SQL-first migrations)
target_metadata = None


def _split_url_and_schema(db_url: str) -> tuple[str, Optional[str]]:
    """Return database URL string without ?schema=... and the schema value (if any)."""
    url = make_url(db_url)
    schema: Optional[str] = None
    if "schema" in url.query:
        q = dict(url.query)
        schema = q.pop("schema")
        url = url.set(query=q)
    return str(url), schema


def _validate_schema(schema: str) -> None:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise ValueError(f"Invalid schema name in DATABASE_URL: {schema!r}")


def _engine_from_settings():
    url_str, schema = _split_url_and_schema(settings.DATABASE_URL)
    eng = create_engine(url_str, pool_pre_ping=True, future=True)

    if schema:
        _validate_schema(schema)

        @event.listens_for(eng, "connect")
        def set_search_path(dbapi_connection, connection_record):  # type: ignore[no-redef]
            with dbapi_connection.cursor() as cur:
                cur.execute(f"SET search_path TO {schema}")

    return eng, schema


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine;
    by skipping Engine creation we don't need a DBAPI available.
    """
    url_str, schema = _split_url_and_schema(settings.DATABASE_URL)
    context.configure(
        url=url_str,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=schema if schema else None,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable, schema = _engine_from_settings()

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema if schema else None,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
