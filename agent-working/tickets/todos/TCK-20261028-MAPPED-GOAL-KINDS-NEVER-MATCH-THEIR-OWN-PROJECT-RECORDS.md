---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261028-MAPPED-GOAL-KINDS-NEVER-MATCH-THEIR-OWN-PROJECT-RECORDS
phase: open
date: 2026-10-28
tags: []
---

# TCK-20261028-MAPPED-GOAL-KINDS-NEVER-MATCH-THEIR-OWN-PROJECT-RECORDS

## Title
ADVENTURE_ROUTE, SOCIAL_CONTRACT, REGION_STABILIZATION and OCCUPATION_CHANGE candidates never match their own project records, so each win below the cap may add another live duplicate

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found by rpg-implementer during :1610 (TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED). These four candidate GoalKinds are mapped (RouteToProjectMapper and similar) to a ProjectKind that differs from the candidate's own kind. So the existing-record lookup `p.kind == best_candidate.kind` (intelligence.py near :1610) never matches them: their lookup is always "no record", and each win goes through the cap gate as a new project. rpg-designer (2026-10-28) asked for its own ticket, investigation first, separate from :1610.

## Scope
Investigation only, then numbers to rpg-designer before any fix shape:
- On the corpus seeds (the gate worlds, s42-46), per mapped kind: live projects per entity (duplicates, and the maximum held at once), and how often each is refused at the cap.
- The mapping table: candidate GoalKind -> ProjectKind, and where it is built.

- First numbers (rpg-implementer, :1610 head c32db1a41, frontier_living_world s42-46, 5000t, event probe; /mnt/data/scratch-rpg-implementer/c1610/need/):
  - region_stabilization: 1581 gate refusals, plus 12688 'no create' events with no record and no gate refusal. rpg-designer (2026-10-29) reads the 12688 as probably the fresh-path switch loss (evaluate_project_switch returns None) at scale. Split the 12688 into switch-lost vs other.
  - adventure_route, social_contract, occupation_change: 0 events. The candidate never won, so these are "not exercised in 5000t frontier" and the ticket makes no claim about them.
  - Base counts for all four kinds come from the queued base rerun need_probe_base.py on d914bace7, which runs after lane B's D73 traces. The long probe logged only kinds that already had a record, so it has no base numbers for them.
  - Related: TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH (the same switch-loss shape for need kinds).

## Out of Scope
- Any fix before rpg-designer's ruling.
- :1610 (keeps the kind comparison as is).

## Acceptance Criteria
- A counts table per mapped kind (duplicates, max held, cap refusals) from pure probes (state hash equal with and without the probe), sent to rpg-designer through rpg-planner.
- The ticket says whether the counts make it M1-blocking (rpg-designer: not M1-blocking unless the counts say so).

## Related Tickets
- TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED

## Related Docs
- docs/mechanics/04_strategic_cognition.md (project hierarchy)
- docs/guidelines/intentional_divergences.md 2.77, 2.137

## Related Stored Artifacts

## Related Code Areas
- src/engine/intelligence.py (existing-record lookup)
- RouteToProjectMapper and the other GoalKind -> ProjectKind mappings

## Assumptions / Open Questions
- Sequenced after :1610 lands, so it reads the new lookup. Not dispatched yet.

## Implementation Notes

### Like-for-like probe, 2026-10-29 (lane A, need_probe_base.py; data /mnt/data/scratch-rpg-implementer/c1610/needbase/ and needc/)
- Same wrapper both arms, frontier_living_world s42-46, 5000t, base d914bace7 vs :1610 c32db1a41. Counts per decision tick.
- Strict gate refusal = no live record, no create, count at cap, no escalated need. Base 3081 -> new 6814: combat_engage 533->2433, resolve_blocker 1521->2269, region_stabilization 240->1581, town_return 460->175, harvesting 59->146, fatigue 52->77, recover 113->75, combat_retreat 68->31, hunger 29->25, reach_location 6->2. No hunger/fatigue refusal is escalated in either arm.
- NO-CREATE SPLIT: every no-create event is a lost switch in both arms (switch='None' on all 13296 base and 13041 new; zero 'update', zero no-call). There is no "other" cause.
- region_stabilization: 13091 (base) vs 12688 (new) lost-switch no-creates; refusals 240 -> 1581.
- adventure_route, social_contract, occupation_change: 0 events in both arms (the candidate never won). These three still need a scenario that exercises them before any fix is judged.

## Test Summary
## Files Changed
## Completion Summary
