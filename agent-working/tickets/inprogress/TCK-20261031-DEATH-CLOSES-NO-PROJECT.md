---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-DEATH-CLOSES-NO-PROJECT
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-DEATH-CLOSES-NO-PROJECT

## Title
Death closes no project: a dead entity keeps ACTIVE and SUSPENDED project records

## Status
INPROGRESS (dispatched by rpg-planner 2026-11-25; rulings a-d on #715 relay; code written, tests held for the host)

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Split from TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, Q4 (rpg-ubuntu-simq-anchor-bisect-impl d2ed6c8c2, agent-working/staging_artifacts/TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT/evidence/retention_trace/; 15 runs per commit, 3 worlds x s42-46, 2000t). a25619971: 368 dead, 229 with a current project, 240 with an ACTIVE project, 4 with an ACTIVE retreat. d914bace7: 379, 235, 253, 24. About 62-67% of the dead keep a live project at both commits: death closes nothing. Designer: a durable-state lifecycle gap, an ACTIVE record with a dead owner; the history is kept, the status is not.

Rule (designer): death ends every live project of the dead entity (ACTIVE and SUSPENDED) with a typed ended_by DEATH. Records are kept, not deleted.

## Scope
Phase 1 (counts and readers, read-only, before any fix shape):
1. Readers: does anything read a dead entity's live projects today (the :1610 orphan/make-current path, kind counts and capacity, read models and presenters, SimQ pillars, campaign detectors)? Each reader is a finding; any reader means main will not stay hash-identical.
2. Normalise "4 vs 24 dead with an ACTIVE retreat" by retreat projects started per commit (#769 starts more retreats). If the rise is not volume, report it as a finding to rpg-designer.
3. The 2 dead entities per commit whose last dead record is earlier than the last tick: explain.
Phase 2: fix shape after rpg-designer reads Phase 1.

## Out of Scope
- The retreat exit (TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT).
- Orphans from current_project_id clears (TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS) and SUSPENDED never resumed (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK).
- Deleting project records of the dead.

## Acceptance Criteria
(Phase 2, designer to confirm) On death every live project of the entity ends with a typed ended_by DEATH through the authoritative apply path; records are kept; a unit test covers ACTIVE and SUSPENDED; the dead-with-live-project count is 0 on the gate worlds; main hash-identical or every changed run attributed to a reader named in Phase 1; Bible 04 / parity ledger row for the project lifecycle on death.

## Related Tickets
- TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT; TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS; TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK; TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED

## Related Docs
- docs/mechanics/04_strategic_cognition.md; docs/core/entities.md (entity lifecycle)

## Related Stored Artifacts
- rpg-ubuntu-simq-anchor-bisect-impl d2ed6c8c2: evidence/retention_trace/README.md, width_tables.md

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (project lifecycle, :1610 path); the death apply path (to locate)

## Assumptions / Open Questions
- Order: after the retention fix, unless the reader check shows :1610 depends on it (designer). The :1610 path (now live_record_route / orphan_switch_candidate near intelligence.py:1550) skips dead bodies (alive/active filter), so it does not depend on this.
- Candidate follow-up (not filed): a dead body's quest project ends ABANDONED while `quest_status` is unchanged.

## Implementation Notes
Rulings (rpg-planner, 2026-11-25): (a) ABANDONED, `ProjectEnd.DEATH`; (b) staged in `LifecycleSystem.resolve_lifecycle`'s death block via a typed StrategicUpdate; the 1-tick passive-death lag is a limit line; (c) `quest_status` left alone (limit line; follow-up candidate, no ticket yet); (d) `current_project_id_set=""` in the same update. Divergence 2.226 (lane C's births branch takes 2.225). Phase 1 item 1 (readers) is in staging investigation.md; items 2 and 3 ride the measured step.

## Test Summary
Written, NOT RUN (the host is held by another lane): tests/unit/strategic/test_death_ends_live_projects.py, tests/unit/strategic/test_project_end_record.py (enum-set pin gains DEATH).

## Files Changed

## Completion Summary
