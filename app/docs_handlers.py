# app/docs.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import markdown

def setup_docs(app: FastAPI):
    # Mount static files
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
    
    @app.get("/")
    async def redirect_to_docs():
        return RedirectResponse(url="/docs")
