import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

# --- ensure we can import "src" ------------------------------------------------
# env.py lives in: /app/api/alembic/env.py
# src is at:       /app/api/src
ALEMBIC_DIR = os.path.dirname(__file__)
API_DIR = os.path.abspath(os.path.join(ALEMBIC_DIR, ".."))          # /app/api
SRC_DIR = os.path.abspath(os.path.join(API_DIR, "src"))             # /app/api/src
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# mark alembic mode so app's database.py won't create engine on import
os.environ.setdefault("ALEMBIC", "1")

# now it's safe to import your models
from src.models import Base  # noqa: E402

# Alembic Config object
config = context.config

# logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# database url from env or alembic.ini
DB_URL = os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url") or ""
DB_SCHEMA = os.getenv("DB_SCHEMA", "dsl_hub")

def run_migrations_offline() -> None:
    if not DB_URL:
        raise RuntimeError("DATABASE_URL is not set for offline migrations.")
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        compare_type=True,
        version_table_schema=DB_SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    if not DB_URL:
        raise RuntimeError("DATABASE_URL is not set for online migrations.")
    engine = create_engine(DB_URL, poolclass=pool.NullPool, future=True)

    # set search_path on connect
    from sqlalchemy import event
    def _set_search_path(dbapi_connection, _):
        try:
            with dbapi_connection.cursor() as cur:
                cur.execute(f"SET search_path TO {DB_SCHEMA}, public")
        except Exception:
            pass
    event.listen(engine, "connect", _set_search_path)

    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            compare_type=True,
            version_table_schema=DB_SCHEMA,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()