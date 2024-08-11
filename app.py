import uvicorn
import threading
import subprocess
import sys
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
import os

# 读取配置
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))


def start_fastapi():
    # 启动IP和端口
    uvicorn.run("fastapi-app.main:app", host=HOST, port=PORT, reload=False)


def start_streamlit():
    # 启动 Streamlit 子进程
    subprocess.run(["streamlit", "run", "streamlit-app/main.py"])


if __name__ == "__main__":
    def signal_handler(signum, frame):
        print("Received signal to terminate processes")
        sys.exit(0)


    thread_fastapi = threading.Thread(target=start_fastapi)
    thread_streamlit = threading.Thread(target=start_streamlit)
    thread_fastapi.start()
    thread_streamlit.start()
    thread_fastapi.join()
    thread_streamlit.join()
