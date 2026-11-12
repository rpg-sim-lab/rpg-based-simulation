---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF
phase: test_plan
date: 2026-11-12
tags: [platform, observability]
artifact_type: test_plan
---

# Test plan: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF

Static checks first (no stack). D1 to D6 happen in the ONE shared run (see the plan; shares T1 to T4 of the Loki ticket).

## Static (before the run; all `tests/**`-free, as the ticket's amendment says)

- S1. `python3 -c "import json; json.load(open('docker/grafana/dashboards/api.json'))"` passes; the JSON has no top-level `id` key; a scan of every `"datasource"` object shows `uid` only, with values in {`prometheus`, `loki`, `tempo`}, and no datasource name string.
- S2. **SLO equality:** extract the two `expr:` values from `docker/grafana/provisioning/alerting/rules-slo.yaml` and assert each appears character for character as a panel `expr` in the dashboard's `slo` row (a short `python3` or `jq` + `grep -F` check; the exact command goes into the record). The companion "(value)" panels equal those strings minus the trailing comparison.
- S3. `docker compose --profile observability config -q` passes; the backend service renders `OTEL_TRACES_SAMPLER_ARG` (empty by default).
- S4. YAML parse of `datasource.yml`: Loki has exactly one `derivedFields` entry with `name: trace_id`, `datasourceUid: tempo`, and the regex `trace_id=(\w+)`.
- S5. `tests/unit/api/test_tracing_engine_boundary.py` exists and passes (R3's guard; the ticket's acceptance names it). The run is local and cheap: `pytest` that one file only.
- S6. Paths guard, REGISTRY no-drift, compose-hygiene tests pass.

## In the shared run

- D1. After a fresh start, open `api-v1` in Grafana (via `/api/dashboards/uid/api-v1` and by screenshot): no "datasource not found", no panel error state (check each panel's query result for errors with the Grafana API or the rendered page).
- D2. After the burst, every panel but the error-ratio-by-route shows data; the error-ratio "(value)" panel shows 0; the plan states why (risk 1).
- D3. p95 check: the dashboard's p95 panel value vs the same `histogram_quantile` run by hand in Prometheus at the same instant; record both numbers and the instant.
- D4. One request trace: its trace id recorded; a server span named by `http.route`; for `/api/v1/observability/live/stream-health` (redis stream backend) a child Redis client span.
- D5. Round trip: Loki log line (with `trace_id=`) to the trace via the derived field (or the manual fallback, recorded as such), and from the trace to its log lines via the Tempo `tracesToLogsV2` link, and back.
- D6. Screenshots of the dashboard with data stored as PNG in `agent-working/stored_artifacts/TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF/run-<date>/` with the trace id in a `.txt`; secret scan before commit.

## Limits to state in the record

No negative control for the SLO row (a violating load is step 3's Locust job, not run here); no in-flight panel (no metric); the dashboard was written by hand and loaded by the file provider only.
