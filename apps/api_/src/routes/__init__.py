from fastapi import APIRouter
from .flow_routes import router as flow_router
from .thread_routes import router as thread_router
from .pipeline_routes import router as pipeline_router
from .schema_routes import router as schema_router
from .schema_channel_routes import router as schema_channel_router
from .summary_routes import router as summary_router
from .log_routes import router as log_router

router = APIRouter()

router.include_router(flow_router, prefix="/flows", tags=["flows"])
router.include_router(thread_router, prefix="/threads", tags=["threads"])
router.include_router(pipeline_router, prefix="/pipelines", tags=["pipelines"])
router.include_router(schema_router, prefix="/schemas", tags=["schemas"])
router.include_router(schema_channel_router, prefix="/schema-channels", tags=["schemas"])
router.include_router(summary_router, prefix="/summaries", tags=["summaries"])
router.include_router(log_router, prefix="/logs", tags=["logs"])
