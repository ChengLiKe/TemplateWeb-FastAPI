# app/events/startup.py
from app.utils import logger


async def startup():
    logger.info("应用已启动.")
