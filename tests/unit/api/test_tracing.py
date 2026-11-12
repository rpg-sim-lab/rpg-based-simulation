"""API request tracing (issue #622, R3) with an endpoint set: server spans by route template, parented Redis spans, sampling, log fields."""
from __future__ import annotations

import io
import json
import logging

import pytest

pytest.importorskip("opentelemetry.sdk")

import redis  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from opentelemetry.instrumentation.redis import RedisInstrumentor  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402
from opentelemetry.trace import SpanKind  # noqa: E402

from src.api import tracing  # noqa: E402
from src.logging.formatter import JsonFormatter, TraceAwareFormatter  # noqa: E402

ENDPOINT = {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://tempo:4318"}


def _dead_redis() -> redis.Redis:
    return redis.Redis(host="127.0.0.1", port=1, socket_connect_timeout=0.2, socket_timeout=0.2)


def _call_redis(client: redis.Redis) -> None:
    try:
        client.get("k")
    except Exception:  # no server on purpose: the span is recorded either way
        pass


def _build(env=None, ratio="1"):
    exporter = InMemorySpanExporter()
    app = FastAPI()
    log = logging.getLogger("tracing-test")

    @app.get("/items/{item_id}")
    def item(item_id: str):
        log.warning("in-request")
        _call_redis(_dead_redis())
        return {"id": item_id}

    environ = {**ENDPOINT, "OTEL_TRACES_SAMPLER_ARG": ratio, **(env or {})}
    provider = tracing.setup_tracing(app, environ=environ, span_exporter=exporter)
    assert provider is not None
    return app, provider, exporter


@pytest.fixture(autouse=True)
def _undo_global_patches():
    yield
    RedisInstrumentor().uninstrument()
    tracing._remove_log_correlation()


def test_server_span_is_named_by_route_template_and_redis_is_its_child():
    app, provider, exporter = _build()
    assert TestClient(app).get("/items/12345").status_code == 200
    provider.force_flush()
    spans = exporter.get_finished_spans()
    server = [s for s in spans if s.kind == SpanKind.SERVER]
    clients = [s for s in spans if s.kind == SpanKind.CLIENT]
    assert len(server) == 1
    assert "/items/{item_id}" in server[0].name and "12345" not in server[0].name
    assert server[0].attributes["http.route"] == "/items/{item_id}"
    assert server[0].resource.attributes["service.name"] == "rpg-backend"
    assert clients and all(c.parent is not None and c.parent.span_id == server[0].context.span_id for c in clients)
    assert {c.context.trace_id for c in clients} == {server[0].context.trace_id}


def test_service_name_follows_the_environment():
    _, provider, exporter = _build({"OTEL_SERVICE_NAME": "custom"})
    assert provider.resource.attributes["service.name"] == "custom"


def test_redis_call_with_no_active_span_records_nothing():
    _, provider, exporter = _build()
    _call_redis(_dead_redis())  # not inside a request: the event-recorder thread's situation
    provider.force_flush()
    assert exporter.get_finished_spans() == ()


def test_redis_call_on_a_bare_thread_records_nothing():
    import threading

    _, provider, exporter = _build()
    thread = threading.Thread(target=lambda: _call_redis(_dead_redis()))
    thread.start()
    thread.join()
    provider.force_flush()
    assert exporter.get_finished_spans() == ()


def test_client_created_after_setup_is_instrumented():
    _, provider, exporter = _build()
    app_client = _dead_redis()  # created after setup, like the lazy stream-adapter singleton
    with provider.get_tracer("t").start_as_current_span("parent"):
        _call_redis(app_client)
    provider.force_flush()
    assert any(s.kind == SpanKind.CLIENT for s in exporter.get_finished_spans())


def test_sampling_ratio_zero_records_nothing_and_one_records():
    app, provider, exporter = _build(ratio="0")
    TestClient(app).get("/items/1")
    provider.force_flush()
    assert exporter.get_finished_spans() == ()


def test_default_ratio_is_a_tenth():
    env = dict(ENDPOINT)
    assert tracing.sample_ratio(env) == 0.1
    sampler = tracing._build_sampler(0.1)
    assert "0.1" in sampler.get_description()


def test_log_lines_carry_trace_id_inside_a_request_only():
    app, provider, exporter = _build()
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(TraceAwareFormatter("%(levelname)s:%(name)s:%(message)s"))
    log = logging.getLogger("tracing-test")
    log.addHandler(handler)
    try:
        TestClient(app).get("/items/1")
        log.warning("outside")
    finally:
        log.removeHandler(handler)
    inside, outside = stream.getvalue().splitlines()[:2]
    assert inside.startswith("WARNING:tracing-test:in-request trace_id=") and " span_id=" in inside
    trace_hex = inside.split("trace_id=")[1].split()[0]
    assert len(trace_hex) == 32
    assert outside == "WARNING:tracing-test:outside"


def test_json_lines_carry_the_keys_only_inside_a_span():
    _, provider, _ = _build()
    fmt = JsonFormatter()
    with provider.get_tracer("t").start_as_current_span("s"):
        inside = json.loads(fmt.format(logging.getLogger("x").makeRecord("x", 30, "f", 1, "m", (), None)))
    outside = json.loads(fmt.format(logging.getLogger("x").makeRecord("x", 30, "f", 1, "m", (), None)))
    assert len(inside["trace_id"]) == 32 and len(inside["span_id"]) == 16
    assert "trace_id" not in outside and "span_id" not in outside


def test_formatters_are_byte_identical_when_tracing_never_ran():
    record = logging.LogRecord("n", 30, "f", 1, "hello %s", ("x",), None)
    assert TraceAwareFormatter("%(levelname)s:%(name)s:%(message)s").format(record) == "WARNING:n:hello x"
    assert set(json.loads(JsonFormatter().format(record))) == {"message", "timestamp", "level", "component"}


def test_default_exporter_is_otlp_http_and_needs_no_collector_to_start():
    """Without an injected exporter the real OTLP/HTTP exporter is built; nothing connects until a span is exported."""
    app = FastAPI()
    provider = tracing.setup_tracing(app, environ=ENDPOINT)
    assert provider is not None
    processor = provider._active_span_processor._span_processors[0]  # noqa: SLF001
    assert type(processor.span_exporter).__module__.startswith("opentelemetry.exporter.otlp.proto.http")


def test_log_correlation_wraps_the_existing_record_factory_and_installs_once():
    previous = logging.getLogRecordFactory()

    def marking(*args, **kwargs):
        record = previous(*args, **kwargs)
        record.marker = "kept"
        return record

    logging.setLogRecordFactory(marking)
    try:
        app, provider, _ = _build()
        installed = logging.getLogRecordFactory()
        assert installed is not marking
        # a second create_v2_app() in the same process (tests do this) must not stack a second wrapper
        tracing.setup_tracing(FastAPI(), environ={**ENDPOINT, "OTEL_TRACES_SAMPLER_ARG": "1"}, span_exporter=InMemorySpanExporter())
        assert logging.getLogRecordFactory() is installed
        with provider.get_tracer("t").start_as_current_span("s"):
            record = logging.getLogRecordFactory()("n", 30, "f", 1, "x", (), None)
        assert record.marker == "kept"  # the old factory still ran
        assert len(record.trace_id) == 32
        tracing._remove_log_correlation()
        assert logging.getLogRecordFactory() is marking  # and uninstalling restores it
    finally:
        logging.setLogRecordFactory(previous)
