---
status: active
layer: platform
authority: P2
audience: agent
ticket_id: TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE
phase: test_plan
date: 2026-11-12
tags: [platform, observability]
artifact_type: test_plan
---

# Test plan: TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE

Static checks run now; T1 to T4 happen in the ONE shared proof run (with TCK-20261018-API-DASHBOARD-AND-TRACE-PROOF), which needs reviewed plans and lead's heavy-slot go. Run rules: build the backend first; record `df` and `stat -f` for `/` and `/data`; stop before `up` if either `df` is 85% or more; the standing abort watcher (`tools/loadtest/stack_guard.sh`) and mem limits on; `down` without `-v`; outputs on `/data`.

## Static (before the run)

- S1. `docker compose --profile observability config -q` passes; the rendered `loki` service has the `loki_data:/loki` mount, the `-ingester.wal-dir=/loki/wal` argument, and `loki_data` is in `volumes:`.
- S2. `tests/architecture/test_docker_compose_dependency_hygiene.py` and the compose-hygiene tests pass; paths guard and REGISTRY no-drift pass.
- S3. `git grep -n 'loki_data' compose.yaml` shows exactly: the mount and the top-level name.

## In the run

- T1. Start: no Loki permission error on `/loki/wal`; `/ready` returns 200; Loki's startup log shows the WAL dir (answers investigation s5.1).
- T2. At Loki start: record `stat -f` (Blocks, Bfree, Bavail) for `/` and `/data`, and compute `(Blocks-Bfree)/Blocks` for the filesystem under `docker volume inspect` `Mountpoint`. Expect `Mountpoint` under `/data/docker/volumes` and the figure near `/data`'s (about 79% today), below 90%. Also grep the Loki log: there must be no "disk usage exceeded threshold" line.
- T3. Before the request burst: Alloy `loki_write_sent_entries_total` > 0, `loki_write_request_duration_seconds_count{status_code="500"}` = 0, a Loki `query` over the last 5 min returns streams for `container=~".*backend.*"`, `LogShippingErrors` Normal after its 10 min `for`.
- T4. Alloy memory (anon + active_file max, MiB) over the run against 256: say whether 256m holds.
- T5. Negative control: none run (no way to fill a disk safely here). The throttle behaviour is shown from source and from the 2026-11-11 run. State this as a limit in the record.

## Evidence to keep

`agent-working/stored_artifacts/TCK-20261111-LOKI-REJECTS-EVERY-PUSH-ON-WAL-DISK-THROTTLE/run-<date>/` with `.txt` names (`*.log` is gitignored), a secret scan before commit.
