# app/config/settings.py
import os
from typing import List, Optional
from pydantic import BaseModel


class Settings(BaseModel):
    # App
    title: str = "FastAPI Template"
    version: str = "0.1.0"
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: List[str] = ["*"]
    log_level: str = "DEBUG"

    # Metrics
    metrics_enabled: bool = True
    metrics_endpoint: str = "/metrics"

    # Database
    db_enabled: bool = False
    db_url: Optional[str] = None
    db_echo: bool = False

    # Cache (Redis)
    cache_enabled: bool = False
    cache_url: Optional[str] = None

    # OpenTelemetry Tracing
    tracing_enabled: bool = False
    tracing_service_name: str = "fastapi-template"
    tracing_endpoint: Optional[str] = None  # OTLP endpoint, e.g. http://localhost:4318/v1/traces
    tracing_sampler_ratio: float = 1.0

    @classmethod
    def load(cls) -> "Settings":
        cors_raw = os.getenv("CORS_ORIGINS", "*")
        cors_origins = [x.strip() for x in cors_raw.split(",")] if cors_raw else ["*"]

        def as_bool(name: str, default: bool) -> bool:
            val = os.getenv(name)
            if val is None:
                return default
            return str(val).lower() in ("1", "true", "yes", "on")

        def as_float(name: str, default: float) -> float:
            val = os.getenv(name)
            try:
                return float(val) if val is not None else default
            except Exception:
                return default

        return cls(
            title=os.getenv("TITLE", cls().title),
            version=os.getenv("VERSION", cls().version),
            host=os.getenv("HOST", cls().host),
            port=int(os.getenv("PORT", cls().port)),
            cors_origins=cors_origins,
            log_level=os.getenv("LOG_LEVEL", cls().log_level),
            metrics_enabled=as_bool("METRICS_ENABLED", cls().metrics_enabled),
            metrics_endpoint=os.getenv("METRICS_ENDPOINT", cls().metrics_endpoint),
            db_enabled=as_bool("DB_ENABLED", cls().db_enabled),
            db_url=os.getenv("DATABASE_URL", cls().db_url),
            db_echo=as_bool("DB_ECHO", cls().db_echo),
            cache_enabled=as_bool("CACHE_ENABLED", cls().cache_enabled),
            cache_url=os.getenv("CACHE_URL", cls().cache_url),
            tracing_enabled=as_bool("TRACING_ENABLED", cls().tracing_enabled),
            tracing_service_name=os.getenv("TRACING_SERVICE_NAME", cls().tracing_service_name),
            tracing_endpoint=os.getenv("TRACING_ENDPOINT", cls().tracing_endpoint),
            tracing_sampler_ratio=as_float("TRACING_SAMPLER_RATIO", cls().tracing_sampler_ratio),
        )