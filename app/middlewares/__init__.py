# fastapi-app/events/__init__.py

"""
1. 中间件相关功能的包初始化模块
- Middleware-related function package initialization module.
2. 该模块包含与事件处理相关的，因此在应用启动和关闭时会被调用。
- This module contains event handling related to it, so it will be called when the application starts and shuts down.
"""

# 导入事件处理程序模块
from .auth import AuthMiddleware
import asyncio
import time
from fastapi import Request, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from fastapi import FastAPI
from app.utils import logger

# 包元数据
__version__ = "1.0.0"
__author__ = "like"

__all__ = [
    "middlewares",
    "AuthMiddleware",
]


def middlewares(app: FastAPI):
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许访问的源
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # 自定义中间件以添加安全头部
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    @app.middleware("http")
    async def ensure_event_loop_middleware(request: Request, call_next):
        # 中间件一：检查事件循环
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        response = await call_next(request)
        return response

    @app.middleware("http")
    async def catch_exceptions_middleware(request: Request, call_next):
        # 中间件二：异常处理
        try:
            response = await call_next(request)
        except Exception as e:
            return JSONResponse(content={"detail": str(e)}, status_code=500)
        return response

    @app.middleware("http")
    async def log_requests_middleware(request: Request, call_next):
        # 中间件三：日志记录
        start_time = time.time()  # 请求到达时计时
        response = await call_next(request)
        duration = time.time() - start_time  # 计算持续时间
        # 记录日志
        if int(response.status_code) > 400:
            logger.error(f"{request.url} - time: {duration:.2f} seconds")
        else:
            logger.info(f"{request.method} {request.url.path} - time: {duration:.2f} seconds")
        return response
