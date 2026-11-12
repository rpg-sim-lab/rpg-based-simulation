---
status: active
layer: platform
authority: P2
audience: agent
tags: [platform, observability]
---

# Loki named volume and the API dashboard, proved in one stack run (2026-11-12)

**Label: running locally** (VM host ubuntu). Tickets: `TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE` and `TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF` (one batch, one run; owner option A, #715 6819928388). Raw files: `agent-working/stored_artifacts/TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE/run-2026-11-12/` (run, guard, memory, logs) and `agent-working/stored_artifacts/TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF/run-2026-11-12/` (dashboard, trace, screenshots). Earlier record this follows from: [2026-11-11-compose-image-bumps.md](2026-11-11-compose-image-bumps.md), section 5.

## 1. Result in one paragraph
Loki accepted every push (Alloy sent 3,885 entries in 370 requests, all HTTP 204, 0 dropped, 0 retries) with its data in a named volume under `/data/docker/volumes`, and `LogShippingErrors` stayed inactive; the 2026-11-11 run lost every push. The dashboard `api-v1` loaded with no datasource or panel error, every panel query ran through Grafana, the p95 value agrees with a by-hand `histogram_quantile` in Prometheus, and one trace shows a server span (`http.route`) with a child Redis span. **Not shown in this run:** the Loki-line to trace round trip, because no backend line carried a `trace_id` (section 5); run A the same morning shows it (section 9). One run-only deviation was needed to get any 2xx (section 6). The run lasted 11 minutes 32 seconds (up 10:01:28Z, down 10:13:00Z), plus the build (10:00:04Z to 10:01:03Z). `down` without `-v`.

## 2. What changed (branch `platform-implementer-local-loki-volume-and-api-dashboard`)
- `compose.yaml`: loki gets `volumes: - loki_data:/loki` and `-ingester.wal-dir=/loki/wal`; top-level `loki_data`; backend passes `OTEL_TRACES_SAMPLER_ARG=${OTEL_TRACES_SAMPLER_ARG:-}`.
- `docker/grafana/dashboards/api.json` (new, uid `api-v1`), `docker/grafana/provisioning/datasources/datasource.yml` (Loki `derivedFields`), `docs/runbooks/log-shipping.md` (the Loki throttle symptom and the 85% gate).
- `tools/loadtest/stack_guard.sh`: a disk trigger, `MAX_DISK_PCT` (default 0, off) over `DISK_PATHS` (default `/ /data`). Proved in dry mode first (`dry/guard_disk_trigger.txt`: `WOULD DOWN ... /=72% /data=84%` at a 1% threshold; `dry/guard_quiet.txt`: silent at 99%). The real run used `MAX_DISK_PCT=90`.

## 3. The run (11 services, profile observability)
backend, redis, prometheus, grafana, loki, alloy, docker-socket-proxy, node-exporter, ntfy, redis-exporter, tempo; no watchdog, ai_worker or frontend. Started with `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318` and `OTEL_TRACES_SAMPLER_ARG=1` on the command, `--no-build --pull never`.

| Gate or step | Reading |
|---|---|
| Launch gate 09:59:18Z | loadavg1 0.36, MemAvailable 5,604 MiB, swap 2,245 MiB flat over three readings; `/` 72%, `/data` 84%. `docker system df` before: images 7.171 GB, volumes 5 (713.7 MB), build cache 641.7 MB. |
| Watcher | real mode from 09:59:51Z, 20 s interval: abort at MemAvailable < 1,500 MiB, swap > 7,500 MiB or `/` or `/data` at 90% or more. Never triggered: lowest MemAvailable 4,374 MiB, highest swap 2,487 MiB, highest disk 84% on `/data` and 73% on `/`. |
| Build | backend image `4613dfdaefb5`, created 10:00:40Z. Post-build gate: `/` 73%, `/data` 84%, under 85%, so the run went on. |
| After `down` | 0 platform containers, the other container on the host untouched, the six named volumes kept. `docker system df`: images 7.425 GB (16), volumes 665 MB (6), **build cache 2.039 GB (31 entries, 1.426 GB reclaimable), up from 641.7 MB**: the backend build grew it by about 1.4 GB. Left in place, no prune. Final `df`: `/` 73%, `/data` 84%. |

## 4. Loki
| Check | Result |
|---|---|
| Permissions on `/loki` and `/loki/wal` | No permission-denied line. The only error line in Loki's log is the usual start-up `error getting ingester clients ... empty ring` (`logs_loki.txt`). |
| Throttle | No `disk usage exceeded threshold` line, no `push (500)`, `/ready` 200. |
| Volume | `docker volume inspect platform_loki_data` Mountpoint `/data/docker/volumes/platform_loki_data/_data`. `docker diff platform-loki-1` is empty: nothing in the container layer. The host user cannot read Docker's volumes directory (root only), so the WAL directory itself was not listed; with the explicit `-ingester.wal-dir=/loki/wal` and an empty layer diff, it is in the volume. No `sudo` or `chmod` was used. |
| Formula on a second filesystem | `/data`: Blocks 25,721,923, Bfree 5,352,059, so `(Blocks - Bfree) / Blocks` = **79.19%** (df-style 83.01%), under 90%. This agrees with the earlier fit on `/` (a full `/` reads 94.8% because 5.14% of its blocks are reserved and counted as free). |
| Alloy to Loki, before the burst (10:02:42Z) | `loki_write_sent_entries_total` 673; 29 requests, all `204`; dropped 0; retries 0; Loki returned streams for 9 containers. |
| Alloy to Loki, at the end (10:12:38Z) | sent 3,885; 370 requests, all `204`; dropped 0; retries 0. |
| `LogShippingErrors` | inactive (it was Pending from 16:28:40Z in the 2026-11-11 run). |
| 9 of 9 Prometheus targets | up. Alerts at the end: all inactive except `AiWorkerLagHigh` (firing; ai_worker was not started, as in the earlier runs). |

## 5. Dashboard and trace
| Check | Result |
|---|---|
| Load (D1) | `api-v1` served by Grafana (provisioned from the file; a re-generated file was picked up within 15 s, version 1 to 2). All 12 data panels ran with no error (11 through `/api/ds/query`, the Tempo table through Grafana's Tempo proxy); the page text had no "datasource" or "not found". Screenshot `screens/dashboard_api-v1.png`. |
| Data (D2) | request rate by route and by status class, latency percentiles and p95 by route, logs (250 points) and the Tempo table (20 traces) all show data. As expected: "5xx ratio, overall" reads 0 (numerator `or vector(0)`); "5xx ratio by route" and the SLO row's "5xx ratio (value)" read No data (R2 creates a `status_class` series only when one is observed); the two SLO expression panels read "not violated". |
| p95 (D3) | the "p95 latency (value)" panel through Grafana = **0.00475 s**; the same expression run directly in Prometheus at the same instant = **0.00475 s** (10:07:08Z); they agree. (0.00475 is a bucket interpolation inside the 0.0025 to 0.005 bucket.) |
| Trace (D4) | trace id **`b97bc419c7316b64bb7a1d0ca976bf6a`**: a SERVER span `GET /api/v1/observability/live/stream-health` with `http.route` = `/api/v1/observability/live/stream-health` and status 200, and a CLIENT span `PING` (`db.system` = `redis`) whose parent is that server span (4 spans in all, two are `http send` internal spans). Screenshot `screens/trace_b97bc419c7316b64bb7a1d0ca976bf6a.png`. |
| Provisioning of the link | Grafana loaded the Loki `derivedFields` as `matcherRegex trace_id=(\w+)`, `datasourceUid tempo`, `url ${__value.raw}`: the `$$` escape in the provisioning file is correct. |
| **Round trip (D5): NOT shown** | The backend printed **0** lines carrying `trace_id=` in the whole run, so there was nothing for the derived field to match and the Tempo trace-to-logs query (`{container=~".*backend.*"} |= "<trace id>"`) returned 0 lines. Cause: a line carries a trace id only when it is logged while a span is active, and none of the routes the burst hit logs anything; uvicorn's access lines are emitted outside any span. The routes that do log at INFO inside the handler (`/api/v1/observability/search/*`) answered 429 (below). Supporting check only, on a synthetic record: the project's `TraceAwareFormatter` output `INFO:...:msg trace_id=<id> span_id=<id>` is matched by `trace_id=(\w+)` and yields the id; a line without a span does not match. This shows the regex fits the formatter, not that the link works live. **Run A (section 9) later showed the round trip.** |

## 6. Findings that were not in the plan
1. **The compose stack has no API key configured, so every route but `/health` answers 401 (fail-closed).** The first burst (10:03:01Z to 10:03:25Z; 40 rounds over 8 routes) got only 401s, so the 2xx latency panels and the Redis span could not be shown. With platform-planner's yes, the backend alone was recreated at 10:05:16Z with a run-only override file outside the repo that sets `RPG_API_KEY_HASHES` to the committed dev-only pair of `make dev` (`docs/architecture/http_api_key_authentication.md`, section 6: "not a real secret"; the override is in the evidence folder, the hash only). The raw dev key was sent through a `curl -K -` config on stdin, never on argv; a scan of both evidence folders finds neither it nor any other secret. The env name is `RPG_API_KEY_HASHES` (prefix `RPG_`, `src/config/loader.py`). A follow-up ticket is platform-planner's.
2. **Per-client admission control refused most of the authenticated burst, and a client that waits out `Retry-After` is still refused.** The second burst (10:05:55Z to 10:06:31Z; 60 rounds over the same 8 routes) got 200 for 39 requests and 429 for 381 (`checks_5_burst2_codes.txt`); `/health` answered 200 all 60 times. A 429 carries `retry-after=5`. The later probe (10:08:41Z, about 2 minutes after the burst ended) sent `observability/search/*` calls back to back, all 429, followed by a `/api/v1/manifest` call that answered 200. rpg-planner-ubuntu replayed `_check_admission` (`src/api/admission_control.py`): all routes share one bucket per API key, and recovery counts calls, not time, so a client that waited out the retry-after was still refused. That is tracked in rpg's `TCK-20261112-A-THROTTLED-CLIENT-THAT-WAITS-OUT-RETRY-AFTER-IS-STILL-REFUSED`. The engine's `Tick ... exceeded budget` warnings and the `WatchdogTrip` line on this VM do not feed admission. The 2xx samples were enough to fill the latency panels.
3. **Alloy's memory with working pushes is close to its limit: 246.7 of 256 MiB (96.4%) anon + active_file; `memory.current` reached 256.0.** In the failed 2026-11-11 run it was 225.9 (88%). With pushes working, 256m held (no OOM kill, 0 restarts), but the headroom is about 9 MiB over an 11-minute run, so a longer run may not hold. Whether to raise it (for example to 384m) is platform-planner's call; this ticket changed no `mem_limit`.
4. Other memory (anon + active_file max, MiB of limit): grafana 854.5 of 1024 (83.4%), ntfy 76.3 of 96 (79.5%), tempo 300.6 of 512 (58.7%), loki 130.4 of 512 (25.5%), prometheus 135.3 of 512, backend 128.6 of 1024. Nothing was OOM-killed.
5. The build cache grew about 1.4 GB in one build (section 3); left in place on lead's instruction.
6. The Tempo table panel (a `traceqlSearch` query, `tableType traces`) rendered 6 rows in the screenshot and 20 in the API search; its query shape worked on first try.

## 7. Dashboard change made during the run
The first screenshot showed "5xx ratio, overall" with a Y axis to 10000% around a flat zero line (an all-zero series autoscaled in `percentunit`). The two ratio panels now have a fixed range 0 to 1; Grafana picked the new file up, and the second screenshot is the final one. The static checks were re-run: the file parses, has no `id`, uses uids only, and the SLO expressions are still verbatim.

## 8. Not covered
- The logs-to-trace and trace-to-logs round trip in the first run (section 5): not observed there; **closed by run A (section 9)**, which used a route that logs inside a span and traffic paced at 1 request per second.
- A violating load (the SLO row has no negative control; step 3's Locust job would show it) and a real 5xx (no route to hit).
- The WAL directory listing inside the volume (root-only on the host; no shell in the Loki image).
- A longer run: 11 minutes 32 seconds, so the memory figures are a short-run peak.
- `docker volume`, image and build-cache cleanup, and freeing space on `/`: the owner's.

## 9. Run A: the trace and log round trip (same day, 10:28Z to 10:35Z)
Owner chose option A after the first run (#715); lead gave the slot. Branch `platform-implementer-local-loki-volume-and-api-dashboard` at `2d00aacfe` (the 384m alloy limit is in it). Evidence: `agent-working/stored_artifacts/TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF/run-2026-11-12-runA/`.

**Setup.** No rebuild: the backend image is the one built for the first run (`4613dfdaefb5`, created 10:00:40Z), and `src/` has not changed since (`git diff 731872b7f..HEAD -- src` is empty). Services: backend, loki, alloy, tempo, grafana, plus the ones they depend on (redis, docker-socket-proxy, and prometheus, which grafana waits for). `--no-build --pull never`, `OTEL_EXPORTER_OTLP_ENDPOINT=http://tempo:4318`, sampler 1, and the same run-only API-key override as section 6 (the key on stdin, redacted; a scan of the evidence finds none of the four secrets). Launch gate 10:28:02Z to 10:28:20Z: loadavg1 1.18 falling to 0.92, MemAvailable 5.65 to 5.71 GB, swap 2,424 to 2,423 MiB, `/` 73%, `/data` 84%. Watcher armed in real mode at 10:28:41Z (90% disk, 1,500 MiB, 7,500 MiB swap); never triggered (lowest MemAvailable 3,973 MiB, highest swap 2,503 MiB, highest disk 84% on `/data`). Up 10:28:45Z, down (no `-v`) 10:35:33Z: 6 minutes 48 seconds.

**Traffic.** One probe to `/api/v1/observability/search/runs` at 10:30:01Z (200, and a backend line `... result_count=16 trace_id=... span_id=...`). Then, 12 seconds after the last request from my side (the planner asked for at least 10), 150 requests to the same route at 1 per second, 10:30:13Z to 10:32:48Z: **150 x 200, no 429** (`checks_2_traffic_codes.txt`). The backend printed 151 lines with `trace_id=` (150 plus the probe). In the first run no route that logs inside a span answered 2xx, which is why the round trip could not be shown there.

**Round trip, through the API (`checks_3_roundtrip.txt`).**
1. A Loki line: `INFO:api.observability.search:Search runs: scenario_name=ALL status=ALL sort=DEFAULT limit=50 result_count=16 trace_id=56016e92030d5e84ff01352c32300d29 span_id=98f122901ee789ad`.
2. The provisioned `derivedFields` (as Grafana loaded them: `matcherRegex trace_id=(\w+)`, `datasourceUid tempo`, `url ${__value.raw}`) capture trace id **`56016e92030d5e84ff01352c32300d29`**.
3. Tempo has that trace: 3 spans, a SERVER span `GET /api/v1/observability/search/runs` with `http.route` = `/api/v1/observability/search/runs` and status 200, and two internal `http send` children. (No Redis span: this route does not call Redis.)
4. Back: the Tempo datasource's `tracesToLogsV2` query (`{container=~".*backend.*"} |= "<trace id>"`) on Loki returns exactly 1 line, equal to the original, and every returned line carries the trace id.

**Round trip, through the UI (`checks_4_screens.txt`, `screens/runA_1` to `runA_6`).** Loki Explore showed the line (`runA_1`, `runA_2`); clicking the Tempo link on its `trace_id` field opened the trace (`runA_3`); the trace view opened by id (`runA_4`) and its **Related logs** button opened a Loki pane with the line (`runA_6`). My first script looked for a button named "Logs for this span", which this Grafana version does not have (`runA_5` is that failed attempt); the button is called "Related logs". The result of each click was checked in the page text, and the screenshots were taken at both ends.

**Alloy memory against 384m (the limit set after the first run).** anon + active_file max **189.4 MiB of 384 (49.3%)**; `memory.current` max 336.5, peak 339.4; no OOM kill, 0 restarts, in 6 minutes 48 seconds with 2,076 entries sent in 240 requests, all `204`, 0 dropped, 0 retries. This is a shorter run than the first (11.5 minutes, 246.7 of 256), so it supports the new limit but does not show it for an hour; the gap stays open. Others (anon + active_file max of limit, MiB): grafana 810.0 of 1024 (79.1%), tempo 280.9 of 512, loki 170.7 of 512, prometheus 114.8 of 512, backend 127.9 of 1024.

**After `down`.** 0 platform containers left; the other container on the host untouched; the six named volumes kept. `docker system df`: images 16 (7.425 GB), volumes 6 (666.8 MB), build cache 31 (2.039 GB, unchanged: no build this time). `df`: `/` 73%, `/data` 84%.

**What run A does not cover.** A run of an hour (the memory figure above); a route that fails (no 5xx was produced); the Tempo span-level "Logs for this span" link of other Grafana versions.
