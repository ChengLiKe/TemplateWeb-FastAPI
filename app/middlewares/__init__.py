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

from app.utils import get_logger, kv
from app.models.response import ErrorResponse
from app.models.errors import ErrorCode

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
    http_logger = get_logger("HTTP")
    @app.middleware("http")
    async def _logging_middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.time()
        request_id = getattr(request.state, "request_id", None)
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ("authorization", "cookie", "x-api-key")}
        method_path = f"{request.method} {request.url.path}"
        client_ip = request.client.host if request.client else "unknown"
        rid = request_id or "-"

        # Single-line separator to visually isolate requests
        http_logger.info("-" * 120, extra={"type": "separator", "request_id": request_id})

        # START
        http_logger.info(
            "[▶] START " + kv(rid=rid, method=request.method, path=request.url.path, ip=client_ip, ua=request.headers.get("user-agent")),
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

        try:
            response = await call_next(request)
            latency = time.time() - start
            latency_ms = round(latency * 1000)
            response_size = response.headers.get("content-length") or "-"

            log_level = logging.INFO
            if 500 <= response.status_code < 600:
                log_level = logging.ERROR
            elif 400 <= response.status_code < 500:
                log_level = logging.WARNING

            # DONE
            http_logger.log(
                log_level,
                "[✔] DONE " + kv(
                    rid=rid,
                    method=request.method,
                    path=request.url.path,
                    status=response.status_code,
                    latency_ms=latency_ms,
                    size=response_size,
                    ip=client_ip,
                ),
                extra={
                    "type": "request_complete",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "latency_ms": latency_ms,
                    "latency": round(latency, 3),
                    "user_agent": request.headers.get("user-agent"),
                    "real_ip": request.client.host if request.client else None,
                    "response_size": response_size,
                },
            )
            return response
        except Exception as e:
            latency = time.time() - start
            latency_ms = round(latency * 1000)
            # ERROR
            http_logger.error(
                "[✖] ERROR " + kv(
                    rid=rid,
                    method=request.method,
                    path=request.url.path,
                    err=str(e),
                    latency_ms=latency_ms,
                    ip=client_ip,
                ),
                extra={
                    "type": "request_error",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error": str(e),
                    "latency": round(latency, 3),
                    "real_ip": request.client.host if request.client else None,
                },
                exc_info=True,
            )
            raise


# -------------------- Exception Handlers --------------------
# Replace legacy logger with unified style
def _add_exception_handlers(app: FastAPI) -> None:
    http_logger = get_logger("HTTP")
    @app.exception_handler(RequestValidationError)
    async def _validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", None)
        http_logger.exception("Validation error " + kv(path=request.url.path, request_id=request_id), exc_info=exc)
        payload = ErrorResponse(
            code=ErrorCode.E_VALIDATION.value,
            message="Validation error",
            detail=exc.errors(),
        ).model_dump()
        payload["request_id"] = request_id
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(HTTPException)
    async def _http_exception_handler(request: Request, exc: HTTPException):
        request_id = getattr(request.state, "request_id", None)
        code = ErrorCode.from_status(exc.status_code).value
        # detail may already be structured; extract message when possible
        message = exc.detail if isinstance(exc.detail, str) else (
            exc.detail.get("message") if isinstance(exc.detail, dict) else "HTTP error"
        )
        http_logger.exception(
            "HTTPException " + kv(status=exc.status_code, code=code, message=message, path=request.url.path, request_id=request_id),
            exc_info=exc,
        )
        payload = ErrorResponse(code=code, message=message, detail=(exc.detail if not isinstance(exc.detail, str) else None)).model_dump()
        payload["request_id"] = request_id
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def _unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", None)
        http_logger.exception("Unhandled error " + kv(path=request.url.path, request_id=request_id), exc_info=exc)
        payload = ErrorResponse(
            code=ErrorCode.E_SERVER_ERROR.value,
            message="Internal server error",
            detail=str(exc),
        ).model_dump()
        payload["request_id"] = request_id
        return JSONResponse(status_code=500, content=payload)


# -------------------- Graceful Shutdown --------------------
# Use unified logger for clarity
def _add_graceful_shutdown(app: FastAPI) -> None:
    get_logger("APP").debug("Graceful shutdown handled via lifespan events; no on_event used here.")
    return
