import threading

import uvicorn
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
import os

# 读取配置
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))


def start_fastapi():
    # 启动IP和端口
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    start_fastapi()
    # thread_fastapi = threading.Thread(target=start_fastapi)
    # thread_fastapi.start()
    # thread_fastapi.join()
