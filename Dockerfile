FROM python:3.12-slim

WORKDIR /app

# 复制依赖文件和 .env 文件
COPY requirements.txt .
COPY .env .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码（包含 app.py 与 app/ 目录）
COPY . .

EXPOSE 8000

# 启动FastAPI应用（与仓库结构一致）
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
