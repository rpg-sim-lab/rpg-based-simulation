"""API request tracing (issue #622, R3): OpenTelemetry server spans and Redis client spans, off unless an OTLP endpoint is set.

`setup_tracing(app)` is called once from `create_v2_app()`. With `OTEL_EXPORTER_OTLP_ENDPOINT` unset or blank it returns at once:
nothing from opentelemetry is imported, and no middleware, instrumentor, sampler, provider or log hook is installed.

With an endpoint set it installs, for this process:
  * a TracerProvider (`service.name` from `OTEL_SERVICE_NAME`, default `rpg-backend`) exporting OTLP over HTTP (port 4318) through a
    BatchSpanProcessor; the exporter reads the standard `OTEL_EXPORTER_OTLP_*` variables;
  * FastAPI server spans named by the route template;
  * Redis client spans, by instrumenting the redis library before any client is created;
  * head sampling `ParentBased(TraceIdRatioBased(r))`, r from `OTEL_TRACES_SAMPLER_ARG` (default 0.1), except that a root span of kind
    CLIENT is never sampled, so a Redis call with no request span above it records nothing (the event-recorder thread publishes once per
    envelope; rooting those would flood the backend);
  * `trace_id` / `span_id` attributes on log records made while a span is active (src/logging/formatter.py prints them).

The engine imports none of this (tests/unit/api/test_tracing_engine_boundary.py).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Mapping, Optional

logger = logging.getLogger(__name__)

ENDPOINT_ENV = "OTEL_EXPORTER_OTLP_ENDPOINT"
SERVICE_NAME_ENV = "OTEL_SERVICE_NAME"
SAMPLER_ARG_ENV = "OTEL_TRACES_SAMPLER_ARG"
DEFAULT_SERVICE_NAME = "rpg-backend"
DEFAULT_SAMPLE_RATIO = 0.1


def sample_ratio(environ: Mapping[str, str]) -> float:
    """The head-sampling ratio from OTEL_TRACES_SAMPLER_ARG; anything missing, unparseable or outside [0, 1] gives the default."""
    raw = (environ.get(SAMPLER_ARG_ENV) or "").strip()
    if not raw:
        return DEFAULT_SAMPLE_RATIO
    try:
        ratio = float(raw)
    except ValueError:
        return DEFAULT_SAMPLE_RATIO
    return ratio if 0.0 <= ratio <= 1.0 else DEFAULT_SAMPLE_RATIO


def tracing_enabled(environ: Mapping[str, str]) -> bool:
    """True when an OTLP endpoint is configured."""
    return bool((environ.get(ENDPOINT_ENV) or "").strip())


def _build_sampler(ratio: float) -> Any:
    from opentelemetry import trace  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off
    from opentelemetry.sdk.trace.sampling import (  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off
        Decision,
        ParentBased,
        Sampler,
        SamplingResult,
        TraceIdRatioBased,
    )

    class ParentedClientSampler(Sampler):
        """ParentBased(TraceIdRatioBased(ratio)), but a CLIENT span with no valid parent is dropped."""

        def __init__(self) -> None:
            self._inner = ParentBased(TraceIdRatioBased(ratio))

        def should_sample(self, parent_context, trace_id, name, kind=None, attributes=None, links=None, trace_state=None) -> Any:  # noqa: ANN001, PLR0913  # fixed by opentelemetry's Sampler interface
            parent = trace.get_current_span(parent_context).get_span_context()
            if kind == trace.SpanKind.CLIENT and not parent.is_valid:
                return SamplingResult(Decision.DROP, trace_state=trace_state)
            return self._inner.should_sample(parent_context, trace_id, name, kind, attributes, links, trace_state)

        def get_description(self) -> str:
            return f"ParentedClientSampler{{{self._inner.get_description()}}}"

    return ParentedClientSampler()


_previous_record_factory: Optional[Any] = None
_installed_record_factory: Optional[Any] = None


def _install_log_correlation() -> None:
    """Make every LogRecord created while a span is active carry `trace_id` (32 hex) and `span_id` (16 hex)."""
    global _previous_record_factory, _installed_record_factory
    if _installed_record_factory is not None:
        return
    from opentelemetry import trace  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off

    previous = logging.getLogRecordFactory()

    def factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = previous(*args, **kwargs)
        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            record.trace_id = format(context.trace_id, "032x")
            record.span_id = format(context.span_id, "016x")
        return record

    _previous_record_factory, _installed_record_factory = previous, factory
    logging.setLogRecordFactory(factory)


def _remove_log_correlation() -> None:
    """Undo `_install_log_correlation` (tests)."""
    global _previous_record_factory, _installed_record_factory
    if _installed_record_factory is not None and logging.getLogRecordFactory() is _installed_record_factory:
        logging.setLogRecordFactory(_previous_record_factory or logging.LogRecord)
    _previous_record_factory = _installed_record_factory = None


def setup_tracing(app: Any, environ: Optional[Mapping[str, str]] = None, span_exporter: Any = None) -> Optional[Any]:
    """Install tracing on `app` when an OTLP endpoint is configured; return the TracerProvider, or None when tracing is off.

    `span_exporter` replaces the OTLP exporter (tests pass an in-memory one)."""
    env = os.environ if environ is None else environ
    if not tracing_enabled(env):
        return None
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off
        from opentelemetry.instrumentation.redis import RedisInstrumentor  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415  # lazy on purpose: nothing is imported while tracing is off

        if span_exporter is None:
            import opentelemetry.exporter.otlp.proto.http.trace_exporter as otlp_http  # noqa: PLC0415  # lazy on purpose

            span_exporter = otlp_http.OTLPSpanExporter()
        service_name = (env.get(SERVICE_NAME_ENV) or "").strip() or DEFAULT_SERVICE_NAME
        provider = TracerProvider(resource=Resource.create({"service.name": service_name}), sampler=_build_sampler(sample_ratio(env)))
        provider.add_span_processor(BatchSpanProcessor(span_exporter))
        # Redis first: the library is patched before the first client exists (the stream adapter builds its client lazily).
        RedisInstrumentor().instrument(tracer_provider=provider)
        FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        _install_log_correlation()
    except Exception:  # tracing never stops the API from starting
        logger.warning("request tracing could not be set up; continuing without it", exc_info=True)
        return None
    return provider
