---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE

## Title
NavigationComponent.last_failure_reason is written only when a failure carries a code and is never cleared, so a stale PATH_NOT_FOUND/STUCK/OSCILLATING keeps being read by infer_blockers on every strategic pass

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by lane A's read-only F2 code read (2026-11-17, F1 head 46ac46e40; the cited files are identical on main 3aafdb383 apart from F1's own movement.py hunks).
- patches.py:288: `last_failure_reason = u_nav.failure_reason if u_nav.failure_reason is not None else new_nav.last_failure_reason`. An update with None keeps the old value.
- The only assignments are patches.py:288 and the builder default (core/builder.py:388/407). Nothing ever sets it back to None, including a successful move, a new target or a give-up.
- infer_blockers reads it on every strategic pass (intelligence.py:495), and files an ACCESS blocker for PATH_NOT_FOUND, STUCK or OSCILLATING keyed on the task payload's target_position (intelligence.py:190-191).
- So one old failure can keep re-inferring an access blocker long after the failure, against whatever target the task holds now. That defeats a lifecycle which expects a blocker to stop being re-inferred once its cause is gone (the churn fix's merge and quiet-spell rules).
- The way-round give-up itself sets failure_reason None (movement.py:362-365, :459), so it leaves the stale value in place and writes no code of its own.

## Scope
1. RULED by rpg-designer (F2 v2, 2026-11-17): last_failure_reason = the outcome of the LAST step. A successful step clears it with an explicit typed NavigationUpdate.failure_reason_clear, and a None never carries it forward. F2 does not use last_failure_reason.
   SCHEDULE: land before or with the churn fix, because a stale reason re-infers blockers against the churn lifecycle.
2. A typed clear in NavigationUpdate, applied in patches.py; tests; parity and Bible text.
3. Measure whether stale re-inference happens today: count access blockers inferred while the current failure is more than N ticks old.

## Out of Scope
- F2's giveup_records design (TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON), though it should be designed together with this.

## Acceptance Criteria
- last_failure_reason has a defined lifecycle: written, cleared, with a documented owner.
- Blocker inference never acts on a failure older than the rule allows. A test pins it.

## Related Tickets
- TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON (F2)
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION (churn lifecycle)
- TCK-20261117-MATERIAL-AND-PARTNER-BLOCKERS-NAME-A-SUBJECT-NOTHING-CAN-MATCH (subject format: intelligence.py:192 builds "(25.0, 25.0)" float strings, which score_modifiers.py:58 matches against target_id)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (blocker inference)

## Related Stored Artifacts
- Lane A's V2-V5 code read (relayed to rpg-designer, 2026-11-17)

## Related Code Areas
- src/engine/patches.py:288, src/systems/strategic_systems/intelligence.py:176-202 and :495, src/engine/movement.py:362-365 and :456-472

## Assumptions / Open Questions
- Whether a stale reason has ever filed a wrong blocker in a real run is unmeasured.
- Any fix touching intelligence.py waits for the intelligence.py split (owner schedule).

## Implementation Notes

**Ruled move law (rpg-designer, owner #715 6967356642 and 6967398421, after the first own-job tripped R1/R3):** any position change by the movement apply path is a MOVE: the subject's own step, a swap, or a yield displacement (lodge entry and exit are not). A move carries `failure_reason_clear` and NO failure code. The yield (`movement.py` `_yield_update`) drops `YIELDING`; the position-swap update (`pipeline_phases/movement.py`) drops `POSITION_SWAP`; both carry the clear. A failure code the movement-routing phase itself wrote for a body earlier in the tick is dropped when the body is then displaced (`_merge_move_update`, provenance-tracked per phase); codes from earlier phases (action routing runs BEFORE position swaps and movement routing, so the body's existing update may hold an action code) survive, and a code written later still wins at the patch. `OCCUPANCY_CONFLICT` becomes a `ReasonCode` member (same value). The swap merge in the swap phase is unchanged: swaps run before movement routing, so a swapped body has no prior movement code, only possibly an action code, which survives.

## Test Summary

## Files Changed

## Completion Summary
