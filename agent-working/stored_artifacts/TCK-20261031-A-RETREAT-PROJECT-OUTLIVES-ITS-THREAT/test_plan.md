---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT
phase: done
date: 2026-10-31
tags: []
---

# Test plan: a retreat project completes when its threat is gone

Preliminary: written at the investigation stop; plan.md follows rpg-planner's go.

## Unit (AC2)
1. A COMBAT_RETREAT project with an ACTIVE retreat objective and a perceived hostile that acts on the entity (`acting_threat_to`): `objective_outcome` returns None; the project stays ACTIVE.
2. Same, with a decision-32 orthogonally adjacent perceived hostile and no acting threat: stays ACTIVE.
3. Same entity with no acting threat and no adjacent hostile: the outcome is (RESOLVED, COMPLETED) with the typed end (THREAT_CLEARED); `ended_by` is a `ProjectEnd` value, no reason string, no `lock_until_tick` use.
4. After completion, the threat returns (acting hostile again): the retreat scorer proposes a new retreat; a new project is created through the ordinary path (no resurrection of the old record).
5. Hurt entity (hp < 0.5) with the threat gone: the retreat completes and the next selection is the ordinary re-decision (RECOVER/REST on its own scores).
6. The work queue schedules the evaluation for a retreat whose threat has cleared (shares the predicate with the evaluator): the two cannot disagree.
7. Other kinds are unchanged: a non-retreat project's `objective_outcome` is identical to before (regression pin for harvesting, detour, contract and entity-targeted).
8. Typed round trip: `ended_by` serializes/deserializes and enters the canonical dict only when set (a project never ended this way keeps its hash); `cognition_export` copies it.

## Determinism / hash (AC3)
Gate worlds (frontier_living_world, crowded_frontier, urban_political, s42, 300t and the existing gate set): final hash equal to main, or every changed run is attributed to a completed retreat (first diff is a THREAT_CLEARED end). Procedure: run before/after per world with a state-hash diff of the first divergence tick.

## Width (AC1, AC6) on the heavy slot
3 worlds x s42-46 x 2000t x 2 arms (main `6fdfdf555`, fix), `evidence/probe7.py`, sequential. Gate: stale N=200 and N=1000 are 0 in the fix arm; N=50 and flapping counts reported. Baseline on main: N=50 8, N=200 4, N=1000 1. s42 re-measured at 500/1000/2000t. No death or combat regression: death count, kill/damage tallies and the extinction rule equal or attributed.

## Docs / ledger (AC4, AC5)
Bible 04 + tactical contract section 4 law; parity ledger row; divergence entry (Enforced); mechanism registry entry check (`mechanism_registry_changed_code_check.py`) at close.

## Pre-push checks (lessons from #779)
`python3 -m codebase.health check`, `codebase.structure.import_contracts ci`, the completeness pins test, the perf inventories in-sync test, and the scoped suites (tests/unit/engine, simulation, strategic).
