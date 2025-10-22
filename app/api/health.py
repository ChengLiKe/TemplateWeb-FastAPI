# app/api/health.py
import time
import platform
from fastapi import APIRouter
from app.utils import get_logger, kv

router = APIRouter()
log = get_logger("APP")

@router.get("/healthz", tags=["Health"], summary="Liveness probe")
async def healthz():
    ts = time.time()
    log.info("✔ HEALTHZ " + kv(ts=ts))
    return {
        "status": "ok",
        "ts": ts,
        "python": platform.python_version(),
    }

@router.get("/readyz", tags=["Health"], summary="Readiness probe")
async def readyz(request):
    ts = time.time()
    state = request.app.state
    db_ready = getattr(state, "db_ready", False)
    cache_ready = getattr(state, "cache_ready", False)
    ready = db_ready and cache_ready if any([getattr(state, "settings", None) and (state.settings.db_enabled or state.settings.cache_enabled)]) else True
    log.info("✔ READYZ " + kv(ts=ts, ready=ready, db_ready=db_ready, cache_ready=cache_ready))
    return {
        "ready": ready,
        "ts": ts,
        "db_ready": db_ready,
        "cache_ready": cache_ready,
    }