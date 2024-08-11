# app/main.py

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

from .events import setup_logger

logger = setup_logger(__name__)

# 加载 .env 文件
load_dotenv()

# 读取配置
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", 8000))

app = FastAPI(
    title="Template-FastAPI",
    description=(
        "这是一个FastAPI的模板项目. 如果想知道更多详情, 请点击链接获取: "
        "[README.md](http://{}:{}/README)".format(HOST, PORT)
    ),
    version="0.0.1",
    docs_url=None,
    redoc_url=None
)

# [1] 配置监控组件
# ----------------------------------------------------------------------------
from prometheus_fastapi_instrumentator import Instrumentator

# 自动收集请求的监控数据
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)
# ----------------------------------------------------------------------------


# [2] 配置静态swagger模板
# ----------------------------------------------------------------------------
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )


@app.get("/README", include_in_schema=False, response_class=HTMLResponse)
async def read_readme():
    if not os.path.exists("README.md"):
        raise HTTPException(status_code=404, detail="README.md file not found")

    with open("README.md", "r", encoding="utf-8") as f:
        md_content = f.read()

    # 将 Markdown 转换为 HTML
    html_content = markdown.markdown(md_content)
    return HTMLResponse(content=html_content)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/static/templates/index.html")


@app.get("/pdf", include_in_schema=False)
async def pdfs():
    """
    列出 pdf_directory 目录下的所有 PDF 文件，并生成 HTML 页面
    """
    # 配置 Jinja2 模板引擎
    env = Environment(loader=FileSystemLoader("app/static/templates"))
    try:
        files = os.listdir("app/static/templates/pdf")
        pdf_files = [file for file in files if file.endswith(".pdf")]
        print(pdf_files)
        template = env.get_template("pdf.html")
        html_content = template.render(pdf_files=pdf_files)
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------

# [3] 配置事件
# ----------------------------------------------------------------------------
from .events import startup_event, shutdown_event


@app.on_event("startup")
async def on_startup():
    # 生命周期-启动
    await startup_event()  # 在应用启动时执行


@app.on_event("shutdown")
async def on_shutdown():
    # 生命周期-结束
    await shutdown_event()  # 在应用结束时执行


# ----------------------------------------------------------------------------

# [4] 配置中间件
# ----------------------------------------------------------------------------
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
import asyncio
import time

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许访问的源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def ensure_event_loop_middleware(request: Request, call_next):
    # 中间件一：检查事件循环
    try:
        # 如果事件循环已经被创建
        asyncio.get_event_loop()
    except RuntimeError as e:
        # 没有事件循环时创建新的
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    response = await call_next(request)
    return response


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    # 中间件二：异常处理
    try:
        response = await call_next(request)
    except Exception as e:
        return JSONResponse(content={"detail": str(e)}, status_code=500)
    return response


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    # 中间件三：日志记录
    start_time = time.time()  # 请求到达时计时
    response = await call_next(request)
    duration = time.time() - start_time  # 计算持续时间
    # 记录日志
    if int(response.status_code) > 400:
        logger.error(f"{request.url} - Duration: {duration:.2f} seconds")
    else:
        logger.info(f"{request.method} {request.url.path} - Duration: {duration:.2f} seconds")
    return response


# ----------------------------------------------------------------------------


# 引入功能模块
# ----------------------------------------------------------------------------
from .routes import example

app.include_router(
    example.router, prefix="/example", tags=["Example"]
)

# ----------------------------------------------------------------------------
