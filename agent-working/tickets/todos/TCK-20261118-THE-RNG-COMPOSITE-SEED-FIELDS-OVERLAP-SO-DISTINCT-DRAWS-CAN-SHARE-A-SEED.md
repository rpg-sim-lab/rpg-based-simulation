---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261118-THE-RNG-COMPOSITE-SEED-FIELDS-OVERLAP-SO-DISTINCT-DRAWS-CAN-SHARE-A-SEED
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-THE-RNG-COMPOSITE-SEED-FIELDS-OVERLAP-SO-DISTINCT-DRAWS-CAN-SHARE-A-SEED

## Title
DeterministicRNG._composite_seed XORs its fields into overlapping bit ranges, so two different (base, domain, tick, entity, sub_id) draws can get the same seed

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Raised by rpg-designer (via lead-planner-u24, 2026-11-18) during the births registry review. It is engine-wide and latent, not a births issue.

`src/platform/rng.py::DeterministicRNG._composite_seed` builds the seed as `base ^ (domain << 48) ^ (tick << 32) ^ (entity << 16) ^ sub_id`. The fields have no width limits, so they overlap:
- `base_seed` overlaps `entity << 16` once it reaches 2^16. EntityGenerator is built with base = world seed + tick (TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1 cites `EntityGenerator(state.seed + state.tick)`), so the base reaches 2^16 at tick >= 65536 - seed.
- `entity_id` overlaps `tick << 32` once it reaches 2^16. A **string** entity id is hashed to 32 bits before the shift, so a string id overlaps the tick field (and the domain field) whatever its value.
- `sub_id` overlaps `entity << 16` once it reaches 2^16.
- `tick` overlaps `domain << 48` once it reaches 2^16.

XOR of overlapping fields means distinct tuples can map to one seed, and two draws meant to be independent then return the same value. M1's integer seeds, ticks, ids and sub_ids are far below 2^16, so nothing is known to collide today. That is an inference from those ranges, not a measurement, and the string-id case was not checked.

Not covered by TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE (DONE). That ticket fixed spawn TILE collisions, where draws keyed by entity id gave two entities the same tile. It did not touch the seed composition.

## Scope
1. Measure first: list every production caller's domain, its tick and entity-id ranges, whether it passes string ids, and its largest sub_id. Count the actual collisions, if any, on the 3 standard cells at 5000 ticks.
2. Decide the fix with rpg-designer. A collision-free composition (for example, hash the full tuple, or give each field a fixed width with range checks) changes every draw, so every hash pin and grade pin moves. That needs a recorded determinism re-baseline and an owner ask. It must NOT ride another behaviour PR.
3. Docs: `docs/engine/deterministic_execution.md` Rule 1 states the field widths and the range in which draws are collision-free.

## Out of Scope
- Changing any draw before step 2 is ruled.
- The spawn-tile occupancy fix (done).

## Acceptance Criteria
- The collision-free range is stated in deterministic_execution.md, and a test pins it (distinct tuples inside the range give distinct seeds).
- Either the composition is collision-free for every production range, or the limit is enforced (a typed error outside the range), as rpg-designer rules.

## Related Tickets
- TCK-20260817-STANDARD-SPAWN-OCCUPANCY-COLLISION-RNG-ROOT-CAUSE (different defect, done)
- TCK-20261014-A-CONQUEST-STRONGHOLD-OVERWRITES-ENTITY-1 (`EntityGenerator(state.seed + state.tick)` base)

## Related Docs
- docs/engine/deterministic_execution.md (Rule 1, DeterministicRNG)
- docs/parity_ledger/infrastructure.yaml (INFRA-108)

## Related Stored Artifacts
- none

## Related Code Areas
- src/platform/rng.py::DeterministicRNG._composite_seed
- EntityGenerator construction sites (the base = seed + tick)

## Assumptions / Open Questions
- Whether any production caller passes string entity ids today is unchecked.
- Fix timing: after Milestone 1, unless the step 1 measurement finds a real collision.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
