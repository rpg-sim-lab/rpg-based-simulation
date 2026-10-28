---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER

## Title
A dispatch that fails the same way more than 1100 times (EAT at a non-serving building, SOURCE_MISSING) never becomes a blocker, so the subject loops in place until it dies

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Finding from rpg-designer (2026-10-29), based on rpg-implementer-2's D73 trace3: urban_political s46, tree 58c0821dc (src = 7cfd2cc0c), pure. Data: /mnt/data/scratch-rpg-implementer-2/d73/trace3/d73_s46.jsonl.
- Hero 22 stands next to building 20000 at (32,19) with path_len 0.
- Every tick, the router dispatches EAT at 20000. It fails with SOURCE_MISSING (nav.last_failure_reason SOURCE_MISSING).
- _hold_in_place (src/engine/domain/action_router.py:74) clears the target, and the hunger goal points back at the same building.
- This loops from about t800 until death, 1100+ ticks.
- Bible 04 / intelligence contract STRAT-191-194: infer_blockers() (src/systems/strategic_systems/intelligence.py about l.176) produces BlockerState from recent failures. Nothing learned from this one.
- First reading of the code (rpg-planner, not verified): infer_blockers maps navigation failures (PATH_NOT_FOUND, STUCK, OSCILLATING), congestion (wait or oscillation counts), and INTERACT capacity failures on harvesting projects. A failed EAT/service action with SOURCE_MISSING has no branch.
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO removes this instance. Any other wrong dispatch would loop the same way.

## Scope
Counts first. Numbers go to rpg-designer through rpg-planner before any fix shape:
- Why the repeated SOURCE_MISSING does not reach infer_blockers. Is the failure not recorded where infer_blockers reads it, or is it not a kind it maps?
- How often a same-target, same-reason action failure repeats 10 or more times in a row, on the gate worlds s42-46 (5000t), by action, reason and kind group. Use a pure probe: hash equal with and without it.
- Design question for rpg-designer: should a failed service dispatch become a blocker that closes that way for the subject (and with what decay or expiry)?

## Out of Scope
- Fixing the earn arrival dispatch (the EARN ticket).
- Any fix before rpg-designer's ruling.

## Acceptance Criteria
- A counts table plus a cause statement (not recorded vs not mapped), sent to rpg-designer.
- If a fix is ruled:
  - a real-kernel test where a subject whose service dispatch fails N times gets a blocker, and the goal stops re-targeting that way;
  - a test where a single transient failure does not block;
  - Bible 04 STRAT-191-194 text, a parity ledger entry, a divergence entry;
  - a paired run.

## Related Tickets
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1

## Related Docs
- docs/mechanics/04_strategic_cognition.md (blockers, STRAT-191-194)

## Related Stored Artifacts

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (infer_blockers)
- src/engine/domain/action_router.py (_hold_in_place)
- src/core/strategic.py (BlockerState)

## Assumptions / Open Questions
- Not a D73 blocker. Sequence after EARN. Not dispatched.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
