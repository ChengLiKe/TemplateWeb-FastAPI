# app/events/shutdown.py
from fastapi import FastAPI

from app.utils import logger


async def shutdown(app: FastAPI):
    logger.info("应用已关闭.")
