---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261119-A-WORKER-BRAIN-THAT-WEIGHS-PAID-WORK-READS-THE-WORLD-INDEX-A-PACKET-DOES-NOT-CARRY
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-A-WORKER-BRAIN-THAT-WEIGHS-PAID-WORK-READS-THE-WORLD-INDEX-A-PACKET-DOES-NOT-CARRY

## Title
A worker brain that weighs paid work for a meal reads state.world_indexes, which the WorkerPacket does not carry, so the run stops with PacketFieldMissingError

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-implementer (lane A) in #781's by-directory sweep at 6b1e03ba6, on 2026-11-19. Three worldassembly grade-stability tests crash with `src.core.worker_protocol.PacketFieldMissingError` (executed). The trace was read by lane A (inspected):
- An ENTITY_BRAIN worker runs on a WorkerPacket (executor.py:296; worker_logic.py:48).
- The call chain is tactical_objective._reach_location_step → building_arrival_update → _hunger_arrival (building_arrival.py:60) → work_shift.shift_takeable (:56) → meal_position_after (:43) → SpatialQueryService.nearest_building (spatial_query.py:34) → WorldIndexService.get_indexes (world_index.py:107).
- That last call reads `state.world_indexes`, which is not a carried packet field and not in PACKET_DERIVED_CACHE_NAMES (worker_protocol.py:26-37).
- PacketFieldMissingError is not an AttributeError, so it stops the run (bounded_concurrency_contract.md §4).

It is LATENT on main. Under CLAMP the path is reached only by a body whose diet the inn cannot serve; the gate worlds and the unit sweeps stay green. D73 (#781, ATOMIC) makes it routine: every broke hungry subject that arrives at an inn reaches it. The production worker path does build this packet, so #781 would ship a crash without this fix.

Every other nearest_building caller (scorers.py:95/269/351, ways.py:45, adventure_scorer.py:286, opening_steps.py) runs in the strategic phase on the real state, so shift_takeable is the only reader on a packet.

## Scope
rpg-planner ruled option (iii), with rpg-designer agreeing that the fix is separate and comes first:
1. meal_position_after scans `state.buildings` for kind "inn", nearest by Manhattan distance, where the first strictly smaller distance wins. That is the same tie order as the index, which is built from state.buildings in order. nearest_building is untouched.
2. It lands as the FIRST commit of #781's branch, before the D73 code. The #781 PR closes this ticket too.

Rejected options: (i) carrying world_indexes in every packet, because it adds a build and pickle cost to every packet; (ii) adding it to PACKET_DERIVED_CACHE_NAMES, because the rebuilt entity index would come from the neighbour view, which hides a future divergence.

## Out of Scope
- Any change to WorkerPacket, its allow-list or nearest_building.
- D73 itself.

## Acceptance Criteria
- A test that is red at the base code: shift_takeable on a real WorkerPacket raises PacketFieldMissingError.
- After the fix, the packet answer equals the state answer, including two equidistant inns and no inn.
- STRICT hash-equal on the 3 gate worlds (s42, 5000t), 025be2faf vs 025be2faf plus the fix, under its own S9.
- The pre-push run covers tests/unit/** by directory plus statics.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#781, which exposes it)

## Related Docs
- docs/engine/contracts/bounded_concurrency_contract.md §4

## Related Stored Artifacts
- /mnt/data2/rpg-wt/freemeal-logs/ (lane A's sweep logs at 6b1e03ba6)

## Related Code Areas
- src/engine/work_shift.py (meal_position_after, shift_takeable); src/engine/world_index.py; src/core/worker_protocol.py; src/engine/executor.py

## Assumptions / Open Questions
- That deep_freeze keeps the insertion order of buildings is not verified. The two-equidistant-inns test checks it.

## Durable state, lifecycle and clocks
None. It reads only the carried buildings.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
