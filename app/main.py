# fastapi-app/main.py

# **************************************************************************************************************************
# 【1】加载.env配置文件
# 【2】初始化FastAPI
# 【3】【dev】配置监控组件prometheus，在API /metrics -- 未完善
# 【4】配置静态swagger模板
# 【5】配置事件 - 生命周期 - 启动 关闭
# 【6】配置中间件 - 事件循环 - 异常处理 - 日志记录
# 【7】【dev】引入功能模块 - 可拓展
# **************************************************************************************************************************

from fastapi import FastAPI, HTTPException, Request
import markdown
import os
from dotenv import load_dotenv
from .events_handlers import setup_events  # 引入事件模块
from .docs_handlers import setup_docs  # 引入swagger静态文件配置模块
from .middlewares_handlers import setup_middlewares  # 引入中间件模块
from .config_handlers import HOST, PORT, TITLE, DESCRIPTION, VERSION  # 引入配置

# 初始化FastAPI
app = FastAPI(
    title=TITLE,
    description=DESCRIPTION,
    version=VERSION,
    docs_url=None,
    redoc_url=None
)


# [2] 配置静态swagger模板
# ----------------------------------------------------------------------------
setup_docs(app)  # 设置 Swagger 和 ReDoc
# ----------------------------------------------------------------------------

# [3] 配置事件
# ----------------------------------------------------------------------------
setup_events(app)  # 设置事件
# ----------------------------------------------------------------------------

# [4] 配置中间件
# ----------------------------------------------------------------------------
# 配置中间件
setup_middlewares(app)  # 设置中间件
# ----------------------------------------------------------------------------


# 引入功能模块
# ----------------------------------------------------------------------------
from .routes import example

app.include_router(
    example.router, prefix="/example", tags=["Example"]
)

# ----------------------------------------------------------------------------
