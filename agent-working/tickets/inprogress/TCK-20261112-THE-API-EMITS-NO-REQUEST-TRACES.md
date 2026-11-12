---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261112-THE-API-EMITS-NO-REQUEST-TRACES
phase: open
date: 2026-11-12
tags: [observability, api-design]
---

# TCK-20261112-THE-API-EMITS-NO-REQUEST-TRACES

## Title
The API emits no request traces: add OpenTelemetry server spans and Redis client spans, off unless an OTLP endpoint is set (#622 R3)

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This is issue #622's ask R3, from platform-planner and relayed by lead-planner: OTel ASGI middleware, plus Redis client spans, with 10% head sampling, and off when the OTLP endpoint is unset. The engine must import no tracing code. The owner's decision is #715 6789636164 (2026-11-11): file and run R3 after the current batch, keeping foundation-first order, "complete them without dropping any". rpg-planner filed this on 2026-11-12, after #884 closed that batch.

R1 (metrics port) and R2 (`RequestDurationMiddleware`, src/api/server.py:191) are on main. Platform's `TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF` (todos/devops-api-dashboard-trace/) is BLOCKED on this ticket. `TCK-20261018-TEMPO-TRACE-BACKEND` (done) deferred three items to R3:
- the log field that carries the trace id (for Loki `derivedFields`);
- the sampling variable;
- the exporter protocol/port (4317 gRPC vs 4318 HTTP).

Compose already passes `OTEL_EXPORTER_OTLP_ENDPOINT` (empty by default) and `OTEL_SERVICE_NAME=rpg-backend` to the backend.

## Scope
1. **One setup module in src/api** (for example `src/api/tracing.py`), called once from `create_v2_app()`, beside `RequestDurationMiddleware`.
   - When `OTEL_EXPORTER_OTLP_ENDPOINT` is unset or empty, it is a strict no-op: no provider, no middleware and no instrumentor installed. The opentelemetry SDK packages are not imported, so startup cost and behaviour don't change.
   - When it is set:
     - a TracerProvider with resource `service.name` from `OTEL_SERVICE_NAME`, defaulting to `rpg-backend`;
     - an OTLP exporter behind a BatchSpanProcessor;
     - FastAPI/ASGI server instrumentation, where the span name and `http.route` use the **route template**, never the raw path;
     - head sampling `ParentBased(TraceIdRatioBased(r))`, where r comes from the standard `OTEL_TRACES_SAMPLER_ARG` and defaults to 0.1.
   - Name the exporter protocol and port chosen (OTLP gRPC 4317 or HTTP 4318), with the reason. That closes the Tempo ticket's deferral.
2. **Redis client spans.** The API reaches Redis through `src/observability/stream/factory.py::get_event_stream_adapter` → `src/observability/stream/adapters.py:139` (`redis.from_url`), used for example by `src/api/routes/live_health.py:11`.
   - Instrument the redis client (opentelemetry-instrumentation-redis) when tracing is on, so a request that touches Redis gets a child span.
   - The investigation lists every Redis touchpoint reachable from the API process, with file:line, and confirms each is covered.
   - Redis is NOT out of scope (owner: "without dropping any").
3. **Log-trace correlation.** Backend log lines carry the active `trace_id` (and `span_id`) under one named field when tracing is on.
   - State the exact field name, because platform's Loki `derivedFields` entry reads it.
   - When tracing is off, the log format doesn't change.
4. **Engine boundary.** Add a test that no module under `src/engine/**` imports `opentelemetry`, checked by static import scan. Decide in the plan whether to extend it to `src/core/**`, `src/systems/**` and `src/domains/**`, and say why.
5. **Dependencies.**
   - Add the opentelemetry-sdk, OTLP exporter, FastAPI instrumentation and redis instrumentation packages as runtime dependencies of the API, in pyproject and uv.lock.
   - Pin versions compatible with the opentelemetry-api fastapi already pulls in (see TCK-20261018-STARLETTE-1X-ROUTES-STAY-AUTHENTICATED-AND-THE-ROUTE-WALK-SEES-THEM-580).
   - lead-planner reviews the pyproject/uv.lock diff.
6. **Docs.**
   - The env vars (endpoint, service name, sampler arg), the protocol/port, the log field and the off-by-default rule go in the API/observability docs that the docs search names.
   - Give platform a short handoff note for the API-DASHBOARD ticket: the log field name, the sampling variable and the port.

## Out of Scope
- Grafana dashboards, Loki `derivedFields`, Tempo config and compose changes (platform: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF).
- Tracing inside the engine tick, in any simulation code, or in workers outside the API process.
- Metrics (R1 and R2 are done) and alerts (step 3).
- Any change to simulation behaviour. A 5000-tick hash must be unchanged; see the acceptance criteria.

## Acceptance Criteria
- Off: with no endpoint set, `create_v2_app()` installs no tracing middleware, provider or instrumentor (tested), and the existing API tests pass unchanged.
- On: with an endpoint set and an in-memory exporter in tests:
  - a request yields one server span named by its route template;
  - a request that touches Redis yields a child redis span (tested with a fake or local redis, or the adapter's in-memory double, whichever the investigation shows is real);
  - the sampling ratio is honoured from `OTEL_TRACES_SAMPLER_ARG`, with a 0.1 default.
- Log lines carry the named trace-id field when tracing is on, and are unchanged when it is off (tested).
- The engine-boundary test exists and passes.
- One plain 5000-tick cell (crowded_frontier s42, pinned runner) hash-matches main, showing the engine is untouched. If the investigation shows the runner imports no API code, a static argument may stand in for this, with the plan saying so.
- The dependency diff is reviewed by lead-planner. The docs and the platform handoff note are written.

## Related Tickets
- TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF (platform, blocked on this)
- TCK-20261018-TEMPO-TRACE-BACKEND (done; deferred items listed above)
- TCK-20261018-SCRAPE-BACKEND-METRICS-PORT (R1)
- TCK-20261018-STARLETTE-1X-ROUTES-STAY-AUTHENTICATED-AND-THE-ROUTE-WALK-SEES-THEM-580 (opentelemetry-api is already a transitive dependency)

## Related Docs
- docs/runbooks/api-latency-slo.md
- docs/observability/ (the docs search names the exact files)
- GitHub issue #622 (R1-R3), #715 6789636164 (owner decision)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261018-TEMPO-TRACE-BACKEND/

## Related Code Areas
- src/api/server.py (`create_v2_app`, :111; `RequestDurationMiddleware` added at :191)
- src/api/http_metrics.py (`RequestDurationMiddleware`, :82, the pattern to follow)
- src/observability/stream/factory.py, src/observability/stream/adapters.py:139 (redis client)
- src/api/routes/live_health.py:11
- pyproject.toml, uv.lock

## Assumptions / Open Questions
- Whether the backend log format today is structured (JSON) or plain decides how the trace id is added. The investigation reads it.
- Whether any other Redis client is created in the API process apart from the stream adapter. The investigation lists them all.
- The line numbers are from main 5e58ae857.

## Implementation Notes
OpenTelemetry is a new runtime stack; lead-planner-u24 adds the tech-stack registry entry after R3 lands. Dependency diff approved by lead-planner-u24 at pyproject sha256 03fb919b…, uv.lock sha256 34ffcb76… (a change to either needs a fresh review). protobuf moves to a new major (7.x) and the image grows by the OpenTelemetry wheels (about 11 MB installed here); disclose both in the PR.
Owner approval to run: #715 6813227854; scope decision #715 6789636164. rpg-planner scope rulings of 2026-11-12 are in staging plan.md (D2: Redis spans only with a parent; D4: OTLP HTTP 4318; D6: trace_id/span_id log fields).

## Test Summary

## Files Changed

## Completion Summary
