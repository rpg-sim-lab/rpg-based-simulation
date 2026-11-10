---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261110-MONITORING-CLOSE-WEEK-BACKLOG
phase: done
date: 2026-11-10
tags: []
---

# TCK-20261110-MONITORING-CLOSE-WEEK-BACKLOG

## Title
Monitoring weeks 2026-W41 to W45 are closed: their per-batch shards are folded into the canonical files.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Five finished ISO weeks (2026-W41, W42, W43, W44, W45) still carry per-batch monitoring shards. Close each with `make agent-monitoring-close-week WEEK=<week>`, one commit per week. Owner approval #715 6770665726 (relayed by lead), dispatched by agent-working-planner.

## Scope
- Run the week close for W41, W42, W43, W44 and W45, one commit each, ticket ID in every subject.
- Never edit a shard by hand to make week_close accept it; a refusal is reported.

## Out of Scope
- 2026-W46 (the current week) and any code change to week_close.py.
- Shard rows that live only on unmerged branches (they fold at the next close of their week).

## Acceptance Criteria
1. Each of the five weeks has no per-batch shard left in `agent-working/agent-monitoring/data/<week>/` after its close, apart from the bare per-week files.
2. One commit per week, each subject naming this ticket.
3. `week_close.py` ran without a refusal, or any refusal is reported and the week left as it was.

## Related Tickets
TCK-20261001-MONITORING-WEEK-CLOSE-COMMAND

## Related Docs
`tools/agent-monitoring/week_close.py`

## Related Stored Artifacts
None.

## Related Code Areas
`agent-working/agent-monitoring/data/`, `agent-working/tickets/working_log.csv`

## Assumptions / Open Questions
None open. W44 has 341 shard files, 6 MB: a light JSONL fold, no heavy slot needed.

## Implementation Notes
Branch agent-working-monitoring-close-week-backlog, cut from origin/main 61e0b4122, in worktree agent-working-close-week.

## Test Summary
`week_close.py` ran without a refusal for all five weeks (exit 0). Per-week shard files after the close: W41 6, W42 7, W43 7, W44 8, W45 7 (bare per-week files only). W44: 341 shards, 6 MB, a light fold, no heavy slot. Late W45 rows (6 tools rows from the PR 859 session) were folded by a second W45 close in its own commit.

## Files Changed
`agent-working/agent-monitoring/data/2026-W41..W45/`, `agent-working/tickets/working_log.csv` (W44: 99 rows, W45: 21 rows folded from pending shards), plus carried W46 rows from the PR 859 session (review events, tools rows, one governing-edit row).

## Completion Summary
Weeks 2026-W41 to W45 are closed, one commit per week. Nothing was hand-edited.
