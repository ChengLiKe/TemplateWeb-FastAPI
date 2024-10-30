# fastapi-app/__init__.py

__version__ = "1.0.0"
__author__ = "like"
__email__ = "your.email@example.com"

# 导入路由
from .routes import example

# 导入中间件
from .middlewares.auth import AuthMiddleware

# 导入事件处理程序
from .events.life_cycle import startup_event, shutdown_event

# 将重要内容纳入包的公共接口
__all__ = [
    "example",
    "AuthMiddleware",
    "startup_event",
    "shutdown_event",
]
