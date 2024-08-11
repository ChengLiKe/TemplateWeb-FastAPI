if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    import os

    # 加载 .env 文件
    load_dotenv()

    # 读取配置
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))

    # 启动IP和端口
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=False)
