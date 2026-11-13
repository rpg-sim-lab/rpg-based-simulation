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

## Test Summary

## Files Changed

## Completion Summary
