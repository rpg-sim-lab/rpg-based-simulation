---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261112-THE-API-EMITS-NO-REQUEST-TRACES
artifact_type: test_plan
tags: [observability, api-design]
---

# Test plan

All with an in-memory span exporter and fakeredis-style double or a stub redis client (no network); single test files, `-n 1`.
1. Off: env unset and blank; `create_v2_app()` adds no extra middleware, `sys.modules` gains no `opentelemetry.sdk`, no `RedisInstrumentor` patch (`is_instrumented_by_opentelemetry` false), no log filter on any handler.
2. On, server span: a request to `/items/{id}` yields one SERVER span named by the template, `http.route` the template, never the raw path; an unmatched path does not leak the raw path.
3. On, redis: inside a request, a redis call yields a child CLIENT span; with no active span a redis call records nothing (D2); the adapter singleton created after setup is instrumented (D5); site 1b-style call on a thread with no span records nothing.
4. Sampling: ratio from `OTEL_TRACES_SAMPLER_ARG`; default 0.1; invalid falls back to 0.1; 1.0 records, 0.0 drops; parent-sampled children follow the parent.
5. Logs: off -> plain and JSON output byte-identical to today; on -> `trace_id=` / `span_id=` inside a request (plain) and keys (JSON), absent outside a request; uvicorn logger lines get it too.
6. Boundary: ast scan of src/engine, src/core, src/systems, src/domains for `opentelemetry` imports (and a self-test that the scanner detects a planted import in a temp tree).
7. Existing: tests/unit/api (test_http_metrics, characterization snapshot of create_v2_app routes/middleware) unchanged and passing.
8. Hash: plain crowded_frontier s42 5000 ticks, branch vs main, final hash equal (HOST FREE).
