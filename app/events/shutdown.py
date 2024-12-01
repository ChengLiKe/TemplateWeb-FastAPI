# app/events/shutdown.py
from .logger_config import setup_logger

logger = setup_logger(__name__)


async def shutdown():
    logger.info("应用已关闭.")
