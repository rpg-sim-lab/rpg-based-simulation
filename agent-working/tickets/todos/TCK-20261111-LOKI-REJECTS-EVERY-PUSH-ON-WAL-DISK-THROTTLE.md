---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE
phase: open
date: 2026-11-11
tags: [platform, observability]
---

# TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE

## Title
Loki accepted no log push during the 2026-11-11 stack run (WAL disk throttle, then "Ingester is shutting down")

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
During the compose-image-bumps proof run (record `docs/runbooks/records/2026-11-11-compose-image-bumps.md`,
section 5), Loki 3.7.9 accepted no push at all:
- Alloy recorded 19 write requests, all HTTP 500, 0 entries sent, and 213 dropped.
- Loki answered `Ingester is shutting down` (first at 16:34:13Z).
- At start-up (16:28:00Z), Loki logged `wal.go:215 disk usage exceeded threshold, throttling writes
  usage_percent=94.80% threshold_percent=90.00%`.
- `LogShippingErrors` was Pending from 16:28:40Z.

The four bumped images (redis, prometheus, ntfy, redis_exporter) are not on Loki's path, so that ticket closes with
this stated as a known gap. So far, local log shipping is known broken in that run only. Whether it reproduces is
open. The 2026-10-28 Alloy run shipped normally.

## Scope
1. **Where the 94.8% comes from.** Find which path Loki's WAL disk check measures and how it computes the
   percentage. Read the Loki 3.7 source and docs for `wal.go` disk throttling. Facts known so far:
   - Unverified: which path and which statfs fields Loki's check measures. The facts below locate the data, not the measurement.
   - The loki service has no volume and no bind mount (compose.yaml), and the image declares no VOLUME. Its data
     sits in the container layer under Docker's root `/data/docker`, on `/data` (/dev/sdb1, 99G).
   - At 16:37 `/data` read 83% used (`df`), or 79% (`findmnt`).
   - The host root `/` (/dev/sda2) was at 100% with 20 MB free. Lead-planner is raising that with the owner as a
     host issue. No Loki or Alloy mount resolves to `/` (Alloy has only the read-only `config.alloy` bind from the
     worktree on /data).
   - Hypothesis, not established: the backend image build finished at 16:25Z, three minutes before Loki started. A
     build can briefly fill `/data` and then free it. Check whether usage at 16:28 could have been about 95%.
2. **Why the ingester then reports "shutting down"** and never recovers within the run, even with the disk below 90%
   later. Is this a Loki state machine (throttle -> read-only -> stopping) or something else?
3. **Reproduce** in one short heavy run (owner's go through lead, standing heavy-run rules). Run Loki and Alloy with
   the current pins only after the host `/` problem is settled. Record usage at Loki start.
4. **Fix**, depending on the cause. Options to weigh, without pre-choosing:
   - a named `loki_data` volume, which makes the location explicit and survives a recreate;
   - Loki's WAL disk-threshold settings, if they exist and are configurable;
   - a pre-run free-space check in the run procedure;
   - an alert on Loki's own throttling or ingester state.
   Prove the fix in the same or a following run: Alloy sends > 0 entries, and a Loki query returns streams.
5. Alloy memory: it peaked at anon+active_file 225.9 of 256 MiB (88%) while retrying failed pushes. Re-measure once
   pushes succeed, and say whether 256m still holds.

## Out of Scope
- Freeing space on `/`, or any host cleanup (the owner's).
- Changing the four images taken in TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF.
- Grafana memory (860 of 1024 MiB in the same run). Note it only.

## Acceptance Criteria
- The origin of the 94.8% figure is explained, with source/doc citations (validated).
- The cause of the persistent "Ingester is shutting down" is explained (validated or observed).
- After the fix, a stack run shows Alloy `loki_write_sent_entries_total` > 0, no 500s, a Loki query returning streams,
  and `LogShippingErrors` Normal (observed).
- Alloy's memory against 256m is re-measured with working pushes (observed).
- A record in `docs/runbooks/records/`.

## Related Tickets
- TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF (where it was seen; it closes with this as a known gap).
- TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING (done, #786: the Alloy pipeline, shipped fine on 2026-10-28).
- TCK-20261020-DISK-FILL-ALERT-TUNING (parked; host-disk alerting, possibly related).

## Related Docs
docs/runbooks/records/2026-11-11-compose-image-bumps.md
docs/runbooks/records/2026-10-28-alloy-log-shipping.md
docs/observability/loki_label_policy.md

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261111-COMPOSE-IMAGE-BUMPS-WITH-STACK-PROOF/run-2026-11-11/

## Related Code Areas
compose.yaml
docker/alloy/config.alloy

## Assumptions / Open Questions
- Standard tier, because the cause is unknown and a fix may change the stack's storage layout. It needs the owner's
  dispatch yes, and staging artifacts (plan, investigation, test_plan).

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
