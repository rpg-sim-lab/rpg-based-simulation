---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF
phase: plan
date: 2026-11-12
tags: [platform, observability]
artifact_type: plan
---

# Plan: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF

Standard tier. Runs second in the batch, after TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE; both share ONE proof run (owner, option A, #715 6819928388). Review: platform-planner, before any edit under `docker/` or `compose.yaml`. No stack run, build or pull until the plans are reviewed AND lead gives the heavy-slot go.

## Changes

1. **`docker/grafana/dashboards/api.json`** (new). Fixed `uid` `api-v1`, title `API (requests, errors, latency, logs, traces)`, no top-level `id`, datasources by uid only (`{"type": "...", "uid": "prometheus|loki|tempo"}`), `schemaVersion` as in `simulation.json`'s Grafana generation, refresh 10 s, default range 30 min. Template variables: `route` (multi-select, `label_values(http_request_duration_seconds_count, route)`, All by default), `status` (multi-select on `status_class`), `level` (custom, for the Loki panel). Rows and panels:
   - **Requests:** rate by route (`sum by (route) (rate(http_request_duration_seconds_count{route=~"$route",status_class=~"$status"}[$__rate_interval]))`).
   - **Errors:** 5xx ratio overall and by route (same `5xx / all` shape as the alert).
   - **Latency:** p50, p95, p99 overall and by route (`histogram_quantile` over `_bucket`, with the SLO selectors `status_class="2xx",route!~"/health|unmatched"` for the "SLI" lines).
   - **Backend logs:** Loki `{container=~".*backend.*"} |~ "$level"` (logs panel).
   - **Traces:** a Tempo search panel for `service.name=rpg-backend`.
   - **SLO row (`slo`):** stat panels holding the two alert expressions VERBATIM from `rules-slo.yaml`, plus two companion panels with the same expressions minus ` > 0.3` / ` > 0.01`, titled "(value)". One panel description states: "these expressions are the alert's; edit `rules-slo.yaml` first".
   - **No in-flight panel** (R2 exports none; investigation).
2. **`docker/grafana/provisioning/datasources/datasource.yml`:** on Loki add `jsonData.derivedFields: [{name: trace_id, matcherRegex: 'trace_id=(\w+)', datasourceUid: tempo, url: '$${__value.raw}'}]`. (Escaping `$$` as in the Tempo block, since provisioning expands env vars.) Not adding the JSON regex.
3. **`compose.yaml`, backend env:** `- OTEL_TRACES_SAMPLER_ARG=${OTEL_TRACES_SAMPLER_ARG:-}` next to the other OTEL lines; a comment that blank means the code default 0.1 (checked in `src/api/tracing.py`) and that a proof run sets it to 1.
4. **Record** shared with the Loki ticket: `docs/runbooks/records/2026-11-1x-loki-volume-and-api-dashboard.md`: the run, trace id, panel values, screenshots path.
5. **Doc:** a short pointer in `docs/observability/api_request_tracing.md`? No: that doc is rpg's. Put the "how to open the dashboard and follow a trace" paragraph in the record and in `docs/runbooks/` only if a runbook for the dashboard already exists; otherwise the record is the doc. (Check at implementation.)

## Out of scope (as in the ticket)

Alert rules, ntfy, runbooks (step 3); changes to `simulation.json`; load; an in-flight gauge (an `src/api` change for rpg: I will name it in the record, not build it).

## The shared proof run (one run, after plan review and lead's slot go)

Order: (1) build the backend image first; (2) `df` and `stat -f` on `/` and `/data`, stop before `up` if either `df` is 85% or more; (3) start `--profile observability` with `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318` and `OTEL_TRACES_SAMPLER_ARG=1`, the abort watcher and sampler on, outputs under `/data`; (4) Loki checks first (Loki test plan T1 to T3); (5) a short fixed burst by `curl` loop to a few read endpoints and `/health` (not Locust); (6) dashboard and trace checks (test plan D1 to D6); (7) screenshots and the trace id into stored artifacts; (8) `down` without `-v`. Docker volume and image cleanup is the owner's.

## Risks

1. **Panels with no data.** The burst has no 5xx, and R2 creates a `status_class` series only when a request of that class is observed, so the numerator of any 5xx ratio has no series. Answer (platform-planner review): "5xx ratio, overall" wraps its numerator in `or vector(0)` and reads 0; "5xx ratio by route" and the SLO row's "5xx ratio (value)" are left as they are and read No data, the latter because it must match the alert's query. The acceptance text "every panel shows data" is therefore met for all panels except those two, and the record says so. No errors are faked; a real 5xx needs a route that returns one (rpg's).
2. **`derivedFields` not rendering as a link** on plain lines: fall back to a manual Tempo search by trace id; record it as a limit.
3. **Sampler.** At the default 0.1 a short burst may show no trace; hence `=1` in the run.
4. **Dashboard JSON written by hand** can have Grafana-version drift; the file provider loads it unchanged, and the test plan opens it in the running Grafana to catch "datasource not found" and panel errors.
