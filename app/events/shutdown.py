# app/events/shutdown.py
from app.utils import logger


async def shutdown():
    logger.info("应用已关闭.")
