# app/events/startup.py
from fastapi import FastAPI

from app.utils import get_logger, kv
import logging
import platform
import fastapi


async def startup(app: FastAPI):
    # Unified style: tag + symbol + key=value pairs
    app_logger = get_logger("APP")
    level_name = logging.getLevelName(logging.getLogger("app").getEffectiveLevel())
    log_files = [h.baseFilename for h in logging.getLogger("app").handlers if hasattr(h, "baseFilename")]

    app_logger.info("▶ STARTUP " + kv(title=app.title, version=app.version,python=platform.python_version(), fastapi=fastapi.__version__))
    app_logger.info("Docs " + kv(openapi=app.openapi_url, swagger="/docs", redoc="/redoc"))
    app_logger.info("Logging " + kv(level=level_name, handlers=len(logging.getLogger("app").handlers),file=(log_files[0] if log_files else "N/A")))
    app_logger.info("Topology " + kv(routes=len(app.routes), middlewares=len(app.user_middleware)))
    app_logger.info("Application started.")
