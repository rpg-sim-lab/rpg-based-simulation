---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261101-A-WALKER-WAITS-AT-A-DOOR-TILE-AN-AWAKE-HOLDER-KEEPS
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-WALKER-WAITS-AT-A-DOOR-TILE-AN-AWAKE-HOLDER-KEEPS

## Title
A walker waits at a door or service tile that an awake holder keeps

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Designer ruling 2026-11-01 (F3 Q4): awake door-tile holders are not just a side effect of sleepers. On the F3 arm (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE; 15 runs, urban_political / frontier_living_world / crowded_frontier x s42-46, 5000t), served-bed door sleepers fell about 95%, but awake holders ROSE, base on 6fdfdf555 -> F3 arm (ticks / subjects):
- awake_walker_waiting 36209/164 -> 42999/209 (the designer predicted a fall);
- awake_idle_fatigue_project 57911/153 -> 63296/196;
- awake_other 11306/148 -> 19307/190 (urban 2798 -> 11972; F3's diagnostic (a) classifies it first);
- awake_idle_hunger_project 2951/126 -> 3901/160.
COUNTS FIRST. No fix shape before the designer reads the counts.

## Scope
Read-only counts, measured AFTER N14 lands on top of F3, on the same 15-run set:
1. For each awake_walker_waiting tick, what the walker is waiting FOR: which entity holds its target tile and that holder's category (lodger stepping out, awake fatigue idler, awake hunger idler, sleeper, other).
2. The 153 -> 196 awake idle-fatigue-project holders: why they stand awake on a door tile with a fatigue project current while refused_bed is about 0. Candidates: waiting for the next brain call (cadence), debt below the REST choice line, or something else. Use a per-tick dump of cadence and debt against the REST line.
3. Repeat the F3 holder categories row for row on the N14-on-F3 arm.

## Out of Scope
Any fix (the designer rules after the counts). Bed reservation. The non-person door sleepers on frontier (F3 diagnostic (b)). Precedence-family sites (TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED and siblings).

## Acceptance Criteria
- AC1: the waiting-for table (holder category x world, ticks and subjects) on the N14-on-F3 arm, base stated.
- AC2: the idle-fatigue cause split, from a trace, with how it was measured.
- AC3: the F3 holder categories reported row for row; the probe leaves the state hash unchanged (smoke shown).
- AC4: the designer's ruling recorded here before any plan.

## Related Tickets
TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3); the N14 nav/sleep ticket (2.153 / 2.154); TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT; TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED.

## Related Docs
docs/mechanics/04_strategic_cognition.md; docs/guidelines/intentional_divergences.md 2.153, 2.155; registries/mechanisms.yaml town_services.

## Related Stored Artifacts
Lane B F3 run files n14/out/f3new_*.json (sleeper-lodges worktree).

## Related Code Areas
src/engine (navigation, occupancy), src/ai/goals (fatigue scorer), town services admission.

## Assumptions / Open Questions
Order: after F3 closes and N14 is re-measured on F3 (owner order #715 6543553366). Dispatch needs an owner go.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
