# fastapi-app/events/life_cycle.py

import logging
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取配置
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'  # 自定义格式
)
logger = logging.getLogger(__name__)


async def startup_event():
    logger.info("应用已启动.")
    logger.info(f"prometheus running on http://{HOST}:{PORT}/metrics")


async def shutdown_event():
    logger.info("应用已关闭.")
