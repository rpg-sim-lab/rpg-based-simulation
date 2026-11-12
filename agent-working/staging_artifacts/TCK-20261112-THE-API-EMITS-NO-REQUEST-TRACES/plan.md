---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261112-THE-API-EMITS-NO-REQUEST-TRACES
artifact_type: plan
tags: [observability, api-design]
---

# Plan

Order: (1) deps and lock; (2) src/api/tracing.py; (3) log filter; (4) tests; (5) docs and handoff; (6) hash cell when rpg-planner grants HOST FREE. Nothing is pushed; push and merge are owner asks. The pyproject/uv.lock diff goes to rpg-planner before any push ask.

## Decisions
- D1 No-op when off. `setup_tracing(app)` reads `OTEL_EXPORTER_OTLP_ENDPOINT`; unset or blank returns at once, importing no opentelemetry SDK module and installing no middleware, provider, instrumentor or log filter. Imports of the SDK sit inside the on-path function.
- D2 Redis spans only with a parent (rpg-planner ruling 2026-11-12). Site 1b publishes once per event envelope on the recorder drain thread; rooting those would flood at 10%. A custom sampler inside the tracing module: a root span (no valid parent) of kind CLIENT is dropped; everything else follows `ParentBased(TraceIdRatioBased(r))`. event_recorder, feed.py and adapters.py are not edited. Sites 1b and 2 are covered when parented, never as roots.
- D3 Sampling: `OTEL_TRACES_SAMPLER_ARG` ratio, default 0.1; bad or out-of-range values fall back to 0.1.
- D4 Exporter: OTLP HTTP/protobuf, 4318. Tempo enables both receivers, so the lighter wheel set wins (no grpcio, a large native wheel in the API image). The endpoint is the standard `OTEL_EXPORTER_OTLP_ENDPOINT` compose already passes.
- D5 Redis instrumentation is called from setup, before any `from_url`.
- D6 Log correlation: field names `trace_id` (32 hex) and `span_id` (16 hex). Changed in implementation from the approved handler filter: the tracing setup installs a `logging` record factory (only when tracing is on), because uvicorn builds its handlers after `create_v2_app()` returns, so a handler filter cannot reach them, and uvicorn's access lines are emitted after the server span has ended. The factory sets the attributes only when a valid span is active. `formatter.py` prints them: JSON adds the keys; plain (`TraceAwareFormatter`) appends ` trace_id=… span_id=…`. With tracing off no factory is installed, so both formats are byte-identical.
- D7 Span names use the route template (instrumentor's own naming with the FastAPI app; unmatched routes tested).
- D8 Engine boundary test: static `ast` scan that no module under `src/engine/**` imports `opentelemetry`. Widen to `src/core/**`, `src/systems/**` and `src/domains/**`: yes. The risk is not the engine folder alone; the tick calls into those packages, and an import there would put tracing code on the deterministic path. They are the other simulation-side packages and today import no opentelemetry, so the wider test costs nothing now and keeps the promise.
- D9 Engine untouched: static argument plus one plain crowded_frontier s42 5000-tick hash match against main (ask rpg-planner for HOST FREE). The diff touches only src/api, src/logging/formatter.py, pyproject, uv.lock, tests, docs.

## Files
New: src/api/tracing.py, tests/unit/api/test_tracing.py, tests/unit/api/test_tracing_off.py, an engine-boundary test, docs section and a platform handoff note. Edited: src/api/server.py (one call), src/logging/formatter.py (print attrs), pyproject.toml, uv.lock.

## Acceptance map
Off no-op -> test_tracing_off. On: one server span by template, redis child span, ratio from env -> test_tracing. Logs on/off -> tests. Boundary -> scan test. Hash -> D9. Dep review and docs -> rpg-planner diff, docs.
