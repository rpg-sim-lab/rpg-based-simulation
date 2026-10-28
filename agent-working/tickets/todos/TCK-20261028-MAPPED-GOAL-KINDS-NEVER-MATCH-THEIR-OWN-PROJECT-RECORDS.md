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
## Test Summary
## Files Changed
## Completion Summary
