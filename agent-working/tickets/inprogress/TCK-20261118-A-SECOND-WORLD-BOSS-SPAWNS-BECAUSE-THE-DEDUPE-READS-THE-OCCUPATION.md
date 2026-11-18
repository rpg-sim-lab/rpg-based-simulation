---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261118-A-SECOND-WORLD-BOSS-SPAWNS-BECAUSE-THE-DEDUPE-READS-THE-OCCUPATION
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-A-SECOND-WORLD-BOSS-SPAWNS-BECAUSE-THE-DEDUPE-READS-THE-OCCUPATION

## Title
A second world boss spawns because BossService's dedupe reads the occupation, which kind=species step 4 (#952) moved to the species

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
Scheduled slow-regression has been red since #952 (TCK-20261118-SLOW-REGRESSION-LANE-RED-SIX-UNOWNED-FAILURES-SINCE-M1, row 6). test_living_world_ph9 reports "Duplicate bosses at tick 200: 2", both kind='world_boss'.

rpg-designer and lead-planner-u24 verified it, and rpg-planner re-inspected it on main 51a6516cf:
- src/world/boss.py:85 dedupes on `entity.identity.occupation == "world_boss"`;
- but the spawn at :151-152 writes species="world_boss" with occupation="ancient_sentinel" (step 4: kind is the named non-living world_boss, and the label is the occupation).
So the existing boss is never found, and a second one spawns.

The dragonkin read at :219 (`occupation == "dragonkin"`) matches today only because its spawn writes occupation "dragonkin" too (:263-264). It is the same latent defect.

## Scope
1. boss.py:85 reads `species_of(entity) == "world_boss"`.
2. Re-check EVERY identity read in boss.py. Move the dragonkin read at :219 to `species_of(entity) == "dragonkin"`.
3. A regression test: a state with one world boss alive, run across two boss-spawn ticks, still has exactly one boss. The same for dragonkin.
4. After it lands, rerun the slow failing set of TCK-20261118-SLOW-REGRESSION-... before any re-pin. Row 6 closes only when `len(bosses) <= 1` passes UNCHANGED.

## Out of Scope
- The other 5 slow rows, which are attributed separately under rule (a).
- Boss spawn rates or content.

## Acceptance Criteria
- The regression test fails on main and passes with the fix.
- test_living_world_ph9::test_long_run_simulation_ph9 passes, with its boss assert unchanged (an S9-free plain pytest of that file).
- No new read of properties["species_id"]: species_of()/occupation_of() only.
- Statics after the src commit. The ledger/Bible text, if it describes the dedupe, says "species".

## Related Tickets
- TCK-20261118-SLOW-REGRESSION-LANE-RED-SIX-UNOWNED-FAILURES-SINCE-M1 (testing-planner, ubuntu; row 6)
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC (step 4, #952)
- TCK-20261118-MID-RUN-SPAWNED-BODIES-SKIP-THE-SENSES-CHECK (boss.py spawns; a file overlap)

## Related Docs
- docs/mechanics/05_world_evolution.md (calamities and bosses)

## Related Stored Artifacts
- None.

## Related Code Areas
- src/world/boss.py (:85, :151-152, :219, :263-264)

## Durable state, lifecycle and clocks
No new durable state. The fix corrects which identity field the dedupe reads.

## Assumptions / Open Questions
- Merge segment: it is a step-4 defect, so it belongs to step 4's identity segment. The merge order is set with lead-planner-u24.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
