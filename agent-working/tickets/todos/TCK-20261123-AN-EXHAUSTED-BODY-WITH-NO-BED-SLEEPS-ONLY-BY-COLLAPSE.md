---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261123-AN-EXHAUSTED-BODY-WITH-NO-BED-SLEEPS-ONLY-BY-COLLAPSE
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-AN-EXHAUSTED-BODY-WITH-NO-BED-SLEEPS-ONLY-BY-COLLAPSE

## Title
An exhausted body with no bed way never chooses to sleep; it sleeps only by collapsing

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by rpg-designer's h3 trace read (freemeal_pre/trace_h3_designer_read/READ.md, kit v7, 13844fee8 urban_political s42; executed reads):
- Human 3's fatigue ranks first in utility from t17798 to t18658, at 130-190, but never wins. It has no target and no affordable bed.
- The body sleeps only by the tactical collapse at fatigue 100: 421 ticks, 18638-19058. That collapse made up most of #995's 619-tick P2 over-line.

## Scope
1. Read why the fatigue goal has no target without a bed way. Candidates: the goal's target rule, the bed admission, or whether sleeping in place exists as a typed way.
2. rpg-designer rules a fix, kind-neutral and from properties. For example: a typed way to rest where the body stands, with its own risk. Mechanic-scenario tests plus a failing control.
3. Measure the effect on the collapse count and the over-line time against the base.

## Out of Scope
- The maintenance slot contest (T1: TCK-20261123-A-SECOND-WORKER-STARTS-A-MAINTENANCE-SHIFT-ANOTHER-ALREADY-HOLDS-AND-LOSES-IT-UNPAID).
- Bed prices.

## Acceptance Criteria
1. The cause is named (inspected or executed).
2. The fix and its tests land. A tired body with no bed way rests by choice before the collapse line, or the designer records why it must not.
3. The measured collapses and over-line time are reported.

## Related Tickets
- TCK-20261123-A-SECOND-WORKER-STARTS-A-MAINTENANCE-SHIFT-ANOTHER-ALREADY-HOLDS-AND-LOSES-IT-UNPAID; #995

## Related Docs
- docs/world_rules/life-body/survival-needs.md; docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- /mnt/data2/rpg-measure/freemeal_pre/trace_h3_designer_read/

## Related Code Areas
- src/ai/goals/ (the fatigue goal); the tactical collapse sleep; the bed admission

## Assumptions / Open Questions
- Order: the backlog, after T1.

## Durable state, lifecycle and clocks
To be filled at scope.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
