---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261114-REROUTE-RUNG-STEPS-PAST-THE-READINESS-GATE-AND-STATUS-BLOCK
phase: open
date: 2026-11-14
tags: [combat, legality, engine]
---

# TCK-20261114-REROUTE-RUNG-STEPS-PAST-THE-READINESS-GATE-AND-STATUS-BLOCK

## Title
The congestion ladder's reroute rung steps a subject past the readiness gate and the frozen/stunned block, in every movement mode

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by the HOLD spy (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, finding (a), lane A trace 2026-11-14, verified by rpg-planner and rpg-designer on origin/main). Rung 3.3 "Reroute" of MovementSystem.resolve_move (src/engine/movement.py:287-296) fires once navigation.wait_count >= 2 and takes the first free orthogonal neighbour, checking ONLY LegalityServiceV2.verify_occupancy (extent, terrain, buildings, claims, occupants). It skips the rest of verify_movement_legality (src/engine/legality.py:183-208): the readiness gate (ACTION_EXHAUSTION, readiness < move_cost/speed) and the frozen/stunned status block (:195). Each refusal adds wait_count 1 (movement.py:299-300) and a success resets it, so a subject whose legality keeps failing steps every third call whatever its readiness or status. Sidestep (3.1) re-runs full legality; yield (3.2) only displaces an occupant.

Evidence (HOLD cells, fm/crowded s42 5000t, /mnt/data2/rpg-measure/holdmove/cells/; report /mnt/data2/rpg-measure/briefs/hold-cells-report.md): F,F,S call sequences; 13 of 79 HOLD steps below the 10x HOLD price, all via this rung (fm entity 34 ticks 1976/1986/1996 step at readiness 40; fm entity 62 steps at 85 and 30; crowded worker 1 ticks 142-144 step at 70). The frozen/stunned bypass is a code reading; no stepped stunned/frozen subject is observed yet.

Designer ruling (rpg-designer, 2026-11-14, session message): the ladder is a CONGESTION ladder; a refusal for ACTION_EXHAUSTION or ATTACKER_STATUS_BLOCKED never earns a reroute. P2 stands on the exhaustion bypass across all modes even if no stunned case is found.

## Scope
1. Read-only sizing first (existing outputs if rows allow; else a small spy the designer approves): rung-3.3 steps by the refusal reason of the previous call (occupancy / ACTION_EXHAUSTION / STATUS_BLOCKED), split by movement mode; frozen/stunned cases explicitly; OA events and damage on those steps.
2. Designer rules build after sizing. Ruled fix shape (not to build before sizing): the reroute tile goes through full verify_movement_legality, as sidestep does (simpler; alternative: gate 3.3 on an occupancy refusal reason).
3. A build changes movement rate in every mode: full measurement (not a 2-cell look), owner ask via lead with NO CHANGE named.
4. Parity: the movement_readiness_gating ledger entry (VERIFIED v2 tag at movement.py:258) gets a support_boundary naming rung 3.3 until the fix lands; check Bible 02 / 01 readiness-gating text for an unqualified claim; before/after to the designer. Ledger edits via tools/parity_ledger_writer.py only.

## Out of Scope
- wait_count counting readiness refusals as congestion (leave as is).
- HOLD mode lifecycle (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP).
- The collapsed sleeper's walk intent (TCK-20261114-A-COLLAPSED-SLEEPER-WALKS-UNDER-A-LIVE-SLEEP-TASK).

## Acceptance Criteria
- Sizing table delivered and ruled by the designer.
- Ledger support_boundary + Bible check done (before/after approved).
- If built: rung 3.3 never steps a subject that full movement legality refuses for exhaustion or status; unit tests for exhausted, stunned and frozen subjects at wait_count >= 2; full measurement reported.

## Related Tickets
- TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP (found by; shared rows)
- TCK-20261114-A-COLLAPSED-SLEEPER-WALKS-UNDER-A-LIVE-SLEEP-TASK (12 fm rows shared; this rung is how those steps passed the price)
- TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE (readiness/movement history)

## Related Docs
- docs/mechanics/02_combat_laws.md, docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/combat_movement.yaml (movement_readiness_gating)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/briefs/hold-cells-report.md (off-repo)

## Related Code Areas
- src/engine/movement.py:258, :287-300
- src/engine/legality.py:100-130, :183-208

## Assumptions / Open Questions
- Does any frozen/stunned subject actually step this way in play?

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
