# app/services/db.py
import os
from typing import Optional
from pathlib import Path

from fastapi import FastAPI


def _import_sqlalchemy():
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import sessionmaker
        return create_engine, sessionmaker, text
    except Exception as e:
        from app.utils import get_logger, kv
        db_logger = get_logger("DB")
        db_logger.warning("SQLAlchemy import " + kv(ok=False, err=str(e)))
        return None, None, None


async def init_db(app: FastAPI) -> None:
    # 延迟导入以避免循环导入
    from app.utils import get_logger, kv
    db_logger = get_logger("DB")
    
    settings = getattr(app.state, "settings", None)
    if not settings or not settings.db_enabled:
        db_logger.info("DB " + kv(enabled=False))
        app.state.db_ready = False
        return

    if not settings.db_url:
        db_logger.warning("DB " + kv(enabled=True, ready=False, err="missing DATABASE_URL"))
        app.state.db_ready = False
        return

    create_engine, sessionmaker, text = _import_sqlalchemy()
    if not create_engine:
        app.state.db_ready = False
        return

    try:
        # 对于SQLite数据库，确保目录存在
        if settings.db_url.startswith("sqlite:///"):
            # 提取数据库文件路径
            db_path = settings.db_url.replace("sqlite:///", "")
            # 获取目录部分
            db_dir = os.path.dirname(db_path)
            if db_dir:
                # 创建目录（如果不存在）
                Path(db_dir).mkdir(parents=True, exist_ok=True)
                from app.utils import get_logger
            db_logger = get_logger("DB")
            db_logger.info(f"Created database directory: {db_dir}")
        
        engine = create_engine(settings.db_url, echo=settings.db_echo, future=True)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        app.state.db_engine = engine
        app.state.db_session_factory = SessionLocal
        # 设置全局引擎实例，供其他模块使用
        set_db_engine(engine)
        # simple readiness check
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        app.state.db_ready = True
        from app.utils import get_logger, kv
        db_logger = get_logger("DB")
        db_logger.info("DB " + kv(enabled=True, ready=True))
    except Exception as e:
        app.state.db_ready = False
        from app.utils import get_logger, kv
        db_logger = get_logger("DB")
        db_logger.error("DB init " + kv(enabled=True, ready=False, err=str(e)))


async def close_db(app: FastAPI) -> None:
    engine = getattr(app.state, "db_engine", None)
    if engine is not None:
        # 延迟导入以避免循环导入
        from app.utils import get_logger, kv
        db_logger = get_logger("DB")
        try:
            engine.dispose()
            db_logger.info("DB closed " + kv(ok=True))
        except Exception as e:
            db_logger.warning("DB close " + kv(ok=False, err=str(e)))


# Dependency helper (sync sessions)
def get_db_session(app: FastAPI):
    SessionLocal = getattr(app.state, "db_session_factory", None)
    if not SessionLocal:
        raise RuntimeError("DB session factory not initialized")
    return SessionLocal()


# 用于获取数据库引擎的全局函数，供logger_config等模块使用
_engine_instance = None

def get_db_engine():
    """获取数据库引擎实例"""
    global _engine_instance
    return _engine_instance


def set_db_engine(engine):
    """设置数据库引擎实例，由init_db函数在初始化时调用"""
    global _engine_instance
    _engine_instance = engine