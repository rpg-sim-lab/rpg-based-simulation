---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF
phase: open
date: 2026-11-11
tags: [platform, observability]
---

# TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF

## Title
Take Dependabot #878's compose image bumps by hand, with their comments updated and a short stack proof run

## Status
OPEN

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
## Test Summary
## Files Changed
## Completion Summary
