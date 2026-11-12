---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF
phase: investigation
date: 2026-11-12
tags: [platform, observability]
artifact_type: investigation
---

# Investigation: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF

Read-only; no stack was started. Facts below are from the files at this branch's HEAD (which includes #891, R3, on origin/main 4226f3bfc).

## What exists

- **R2 metric** (`src/api/http_metrics.py`): one histogram, `http_request_duration_seconds{method, route, status_class}`, buckets `0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.3, 0.5, 1.0, 2.5, 5.0, 10.0` (an edge at 0.3, which the SLO needs). `route` is the matched route's TEMPLATE or the fixed label `unmatched`; `status_class` is `1xx..5xx` or `other`; `method` is one of a fixed set or `OTHER`. HTTP only (websockets are not timed). Scraped as job `rpg-backend`, target `backend:9109` (`docker/prometheus.yml`).
  - **No in-flight gauge exists.** The ticket says "in-flight requests, if R2 exports them": it does not, so that panel is out. Not a gap in this ticket; a gauge would be an `src/api` change (rpg).
  - Route cardinality is bounded by construction, so the ticket's stop condition ("if R2 ships raw paths") does not apply.
- **R3 tracing** (`src/api/tracing.py`, `docs/observability/api_request_tracing.md`): off unless `OTEL_EXPORTER_OTLP_ENDPOINT` is non-blank; OTLP HTTP on 4318; sampler ratio from `OTEL_TRACES_SAMPLER_ARG`, where **missing, blank or invalid gives the default 0.1** (read: `(environ.get(...) or "").strip()`). So an empty compose default is safe. Server spans carry `http.route` = the template. A Redis client span appears only with a parent span; `/api/v1/observability/live/stream-health` with the redis stream backend gives one. Log lines gain ` trace_id=<32 hex> span_id=<16 hex>` (plain format) while a span is active; the container logs plain text today.
  - Engine-boundary guard exists: `tests/unit/api/test_tracing_engine_boundary.py` (plus `test_tracing.py`, `test_tracing_off.py`).
- **compose.yaml, backend:** already passes `OTEL_EXPORTER_OTLP_ENDPOINT=${OTEL_EXPORTER_OTLP_ENDPOINT:-}` and `OTEL_SERVICE_NAME=rpg-backend`. It does **not** pass `OTEL_TRACES_SAMPLER_ARG` yet (that is this ticket).
- **Grafana provisioning:** datasources with fixed uids `prometheus`, `loki`, `tempo`. Tempo already has `tracesToLogsV2` (datasource `loki`, query `{container=~".*backend.*"} |= "$${__trace.traceId}"`) and `tracesToMetrics`. **Loki has no `derivedFields` yet.** Dashboards are loaded from `/etc/grafana/dashboards` by a file provider (10 s poll); the only dashboard today is `simulation.json` (uid `sim-v2`, 25 panels, no top-level `id`).
- **Loki labels** (Alloy relabel): `container` (container name) and the compose service label; the Tempo-to-Loki query already filters on `container`.
- **SLO source of truth** (`docker/grafana/provisioning/alerting/rules-slo.yaml`): latency `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{status_class="2xx",route!~"/health|unmatched"}[5m]))) > 0.3`; error ratio `sum(rate(http_request_duration_seconds_count{status_class="5xx"}[5m])) / sum(rate(http_request_duration_seconds_count[5m])) > 0.01`. Both carry their comparison and return a series only while violated.

## Consequences for the design

1. The SLO row on the dashboard must use these two expressions verbatim (incl. the comparison) in dedicated stat/time-series panels, so the dashboard shows "violated" as a series and cannot drift from the alert.
2. Because the SLO expressions return nothing while healthy, the SLO row needs a companion panel with the same expression minus the comparison (clearly titled as the un-thresholded value) so there is something to see. That minus-the-comparison query is derived from the rule, not copied; the test plan checks both.
3. Latency and error panels for the main view use the same selectors (`status_class="2xx"`, `route!~"/health|unmatched"`) so the numbers agree with the alert's.
4. The Loki-to-Tempo link needs `derivedFields` with `matcherRegex` `trace_id=(\w+)`, `datasourceUid` `tempo`, `name` `trace_id`, and `url` `$${__value.raw}` (internal link). **Unverified** until the run: whether the field renders as a link on the plain lines. The JSON-format regex is NOT added (the container does not print JSON).

## Open / unverified, settled only by the shared run

- Whether every panel shows data after a short burst (the burst must hit routes of both 2xx and, for the error panel, something that returns 5xx; there may be no 5xx route to hit: see the plan, risk 2).
- The trace and its Redis child span; the trace-to-logs and logs-to-trace round trip.
- The p95 panel value against the same `histogram_quantile` run by hand in Prometheus (both recorded).
