# app/events/startup.py
from app import logger


async def startup():
    logger.info("应用已启动.")
