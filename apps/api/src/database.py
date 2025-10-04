from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import make_url
import re

from .config import settings

url = make_url(settings.dsn)
schema = None
if "schema" in url.query:
    q = dict(url.query)
    schema = q.pop("schema")
    url = url.set(query=q)

engine = create_engine(url, pool_pre_ping=True, future=True)

if schema:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", schema):
        raise ValueError(f"Invalid schema name in DATABASE_URL: {schema!r}")

    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_connection, connection_record):
        with dbapi_connection.cursor() as cur:
            cur.execute(f"SET search_path TO {schema}")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()
