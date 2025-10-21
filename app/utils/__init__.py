# 导入事件处理程序模块
from .logger_config import setup_logger, get_logger, kv

# 包元数据
__version__ = "1.0.0"
__author__ = "like"
# 初始化基础日志器（适用于简单场景）；推荐按组件获取 logger
logger = setup_logger("app")
