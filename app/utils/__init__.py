# 导入事件处理程序模块
from .logger_config import setup_logger

# 包元数据
__version__ = "1.0.0"
__author__ = "like"
# 初始化日志配置
logger = setup_logger("app")
