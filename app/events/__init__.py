# fastapi-app/events/__init__.py

"""
1. 事件相关功能的包初始化模块
- Event-related function package initialization module.
2. 该模块包含与事件处理相关的，因此在应用启动和关闭时会被调用。
- This module contains event handling related to it, so it will be called when the application starts and shuts down.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

# 导入事件处理程序模块
from .startup import startup
from .shutdown import shutdown

# 包元数据
__version__ = "1.0.0"
__author__ = "like"

__all__ = [
    "events",
    "startup",
    "shutdown",
]


@asynccontextmanager
async def events(app: FastAPI):
    await startup(app)  # 在应用启动时执行
    yield
    await shutdown(app)  # 在应用关闭时执行
