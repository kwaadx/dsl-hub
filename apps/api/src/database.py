from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import settings

# --- Build URL & extract ?schema=... from DSN --------------------------------
url = make_url(settings.dsn)

schema: Optional[str] = None
if url.query and "schema" in dict(url.query):
    q = dict(url.query)
    schema = q.pop("schema") or None
    url = url.set(query=q)

# --- Declarative Base is always importable (needed by Alembic) ----------------
Base = declarative_base()

# --- Create engine / SessionLocal only when NOT running Alembic ---------------
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker[Session]] = None

if not os.getenv("ALEMBIC"):
    # NOTE: str(url) to pass a DBAPI-compatible URL to create_engine
    engine = create_engine(
        str(url),
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        future=True,
    )
    SessionLocal = sessionmaker(
        bind=engine,
        class_=Session,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    # Set search_path if ?schema=... was provided
    if schema:
        @event.listens_for(engine, "connect")
        def _set_search_path(dbapi_connection, connection_record) -> None:
            with dbapi_connection.cursor() as cur:
                # include public for safety, so extensions remain visible
                cur.execute(f"SET search_path TO {schema}, public")

# --- DB session provider (only valid in app/runtime, not in Alembic) ----------
@contextmanager
def get_db() -> Iterator[Session]:
    """
    Yields a SQLAlchemy Session bound to the app engine.
    NOT intended for Alembic (engine/SessionLocal are not created under ALEMBIC=1).
    """
    if SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized (likely running under Alembic).")
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
