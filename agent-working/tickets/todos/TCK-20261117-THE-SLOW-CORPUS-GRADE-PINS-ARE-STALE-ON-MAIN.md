---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN

## Title
The slow corpus grade-stability pins in test_corpus_diversity.py fail on main, so they are stale; re-anchor them in Phase 3 with the boundary reads

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found in M1 Phase 1 (2026-11-17) by rpg-implementer-4 and checked by rpg-planner. The @slow grade-stability tests in tests/unit/worldassembly/test_corpus_diversity.py fail locally on main's behaviour, so their anchors are stale on main, not moved by any Phase 1 PR. The CI lanes run "not slow", so CI never runs them. The night helper is identical to main below t=3000, and its runs reproduce the same numbers (a proof run on bb26e4e5f confirms it); kind=species step 4 gives the same numbers again.

Pins failing on main (anchor → main):
- urban_political s42 1000t SOCIAL: 51.887 → 36.50;
- urban_political s123 1000t SOCIAL: 53.8 → 31.63; WORLD 0.32 → 0.19; PROGRESSION 0.42 → 0.30;
- hero_guild_routing s42 1000t COGNITION: 2.10 → 4.21;
- simq_routing_test s42 500t and 1000t COGNITION: no-data → S 2.89, an artefact of TCK-20261117-THE-COGNITION-SCORER-COUNTS-ONE-STALE-DIVERGENCE-ONCE-PER-TICK;
- urban selfmodel_probe s42 200t: 1 pillar;
- frontier_extended s123 200t: 1 pillar.
The urban SOCIAL drop is mostly normalisation (raw divided by the last tick with SOCIAL events), and the early stop comes from the N10 slot leak (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK).

Owner ruling #715 6941107808 (rule a): a Phase 1 PR re-pins only what its OWN change moves vs main, with attribution, and lead-planner-u24 verifies and records it before the push. Main's stale pins are covered by this ticket instead.

## Scope
1. In Phase 3, after the boundary reads, re-anchor each stale pin under a ruling, with the cause named per pin.
2. Don't re-anchor the simq_routing COGNITION pins until the scorer ticket is fixed.
3. Decide whether some of these slow tests belong in a CI slow lane, so they can't go stale unseen again.

## Out of Scope
- Pins a Phase 1 PR moves vs main (owner rule a, recorded per PR).

## Acceptance Criteria
- Every pin listed above is re-anchored under a ruling, with its cause, or retired.
- A recorded decision on running the slow corpus tests in CI.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261117-THE-COGNITION-SCORER-COUNTS-ONE-STALE-DIVERGENCE-ONCE-PER-TICK
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py

## Assumptions / Open Questions
- Whether the anchors went stale over several earlier merges; a bisect is optional.

## Implementation Notes
- 2026-11-19 CURRENT VALUES on main (rpg-planner; executed by lane C's fresh 5713e2025 main control and lane B's sweep at 79a93da88, which is main 025be2faf plus #965; confirmed identical by births on 025be2faf). The 5 failing grade-stability pins are:
  - urban_political s123 1000t: SOCIAL 39.691 and ECONOMY 0.3083 (anchors 53.8 and 0.4966). This replaces the 31.63 recorded on 11-17; main has moved since.
  - urban_political selfmodel_probe s42 200t: WORLD 0.16 (anchor 0.32).
  - generated_frontier_3_42 s123 200t: COMBAT 0.1869 (anchor 0.3402). NEW to this list.
  - frontier_extended s42 200t: NARRATIVE 1.59 (anchor 2.2778). NEW to this list.
  - frontier_extended s123 200t: COMBAT 0.2323 and PROGRESSION 0.5879 (anchors 0.2914 and 0.4241).
  The hero_guild_routing and simq_routing rows listed above are not red at these heads. Phase 3 re-anchors against values read fresh at that time, not against this list.
- Filed by rpg-planner. The test-tree owner (testing-planner) is told on its restart, through the lead.

## Test Summary

## Files Changed

## Completion Summary
