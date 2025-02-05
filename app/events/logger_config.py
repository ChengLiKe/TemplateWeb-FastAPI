# app/events/logger_config.py
"""格式化日志，本地打印"""

import logging
import os
from logging.handlers import RotatingFileHandler

logger_level = logging.DEBUG
log_path = 'app/logs/'
if not os.path.exists(log_path):
    os.makedirs(log_path)

# ANSI 转义序列
RESET = "\033[0m"
GREEN = "\033[92m"  # DEBUG
BLUE = "\033[32m"  # INFO
YELLOW = "\033[93m"  # WARNING
RED = "\033[91m"  # ERROR
MAGENTA = "\033[95m"  # CRITICAL


# 创建一个自定义的格式化器
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': GREEN,
        'INFO': BLUE,
        'WARNING': YELLOW,
        'ERROR': RED,
        'CRITICAL': MAGENTA,
    }

    def format(self, record):
        # 获取当前日志级别的颜色
        color = self.COLORS.get(record.levelname, RESET)
        # 格式化时间戳和级别名称部分
        record.asctime = self.formatTime(record, self.datefmt)
        # 将整个部分变色
        msecs = int(record.msecs)  # 转换为整数
        formatted_message = f"{color}[{record.asctime},{msecs:03d}] [{record.levelname:>8s}]{RESET} - {record.msg}"
        return formatted_message


def setup_logger(logger_name):
    # 创建日志记录器
    logger = logging.getLogger(logger_name)
    logger.setLevel(logger_level)

    # 创建控制台处理器并设置级别为DEBUG
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # 创建文件处理器，文件大小达到1MB时回滚
    file_handler = RotatingFileHandler(f"{log_path}app.log", maxBytes=1 * 1024 * 1024, backupCount=3)
    file_handler.setLevel(logging.INFO)

    # 创建格式器并添加到处理器
    formatter = ColoredFormatter('%(message)s',
                                 datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 将处理器添加到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # 禁止日志消息向上传递给父记录器，避免重复输出
    logger.propagate = False
    return logger
