---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF
phase: inprogress
date: 2026-10-18
tags: [platform, observability]
---

# TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF

## Title
Grafana: one provisioned API dashboard (rate, errors, latency percentiles by route, backend logs, trace links), and the step-2 end-to-end local proof

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Step 2's deliverable: "one API dashboard (metrics and logs) and one request trace". The dashboard reads R2's request
histogram (scraped by `TCK-20261018-SCRAPE-BACKEND-METRICS-PORT`), Loki's backend logs, and links to Tempo traces
(`TCK-20261018-TEMPO-TRACE-BACKEND`). Step 3's SLO alert and load test read the same panels, so their queries are the
reference for the alert rule.

## Scope
- **`docker/grafana/dashboards/api.json`**, provisioned by the existing file provider. Fixed `uid`, datasources by uid
  (`prometheus`, `loki`, `tempo`), no hard-coded instance values. Panels:
  - request rate by route;
  - error ratio, 5xx over all requests, by route and overall;
  - latency p50/p95/p99 via `histogram_quantile` over R2's buckets, overall and by route;
  - in-flight requests, if R2 exports them;
  - backend container logs from Loki, filtered by a level variable;
  - a link from a log line to its trace (Loki `derivedFields`, from the Tempo ticket), and a Tempo search panel for
    `service.name=rpg-backend`.
- **`docker/grafana/provisioning/datasources/datasource.yml`**: add `derivedFields` on the Loki datasource. Its name is
  `trace_id`, its `datasourceUid` is `tempo`, and its `matcherRegex` is `trace_id=(\w+)`, for the plain log format the
  container prints today. The JSON-format regex is `"trace_id":\s*"(\w+)"` (`docs/observability/api_request_tracing.md`,
  handoff section). Add it only if the container switches to `--json-logs`.
- **`compose.yaml`**, backend environment: pass `OTEL_TRACES_SAMPLER_ARG=${OTEL_TRACES_SAMPLER_ARG:-}`, empty by default.
  Check in R3's code how an empty value is handled: the doc says an invalid value falls back to 0.1.
- Template variables: `route` and `status` (multi-select), derived from labels.
- **One file holds the PromQL** that step 3's SLO rule reuses (the p95 query and the error ratio), for example a
  "SLO" row with the exact expressions, so the alert and the dashboard can't drift apart.
- **End-to-end proof** (one stack run, after asking lead-planner):
  - rebuild the backend image first (src changed in #891). Then check `df` on `/` and `/data`. If either is at 85% or
    more, stop before starting the stack and report;
  - start `--profile observability` with `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318` and `OTEL_TRACES_SAMPLER_ARG=1`
    (the default 0.1 can show no trace for a short burst);
  - check that Loki accepts pushes before the burst: Alloy `loki_write_sent_entries_total` > 0 and no 500s. This is the
    proof for TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE in the same run;
  - send a short fixed burst of requests to a few read endpoints and `/health` (curl loop, not Locust);
  - open one request's trace in Tempo: a server span named by the route template (`http.route`), and, for
    `/api/v1/observability/live/stream-health` with the redis stream backend, a child Redis client span. R3 traces a
    Redis call only when it has a parent span;
  - go from the trace to its log lines in Loki, and back;
  - screenshot the dashboard with data. Store the screenshots and the trace id in this ticket's staging artifacts.

## Out of Scope
- Alert rules, ntfy, the runbook (step 3).
- Fixing or removing panels of the existing `simulation.json`.
- Load (step 3). The burst here only makes the panels non-empty.

## Acceptance Criteria
- After a fresh `--profile observability` start, the dashboard loads with no "datasource not found" and no panel
  errors (**running locally**).
- Every panel shows data after the burst. The p95 panel's value matches the same `histogram_quantile` run in
  Prometheus by hand (record both values).
- One request trace is shown end to end (trace id recorded): Grafana → Tempo → Loki line → back to the trace.
- R3's engine-boundary test exists and passes: `tests/unit/api/test_tracing_engine_boundary.py` (an `ast` scan covering
  `src/engine`, `src/core`, `src/systems` and `src/domains`).
- One trace shows a server span and a child Redis span (stream-health), and the trace id is recorded.
- `python3 -c "import json; json.load(open('docker/grafana/dashboards/api.json'))"` passes, and the dashboard JSON has
  no `id` field and no datasource names, only uids.
- (amended 2026-10-19) The dashboard's "SLO" row uses exactly the PromQL of `docker/grafana/provisioning/alerting/rules-slo.yaml`
  (`TCK-20261018-API-SLO-ALERT-NTFY-RUNBOOK`, the single source). The test plan proves it with a jq/grep equality check of the expressions (no `tests/**`).

## Related Tickets
Was the last child of epic `TCK-20261018-EPIC-DEVOPS-STEP2-OBSERVABILITY-LOCAL`. That epic closed on 2026-10-27, with this
ticket split out into its own folder (owner choice; rpg-planner-ubuntu confirmed R3 has no date). Already on main:
`TCK-20261018-TEMPO-TRACE-BACKEND`, `TCK-20261018-SCRAPE-BACKEND-METRICS-PORT` and rpg's R2 (request histogram).
Unblocked 2026-11-12: rpg's R3 (#622) merged as #891 (3cd1c4fdd; #715 6819697911), and lead-planner verified it is an
ancestor of main. Owner dispatch yes, option A (#715 6819928388): one batch with
TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE. Loki goes first, then this ticket, then ONE proof run for both
with the 85% disk gate. The run needs its own heavy-slot go from lead-planner. Run in full, trace panels included (owner
on #622, 6789636164).

## Related Docs
`docs/observability/api_request_tracing.md` (R3's handoff: port, sampler, regexes), `docs/architecture/devops_plan_amendment_proposal.md` (step 2), `docs/architecture/devops_baseline_adr.md` (D4, D7)

## Related Stored Artifacts
None yet. Screenshots and the trace id go to this ticket's staging artifacts.

## Related Code Areas
`docker/grafana/dashboards/api.json` (new), `docker/grafana/provisioning/**`

## Assumptions / Open Questions
- Route-label cardinality is R2's job (templates, not raw paths). If R2 ships raw paths, stop and report to
  platform-planner; don't work around it with `label_replace`.

## Implementation Notes
(open)

## Test Summary
(open)

## Files Changed
(open)

## Completion Summary
(open)
