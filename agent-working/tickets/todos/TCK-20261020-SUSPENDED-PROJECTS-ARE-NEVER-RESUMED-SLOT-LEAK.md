---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK

## Title
Suspended projects are never resumed and never expire, so they hold project slots forever (slot leak)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A traced blacksmith 13 on crowded_frontier s45 (2026-10-20, at 23fbe0ecf and in base 7b1528861). It holds 3 SUSPENDED resolve_blocker projects (plus 4 ABANDONED). Since divergence 2.77 (TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START), ACTIVE and SUSPENDED count as live against max_active_projects (3). Nothing resumes those three or ends them, so the entity sits at 3 of 3 for its whole life: 52 of 52 strategic calls from t1207 to t2227 in the fix arm, and 99 of 99 calls from t1207 to t3167 in base.

At intelligence.py:1771 (`if not existing and not has_project_capacity(...): return StrategicUpdate()`), every winning goal is discarded. Sampled every 20 ticks, 16 to 27 entities per gate world are in "no project, no capacity".

Before v1, the designer's step 2 (TCK for "an escalated need is never refused for capacity") covers survival needs only. This ticket is the root leak itself: suspended projects need a lifecycle that resumes or ends them. The designer ruled (2026-10-20) that this is new behaviour (a timer or a rule), so it goes after v1 and is measured against v1.

## Scope
- Designer first: the rule for when a SUSPENDED project resumes (for example, its blocker clears or the pre-empting goal ends) or ends (expiry, or it becomes unreachable), with its record and reason.
- Implement it in the authoritative path, with a typed transition, and keep 2.77's live predicate as it is.
- Tests: a suspended project resumes when its condition clears, ends under the ruled rule, and an entity can never hold 3 of 3 suspended projects indefinitely.
- Measure paired against v1 (seeds 42-46, D76), and report the "no project, no capacity" entity counts per world before and after.

## Out of Scope
- Reversing 2.77 (SUSPENDED stops counting as live): rejected by the designer.
- Eviction of a live project to make room: rejected (it needs a new choice rule).
- The escalated-need admission (before-v1 step 2).

## Acceptance Criteria
- The designer's rule is in Bible 04 and the parity ledger, with a divergence entry.
- No entity stays at capacity with only SUSPENDED projects past the ruled bound in the 3 gate worlds × seeds 42-46.
- D76 shows no unexplained drift against v1.

## Related Tickets
- TCK-20261007-STRATEGIC-CAPACITY-GATE-COUNTS-TERMINAL-PROJECTS-SO-NO-NEW-PROJECT-KIND-CAN-START (2.77)
- TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (the corpse fix, which exposed this)
- TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND
- TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1, §4
- docs/guidelines/intentional_divergences.md 2.77

## Related Stored Artifacts
- Lane A probes: /mnt/data/scratch-rpg-implementer/probes_hs/ (bs13_calls.py, bs13_trace.py), output in /mnt/data/scratch-rpg-implementer/cn_meas/

## Related Code Areas
- src/ai/intelligence.py (~L1771 capacity gate)
- src/core/strategic.py (is_live_project, has_project_capacity)

## Assumptions / Open Questions
- What suspends a resolve_blocker project, and does anything resume any project kind today?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
