# app/events/startup.py
from fastapi import FastAPI
import os

from app.utils import get_logger, kv
from app.services.db import init_db
from app.services.cache import init_cache
from app.utils.telemetry import setup_tracing
import logging
import platform
import fastapi


async def startup(app: FastAPI):
    # Unified style: tag + symbol + key=value pairs
    app_logger = get_logger("APP")
    level_name = logging.getLevelName(logging.getLogger("app").getEffectiveLevel())
    log_files = [h.baseFilename for h in logging.getLogger("app").handlers if hasattr(h, "baseFilename")]

    # Metrics status logged only; instrumentation happens before app starts
    settings = getattr(app.state, "settings", None)
    if settings and settings.metrics_enabled:
        app_logger.info("Metrics " + kv(enabled=True, endpoint=settings.metrics_endpoint))
    else:
        app_logger.info("Metrics " + kv(enabled=False))

    # Initialize DB, Cache, and Tracing
    await init_db(app)
    
    # 数据库初始化完成后，激活数据库日志功能
    if settings.db_logging_enabled:
        try:
            from app.utils.logger_config import DatabaseHandler
            # 为所有已配置的数据库日志处理器设置为活动状态
            for logger_name in ['app']:
                logger = logging.getLogger(logger_name)
                for handler in logger.handlers:
                    if isinstance(handler, DatabaseHandler):
                        handler.is_active = True
                        # 尝试创建表
                        from app.services.db import get_db_engine
                        engine = get_db_engine()
                        if engine and not handler.table_created:
                            with engine.connect() as conn:
                                try:
                                    from sqlalchemy import text
                                    conn.execute(text("""
                                        CREATE TABLE IF NOT EXISTS logs (
                                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                                            timestamp TEXT,
                                            level TEXT,
                                            logger TEXT,
                                            module TEXT,
                                            line INTEGER,
                                            message TEXT,
                                            component TEXT,
                                            trace_id TEXT
                                        )
                                    """))
                                    conn.commit()
                                    handler.table_created = True
                                except Exception as table_err:
                                    app_logger.warning(f"Failed to create log table: {str(table_err)}")
        except Exception as e:
            app_logger.warning(f"Failed to activate database logging: {str(e)}")
    
    await init_cache(app)
    await setup_tracing(app)

    app_logger.info("▶ STARTUP " + kv(title=app.title, version=app.version, python=platform.python_version(), fastapi=fastapi.__version__))
    app_logger.info("Docs " + kv(openapi=app.openapi_url, swagger="/docs", redoc="/redoc"))
    app_logger.info("Logging " + kv(level=level_name, handlers=len(logging.getLogger("app").handlers), file=(log_files[0] if log_files else "N/A")))
    app_logger.info("Topology " + kv(routes=len(app.routes), middlewares=len(app.user_middleware)))
    app_logger.info("Application started.")
