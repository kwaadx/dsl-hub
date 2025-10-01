from fastapi import APIRouter
from sqlalchemy.orm import Session
from ..models.database import get_db

router = APIRouter()

@router.get("/")
async def health_check():
    """
    Health check endpoint.
    """
    # Check database connection if configured
    try:
        for db in get_db():
            db.execute("SELECT 1")
            db_status = "up"
            break
        else:
            db_status = "down"
    except Exception:
        db_status = "down"

    return {
        "status": "ok",
        "database": db_status
    }
