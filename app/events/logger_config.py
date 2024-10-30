#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
格式化日志，本地打印
"""

import logging
import os
from logging.handlers import RotatingFileHandler

logger_level = logging.DEBUG
log_path = 'logs/'
if not os.path.exists(log_path):
    os.makedirs(log_path)


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
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(filename)s - line:%(lineno)d - %(funcName)s() - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 将处理器添加到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # 禁止日志消息向上传递给父记录器，避免重复输出
    logger.propagate = False
    return logger
