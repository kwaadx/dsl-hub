import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from alembic import context

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DB_SCHEMA = os.getenv("API_DB_SCHEMA", "api")


def get_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    user = os.getenv("DB_USER", "postgres")
    pwd = os.getenv("DB_PASSWORD", "postgres")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "dsl_hub")
    return f"postgresql+psycopg://{user}:{pwd}@{host}:{port}/{name}"


config = context.config
config.set_main_option("sqlalchemy.url", str(get_url()))
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from src.infrastructure.db.base import Base  # noqa: F401
from src.infrastructure.db import models as _models  # noqa: F401

target_metadata = Base.metadata


def _ensure_schema_and_extensions(connection, schema: str = DB_SCHEMA) -> None:
    connection.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == "table" and name in {"flow_active_pipeline", "job_run_all"}:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        include_schemas=True,
        include_object=include_object,
        version_table_schema=DB_SCHEMA,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url(), poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        # _ensure_schema_and_extensions(connection, DB_SCHEMA)
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            include_object=include_object,
            version_table_schema=DB_SCHEMA,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
