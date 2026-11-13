---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Compose image bumps proven on the observability stack (2026-11-11)

**Label: running locally** (VM host ubuntu). Ticket: `TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF` (supersedes Dependabot #878). Raw files: `agent-working/stored_artifacts/TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF/run-2026-11-11/`. Owner go: #715 issuecomment-6801197149.

## 1. Result in one paragraph
Items 1 to 5 of the plan are shown, with one correction (Prometheus has no rule files) and **one red check that the bumps do not explain but that I did not resolve: Loki accepted no log push during the run, so Alloy dropped data and `LogShippingErrors` sat in Pending**. I stopped as the run plan says, took the project down without `-v`, and changed nothing. The run lasted 12 minutes 43 seconds (up 16:25:57Z, down 16:38:40Z), not the planned 25 to 30, because of the stop.

## 2. What changed
Four pins in `compose.yaml`, each `tag@sha256:<multi-arch index digest>`, read with `docker buildx imagetools inspect` on 2026-11-11 and equal to Dependabot #878's: `redis:8.10.3-alpine` (`sha256:71885d8c...fb80`), `prom/prometheus:v3.16.0` (`sha256:e0498764...0f06`), `binwiederhier/ntfy:v2.37.2` (`sha256:1875ddcf...2bd7`), `oliver006/redis_exporter:v1.97.0` (`sha256:f5f903fb...9b83`). The running containers' image ids matched these digests (`checks_2_rules_images.txt`). Release notes were read for ntfy v2.35.0 to v2.37.2, prometheus v3.16.0, redis 8.10.3 and redis_exporter v1.97.0. None needed a config change (details in the ticket's Implementation Notes).

## 3. The run (11 services, profile observability)
backend, redis, prometheus, grafana, loki, alloy, docker-socket-proxy, node-exporter, ntfy, redis-exporter, tempo. Left out: watchdog, ai_worker, frontend. The backend image did not exist locally, so it was built first (`build.txt`, image created 23:25 +07, after the last `src/` commit at 22:58 +07). `stack_guard.sh` was proven in dry mode first (`guard_dry.txt`: `WOULD DOWN` and 2 lines in the log), then ran in real mode with the defaults (1500 MiB available, 7500 MiB swap). It never triggered: lowest MemAvailable 4981 MiB, highest swap 3513 MiB (`guard.txt`).

| # | Check | Result |
|---|---|---|
| 1 | Prometheus targets | 9 of 9 up: alloy, grafana, loki, node-exporter, ntfy, prometheus, redis, rpg-backend, tempo (`checks_1`). |
| 1 | Rules | **Premise correction:** `docker/prometheus.yml` has no `rule_files`, and Prometheus `/api/v1/rules` returns 0 groups. The alert rules are Grafana-managed. Grafana loaded 11 rules in 4 groups, all health `ok`, none with a `lastError` (`checks_2`). Prometheus logged only the expected DNS errors for `ai_worker` (not started); Grafana logged one unrelated error for a missing `provisioning/plugins` directory. |
| 2 | Redis | `redis_instance_info{redis_version="8.10.3"}` = 1, `redis_up` = 1. |
| 3 | ntfy auth (v2.37.2 started healthy with `NTFY_BASE_URL` set, so the v2.36 config re-check passed) | Anonymous publish **403**, anonymous read **403**, publish with the Grafana write-only token **200**. Credentials went over stdin (`curl -K -`), the topic was never printed. A temporary read-only user was created for the read-back and deleted afterwards (`checks_4`). |
| 4 | Fire test | Stopped redis-exporter 16:29:22Z. `TargetDown{job=redis}` Pending 16:29:58, Alerting 16:31:59. ntfy received `[firing] TargetDown / Scrape target redis is down` (priority 4, tag `bell`) stamped **16:32:17Z**. Started redis-exporter 16:32:50; Normal at 16:33:55; ntfy `[resolved] TargetDown` stamped **16:37:17Z** (`fire_states.txt`, `checks_5`, `checks_6`). This closes the #786 gap "ntfy not re-proven", on ntfy v2.37.2. Two earlier messages also arrived through the same path at start-up: `[firing] AiWorkerLagHigh` (ai_worker not started) and `[resolved] TargetDown` for tempo. |
| 5 | Memory | Section 4. |

## 4. Memory (sampler every 10 s, 12 minutes; MiB; judged on anon + active_file)
| service | limit | anon max | anon + active_file max | memory.current max |
|---|---|---|---|---|
| ntfy | 96 | 19.9 | 24.9 | 86.5 |
| redis-exporter | 32 | 9.5 | 19.7 | 21.5 |
| prometheus | 512 | 106.8 | 137.4 | 292.4 |
| alloy | 256 | 64.3 | 225.9 | 256.0 |
| grafana | 1024 | 268.9 | 860.2 | 1024.0 |
| loki | 512 | 75.4 | 75.5 | 226.7 |
| backend, redis, tempo, node-exporter, docker-socket-proxy | | all well under their limits | | |

No container was OOM-killed or restarted. No `mem_limit` is changed by this ticket. Two to watch, not caused by the bumps: alloy used 88 percent of its 256m limit on anon + active_file while it was retrying failed pushes (section 5); grafana 84 percent, as in the earlier records.

## 5. Red check: Loki rejected every push
- Alloy's `loki_write_request_duration_seconds_count` shows **19 requests, all status 500**, and `loki_write_sent_entries_total` is 0; `loki_write_dropped_entries_total` reached 213 on one series. Loki logged zero `push (204)` lines. A Loki query for the last 10 minutes returned no streams.
- Loki's answer was `Ingester is shutting down` (500), first at 16:34:13Z. Before that, at start-up (16:28:00Z), Loki logged `wal.go:215 disk usage exceeded threshold, throttling writes usage_percent=94.80% threshold_percent=90.00%`. At 16:37 `df` showed /data at 83 percent used (17 GB free), and Docker's root is on /data. I did not find out where Loki's 94.8 percent comes from.
- Effect: `LogShippingErrors` went Pending at 16:28:40Z (its `for` is 10m, so it would have fired at about 16:38:40Z, the minute I took the stack down; I did not observe Alerting). Retries rate 0.034/s, dropped rate 0.71/s, sd-refresh failures 0.
- Not caused by this change as far as I can tell: Loki 3.7.9 and Alloy are not touched by the bumps. But I did not run the old pins for comparison, and the 2026-10-28 Alloy run shipped logs normally with /data at roughly 90 percent used, so the disk percentage alone does not explain it. **Open:** why Loki computes 94.8 percent and throttles. Tracked in `TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE` (platform-planner, option (a): the four bumped images are not on Loki's path, so the pins stay). **Answered 2026-11-12:** Loki's check is `(Blocks - Bfree) / Blocks` of the WAL filesystem, which counts root-reserved blocks as free; its data was in the container layer, which the containerd image store keeps on `/` (not `/data`), and `/` was full, so it read 94.8%. A named volume fixed it; see [2026-11-12-loki-volume-and-api-dashboard.md](2026-11-12-loki-volume-and-api-dashboard.md). The `/data` percentages above are not the figure Loki measured.
- Evidence: `checks_7` to `checks_12`.

## 6. Not covered
- The ticket's premise "Prometheus loads every rule file with no rule error" did not hold: this stack's Prometheus has no rule files, because the alert rules are Grafana-managed. Check 1 was therefore made on Grafana's rule API (11 rules, all health `ok`) plus the Prometheus logs.
- Log shipping end to end on this stack (section 5). The `TargetDown` check shows ntfy delivery; it says nothing about Loki.
- A 25 to 30 minute run: this was 12 minutes 43 seconds, so the memory numbers are a short-run peak.
- `DiskSpaceLow` and `LogShippingErrors` were Pending and `AiWorkerLagHigh` Alerting (no data) at the end, all expected for this stack on this host (disk at 83 percent, ai_worker not started) except the log-shipping one above.
- ntfy features that are off by default (the admin socket, UnifiedPush rate limits) were not exercised.
- 11 containers from other projects were running on the host and were not touched; `down` was scoped to the `platform` project and removed no volume.
