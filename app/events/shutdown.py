# app/events/shutdown.py
from app import logger


async def shutdown():
    logger.info("应用已关闭.")
