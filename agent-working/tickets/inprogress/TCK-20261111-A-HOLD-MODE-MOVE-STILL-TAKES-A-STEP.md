---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
phase: open
date: 2026-11-11
tags: []
---

# TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP

## Title
A subject whose movement mode is HOLD still takes a step toward its stored target

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
rpg-designer found this in the Scope 1 trace of TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING. rpg-planner filed it on 2026-11-11.

def2 crowded s43 #1, t2942 (tree 3300928e8, hash-matched): `resolve_move` ran with mode HOLD toward the stored target (25,25), written at t2939 by intelligence.py ~:670. The subject stepped and took the opportunity attack (attacker 30, hp 9, damage 23).

Raw data: /mnt/data2/scratch-b/fst_out/def2_c43.json.

## Scope
1. Read-only check on main 5c6990e51: what HOLD means in MovementSystem.resolve_move and route_movement_intent, and in the docs (Bible 02, docs/engine movement contracts). Is a HOLD step intended?
2. If it isn't intended, the fix is that HOLD takes no step. rpg-designer rules first, with a paired measurement only if the rule moves any outcome.

## Out of Scope
- The lethal free-swing hold (the non-flight P2 ticket).
- The stored-target-while-engaged question (COMBAT-RETREAT P2, widened).

## Acceptance Criteria
- HOLD's meaning is cited from the docs and the code, with a verdict.
- If it's a defect, a unit test pins "HOLD takes no step".

## Related Tickets
- TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
- TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/engine/contracts/tactical_contract.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/systems/movement.py (resolve_move)
- src/engine/pipeline_phases/movement.py (route_movement_intent)

## Assumptions / Open Questions
- The answer may simply be that HOLD is a mode for speed or terrain, not a "don't move" instruction. If so, close it with the citation.

## Implementation Notes

Design approval (rpg-designer, 2026-11-14, session message): HOLD plan v3 at d7b872287 (plan.md sha256 1e71d299…, test_plan.md 71d0407f…) is approved as a DESIGN only. The build waits for the owner's answer on the HOLD row (lead-planner-u24 carries it); no src edit and no push before then. BUILD CONDITION: the limit stated at plan.md line 43 ("Limit, said plainly: the predicate is 'an action task is live', not 'THE task that entered the HOLD is live': the state does not store which task entered the HOLD. It errs toward keeping HOLD: a typed-wait HOLD that persists while the subject has since started an unrelated live action (e.g. an ATTACK) is not reset by a walk decision until that action ends. That is the safe direction (it never makes a walk cheaper than today), and it costs at most the time until that action ends.") is written in the same words into the Disclosed line of divergence 2.206 and into the tactical_contract.md :89 note; no ledger row may claim "the entering task" anywhere.

## Test Summary

## Files Changed

## Completion Summary
