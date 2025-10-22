# app/services/cache.py
from typing import Optional

from fastapi import FastAPI

from app.utils import get_logger, kv

cache_logger = get_logger("CACHE")


async def init_cache(app: FastAPI) -> None:
    settings = getattr(app.state, "settings", None)
    if not settings or not settings.cache_enabled:
        cache_logger.info("Cache " + kv(enabled=False))
        app.state.cache_ready = False
        return

    if not settings.cache_url:
        cache_logger.warning("Cache " + kv(enabled=True, ready=False, err="missing CACHE_URL"))
        app.state.cache_ready = False
        return

    try:
        import redis.asyncio as redis
    except Exception as e:
        cache_logger.warning("Redis import " + kv(ok=False, err=str(e)))
        app.state.cache_ready = False
        return

    try:
        client = redis.from_url(settings.cache_url, encoding="utf-8", decode_responses=True)
        # simple readiness check
        pong = await client.ping()
        app.state.redis = client
        app.state.cache_ready = bool(pong)
        cache_logger.info("Cache " + kv(enabled=True, ready=bool(pong)))
    except Exception as e:
        app.state.cache_ready = False
        cache_logger.error("Cache init " + kv(enabled=True, ready=False, err=str(e)))


async def close_cache(app: FastAPI) -> None:
    client = getattr(app.state, "redis", None)
    if client is not None:
        try:
            await client.close()
            cache_logger.info("Cache closed " + kv(ok=True))
        except Exception as e:
            cache_logger.warning("Cache close " + kv(ok=False, err=str(e)))