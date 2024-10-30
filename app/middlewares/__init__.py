# fastapi-app/events/__init__.py

"""
1. 中间件相关功能的包初始化模块
- Middleware-related function package initialization module.
2. 该模块包含与事件处理相关的，因此在应用启动和关闭时会被调用。
- This module contains event handling related to it, so it will be called when the application starts and shuts down.
"""

# 导入事件处理程序模块
from .auth import AuthMiddleware

# 包元数据
__version__ = "1.0.0"
__author__ = "like"

__all__ = [
    "AuthMiddleware"
]
