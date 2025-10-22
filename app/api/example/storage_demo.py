# app/api/example/storage_demo.py
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Query
from sqlalchemy import text

from app.models.response import SuccessResponse

router = APIRouter(prefix="/storage", tags=["Demo"])


# Redis demos
@router.get("/redis/set")
async def redis_set(request: Request, key: str = Query(...), value: str = Query(...)):
    client = getattr(request.app.state, "redis", None)
    if not client:
        raise HTTPException(status_code=503, detail={"code": "E_SERVER_ERROR", "message": "Redis not initialized"})
    ok = await client.set(key, value)
    return SuccessResponse[dict](data={"ok": bool(ok), "key": key, "value": value}).model_dump()


@router.get("/redis/get")
async def redis_get(request: Request, key: str = Query(...)):
    client = getattr(request.app.state, "redis", None)
    if not client:
        raise HTTPException(status_code=503, detail={"code": "E_SERVER_ERROR", "message": "Redis not initialized"})
    value = await client.get(key)
    return SuccessResponse[dict](data={"key": key, "value": value}).model_dump()


# DB demos (SQLite recommended for quick start)
@router.post("/db/init")
async def db_init(request: Request):
    engine = getattr(request.app.state, "db_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail={"code": "E_SERVER_ERROR", "message": "DB not initialized"})
    sql = """
    CREATE TABLE IF NOT EXISTS kv (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT
    );
    """
    try:
        with engine.begin() as conn:
            conn.exec_driver_sql(sql)
        return SuccessResponse[dict](data={"ok": True}).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "E_SERVER_ERROR", "message": str(e)})


@router.post("/db/upsert")
async def db_upsert(request: Request, key: str = Query(...), value: str = Query(...)):
    engine = getattr(request.app.state, "db_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail={"code": "E_SERVER_ERROR", "message": "DB not initialized"})
    # SQLite upsert syntax; for other DBs adjust accordingly
    sql = text("""
        INSERT INTO kv(key, value) VALUES(:key, :value)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
    """)
    try:
        with engine.begin() as conn:
            conn.execute(sql, {"key": key, "value": value})
        return SuccessResponse[dict](data={"ok": True, "key": key, "value": value}).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "E_SERVER_ERROR", "message": str(e)})


@router.get("/db/get")
async def db_get(request: Request, key: str = Query(...)):
    engine = getattr(request.app.state, "db_engine", None)
    if not engine:
        raise HTTPException(status_code=503, detail={"code": "E_SERVER_ERROR", "message": "DB not initialized"})
    sql = text("SELECT key, value FROM kv WHERE key=:key")
    try:
        with engine.connect() as conn:
            row = conn.execute(sql, {"key": key}).fetchone()
        value = row[1] if row else None
        return SuccessResponse[dict](data={"key": key, "value": value}).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail={"code": "E_SERVER_ERROR", "message": str(e)})