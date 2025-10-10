from typing import Any
import asyncio
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from fastapi import APIRouter, Response, HTTPException

from ..config import settings
from ..metrics import prometheus_body


async def is_database_online() -> bool:
    """Check DB connectivity with a lightweight SELECT executed in a threadpool."""

    async def _run_with_timeout() -> bool:
        loop = asyncio.get_running_loop()

        def _check_sync() -> bool:
            # Local import to avoid circular dependencies at import time
            from ..deps import db_session
from sqlalchemy.orm import Session

            db: Session = Depends(db_session)  # injected
            try:
                db.execute(text("SELECT 1"))
                return True
            except SQLAlchemyError:
                return False
            finally:
                db.close()

        return await loop.run_in_executor(None, _check_sync)  # type: ignore[arg-type]

    try:
        return await asyncio.wait_for(_run_with_timeout(), timeout=10)
    except asyncio.TimeoutError:
        return False


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    """Simple health endpoint used by Docker healthcheck."""
    ok = await is_database_online()
    if ok:
        return {"status": "ok"}
    raise HTTPException(status_code=503, detail="Database unreachable")


@router.get("/version")
def version() -> dict[str, Any]:
    return {"app": "dsl-hub", "version": settings.APP_VERSION}


@router.get("/metrics")
def metrics() -> Response:
    body, ctype = prometheus_body()
    return Response(content=body, media_type=ctype)
