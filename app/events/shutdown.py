# app/events/shutdown.py
from fastapi import FastAPI

from app.utils import get_logger, kv
from app.services.db import close_db
from app.services.cache import close_cache
from app.utils.telemetry import shutdown_tracing


async def shutdown(app: FastAPI):
    app_logger = get_logger("APP")
    await close_db(app)
    await close_cache(app)
    await shutdown_tracing(app)
    app_logger.info("Application shutdown.")
