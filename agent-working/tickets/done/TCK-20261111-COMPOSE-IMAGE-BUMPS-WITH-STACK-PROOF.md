---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF
phase: done
date: 2026-11-11
tags: [platform, observability]
---

# TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF

## Title
Take Dependabot #878's compose image bumps by hand, with their comments updated and a short stack proof run

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Dependabot #878 ("compose-minor-patch group with 4 updates", opened 2026-11-11 after #875) moves 4 pinned images in
`compose.yaml`. The owner decided on 2026-11-11 (#715 6800739670, item 3) to **hold #878** and take the bumps in a
platform hotfix instead, with the comments updated and a short proof run on the observability stack. There are two
reasons. compose.yaml says the redis pin moves with redis-py 8 and is "Bump deliberately". The redis_exporter comment
cites "this file's redis:8.10.2" as proven by a live run. A plain merge would leave both comments stale, and nothing
would have run the new versions together. #878 is superseded by this ticket (the user closes it).

## Scope
- `compose.yaml`, the same 4 image lines as #878, each still pinned `tag@sha256:<multi-arch index digest>`:
  - `redis:8.10.2-alpine` -> `8.10.3-alpine`
  - `prom/prometheus:v3.15.1` -> `v3.16.0`
  - `binwiederhier/ntfy:v2.34.0` -> `v2.37.2`
  - `oliver006/redis_exporter:v1.96.0` -> `v1.97.0`

  Verify each digest yourself: it must be the multi-arch index digest for that tag (`docker buildx imagetools inspect`
  or the registry API). Don't copy it from #878 unchecked. Note any mismatch with #878.
- Comments next to these lines: the redis block (version, digest verification date, still moving with redis-py 8),
  the redis_exporter block ("this file's redis:8.10.3 ... proven by the live run" now cites the new record), and the
  version and date mentions in the prometheus and ntfy blocks, where present. Change no `mem_limit` unless the proof run
  measures it over the limit. If it does, raise the limit with the measured anon and anon+active_file numbers in the
  comment, as the existing ones do.
- Read the upstream release notes for ntfy v2.35-v2.37.2 and prometheus v3.16.0. Record in the ticket any breaking or
  config-affecting change (ntfy auth/`auth-default-access`, the cache, the metrics listener; prometheus rule/scrape
  config). If one requires a config change, stop and report before making it.
- **Proof run** (heavy). It needs the owner's go through lead-planner before it starts. Use one slot, the abort watcher
  proven first, and the standing heavy-run rules: `down` without -v, outputs on /data. Keep it short (target 30 min or
  less). Bring up the stack with the observability profile as in the earlier records. Show:
  1. All Prometheus targets up, including `redis`, `ntfy` and `alloy`. Prometheus loads every rule file with no rule
     error (`/api/v1/rules` and the logs).
  2. `redis_instance_info` reports `redis_version=8.10.3`, and `redis_up` is 1.
  3. ntfy's deny-all auth still holds: an anonymous publish is refused (403), and the authenticated test publish is
     accepted. Credentials come over stdin and are never printed or put on argv.
  4. One real alert notification reaches ntfy end to end, through a short, safe fire test such as the earlier
     records' (for example stop redis_exporter until `TargetDown` fires, then restart it). This also closes the #786
     gap "ntfy not re-proven".
  5. Memory for ntfy (96m), redis_exporter (32m) and prometheus (512m): anon and anon+active_file, read against each
     limit.
- Record: `docs/runbooks/records/2026-11-<dd>-compose-image-bumps.md`, in the shape of the earlier records. Evidence in
  `agent-working/stored_artifacts/TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF/` (.txt/.jsonl, not .log/.json).
- **Ride-along** (#715 6793205403): on the done ticket `TCK-20261111-DEPENDABOT-WATCHES-WEBSITE`, replace its
  "Known gap:" line with an observed line. The /website entry fired 2 minutes after #875 merged: #879, one grouped PR
  "npm-minor-patch group in /website", labels [dependencies, platform]. So the config is valid and the first run is OK.

## Out of Scope
- Merging or closing #878 or any other Dependabot PR (user).
- `tests/perf/test_simq_isolation_overhead.py` line 17, which cites the old redis digest in a manual proof command.
  It's not platform's file, so platform-planner tells perf-planner instead.
- Historical records (`docs/runbooks/records/2026-10-*`): they stay as written.
- The Dependabot docker-group change for digest-only updates (`patterns: ["*"]`). The docs don't say whether it works.
- Image bumps beyond these 4.

## Acceptance Criteria
- `compose.yaml` has the 4 new pins, each a verified multi-arch index digest, and `docker compose config` parses
  (validated).
- No comment in compose.yaml still names a replaced version as current (validated by grep).
- Release-note check recorded, with no unhandled breaking change (validated).
- Proof run items 1-5 shown in the record, with the watcher evidence (observed). If the owner doesn't give the go, the
  ticket stays open with the code change ready, and it does not close.
- Ride-along line on the done ticket.

## Related Tickets
- TCK-20261111-DEPENDABOT-WATCHES-WEBSITE (done, #875; the ride-along).
- TCK-20261018-DEPS-REDIS-8 (redis-py 8, the reason the redis pin moves deliberately).
- TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING (done, #786; gap "ntfy not re-proven", closed by item 4).

## Related Docs
docs/runbooks/records/2026-10-19-api-slo-alert-fire-test.md
docs/runbooks/records/2026-10-26-ai-worker-lag-alert.md
docs/runbooks/records/2026-10-28-alloy-log-shipping.md

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING/

## Related Code Areas
compose.yaml

## Assumptions / Open Questions
- A redis 8.10.2 -> 8.10.3 patch needs no redis-py change. If the release notes say otherwise, stop and report to
  platform-planner (redis-py is rpg's).
- Dependabot may refresh #878 or open a new compose PR before this lands. If it does, the digests checked here win.

## Implementation Notes
**Light part done and proof run done (2026-11-11, owner go #715 6801197149). One red check (Loki), decided by platform-planner as option (a): the pins stay, the Loki fault is `TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE`.**
- **Digests.** Each is the multi-arch index digest, read with `docker buildx imagetools inspect <tag>` on 2026-11-11. All four equal the ones in Dependabot #878 (no mismatch):
  - `redis:8.10.3-alpine` `sha256:71885d8cc6e4...fb80` (OCI index; amd64, arm64, arm/v6, arm/v7, 386, ppc64le, riscv64, s390x).
  - `prom/prometheus:v3.16.0` `sha256:e04987641b57...0f06` (OCI index; amd64, arm64, arm/v7, ppc64le, riscv64, s390x).
  - `binwiederhier/ntfy:v2.37.2` `sha256:1875ddcf815c...2bd7` (Docker manifest list; amd64, arm64, arm/v6, arm/v7).
  - `oliver006/redis_exporter:v1.97.0` `sha256:f5f903fbe775...9b83` (OCI index; amd64, arm64, arm/v7).
- **Age.** ntfy v2.37.2 (2026-11-04), redis_exporter v1.97.0 (2026-11-04) and prometheus v3.16.0 (2026-11-05) are under the repo's usual two-week age. The owner chose them on 2026-11-11 (#715 6800739670, item 3); the compose comments say so.
- **Comments** updated in compose.yaml: redis (8.10.3, verified 2026-11-11), prometheus (v3.16.0), ntfy (v2.37.2; the old text still said v2.28.0), redis_exporter (v1.97.0; the old text still said v1.93.0, and "this file's redis:8.10.3"). The redis_exporter comment cites `docs/runbooks/records/2026-11-compose-image-bumps.md`: the record is `docs/runbooks/records/2026-11-11-compose-image-bumps.md`. No `mem_limit` changed.
- **Release notes read** (GitHub releases, 2026-11-11):
  - redis 8.10.3 (2026-10-26): security fix only (heap overflow on a >4 GB PUBLISH over the cluster bus, cluster mode). We don't run cluster mode. No redis-py impact in the notes.
  - prometheus v3.16.0: six [CHANGE] lines: search endpoint `batch_size` clamp, `--web.external-url` https default when TLS is on, subquery sample statistics, removal of four deprecated remote-write 2.0 metadata metrics, a remote-write receiver counter, exemplar label-name uniqueness. None touches our flags (`--config.file`, `--storage.tsdb.path` only), scrape or rule files, or any remote-write setting (grep of docker/, compose.yaml and docs/runbooks found no use).
  - ntfy v2.35.0-v2.37.2: no change to auth-default-access, the message cache file or the metrics listener. Items that touch us or need a look in the proof run: (a) v2.36.0 says the whole server config is checked again when `base-url` is set, "so an invalid config that used to start now fails at startup". We set `NTFY_BASE_URL=http://ntfy` plus listen, cache file, auth file, deny-all and a metrics listener, so the proof run must show ntfy starts healthy. (b) v2.36.0 zeroes everyone's daily counts once and stores them in the user database (harmless here). (c) v2.35.0 fixes intermittent 403s under concurrent requests from the same IP (a fix for the auth path we depend on). (d) v2.36.0 adds an experimental admin socket, off by default (`experimental-listen-admin-unix`); we don't set it. The v2.37.2 release body only lists a merge commit.
  - redis_exporter v1.97.0: opt-in KEYSIZES metrics, options to exclude slowlog/commandlog metrics, an error on an empty CA cert file. We pass only `--redis.addr`. Nothing changes by default.
  - Result: no breaking or config-affecting change that needs a config edit. The one watch item is (a).
- **Light checks.** `docker compose --profile observability config -q` parses; grep for the old versions in compose.yaml finds none; compose hygiene, repo-root and platform-domain tests: 14 passed. The ride-along on `TCK-20261111-DEPENDABOT-WATCHES-WEBSITE` is done (#879, opened 2 minutes after #875 merged, labels [dependencies, platform]).
- Out of scope and for platform-planner to route: `tests/perf/test_simq_isolation_overhead.py` line 17 still cites the old redis digest.

## Test Summary
- **observed (run 16:25:57Z to 16:38:40Z, 12 min 43 s; record `docs/runbooks/records/2026-11-11-compose-image-bumps.md`, evidence in `agent-working/stored_artifacts/TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF/run-2026-11-11/`):**
  - 9 of 9 Prometheus targets up (redis, ntfy, alloy included). Prometheus has no rule files (`rule_files` absent), so the premise "Prometheus loads every rule file" was corrected: Grafana loaded 11 rules, all health ok.
  - `redis_version=8.10.3`, `redis_up=1`. Running image ids equal the pinned digests.
  - ntfy v2.37.2 deny-all: anonymous publish 403, anonymous read 403, token publish 200; healthy with `NTFY_BASE_URL` set.
  - Fire test: `[firing] TargetDown` for redis reached ntfy at 16:32:17Z (Pending 16:29:58, Alerting 16:31:59); `[resolved]` at 16:37:17Z. Closes the #786 gap "ntfy not re-proven".
  - Memory (anon + active_file max, MiB): ntfy 24.9 of 96, redis-exporter 19.7 of 32, prometheus 137.4 of 512. No `mem_limit` changed.
- **red check, not resolved:** Loki returned 500 `Ingester is shutting down` to every Alloy push (19 requests, 0 accepted), after logging `disk usage exceeded threshold ... usage_percent=94.80% threshold_percent=90.00%` while /data was 83 percent used. `LogShippingErrors` stayed Pending. The bumps do not touch Loki or Alloy, but I did not run the old pins to compare. Reported to platform-planner.
- **validated:** compose config parses; compose hygiene, repo-root and platform-domain tests passed (14).
## Files Changed
- `compose.yaml`: four image pins and the comments next to them.
- `docs/runbooks/records/2026-11-11-compose-image-bumps.md`: the record.
- `agent-working/stored_artifacts/TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF/run-2026-11-11/`: run evidence.
- `agent-working/tickets/done/TCK-20261111-DEPENDABOT-WATCHES-WEBSITE.md`: ride-along observed line.
## Completion Summary
The four compose image bumps from Dependabot #878 are taken by hand: redis 8.10.3-alpine, prometheus v3.16.0, ntfy v2.37.2, redis_exporter v1.97.0, each pinned by a multi-arch index digest I read myself, with the compose comments updated. The stack proof run showed all 9 targets up, `redis_version=8.10.3`, ntfy's deny-all auth (403 anonymous, 200 with the token), a real `[firing]` and `[resolved]` TargetDown message through ntfy, and memory well under the limits of ntfy, redis-exporter and prometheus (record `docs/runbooks/records/2026-11-11-compose-image-bumps.md`). This also closes the #786 gap "ntfy not re-proven". Supersedes Dependabot #878 (the user closes it). Ride-along done: the observed line on `TCK-20261111-DEPENDABOT-WATCHES-WEBSITE`.
Known gap: Loki accepted no log push during the proof run (cause open), tracked in TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE
Also not covered: the run lasted 12 min 43 s, not 25 to 30, so the memory numbers are a short-run peak. The Prometheus rules premise was corrected (Prometheus has no rule files; Grafana's 11 rules were checked instead).
