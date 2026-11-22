---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM

## Title
Every "can I win" judgement goes through one power-judgement seam

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The owner's direction (#715 7078469868, relayed by lead-planner-u24): "can I win" is ONE power-judgement component, the observer's estimate of the opponent's power from observation, inspection or memory, with no quick inline comparisons.

Step B (TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN) adds the seam `judge_power(observer, other, state) -> PowerJudgement` and uses it. Two known callers bypass it today (a read-only fact from the ubuntu side):
1. CONFLICT-03's hunting/wariness appraisal (the PREDATION/WARY `can_overcome`, src/engine/appraisal.py);
2. src/…/tactical_threat.py:93-94, which compares `apparent_power()` directly (OUTMATCHED), bypassing `OpponentPerceptionService` (src/domains/combat_engagement/perception.py).

rpg-designer (2026-11-22): moving them changes hunting, wariness and flight in every world, which moves the PREDATION/WARY and OUTMATCHED hashes. So it is its own ticket, with its own measurement and disclosure.

## Scope
1. Route both callers through `judge_power`. Remove them from Step B's source-test allow-list, so the list is empty.
2. Decide, with rpg-designer at plan time, whether `judge_power` v2 reads OpponentPerceptionService's observation and memory (basis OBSERVED / REMEMBERED) in this ticket or a later one.
3. Measure the behaviour change: a pre-registered before/after on hunting, wariness and flight counts, with its own S9. Disclose the hash change, and add a divergence entry if behaviour changes.

## Out of Scope
- The seam's introduction (Step B).
- Declared fight dispositions (decision 62).

## Acceptance Criteria
1. No inline power comparison remains anywhere (a source test with an empty allow-list).
2. The measured change is reported and ruled by rpg-designer; the Bible, parity and divergence are updated.

## Related Tickets
- TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN (adds the seam; this ticket follows it)
- TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS

## Related Docs
- docs/world_rules/ (CONFLICT-03, AGENCY-07); docs/mechanics/02_combat_laws.md; docs/mechanics/04_strategic_cognition.md (perception)

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/appraisal.py; tactical_threat.py:93-94; src/domains/combat_engagement/perception.py

## Assumptions / Open Questions
- The exact path of tactical_threat.py is to be confirmed at investigation (cited as relayed).

## Durable state, lifecycle and clocks
OpponentModel memory already exists. This ticket adds no new durable state unless v2 is chosen; then the plan names it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
