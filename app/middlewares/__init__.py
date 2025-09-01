# fastapi-app/middlewares/__init__.py
"""
Enhanced FastAPI middleware package
- CORS / Security headers
- Request-ID tracing
- Structured logging
- Rate limiting
- GZip
- Graceful shutdown
"""
from __future__ import annotations

import asyncio
import os
import time
import uuid
from typing import Awaitable, Callable

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import logging

from app.utils import logger

__version__ = "1.1.0"
__author__ = "like"

__all__ = ["middlewares", "AuthMiddleware", "limiter"]

# -------------------- 限流器 --------------------
limiter = Limiter(key_func=get_remote_address)


def middlewares(app: FastAPI) -> None:
    """注册所有中间件（按顺序调用）"""
    _add_cors(app)
    _add_gzip(app)
    _add_security_headers(app)
    _add_request_id(app)
    _add_rate_limiter(app)
    _add_structured_logging(app)
    _add_exception_handlers(app)
    _add_graceful_shutdown(app)


# -------------------- CORS --------------------
def _add_cors(app: FastAPI) -> None:
    # 获取CORS_ORIGINS环境变量，如果没有设置，则默认为"*"
    origins_raw = os.getenv("CORS_ORIGINS", "*")
    # 将origins_raw按逗号分隔，并去除空格，得到origins列表
    origins = [o.strip() for o in origins_raw.split(",")]

    # 添加CORS中间件
    app.add_middleware(
        CORSMiddleware,
        # 允许的源
        allow_origins=origins,
        # 是否允许发送Cookie
        allow_credentials=True,
        # 允许的请求方法
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        # 允许的请求头
        allow_headers=["*"],
        # 预检请求的缓存时间
        max_age=int(os.getenv("CORS_MAX_AGE", "600")),
    )


# -------------------- GZip --------------------
# 定义一个函数，用于向FastAPI应用添加GZip中间件
def _add_gzip(app: FastAPI) -> None:
    # 向应用添加GZip中间件，设置最小压缩文件大小为500字节，压缩级别为6
    app.add_middleware(
        GZipMiddleware,
        minimum_size=500,
        compresslevel=6,
    )


# -------------------- Security Headers --------------------
def _add_security_headers(app: FastAPI) -> None:
    # 添加安全头信息
    @app.middleware("http")
    async def _security_headers_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 调用下一个中间件
        response = await call_next(request)
        # HSTS
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )
        # Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )
        return response


# -------------------- Request-ID --------------------
def _add_request_id(app: FastAPI) -> None:
    # 添加一个中间件，用于为每个请求添加一个唯一的请求ID
    @app.middleware("http")
    async def _request_id_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 从请求头中获取X-Request-ID，如果不存在则生成一个新的UUID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        # 将请求ID存储在请求的状态中
        request.state.request_id = request_id
        # 调用下一个中间件或路由处理函数
        response = await call_next(request)
        # 将请求ID添加到响应头中
        response.headers["X-Request-ID"] = request_id
        # 返回响应
        return response


# -------------------- Rate Limit --------------------
def _add_rate_limiter(app: FastAPI) -> None:
    """
    中间件里没有任何限流逻辑；真正的“按接口、按规则检查”应该由 装饰器（@limiter.limit(...)）完成。
    中间件只负责把 slowapi 的钩子挂进请求生命周期，全局生效的是 装饰器本身
    但 slowapi 的中间件内部会判断：
        当前路由有没有被 @limiter.limit(...) 装饰？
        有 → 执行对应规则；
        没有 → 直接放过。
    """
    # 将 limiter 添加到 app 的状态中
    app.state.limiter = limiter
    # 添加一个异常处理程序，当 HTTPException 发生时，调用 _rate_limit_exceeded_handler
    app.add_exception_handler(HTTPException, _rate_limit_exceeded_handler)

    # 添加一个中间件，用于处理 HTTP 请求
    @app.middleware("http")
    async def _rate_limit_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 让 slowapi 拦截
        response = await call_next(request)
        return response


# -------------------- Structured Logging --------------------
def _add_structured_logging(app: FastAPI) -> None:
    @app.middleware("http")
    async def _logging_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # 请求开始时间
        start = time.time()
        request_id = getattr(request.state, "request_id", None)
        
        # 提取请求头信息（但不记录敏感信息）
        headers = {k: v for k, v in request.headers.items() 
                 if k.lower() not in ('authorization', 'cookie', 'x-api-key')}
        
        # 记录请求开始信息
        logger.info(
            f"开始处理请求 [{request.method} {request.url.path}] 来自 {request.client.host if request.client else '未知IP'}",
            extra={
                "type": "request_start",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "path_params": dict(request.path_params),
                "query_params": dict(request.query_params),
                "headers": headers,
                "real_ip": request.client.host if request.client else None,
            },
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            latency = time.time() - start
            
            # 根据状态码确定日志级别
            log_level = logging.INFO
            if 500 <= response.status_code < 600:
                log_level = logging.ERROR
            elif 400 <= response.status_code < 500:
                log_level = logging.WARNING
            
            # 确定请求处理结果
            result = "成功" if response.status_code < 400 else "失败"
            
            # 获取响应体大小（Content-Length或估计值）
            response_size = response.headers.get("content-length", "未知")
            
            # 构建结构化日志消息
            log_message = f"请求处理{result} [{request.method} {request.url.path}] "
            log_message += f"状态码: {response.status_code}, 延迟: {round(latency * 1000)}ms, "
            log_message += f"响应大小: {response_size}"
            
            # 记录请求完成信息
            logger.log(
                log_level,
                log_message,
                extra={
                    "type": "request_complete",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": round(latency * 1000),  # 转换为毫秒
                    "latency": round(latency, 3),
                    "user_agent": request.headers.get("user-agent"),
                    "real_ip": request.client.host if request.client else None,
                    "response_size": response_size,
                    "result": result,
                },
            )
            
            return response
        except Exception as e:
            # 记录异常信息
            latency = time.time() - start
            logger.error(
                f"请求处理异常 [{request.method} {request.url.path}]: {str(e)}",
                extra={
                    "type": "request_error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "latency": round(latency, 3),
                    "real_ip": request.client.host if request.client else None,
                },
                exc_info=True
            )
            # 重新抛出异常，让上层异常处理器处理
            raise


# -------------------- Exception Handlers --------------------
def _add_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Validation error",
                "errors": exc.errors(),
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "request_id": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def _all_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": getattr(request.state, "request_id", None),
            },
        )


# -------------------- Graceful Shutdown --------------------
def _add_graceful_shutdown(app: FastAPI) -> None:
    @app.on_event("startup")
    async def _startup() -> None:
        logger.info("Application startup")

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        logger.info("Application shutdown: waiting for background tasks ...")
        # 这里如果有数据库连接池、Redis、MQ 等，可以统一关闭
        await asyncio.sleep(0.1)  # 让已接收的请求完成
        logger.info("Application shutdown complete")
