---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE
phase: plan
date: 2026-11-12
tags: [platform, observability]
artifact_type: plan
---

# Plan: TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE

Standard tier. Finding is in `investigation.md`. Review: platform-planner, before any edit to `compose.yaml`. No stack run, build or pull until the plans are reviewed and lead gives the heavy-slot go.

## Decision

Give Loki a named volume and point the WAL into it explicitly. Keep the 0.9 threshold. Add a pre-run free-space gate to the run procedure. Do not add a Loki alert in this ticket.

## Options weighed

| option | verdict | reason |
|---|---|---|
| A. Named volume `loki_data` mounted at `/loki`, plus `-ingester.wal-dir=/loki/wal` | **chosen** | Moves chunks, rules and WAL off the container layer (on `/`) to `/data/docker/volumes` (on `/data`), the same pattern as the five other stateful services. Survives a recreate. The explicit flag makes the location independent of whichever default the image config resolves to. |
| B. Raise or disable `disk_full_threshold` | rejected | Hides a full disk; Loki would then fail with ENOSPC instead of throttling. |
| C. Pre-run free-space gate (`df` / `stat -f` at 85% on `/` and `/data`) | **chosen, alongside A** | Already required by the ticket text for the heavy run; this makes it a standing line in the runbook, with the reserve caveat (Loki sees about 5 points lower than `df`). |
| D. Alert on Loki's throttle (metric or `Ingester is shutting down` in logs) | deferred | The metric name is not read yet (investigation s6), and `LogShippingErrors` already fired on this fault (Pending 16:28:40Z, would have fired at 16:38:40Z). A new rule needs its own fire test. Open a ticket if the owner wants it. |
| E. Same volume change for prometheus, grafana, redis | not needed | They already have named volumes (investigation s3). Alloy's state stays in the container by design. |

## Steps

1. `compose.yaml`, service `loki`:
   - `command: -config.file=/etc/loki/local-config.yaml -ingester.wal-dir=/loki/wal`
   - `volumes: - loki_data:/loki`
   - add `loki_data:` to the top-level `volumes:` block.
   - a comment: why (the 2026-11-11 run, record section 5), and that Loki's check uses Bfree.
   Ownership: the image's `/loki` is chowned to uid 10001; a new empty named volume copies that ownership on first mount. **Unverified**, proven by the run (Loki starts, no permission error).
2. No change to `docker/` configs (Loki uses the image config; the repo has no Loki config file).
3. `docs/runbooks/log-shipping.md`: add the Loki throttle symptom (`Ingester is shutting down` is `ErrReadOnly` and also means "disk over 90% by Loki's formula"), where to look (`df` vs `stat -f`, `docker volume inspect`), and the 85% gate.
4. Record `docs/runbooks/records/2026-11-1x-loki-volume-and-api-dashboard.md`, shared with the dashboard ticket (one run, one record).
5. Data migration: none. The volume starts empty; the container layer's old WAL and chunks are not carried over (a local dev stack; logs in the old layer are lost on recreate today anyway). State this in the record.

## Acceptance (from the ticket) and how each is met

- Origin of 94.8%: `investigation.md` s1, with source citations. Remaining: T2 checks the numbers in the run.
- Cause of "shutting down": `investigation.md` s2.
- After the fix: Alloy `loki_write_sent_entries_total` > 0, no 500s, a Loki query returns streams, `LogShippingErrors` Normal: **observed** in the shared run (T3).
- Alloy memory against 256m re-measured with working pushes: T4.
- A record in `docs/runbooks/records/`: step 4.

## Risks and what I am not doing

- Not touching host disk or the other stacks' containers; `down` without `-v`.
- If `/data` itself is over 90% by Loki's formula at the run (df about 94.5%), the fix does not help; the 85% gate stops the run before that.
- If the volume mount shadows something the image needs in `/loki` (rules directories created by the Dockerfile): the first-mount copy preserves them; verify with a Loki start with no errors.
- Known gap carried to the record: the fix is unobserved until the run.
