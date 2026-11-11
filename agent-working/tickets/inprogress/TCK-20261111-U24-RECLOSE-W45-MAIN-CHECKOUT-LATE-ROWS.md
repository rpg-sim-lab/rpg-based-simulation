---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261111-U24-RECLOSE-W45-MAIN-CHECKOUT-LATE-ROWS
phase: open
date: 2026-11-11
tags: [agent-monitoring, data-quality]
---

# TCK-20261111-U24-RECLOSE-W45-MAIN-CHECKOUT-LATE-ROWS

## Title
Re-close 2026-W45 on host u24desktop so the u24 main checkout's late rows (404 `main.tools.jsonl` rows, 1 `manual_actions.jsonl` row) reach the canonical files

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Relayed by lead-planner-u24 from agent-working-planner (ubuntu) via the ubuntu lead, 2026-11-11. #860 closed W41-W45
(79df43407) on host ubuntu. The close sweeps only the main checkout of the host it runs on, so the u24 main checkout still
holds W45 rows nobody committed. Checked on 2026-11-11 in `/mnt/data/Working/rpg-based-simulation` (branch `main`):
- `agent-working/agent-monitoring/data/2026-W45/manual_actions.jsonl`: modified, +1 row (2026-11-06T23:52Z);
- `agent-working/agent-monitoring/data/2026-W45/main.tools.jsonl`: untracked, 404 lines.
No other finished week has main-checkout leftovers. README "Closing a finished week": late rows go in through a deliberate
re-close, which counts as back-fill, and are never dropped.

## Scope
1. **Precondition:** ubuntu's TCK-20261111-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-ROLE-BOUNDARY has merged to main. It adds
   `role_boundary.jsonl` to the sweep and re-closes W44/W45 on ubuntu. Starting earlier would mean a second u24 re-close.
2. From a u24 worktree on a fresh branch off that main, run `make agent-monitoring-close-week WEEK=2026-W45`. It is
   idempotent. Record the printed swept counts per kind.
3. Confirm the canonical W45 files now hold the 404 tool rows (less exact duplicates, counted) and the manual_actions row.
   The main checkout's files are left as they are, since the sweep is read-only on them.
4. Also run the same close for W44 and report its counts. Expect 0 swept.

## Out of Scope
- Deleting or reverting the main-checkout files: that is the user's call (delete_worktree_or_data).
- Any change to `week_close.py`; ubuntu's role-boundary ticket owns the code change.
- W46 (current week; the close refuses it).

## Acceptance Criteria
1. After the close, the canonical `data/2026-W45/tools.jsonl` and `manual_actions.jsonl` on the branch contain every row
   from the u24 main checkout's W45 files, by full-row identity.
2. A second close of W45 changes nothing.
3. The PR's diff touches only `agent-working/agent-monitoring/data/2026-W4{4,5}/`, the ticket, the working log and
   `docs/REGISTRY.yaml`.

## Related Tickets
- TCK-20261110-MONITORING-CLOSE-WEEK-BACKLOG (ubuntu, #860, closed W41-W45)
- TCK-20261111-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-ROLE-BOUNDARY (ubuntu, precondition)
- TCK-20261110-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-NON-TOOL-SHARDS (done; added manual_actions to the sweep)
- TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS (done; the tool-row sweep)

## Related Docs
- docs/agent-monitoring/README.md ("Closing a finished week")

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/week_close.py (run only, unchanged)

## Assumptions / Open Questions
- Simpler-fix check: the existing idempotent close is the whole fix, with no code. The alternative of hand-copying rows
  skips de-dup and counting. Cost: one close run, no measurement. Leaves out later late rows, which need another re-close.
- The lead keeps a backup of the two main-checkout files in its scratchpad until this lands.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
