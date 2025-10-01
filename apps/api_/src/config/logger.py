from loguru import logger
import sys
from .env import env

# Configure logger with safe level handling
logger.remove()

# Normalize log level; map common aliases
_level = (env.LOG_LEVEL or "INFO").strip()
_alias_map = {
    "warn": "WARNING",
    "fatal": "CRITICAL",
}
_level_norm = _alias_map.get(_level.lower(), _level.upper())

try:
    logger.add(
        sys.stderr,
        level=_level_norm,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
except ValueError:
    # Fallback to INFO if provided level is invalid
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )

# Export logger
__all__ = ["logger"]
