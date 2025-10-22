# app/services/db.py
from typing import Optional

from fastapi import FastAPI

from app.utils import get_logger, kv

db_logger = get_logger("DB")


def _import_sqlalchemy():
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        return create_engine, sessionmaker
    except Exception as e:
        db_logger.warning("SQLAlchemy import " + kv(ok=False, err=str(e)))
        return None, None


async def init_db(app: FastAPI) -> None:
    settings = getattr(app.state, "settings", None)
    if not settings or not settings.db_enabled:
        db_logger.info("DB " + kv(enabled=False))
        app.state.db_ready = False
        return

    if not settings.db_url:
        db_logger.warning("DB " + kv(enabled=True, ready=False, err="missing DATABASE_URL"))
        app.state.db_ready = False
        return

    create_engine, sessionmaker = _import_sqlalchemy()
    if not create_engine:
        app.state.db_ready = False
        return

    try:
        engine = create_engine(settings.db_url, echo=settings.db_echo, future=True)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        app.state.db_engine = engine
        app.state.db_session_factory = SessionLocal
        # simple readiness check
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        app.state.db_ready = True
        db_logger.info("DB " + kv(enabled=True, ready=True))
    except Exception as e:
        app.state.db_ready = False
        db_logger.error("DB init " + kv(enabled=True, ready=False, err=str(e)))


async def close_db(app: FastAPI) -> None:
    engine = getattr(app.state, "db_engine", None)
    if engine is not None:
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