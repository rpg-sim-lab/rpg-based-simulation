---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261117-EVERY-WORLD-STARTS-AT-MIDNIGHT-SO-EVERY-SHORT-RUN-IS-DARK
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-EVERY-WORLD-STARTS-AT-MIDNIGHT-SO-EVERY-SHORT-RUN-IS-DARK

## Title
Every world starts at t = 0, which the clock calls night, so every short scenario and every run's first 600 ticks are dark

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
A Phase 3 BALANCE and world-clock design ticket (rpg-designer, 2026-11-17).
- Under the night helper (owner Q1) the ticks 0-599 of every day are night.
- With honest perception (PERC-02a, owner Q2a), day-sighted bodies see two levels worse at night.
- Every world starts at t = 0, so every scenario under 600 ticks and the first 600 ticks of every run are dark.
Evidence:
- test_bravery_quartile_combat_rate_2x (0-400 ticks) fell from about 1.74× to 1.20× under 02a. Top 0.3835, bottom 0.3185: the bravery spread compresses at night. Its scenario was given a day clock in the 02a PR.
- The slow corpus grade pins moved by 02a (frontier_extended s42 NARRATIVE; s123 COMBAT, PROGRESSION and NARRATIVE).
This colours every short-run pin and early measurement.

## Scope
1. Decide (designer, then owner if needed) whether a world declares its start hour (content, or a scenario field), or whether the clock starts at day.
2. List every short scenario and pin affected.

## Out of Scope
- The night rule itself (Q1/Q2a stand).

## Acceptance Criteria
- A ruled start-hour rule with a test.
- The affected pins and scenarios are listed and re-read under it.

## Related Tickets
- TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY
- TCK-20261117-THE-SLOW-CORPUS-GRADE-PINS-ARE-STALE-ON-MAIN

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-08), docs/world_rules/knowledge-agency/perception.md (PERC-02)

## Related Stored Artifacts
- none

## Related Code Areas
- src/core/calendar.py, world assembly (the start tick)

## Assumptions / Open Questions
- Phase 3, not gating Phase 1.

## Implementation Notes
- Filed by rpg-planner on rpg-designer's ruling.

## Test Summary

## Files Changed

## Completion Summary
