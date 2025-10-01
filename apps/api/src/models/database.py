from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config.env import env

# Create base class for models
Base = declarative_base()

# Create SQLAlchemy engine lazily, only if DATABASE_URL is provided
_engine = None
_SessionLocal = None
if env.DATABASE_URL:
    _engine = create_engine(env.DATABASE_URL)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

# Dependency to get DB session
def get_db():
    if _SessionLocal is None:
        # Database not configured
        raise RuntimeError("DATABASE_URL is not configured. Set DATABASE_URL in the environment or .env file.")
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
