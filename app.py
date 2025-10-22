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

from app import swagger_ui, events, middlewares

# 【1】加载.env配置文件
env_file = os.getenv("ENV_FILE", ".env")
load_dotenv(env_file)

DESCRIPTION = (
    "这是一个FastAPI的模板项目。"
)

# 【2】初始化FastAPI（使用集中配置）
from app.config.settings import Settings
settings = Settings.load()

app = FastAPI(
    title=settings.title,
    description=DESCRIPTION,
    version=settings.version,
    docs_url=None,
    redoc_url=None,
    lifespan=events,  # 使用 lifespan 事件处理启动/关闭
)
# 将配置挂载到应用状态，便于各模块访问
app.state.settings = settings

# 指标监控：在应用启动前挂载中间件与端点
if settings.metrics_enabled:
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app, endpoint=settings.metrics_endpoint)
        from app.utils import get_logger, kv
        get_logger("APP").info("Metrics " + kv(enabled=True, endpoint=settings.metrics_endpoint))
    except Exception as e:
        from app.utils import get_logger, kv
        get_logger("APP").warning("Metrics " + kv(enabled=False, err=str(e)))

# 【3】配置静态swagger模板
# ----------------------------------------------------------------------------
swagger_ui(app)  # 设置 Swagger 和 ReDoc
# ----------------------------------------------------------------------------

# 【4】配置中间件
# ----------------------------------------------------------------------------
middlewares(app)  # 设置中间件
# ----------------------------------------------------------------------------


# 引入功能模块
# ----------------------------------------------------------------------------
from app.api import example, health
from app.api.auth import auth_router
from app.api.example.storage_demo import router as storage_router

app.include_router(
    example.router, prefix="/example", tags=["Example"]
)
app.include_router(
    health.router
)
app.include_router(
    auth_router
)
app.include_router(
    storage_router
)

# ----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv

    # 加载 .env 文件
    load_dotenv()
    import os

    # 读取配置
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=HOST, port=PORT, reload=False)
