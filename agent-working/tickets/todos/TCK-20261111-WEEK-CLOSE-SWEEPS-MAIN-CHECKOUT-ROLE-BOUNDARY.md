---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-ROLE-BOUNDARY
phase: open
date: 2026-11-11
tags: [agent-monitoring]
---

# TCK-20261111-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-ROLE-BOUNDARY

## Title
The week close also sweeps the main checkout's role_boundary.jsonl, and W44/W45 are re-closed to back-fill the rows it missed

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found 2026-11-11 after #860 (the W41–W45 close-out) merged as 79df43407. lead-planner asked how
a closed week treats leftover rows in a main checkout. A read-only comparison of the ubuntu main
checkout against origin/main found:
- all of its W44/W45 `main.tools.jsonl`, `manual_actions.jsonl` and `reset_boundary.jsonl` rows
  are already in main, because the sweep from TCK-20261021 and TCK-20261110 covers them;
- `role_boundary.jsonl` has 2 rows that main lacks (W44 2026-10-30T17:15Z, lead-planner; W45
  2026-11-08T17:23Z, rpg-planner-ubuntu). `tools/agent-monitoring/week_close.py:49` says
  role_boundary has "nothing of theirs to fold", which holds for branch shards. A main-checkout
  session still writes the bare file, though, and no PR carries it.

On host u24desktop, lead-planner-u24 reports W45 leftovers in that main checkout: one
`manual_actions.jsonl` row (2026-11-06T23:52Z) and an untracked `W45/main.tools.jsonl`. By design
(README, "two limits") the ubuntu close does not sweep the other host.

Rule applied (docs/agent-monitoring/README.md, "Closing a finished week"): a closed week takes
late rows through a deliberate re-close, which is back-fill. Rows are never dropped.

## Scope
- Add `role_boundary.jsonl` to the main-checkout sweep in `week_close.py`, with the same full-row
  identity, read-only handling of the main checkout, and one printed line per kind as the other
  bare kinds.
- Tests next to the existing non-tool-shard sweep tests.
- A deliberate re-close of 2026-W44 and 2026-W45 on host ubuntu, so the 2 rows land. The PR body
  names it as back-fill.
- u24's W45 rows: an agent-working seat on u24desktop runs the same re-close there. The rows ride
  whichever PR lands first, and the other close then changes nothing (idempotent).
- One README sentence: the sweep covers role_boundary too.

## Out of Scope
- Deleting or rewriting anything in either main checkout (the sweep is read-only there).
- Sweeping across hosts.

## Acceptance Criteria
1. A close of a week whose main checkout holds a role_boundary row that canonical lacks appends it
   once, and a second close changes nothing.
2. After the W44/W45 re-close, the ubuntu main checkout has 0 role_boundary rows that main lacks.
3. The run/event/gate_verdicts counts for W44/W45 are unchanged by the re-close (only bare kinds
   gain rows).

## Related Tickets
- TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS
- TCK-20261110-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-NON-TOOL-SHARDS
- TCK-20261110-MONITORING-CLOSE-WEEK-BACKLOG (#860)

## Related Docs
- docs/agent-monitoring/README.md ("Closing a finished week")

## Related Stored Artifacts

## Related Code Areas
- tools/agent-monitoring/week_close.py, tools/sessions/boundary.py (the role_boundary writer)

## Assumptions / Open Questions
- Whether u24's leftovers get their own u24 hotfix or ride this PR is a choice for the two
  agent-working planners. Either way, the close is idempotent.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
