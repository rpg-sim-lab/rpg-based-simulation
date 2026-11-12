---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261112-THE-API-EMITS-NO-REQUEST-TRACES
artifact_type: investigation
tags: [observability, api-design]
---

# Investigation: API request traces (#622 R3)

Base: origin/main 5e58ae857. Owner approval: #715 6813227854; scope decision #715 6789636164. Line numbers are from that base.

## Where the hook goes
- `create_v2_app()` in src/api/server.py adds `RequestDurationMiddleware` last (:191, "outermost"). Tracing setup is called right after it, so the server span wraps the whole stack including the duration middleware.
- `src/api/http_metrics.py` is the pattern: an ASGI middleware, a module-level `route_template(scope)`, no-ops when inactive.

## Redis touchpoints (all `redis.from_url` sites in src; engine has none)
| # | Site | Reached from the API process? | Covered by |
|---|---|---|---|
| 1a | observability/stream/adapters.py:138-139 (`RedisStreamAdapter._connect`), via factory.py:29; routes/live_health.py:11,:29 `get_stream_health()` calls `adapter.health()` | yes, inside a request | child span (parent = request span) |
| 1b | same adapter, `publish()` from event_recorder.py:160,:176 on the recorder drain thread | yes, but no request parent | covered when parented, never root (decision D2) |
| 2 | observability/stream/consumer.py:54-55 (`RedisStreamConsumer.connect`), used by simulation_quality/feed.py:77 `BrokerQualityFeed.start`, built by engine kernel.py:234 via simulation_quality/wiring.py, only when `QUALITY_FEED_MODE=broker` | only in broker mode; background thread | covered when parented, never root (D2) |
| 3 | observability/stream/lag_metrics.py:90 | no: anomaly worker process only (anomaly/worker.py:426-428) | out of the API process |
| 4 | observability/anomaly/worker.py:213 consumer | no: separate worker process | out of the API process |

No other redis import or client in src. `opentelemetry-instrumentation-redis` patches the redis library, so one `RedisInstrumentor().instrument()` covers every client created in the process, as long as it runs before the first `from_url`. The adapter singleton is created lazily on first `get_event_stream_adapter()`, after app creation.

## Log format today
- `src/logging/formatter.py::setup_v2_logging(level, json_format=False)`; called from src/cli/entry.py:274 in `_run_serve`. Container CMD is `python -m src serve --host 0.0.0.0 --port 8000` (docker/backend.Dockerfile:64); compose.yaml:162 `command: serve` passes no `--json-logs`.
- Default is plain: `%(levelname)s:%(name)s:%(message)s`. JSON mode (`JsonFormatter`) emits message, timestamp, level, component, plus tick/component/worker_id/entity_id and `record.extra`.
- `ContextFilter` is a handler filter that copies thread-local context onto the record; it is the existing pattern for adding record fields.
- `uvicorn.run(..., log_level=...)` (entry.py:290) leaves uvicorn's own `uvicorn`, `uvicorn.error`, `uvicorn.access` loggers/handlers in place.
- So the container logs plain text today; a Loki `derivedFields` regex needs a printed token.

## Exporter
docker/tempo.yaml:7-13 enables both OTLP receivers (grpc 0.0.0.0:4317, http 0.0.0.0:4318). Compose passes `OTEL_EXPORTER_OTLP_ENDPOINT` (empty default) and `OTEL_SERVICE_NAME=rpg-backend` (compose.yaml:46-47). Choice: OTLP HTTP/protobuf, port 4318 (D4).

## Dependencies
`uv lock` result (uv.lock, base 5e58ae857). One existing package moves: opentelemetry-api 1.45.1 -> 1.45.2 (fastapi's transitive; the SDK 1.45.2 needs it). anyio and cffi appear twice in the lock (resolution forks) and are unchanged. 16 packages are added, each with the package that requires it (from uv.lock dependency entries):
| Added | Required by |
|---|---|
| opentelemetry-sdk 1.45.2 | project; opentelemetry-exporter-otlp-proto-http; opentelemetry-exporter-otlp-common |
| opentelemetry-exporter-otlp-proto-http 1.45.2 | project |
| opentelemetry-instrumentation-fastapi 0.66b2 | project |
| opentelemetry-instrumentation-redis 0.66b2 | project |
| opentelemetry-instrumentation-asgi 0.66b2 | instrumentation-fastapi |
| opentelemetry-instrumentation 0.66b2 | instrumentation-asgi, -fastapi, -redis |
| opentelemetry-util-http 0.66b2 | instrumentation-asgi, -fastapi |
| opentelemetry-semantic-conventions 0.66b2 | instrumentation, -asgi, -fastapi, -redis, sdk |
| opentelemetry-exporter-otlp-proto-common 1.45.2 | exporter-otlp-proto-http |
| opentelemetry-exporter-otlp-common 0.66b2 | exporter-otlp-proto-http |
| opentelemetry-exporter-http-transport 0.66b2 | exporter-otlp-proto-http |
| opentelemetry-proto 1.45.2 | exporter-otlp-proto-common, exporter-otlp-proto-http |
| googleapis-common-protos 1.76.0 | exporter-otlp-proto-http |
| protobuf 7.36.2 | googleapis-common-protos, opentelemetry-proto |
| wrapt 2.5.2 | instrumentation, instrumentation-redis |
| asgiref 3.13.0 | instrumentation-asgi |
No grpcio. starlette stays >=1,<2. The two odd names (exporter-otlp-common, exporter-http-transport) are required only by exporter-otlp-proto-http 1.45.2 in this lock; whether they are genuine upstream packages is for the dependency review to confirm against PyPI.

## Engine independence (for the hash argument)
The engine run path (`src/engine`) and the rpg_measure runners do not import `src.api` for a plain tick run; the plan states a static argument plus one hash cell. The scan test checks it.

## Open items
None blocking. Unknown until built: the exact FastAPI instrumentor span name for unmatched routes (test pins it).
