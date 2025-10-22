# app/utils/telemetry.py
from typing import Optional

from fastapi import FastAPI

from app.utils import get_logger, kv

otel_logger = get_logger("OTEL")


async def setup_tracing(app: FastAPI) -> None:
    settings = getattr(app.state, "settings", None)
    if not settings or not settings.tracing_enabled:
        otel_logger.info("Tracing " + kv(enabled=False))
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
        # Prefer OTLP exporter if endpoint provided; otherwise console exporter
        exporter = None
        if settings.tracing_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=settings.tracing_endpoint)
            except Exception as e:
                otel_logger.warning("OTLP exporter import " + kv(ok=False, err=str(e)))
        if exporter is None:
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            exporter = ConsoleSpanExporter()

        resource = Resource.create({"service.name": settings.tracing_service_name or app.title})
        provider = TracerProvider(resource=resource, sampler=TraceIdRatioBased(settings.tracing_sampler_ratio))
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except Exception as e:
            otel_logger.warning("FastAPI instrumentation " + kv(ok=False, err=str(e)))

        app.state.tracer_provider = provider
        otel_logger.info("Tracing " + kv(enabled=True, exporter=exporter.__class__.__name__))
    except Exception as e:
        otel_logger.error("Tracing setup " + kv(enabled=True, ok=False, err=str(e)))


async def shutdown_tracing(app: FastAPI) -> None:
    provider = getattr(app.state, "tracer_provider", None)
    if provider is not None:
        try:
            # Flush and shutdown span processors via provider
            provider.shutdown()
            otel_logger.info("Tracing closed " + kv(ok=True))
        except Exception as e:
            otel_logger.warning("Tracing close " + kv(ok=False, err=str(e)))