# app/events/startup.py
from fastapi import FastAPI

from app.utils import logger


async def startup(app: FastAPI):
    logger.info("应用已启动.")
