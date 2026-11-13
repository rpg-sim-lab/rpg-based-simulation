---
status: active
layer: observability
authority: P1
audience: agent
tags: [documentation, observability, api-design]
---

# API Request Tracing

OpenTelemetry server spans and Redis client spans for the API process (issue #622, R3). Code: `src/api/tracing.py`, called once from `create_v2_app()` in `src/api/server.py`, after `RequestDurationMiddleware`.

## Off by default

Tracing is on only when `OTEL_EXPORTER_OTLP_ENDPOINT` is set to a non-blank value (compose passes it, empty by default). While it is unset or blank, `setup_tracing` returns at once: no opentelemetry SDK, instrumentation or exporter module is imported, and no provider, middleware, instrumentor, sampler or log hook is installed. Log lines are byte-identical to a build without tracing.

## Environment

| Variable | Meaning | Default |
|---|---|---|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP base URL; on/off switch | unset (off) |
| `OTEL_SERVICE_NAME` | `service.name` resource | `rpg-backend` |
| `OTEL_TRACES_SAMPLER_ARG` | head-sampling ratio, 0 to 1 (an invalid value falls back to the default) | `0.1` |

Other standard `OTEL_EXPORTER_OTLP_*` variables are read by the exporter itself.

## Protocol and port

OTLP over HTTP/protobuf, port **4318** (e.g. `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318`; the exporter appends `/v1/traces`). Tempo enables both receivers (docker/tempo.yaml); HTTP avoids `grpcio`, a large native wheel, in the API image.

## What is traced

- **Server spans**, one per HTTP request, named and attributed (`http.route`) by the route template, never the raw path.
- **Redis client spans**, from instrumenting the redis library before any client is created, so the lazily built stream-adapter client is covered. A Redis call is traced only when it has a parent span. Reachable touchpoints: `observability/stream/adapters.py:139` (the `/api/v1/observability/live/stream-health` route in `routes/live_health.py` is a request path, so it gets a child span); the event-recorder publish thread (`event_recorder.py:176`) and the broker quality feed consumer (`observability/stream/consumer.py:54`) have no request parent, so they record nothing rather than a root span per event. The anomaly worker's clients (`lag_metrics.py:90`, `anomaly/worker.py:213`) are another process.
- **Sampling**: `ParentBased(TraceIdRatioBased(r))`, plus the rule that a root CLIENT span is dropped.

## Log correlation

While a span is active, log records carry `trace_id` (32 hex) and `span_id` (16 hex) (a log record factory installed by the tracing setup). `src/logging/formatter.py` prints them:

- plain lines: ` trace_id=<hex> span_id=<hex>` appended;
- JSON lines (`--json-logs`): keys `"trace_id"` and `"span_id"`.

Uvicorn's own access lines are emitted outside any span and carry nothing. The container logs plain text today (`serve` without `--json-logs`).

## Engine boundary

No module under `src/engine`, `src/core`, `src/systems` or `src/domains` imports opentelemetry (`tests/unit/api/test_tracing_engine_boundary.py`, an `ast` scan). The wider set is guarded because the deterministic tick calls into those packages.

## Handoff for TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF (platform)

- Log field: `trace_id` (and `span_id`). Loki `derivedFields` `matcherRegex` for the plain format: `trace_id=(\w+)`; for JSON: `"trace_id":\s*"(\w+)"`.
- Sampling variable: `OTEL_TRACES_SAMPLER_ARG` (default 0.1, i.e. 10%). A proof run that must see a trace should set it to `1`.
- Port: OTLP HTTP 4318 (`OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318`).
- A trace shows a server span named by route template; `/api/v1/observability/live/stream-health` shows a child Redis span when the stream backend is `redis`.
