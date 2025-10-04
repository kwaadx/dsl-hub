from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional, Tuple

from alembic import context
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.engine import make_url
from sqlalchemy.engine.base import Engine

# Load environment from project root .env files when running locally
# (docker-compose injects env for containers, but CLI runs may not)
try:  # optional dependency
    from dotenv import load_dotenv  # type: ignore

    # Attempt to load .env and .env.local from repo root
    here = Path(__file__).resolve()
    repo_root = here.parents[2]  # .../apps/api/alembic -> repo root
    load_dotenv(repo_root / ".env")
    load_dotenv(repo_root / ".env.local")
except Exception:
    pass

# ---- Alembic Config ----
config = context.config

# ---- Target metadata import (adjust to your project) ----
# Use the application's Base to support autogenerate.
try:
    from src.database import Base  # type: ignore

    target_metadata = Base.metadata
except Exception:
    target_metadata = None


# ---------------------------
# Helpers
# ---------------------------

def _env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Read environment variable with a default."""
    return os.environ.get(key, default)


def _assemble_dsn() -> str:
    """
    Build a SQLAlchemy DSN using the following precedence:
      1) SQLALCHEMY_DATABASE_URL or DATABASE_URL (if provided)
      2) DB_* variables (DB_USER, DB_PASSWORD, ...)
      3) POSTGRES_* variables (POSTGRES_USER, POSTGRES_PASSWORD, ...)
      4) Sensible defaults for local docker-compose

    Supported extras:
      - DB_SSLMODE (e.g. 'disable'|'require'|'verify-full')
      - DB_APPLICATION_NAME (default: 'alembic')
      - DB_SCHEMA (also supported via '?schema=...')
    """
    # 1) Direct URL from env
    direct_url = _env("SQLALCHEMY_DATABASE_URL") or _env("DATABASE_URL")
    if direct_url:
        return direct_url

    # 2) Prefer DB_* vars, with fallback to POSTGRES_*
    user = _env("DB_USER") or _env("POSTGRES_USER") or "postgres"
    password = _env("DB_PASSWORD") or _env("POSTGRES_PASSWORD") or "postgres"
    host = _env("DB_HOST") or _env("POSTGRES_HOST") or "db"
    port_str = _env("DB_PORT") or _env("POSTGRES_PORT") or "5432"
    try:
        port = int(port_str)
    except Exception:
        port = 5432
    name = _env("DB_NAME") or _env("POSTGRES_DB") or "dsl_hub"
    app_name = _env("DB_APPLICATION_NAME", "alembic")
    sslmode = _env("DB_SSLMODE")  # None if not set
    schema = _env("DB_SCHEMA")  # None if not set

    query = {}
    if app_name:
        query["application_name"] = app_name
    if sslmode:
        query["sslmode"] = sslmode
    if schema:
        # we pass schema via query and handle it below for search_path/version_table_schema
        query["schema"] = schema

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=name,
        query=query,
    )
    return str(url)


def _split_url_and_schema(db_url: str) -> Tuple[str, Optional[str]]:
    """
    Extract ?schema=... from the URL's query part.
    Return (url_without_schema, schema_or_None).
    """
    url = make_url(db_url)
    schema: Optional[str] = None
    if "schema" in url.query:
        q = dict(url.query)
        schema = q.pop("schema")
        url = url.set(query=q)
    return str(url), schema


def _validate_schema(schema: str) -> None:
    """Ensure schema is a valid SQL identifier (no SQL injection)."""
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise ValueError(f"Invalid schema name: {schema!r}")


def _mask_url_password(db_url: str) -> str:
    """
    Return a DSN string with password masked for safe logging.
    """
    try:
        url = make_url(db_url)
        if url.password:
            safe = url.set(password="****")
            return str(safe)
    except Exception:
        pass
    return db_url


def _engine_from_url(url_str: str) -> Tuple[Engine, Optional[str]]:
    """
    Create an Engine with pool_pre_ping and attach search_path setter
    if schema is provided in the URL (?schema=... or DB_SCHEMA).
    """
    url_str, schema = _split_url_and_schema(url_str)
    if schema:
        _validate_schema(schema)
    eng = create_engine(url_str, pool_pre_ping=True, future=True)

    if schema:
        @event.listens_for(eng, "connect")
        def set_search_path(dbapi_connection, _) -> None:  # type: ignore[override]
            with dbapi_connection.cursor() as cur:
                # search_path ensures migrations run against the target schema first
                cur.execute(f"SET search_path TO {schema}")
    return eng, schema


# ---------------------------
# Migration entry points
# ---------------------------

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    In this mode we set only the URL and emit SQL to the script output.
    """
    url_str = _assemble_dsn()
    url_str, schema = _split_url_and_schema(url_str)

    # Make URL visible to Alembic (without leaking the password)
    config.set_main_option("sqlalchemy.url", url_str)
    print(f"[alembic] offline URL: {_mask_url_password(url_str)}"
          f"{f' (schema={schema})' if schema else ''}")

    context.configure(
        url=url_str,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=schema if schema else None,
        include_schemas=True if schema else False,  # helpful if you generate across schemas
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    Here we create an Engine and associate a connection with the context.
    """
    url_str = _assemble_dsn()
    connectable, schema = _engine_from_url(url_str)

    # Make URL visible to Alembic (without leaking the password)
    config.set_main_option("sqlalchemy.url", _split_url_and_schema(url_str)[0])
    print(f"[alembic] online URL: {_mask_url_password(url_str)}"
          f"{f' (schema={schema})' if schema else ''}")

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema if schema else None,
            include_schemas=True if schema else False,
            # Uncomment if you want more verbose autogenerate diffs:
            # compare_type=True,
            # compare_server_default=True,
            # render_as_batch=False,
        )

        with context.begin_transaction():
            # Optionally ensure schema exists before running migrations.
            # This is safe if you rely on a single schema via DB_SCHEMA.
            if schema:
                connection.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}";')
            context.run_migrations()


# ---------------------------
# Dispatcher
# ---------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
