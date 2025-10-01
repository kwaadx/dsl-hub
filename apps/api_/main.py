# Entry point module for running the FastAPI app as `main:app`
# This bridges the internal package structure (src.main) with the runtime command used by docker/uvicorn.
from src.main import app  # re-export

__all__ = ["app"]
