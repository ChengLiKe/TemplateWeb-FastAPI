# app/config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 读取配置
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

# FastAPI 配置
TITLE = "Template-FastAPI"
DESCRIPTION = (
    "这是一个FastAPI的模板项目. 如果想知道更多详情, 请点击链接获取: "
    "[README.md](http://{}:{}/README)".format(HOST, PORT)
)
VERSION = "0.0.1"
