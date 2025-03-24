import uvicorn
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()
if __name__ == "__main__":
    import os

    # 读取配置
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))
    # 启动服务
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
