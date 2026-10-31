---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261101-A-PANIC-FLIGHT-FIRES-WITH-NO-HOSTILE-PERCEIVED
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-PANIC-FLIGHT-FIRES-WITH-NO-HOSTILE-PERCEIVED

## Title
A panic flight fires with no hostile perceived

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Designer follow-up row, 2026-11-01, from the retention batch (TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, lane C, 15 runs, base 6fdfdf555 and fix 23e0f9967). In frontier_living_world s42, entity 29 issues PANIC_RETREAT at t59 (hp 0.09) with no hostile perceived at all, and dies at t59 in both arms. The retention ticket's tactical gate (option A) does not touch this path. COUNTS FIRST: no fix shape before the designer reads the counts.

## Scope
Read-only first: find the path that issues PANIC_RETREAT with zero perceived hostiles (file:line), and count how often it happens across the 15-run set (subjects, ticks, deaths within 20 ticks).

## Out of Scope
The present-threat flight gate (retention option A). Precedence-law sites.

## Acceptance Criteria
- AC1: the issuing path named at file:line, with a trace of e29.
- AC2: counts per world.
- AC3: the designer's ruling recorded here before any plan.

## Related Tickets
TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT; TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE.

## Related Docs
docs/mechanics/02_combat_laws.md; docs/mechanics/04_strategic_cognition.md (AGENCY-07).

## Related Stored Artifacts
The retention batch tables: staging_artifacts/TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT/evidence/full_batch_23e0f9967/analysis_full.md (retreat worktree).

## Related Code Areas
src/engine/tactical.py; src/engine/tactical_threat.py.

## Assumptions / Open Questions
After retention lands. Dispatch needs an owner go.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
