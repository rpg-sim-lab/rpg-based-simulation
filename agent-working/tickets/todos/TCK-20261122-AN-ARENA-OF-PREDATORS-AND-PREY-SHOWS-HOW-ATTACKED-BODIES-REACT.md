---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-AN-ARENA-OF-PREDATORS-AND-PREY-SHOWS-HOW-ATTACKED-BODIES-REACT
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-AN-ARENA-OF-PREDATORS-AND-PREY-SHOWS-HOW-ATTACKED-BODIES-REACT

## Title
Report-only arena observation: many meat-eaters against many prey, over several seeds, to see how attacked bodies react (flee, fight, die) as a distribution

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner answer "yes, do both" (#715, newest lead-planner comment, 2026-11-22). Small deterministic mechanic scenarios go into Step A and B, and an arena observation is its OWN ticket: for example 50 meat-eaters vs 50 prey, in groups and alone, over several seeds. It is report-only and never pass/fail, judged as a distribution. It needs its own slot GO.
rpg-designer's intent (it rules the shape when this is planned): one failure signal fixed before data, "never reacts" = any engagement with ≥ 5 consecutive hits on a victim with no flight or fight decision (the R7 no-decision measure), which must be 0.

## Scope
1. An arena world or scenario spec, chosen by properties (no kind named in logic), with group and individual setups, several seeds.
2. Measures: the outcome distribution per engagement (victim killed, victim fled, attacker fled, disengaged), hits per engagement, flight and fight decisions, and the motive per engagement (the motive classifier).
3. The "never reacts" signal = 0, fixed before data.
4. Runs: on frozen trees with verified hashes, under its own S9 and HOST FREE. After Step A, and again after Step B.

## Out of Scope
- Any pass/fail bar other than "never reacts".
- Tuning.

## Acceptance Criteria
1. The shape is ruled by rpg-designer before any run.
2. A report per run, with "never reacts" stated.

## Related Tickets
- TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT (Step A)
- TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN (Step B)

## Related Docs
- docs/world_rules/knowledge-agency/agency-decision.md AGENCY-07

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/rpg_measure/ (the person_attack kit as a base)

## Assumptions / Open Questions
- The arena size and the seed count are rpg-designer's to rule.

## Durable state, lifecycle and clocks
None. This is observation only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
