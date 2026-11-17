---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261117-LEAD-BOARD-SEVENTH-PASS
phase: done
date: 2026-11-17
tags: [governance]
---

# TCK-20261117-LEAD-BOARD-SEVENTH-PASS

## Title
The lead board records Milestone 1's three-phase plan, its boundaries and the 2026-11-17 standing approvals, and shows ubuntu with only its RPG seats running

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
On 2026-11-17 the owner re-planned Milestone 1 into three phases (#715 6936893143) and added the rules around it: domain-by-domain merges, host-read extinction, S9 (6937264378, 6937306315, 6937352120), S8 (6936328520), and Phase 1 grade pins (6941107808). N10 moved to u24 (6936812819), #946, #948 and #949 merged, and ubuntu's non-RPG seats were closed (6941107071, 6941470432). The sixth pass did not show any of this. The owner said yes to a seventh pass (6941538090).

## Scope
- Rewrite `agent-working/lead/board.md` as a seventh pass at `main` efba7d95c, with the standing directions first.
- Carry the lead's uncommitted W47 monitoring rows from the main checkout.

## Out of Scope
- The epics' own files and the M1 epic's `SEQUENCE.md`, which their planners own.
- The u24 host page.
- Re-counting remote branches.

## Acceptance Criteria
1. Every board row names a state that matches `main` efba7d95c or cites a #715 comment id.
2. The top section states RPG-first with its Phase 2 lift, the three phases, the grade-pin rule, S8/S9 and the pauses; no row contradicts them.
3. Frontmatter is valid on the board and on this ticket.
4. The carried monitoring shards parse, and none of their rows duplicates one already on main.

## Related Tickets
- TCK-20261116-LEAD-BOARD-SIXTH-PASS (#945)
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- `agent-working/lead/board.md`

## Related Stored Artifacts
None.

## Related Code Areas
None.

## Assumptions / Open Questions
- The u24 rows come from lead-planner-u24's #715 records and were not re-checked on u24.

## Implementation Notes
Hand-orchestrated hotfix. Doc-only, written by lead-planner on branch `lead-board-seventh-pass`.

## Test Summary
- `python3 tools/validate_frontmatter.py` on the board and this ticket.
- The monitoring shards parse as JSON lines.

## Files Changed
`agent-working/lead/board.md`, this ticket, `docs/REGISTRY.yaml`, monitoring shards.

## Completion Summary
The board was rewritten as the seventh pass. It is doc-only; no code or tests changed.
