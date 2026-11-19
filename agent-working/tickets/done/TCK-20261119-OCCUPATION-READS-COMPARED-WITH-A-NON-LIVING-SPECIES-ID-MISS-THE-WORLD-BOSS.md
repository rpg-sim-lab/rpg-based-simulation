---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS
phase: done
date: 2026-11-19
tags: []
---

# TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS

## Title
navigation.py and threat.py compare the occupation with "world_boss", but step 4 writes world_boss as the species (occupation "ancient_sentinel"): the duplicate-boss bug's twin, plus a static test closing the class

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Lane D's static read for the slow-regression attribution (inspected on main 51a6516cf):
- src/systems/world_systems/navigation.py:41 and src/world/threat.py:30 read `identity.occupation == "world_boss"`.
- Since kind=species step 4 (#952), the spawn writes species "world_boss" with occupation "ancient_sentinel", so neither read ever matches a boss.py-spawned boss (a calamity-spawned boss, calamity.py:83, species world_boss with occupation world_boss, did match). This is the same defect as TCK-20261118-A-SECOND-WORLD-BOSS-SPAWNS-BECAUSE-THE-DEDUPE-READS-THE-OCCUPATION (#964).
- It's behind ENABLE_WORLD_BOSS_SPAWN (OFF by default, owner decision 14), so it's latent.
- rpg-designer ruled it a separate P2 hotfix, not part of #964.

## Scope
1. Both reads become `species_of(entity) == "world_boss"`.
2. A source-scan test: no src read of `identity.occupation` (or occupation_of) is compared with a NON_LIVING_KIND_ALLOWLIST species id. That closes the class, not just these two sites.
3. A regression test per site: a world_boss body (species world_boss, occupation ancient_sentinel) is found by each reader.

## Out of Scope
- The boss dedupe (#964). Boss spawn rates and content.

## Acceptance Criteria
- Each site's test fails on main and passes with the fix. The source scan passes, and would fail on main for these two sites.
- No new properties["species_id"] read. Statics after the src commit.

## Related Tickets
- TCK-20261118-A-SECOND-WORLD-BOSS-SPAWNS-BECAUSE-THE-DEDUPE-READS-THE-OCCUPATION (#964)
- TCK-20261118-SLOW-REGRESSION-LANE-RED-SIX-UNOWNED-FAILURES-SINCE-M1

## Related Docs
- docs/mechanics/05_world_evolution.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS/investigation.md (the scan: every hit with file:line, what it compares)

## Related Code Areas
- src/systems/world_systems/navigation.py:41, src/world/threat.py:30

## Durable state, lifecycle and clocks
No new durable state. Only which identity field a read compares changes.

## Assumptions / Open Questions
- None.

## Implementation Notes
- navigation.py:41 and threat.py:30 now read `species_of(e) == "world_boss"` (`species_of` imported from `src.core.species`); the threat clause keeps its active and alive conditions.
- The scan found exactly these two direct comparisons. Four membership reads of the mixed label sets in `entity_kind_constants.py` (event_shapers.py:1172 and :1207, extraction/resources.py:88, extraction/world.py:114) are REPORTED, not fixed (rpg-designer u24, H2 (a)/(b)); they are pinned as known in the scan test and belong to the follow-up P3 rpg-planner (u24) files. The reverse direction (an entity kind compared with an occupation-only literal) has no hit.
- The navigation site is dead code for the WORLD_BOSS target while `FlowFieldService.ANCHORS` carries a fixed WORLD_BOSS waypoint pair; its test removes the pair to reach the reader.
- Docs: divergence 2.216, the ch05 §6 Boss Spawns bullet, parity WORLD-006 support boundary.

## Test Summary
- tests/unit/world/test_world_boss_species_reads.py (new): each reader finds a boss.py boss (occupation ancient_sentinel) and a calamity-style boss (occupation world_boss), rejects another species whose occupation says world_boss, and the threat clause keeps active/alive. On main's text 3 of 8 fail (navigation ancient_sentinel, navigation negative case, threat ancient_sentinel); with the fix 8 pass.
- tests/unit/core/test_occupation_label_readers.py: the source scan (direct hits fail outright; the four known membership hits are pinned; reverse hits none) with planted-snippet positive controls; on main's text of the two files it flags navigation.py:41 and threat.py:30.
- Scoped run: 92 passed (the three files above, tests/architecture/test_no_name_switches_in_decision_paths.py, test_name_switch_scan_sees_occupation.py, tests/unit/movement/test_flow_field_navigation.py, tests/unit/world/test_boss_gate_reachability.py).

## Files Changed
- src/systems/world_systems/navigation.py, src/world/threat.py
- tests/unit/world/test_world_boss_species_reads.py (new), tests/unit/core/test_occupation_label_readers.py
- docs/guidelines/intentional_divergences.md (2.216), docs/mechanics/05_world_evolution.md, docs/parity_ledger/world_dynamics.yaml (WORLD-006)
- agent-working/stored_artifacts/TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS/investigation.md

## Completion Summary
The two readers that look for a world boss now read its species, so a boss.py-spawned boss is found by the threat decay and the flow-field fallback as a calamity-spawned one already was. A source scan closes the class for direct comparisons and pins the four known membership reads. Latent while ENABLE_WORLD_BOSS_SPAWN is OFF.
