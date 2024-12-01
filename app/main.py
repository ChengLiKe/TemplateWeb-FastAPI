# fastapi-app/main.py

# **************************************************************************************************************************
# 【1】加载.env配置文件
# 【2】初始化FastAPI
# 【3】配置静态swagger模板
# 【4】配置事件 - 生命周期 - 启动 关闭
# 【5】配置中间件 - 事件循环 - 异常处理 - 日志记录
# 【6】【dev】引入功能模块 - 可拓展
# **************************************************************************************************************************
import os

from dotenv import load_dotenv
from fastapi import FastAPI

from app.swagger_ui import swagger_ui  # 引入swagger静态文件配置模块
from app.events import events  # 引入事件模块
from app.middlewares import middlewares  # 引入中间件模块

# 【1】加载.env配置文件
env_file = os.getenv("ENV_FILE", ".env.development")
load_dotenv(env_file)

DESCRIPTION = (
    "这是一个FastAPI的模板项目. 如果想知道更多详情, 请点击链接获取: "
    "[README.md](https://{}:{}/README)".format(os.getenv("HOST"), os.getenv("PORT"))
)

# 【2】初始化FastAPI
app = FastAPI(
    title=os.getenv("TITLE"),
    description=DESCRIPTION,
    version=os.getenv("VERSION"),
    docs_url=None,
    redoc_url=None
)

# 【3】配置静态swagger模板
# ----------------------------------------------------------------------------
swagger_ui(app)  # 设置 Swagger 和 ReDoc
# ----------------------------------------------------------------------------

# 【4】配置事件
# ----------------------------------------------------------------------------
events(app)  # 设置事件
# ----------------------------------------------------------------------------

# 【5】配置中间件
# ----------------------------------------------------------------------------
middlewares(app)  # 设置中间件
# ----------------------------------------------------------------------------


# 引入功能模块
# ----------------------------------------------------------------------------
from .routes import example

app.include_router(
    example.router, prefix="/example", tags=["Example"]
)

# ----------------------------------------------------------------------------
