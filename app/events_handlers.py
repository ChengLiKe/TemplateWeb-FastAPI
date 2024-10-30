# app/events.py
from .events import startup_event, shutdown_event


def setup_events(app):
    @app.on_event("startup")
    async def on_startup():
        await startup_event()  # 在应用启动时执行

    @app.on_event("shutdown")
    async def on_shutdown():
        await shutdown_event()  # 在应用结束时执行
