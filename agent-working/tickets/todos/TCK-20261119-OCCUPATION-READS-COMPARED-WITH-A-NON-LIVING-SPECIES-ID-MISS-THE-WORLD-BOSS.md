---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS

## Title
navigation.py and threat.py compare the occupation with "world_boss", but step 4 writes world_boss as the species (occupation "ancient_sentinel"): the duplicate-boss bug's twin, plus a static test closing the class

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Lane D's static read for the slow-regression attribution (inspected on main 51a6516cf):
- src/systems/world_systems/navigation.py:41 and src/world/threat.py:30 read `identity.occupation == "world_boss"`.
- Since kind=species step 4 (#952), the spawn writes species "world_boss" with occupation "ancient_sentinel", so neither read ever matches. This is the same defect as TCK-20261118-A-SECOND-WORLD-BOSS-SPAWNS-BECAUSE-THE-DEDUPE-READS-THE-OCCUPATION (#964).
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
- None.

## Related Code Areas
- src/systems/world_systems/navigation.py:41, src/world/threat.py:30

## Durable state, lifecycle and clocks
No new durable state. Only which identity field a read compares changes.

## Assumptions / Open Questions
- None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
