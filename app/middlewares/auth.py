# fastapi-app/middlewares/auth.py

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 在这里可以添加身份验证逻辑
        response: Response = await call_next(request)
        return response
