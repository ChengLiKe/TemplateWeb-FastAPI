# 使用官方的Python 3.8基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件和 .env 文件
COPY requirements.txt .
COPY .env .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY ./app ./app

# 暴露应用运行的端口
EXPOSE 8000

# 启动FastAPI应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
