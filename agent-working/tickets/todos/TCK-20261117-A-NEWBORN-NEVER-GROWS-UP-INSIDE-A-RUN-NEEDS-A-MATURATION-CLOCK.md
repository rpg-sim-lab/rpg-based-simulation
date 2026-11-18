---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-NEWBORN-NEVER-GROWS-UP-INSIDE-A-RUN-NEEDS-A-MATURATION-CLOCK

## Title
A newborn stays a child for 3,456,000 ticks, so no second generation exists inside any measured run

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Owner backlog, not M1. rpg-designer-ubuntu's births rulings v2.1, D4, say to file this with the births batch. A newborn is born at age_ticks 0 (Q11). LifeStageService ends CHILD at 3,456,000 ticks (12 fantasy years), and births need ADULT parents. So in every measured run a newborn stays CHILD, no second generation exists, and "camps refill by births" means a single generation. The births step discloses this. This ticket decides whether newborns need a maturation clock suited to the run scale, and what it should be.

## Scope
- Rule work first. The owner and rpg-designer decide whether a maturation clock is wanted, and its shape, for example per species and declared in content. It is a ch01 change.
- Then the content declaration and the life-stage transition, with no path ever treating CHILD as ADULT.

## Out of Scope
- Any M1 item.
- The CHILD body scale (TCK-20261117-A-NEWBORN-HAS-AN-ADULT-BODY-UNTIL-A-CHILD-BODY-SCALE-EXISTS).

## Acceptance Criteria
- A newborn reaches ADULT on a declared clock, and every LifeStage gate keeps applying until it does.

## Related Tickets
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
- TCK-20261117-A-NEWBORN-HAS-AN-ADULT-BODY-UNTIL-A-CHILD-BODY-SCALE-EXISTS

## Related Docs
- docs/mechanics/01_entity_anatomy.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND/rpg_designer_ubuntu_births_rulings_v2_2026-11-17.md (D4)

## Related Code Areas
src/ai/life_stage.py, src/systems/lifecycle_systems/lifecycle.py

## Assumptions / Open Questions
- Does an accelerated clock conflict with decision 33's tick-to-day time? That is for rpg-designer.

## Implementation Notes
- 2026-11-18, rpg-designer (u24), relayed by lead-planner: a newborn's bonds to its parents seed at 0.8, which equals RelationshipService.FRIEND_SENTIMENT_THRESHOLD, the M1 mate gate for humanoids. Once newborns can reach ADULT, this ticket must add a kin exclusion to mate eligibility. It is moot in M1, because a CHILD is never eligible.

## Test Summary

## Files Changed

## Completion Summary
