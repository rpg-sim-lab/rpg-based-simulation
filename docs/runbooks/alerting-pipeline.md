---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Runbook: alerting pipeline (PrometheusUnreachable, GrafanaAlertingFailures)

## PrometheusUnreachable
Rule: the query `vector(1)` against the `prometheus` datasource, for 2m. `execErrState: Alerting` on purpose: when Grafana cannot query Prometheus the query errors, and that error is the signal. `noDataState: OK`. Severity critical.
1. `docker compose --profile observability ps prometheus` and its logs.
2. Grafana, Connections, Data sources, Prometheus, Test.
3. `http://127.0.0.1:9090/-/healthy`.

Fix: restart Prometheus (`docker compose --profile observability up -d prometheus`); check its `mem_limit` and the `prometheus_data` volume.

## GrafanaAlertingFailures
Rule: `increase(grafana_alerting_rule_evaluation_failures_total[5m]) + increase(grafana_alerting_notifications_failed_total[5m]) > 0`, for 0s (a failure is rare and worth a message at once). `noDataState: OK`, `execErrState: OK`. Severity warning. Scraped from Grafana's own `/metrics` (job `grafana`).
1. Grafana, Alerting, Alert rules: which rule shows an Error state, and its error text.
2. Grafana, Alerting, Contact points: the ntfy contact point's last delivery error.
3. `docker compose --profile observability logs --tail=100 grafana ntfy`.

## Known limit
If the notifier itself is broken (ntfy down or the token invalid), `GrafanaAlertingFailures` cannot reach ntfy; the Grafana alert state is the only trace. Check the Alerting UI (`http://127.0.0.1:3000/alerting`) when you suspect silence. `TargetDown` for `ntfy` goes through the same broken path.

## Proof runs without ai_worker
A stack proof run that starts the named services (loki, redis, docker-socket-proxy, node-exporter, ntfy, redis-exporter, tempo, backend, alloy, prometheus, grafana) leaves out `ai_worker`, `watchdog` and `frontend`. On that path `AiWorkerLagHigh` is alerting by design from about 2 minutes after the start and stays alerting until `ai_worker` runs: the rule's `noDataState` is `Alerting` and `sim_stream_consumer_lag` has no series without the worker (see [ai-worker-lag.md](ai-worker-lag.md), "Why NoData fires the lag alert"). Do not change the rule to hide it; it is the signal that catches a dead worker.
- **Pre-fire check:** "nothing else alerting" means exactly one alerting instance, expected to be `AiWorkerLagHigh`. Without the Grafana API (it needs credentials) the name is inferred, not proven; the evidence is `grafana_alerting_alerts{state="alerting"}` = 1 on Grafana's `/metrics`, the rule evaluating on its 30 s interval in the Grafana log (`rule_uid=cause-ai-worker-lag`), and Prometheus showing every target up. `GrafanaAlertingFailures` is NOT the usual suspect: run its expression in Prometheus (it returns 0 when healthy).
- **Attribute delivery by the counter:** read ntfy's `ntfy_messages_published_success` (port 9091, `docker exec <ntfy container> wget -qO- http://127.0.0.1:9091/metrics`) before the fire. The standing alert is in its own group (`group_by` is `alertname, job`) and repeats only every 4 h, so the counter is flat until you fire; expect +1 at FIRING and +1 at RESOLVED (the resolved message follows within the 5 m `group_interval`). Anything else, report as observed.
- **Images:** `platform-ai_worker` and `platform-watchdog` are not built on this host (checked 2026-11-12), so `docker compose --profile observability up -d --no-build` fails with "No such image". Start the named services by listing them; 9 of 9 Prometheus targets are then up.
- **Seen in:** the 2026-11-12 ntfy fire test, `agent-working/stored_artifacts/TCK-20261112-ROTATE-LOCAL-NTFY-TOPIC/run-2026-11-12/`.

## Rotating the ntfy topic
The topic and the access token are gitignored secret files; to change the topic (owner-run, with no value printed), see [ntfy-topic-rotation.md](ntfy-topic-rotation.md).

## Silence and escalate
See the README. Escalate to the owner if ntfy delivery stays broken after a restart and a token check (`docker compose exec ntfy ntfy token list`).
