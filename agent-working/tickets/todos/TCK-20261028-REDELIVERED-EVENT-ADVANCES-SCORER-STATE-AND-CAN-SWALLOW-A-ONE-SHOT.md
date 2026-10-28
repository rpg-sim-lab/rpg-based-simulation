---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261028-REDELIVERED-EVENT-ADVANCES-SCORER-STATE-AND-CAN-SWALLOW-A-ONE-SHOT
phase: open
date: 2026-10-28
tags: []
---

# TCK-20261028-REDELIVERED-EVENT-ADVANCES-SCORER-STATE-AND-CAN-SWALLOW-A-ONE-SHOT

## Title
A redelivered event still runs through the stateful scorers before the accumulator dedupe, so it advances scorer state and can consume a one-shot whose record is then dropped

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Follow-up to TCK-20261028-QUALITY-HUB-WRITES-A-SCORE-LINE-FOR-A-REDELIVERED-EVENT (batch 07a88d8f8), raised by lead-planner-u24 in review. That fix stops the duplicate score line: QualityHub writes only when PillarAccumulator.add returns True, deduped per (event_id, pillar). But QualityHub.on_envelope (quality_hub.py ~157-180) calls scorer.score() for every delivery, before the dedupe. Several scorers mutate state inside score():
- agency.py:119-121 `_entity_defer_streak` increments on each defer_with_reason delivery, so a redelivery lengthens the streak.
- agency.py:112, :141 and the `*_fired` one-shots in cognition, combat, economy, faction, information, narrative, progression, social and world_dynamics: if the one-shot condition first becomes true on a redelivered envelope, the flag is set, the record carries the redelivered event_id, the accumulator drops it as already seen, and the penalty is never counted.
- combat.py:80 `_seen_modifiers`, faction.py:81 `_war_tick`.

## Scope
1. Measure first: does redelivery happen in a real run (count envelopes whose event_id was already seen by the hub, light run <=300t, one world). Report the count before the fix shape.
2. Fix shape (if count > 0, or as a guard if 0 and rpg-planner agrees): skip a seen event_id at hub entry, before translation and scoring, so no scorer sees a redelivery. Keep the per-pillar accumulator dedupe as the inner guard.
3. Test: a redelivered defer_with_reason does not lengthen the streak; a one-shot whose condition is met on a redelivery is not consumed.

## Out of Scope
Scorer logic, weights, _entity_count (always 0, separate).

## Acceptance Criteria
- Hub-level seen-event guard with a bounded or run-lifetime set (state which, and its memory cost at 5000t).
- The two tests above pass; tests/simulation_quality passes.
- Pure-run digest unchanged (quality scoring is off the authoritative path; show by code read plus a short-run hash equality).

## Related Tickets
TCK-20261028-QUALITY-HUB-WRITES-A-SCORE-LINE-FOR-A-REDELIVERED-EVENT

## Related Docs
docs/guides/observability.md

## Related Stored Artifacts
None.

## Related Code Areas
src/simulation_quality/quality_hub.py, src/simulation_quality/pillar_accumulator.py, src/simulation_quality/scorers/

## Assumptions / Open Questions
- Whether real redelivery occurs at all (queue retry path) is unmeasured.

## Implementation Notes
Filed on the rpg-planner seat; not dispatched.

## Test Summary

## Files Changed

## Completion Summary
