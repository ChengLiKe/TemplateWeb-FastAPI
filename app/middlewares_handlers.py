# app/middlewares.py
import asyncio
import time
from fastapi import Request
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from fastapi import FastAPI
from .events import setup_logger

logger = setup_logger(__name__)

def setup_middlewares(app: FastAPI):
    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许访问的源
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

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
            logger.error(f"{request.url} - Duration: {duration:.2f} seconds")
        else:
            logger.info(f"{request.method} {request.url.path} - Duration: {duration:.2f} seconds")
        return response
