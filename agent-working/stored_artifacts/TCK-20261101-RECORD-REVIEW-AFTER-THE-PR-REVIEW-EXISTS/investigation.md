---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS
artifact_type: investigation
phase: done
date: 2026-11-01
tags: [agent-monitoring, governance]
---

# Investigation

## Findings
- `record_hand_orchestrated_closure.py` runs at ticket close, before the PR exists. Its `folded_phase_events` writes Review as `skipped`/`no_hand_tool` (events row: run_id, execution_id, seq, phase, status). `--review-ref` (#807) only works if the review already exists, which is the rare order.
- The hand run row carries `execution_mode: "hand"`, `ticket_id`, `execution_id`; events are keyed `(run_id, seq)`; `record_events.validate_record` checks REQUIRED fields and `skip_reason` validity; writers resolve the current-week shard through `monitoring_batch_identifier.resolve_write_target` and append with `writer.write_line(s)` after `session_role.stamp`.
- `path_report.analyze` already counts a phase `ran` when ANY event of the run for that phase is non-skipped, once per run. So a later Review `ok` event already counts as ran exactly once there; only the `skipped` count must not also include it (it does not: `ran` is tested first).
- `generate_retro` Phase Status Distribution (`phase_stats[phase][status] += 1` per event) counts per event: a run with the folded skip plus a later ok would read 1 skipped + 1 ok. That is the double count the ticket's AC2 forbids.
- Both `path_report.main` and the retro read events through `generate_retro._load_runs_and_events()` (SQLite index, fallback to JSONL), a single choke point. `build_index` stores raw event JSON, so the field survives.
- `gate_ledger.py outcome` is the pattern: an append-only row added to an existing verdict later; readers overlay.

## Design choice (i) vs (ii)
(i) a new Review `ok` event for the same run, fresh seq, `supersedes: <seq of the folded skip>`. (ii) a new record kind overlaid by readers.
Choose (i): it is an ordinary events row, so the writer, shard placement, index, validator, and every existing reader work unchanged; (ii) needs a new file kind in `shard_paths`, `build_index`, `validate`, and week-close conservation. The cost of (i) is that the superseded skip stays in the file, so per-event counters need the overlay (`run_dedup.drop_superseded_events`, applied once in `_load_runs_and_events`). A reader bypassing that function would see both rows; `path_report` is unaffected either way (see above).

## Risks
- Readers other than the retro that count events from the raw shards (e.g. `query.py` via the index) still see the skip. Documented in schema.md; not a regression (they see it today).
- Seq collision: take max seq of the run's events + 1 across all shards, never reuse.
- Week close conservation (`week_close.py`) must still pass: appended events land in the current week's shard even if the run is in an older week; verify that closing a week does not reject an event whose run started earlier (checked in tests with a cross-week sample).
