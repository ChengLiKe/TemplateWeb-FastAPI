# app/events/startup.py
from .logger_config import setup_logger

logger = setup_logger(__name__)
async def startup():
    logger.info("应用已启动.")