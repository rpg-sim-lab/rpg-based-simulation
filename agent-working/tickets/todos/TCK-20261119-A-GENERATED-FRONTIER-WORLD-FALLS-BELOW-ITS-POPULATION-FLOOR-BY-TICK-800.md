---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261119-A-GENERATED-FRONTIER-WORLD-FALLS-BELOW-ITS-POPULATION-FLOOR-BY-TICK-800
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-A-GENERATED-FRONTIER-WORLD-FALLS-BELOW-ITS-POPULATION-FLOOR-BY-TICK-800

## Title
generated_frontier_3_42, compiled with its content context, has about 23 of 44 bodies alive at tick 800 on main, below the population-stability floor of 60% (26.4). This is a finding only, to be read across several seeds before anything is claimed

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found during #965 (kind step 5) by rpg-implementer-2's popdiag3 probe (executed, summary sha256 e0a42c1e, 2026-11-19). Filed by rpg-planner on rpg-designer's ruling.
- The test test_corpus_diversity::test_generated_frontier_3_42_extended_population_stability compiles this world WITHOUT a content context, and passes on main.
- Compiled WITH the context, the path every src/tools caller uses, trial 0 has about 23/44 alive at t800 on main 77e4aeb72, and 18/44 on #965 aca8891ff. The floor is 26.4.
- Deaths by engine cause on main with context: COMBAT 12, HAZARD 7, DEFEAT 2. There is no STARVATION, so this is not the hunger-collapse rule (#715 6999193768).
- Limits: n = 1 per arm, and the tick-budget watchdog tripped in every arm, so the counts are noisy. Nothing is claimed beyond "one run fell below the floor".

## Scope
1. A multi-seed read of generated_frontier_3_42 with its context on main: alive per day, deaths by cause and the watchdog trip count. Each run gets its own S9, with its bar and its period stated before data (the bar-period rule).
2. If the drop holds: attribute it (which kinds die, and to what), then hand it to rpg-designer for a ruling.

## Out of Scope
- The #965 interim (TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE, item AC).
- Any balance change before the read.

## Acceptance Criteria
- A multi-seed result with its S9 record, plus a designer ruling: real instability, or watchdog noise.

## Related Tickets
- TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE (stage 4b, item AC: the population test should compile with a context, which would expose this)
- TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD (#965, where it was found)

## Related Docs
- docs/mechanics/05_world_evolution.md

## Related Stored Artifacts
- /mnt/data2/rpg-measure/m1step5/popdiag/popdiag3_summary.txt (sha256 e0a42c1e…), out3_*.txt

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py:515-529; the generated_frontier_3_42 world content

## Assumptions / Open Questions
- rpg-designer's open balance question (report-only under the M1 pace): goblin_survival declares hunger "medium", which is 1.0x base, against humans at 0.5x. Is medium the intended level?

## Durable state, lifecycle and clocks
None. This is a read only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
