# fastapi-app/__init__.py
from utils.logger_config import setup_logger

__version__ = "1.0.0"
__author__ = "like"
__email__ = "your.email@example.com"

# 全局日志配置
logger = setup_logger("app")
