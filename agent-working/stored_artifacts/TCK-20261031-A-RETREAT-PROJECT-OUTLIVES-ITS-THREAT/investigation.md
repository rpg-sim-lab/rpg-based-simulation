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

# Investigation: a retreat project outlives its threat

Base: origin/main `6fdfdf555`. Probe: `evidence/probe7.py` (probe6 from `rpg-ubuntu-simq-anchor-bisect-impl` d2ed6c8c2 plus read-only `capfull` and `live` records), run by `evidence/runw.sh`, `PYTHONHASHSEED=0`, 3 worlds x s42-46 x 2000t, one process at a time, 3 GB cap. Width counts by `evidence/retention_counts.py` (same definitions as Phase 1); output `evidence/width_tables_main_6fdfdf555.md`.

## (a) Where COMBAT_RETREAT's completion facts are defined, and what they test

There are none. Completion is MISSING for this kind; it is not mis-conditioned.

- Per-kind completion lives in `StrategicIntelligenceSystem.evaluate_strategic_intent` (`src/systems/strategic_systems/intelligence.py`, "2. Project Abandonment"): `harvesting` (node exhausted), `hunger` (< 20), `fatigue` (sleep_debt < 20), `career_change` (role no longer CITIZEN), `resolve_blocker` (50-tick timeout, ABANDONED), `shopping` (building not functional, ABANDONED), plus the consecutive-rejection abandon. `combat_retreat` has no branch.
- Arrival completion is `_resolve_active_objective` (same file, ~l.1219): it returns None unless `project.kind == "detour"` and `obj.kind == "reach_location"`. A retreat's objective IS `REACH_LOCATION` toward `town_center` (generic project creation, ~l.1746-1760: `kind=obj_kind or REACH_LOCATION`, `target="town_center"`, `target_pos=state.town_center`), so the objective is typed like a destination objective, but nothing resolves it on arrival. That is why entity 18 sitting at (26,24) next to its destination did not complete: no code looks.
- The shared end predicate `objective_outcome` (`entity_target_objective.py`; used by the evaluator via `close_entity_target_project` AND by `StrategicWorkQueue` to schedule the evaluation) only knows entity-targeted objectives (`target_entity_id`) and contract projects. A retreat has no `target_entity_id`, so it returns None.
- hp is not tested anywhere for retreat. The scorer (`CombatRetreatScorer`, `src/ai/goals/scorers.py`) returns 0.0 when `hp_ratio >= 0.5 and not emotion.is_fleeing`, which only stops it winning selections; it never ends an existing project.
- Why it persists (Phase 1, confirmed again): capacity gate `intelligence.py:1768` blocks new RESOLVE_BLOCKER/RECOVER while 3 of 3 live slots are full; nothing selects against the retreat project.

Precedent for the fix shape: `objective_outcome` is already "the one predicate for has this project's active objective ended", shared with the work queue "so the two can never disagree". A retreat branch there (project kind = combat_retreat, no `acting_threat_to`, no decision-32 adjacent perceived hostile) gets the evaluator and the scheduler for free. Open point for plan.md: `objective_outcome` takes (hero, state, project, objective), enough to compute the threat test.

### What reads `ended_by` / `ProjectEnd` today (for the widening in plan.md)
- Writer: `supersede_record` (`src/core/strategic.py` ~l.407), the only one; sets status ABANDONED + `SUPERSEDED_BY_TARGET`.
- Reader 1: `strategic.py` ~l.344-348, the canonical-dict entry, emitted only when set (a project never ended this way keeps the existing state hash).
- Reader 2: `cognition_export.py:73`, copies `ended_by.value` into exported attributes when set.
- The enum docstring says "set once together with the terminal status ABANDONED"; a THREAT_CLEARED completion pairs with COMPLETED, and lane B's F3 "way closed" needs a second value, so the docstring and the one-writer contract widen in plan.md (generic typed end, not tied to ABANDONED).

## (b) The two SUSPENDED projects filling entity 18's cap; stale SUSPENDED generally (counts only)

Main reproduces the symptom: urban_political s42, entity 18 holds `proj_combat_retreat_42` for 1350 ticks (t43-1402), last present threat t200, hp 1.00 at the end, position (26,24). Final hash `327f8e441f2b678f21d5822b19e076a6ee8c49187f75b88b6a0a15d7cf3c5ad2` (differs from d914bace7's `a745defa...` because main moved on).

Entity 18's live set (logged every 100 ticks, identical throughout): `project_stabilize_bandit_road_t2` (STABILIZE, SUSPENDED, created t2, age 41 at t43 and 1398 at t1400) and `project_stabilize_bandit_road_t22` (STABILIZE, SUSPENDED, created t22, age 21 at t43, 1378 at t1400), plus the ACTIVE retreat. Neither SUSPENDED project is ever resumed.

Across the 15 width runs on main (entity-samples every 20 ticks at cap = live projects >= max_active_projects):
- 15364 entity-samples at cap, over 359 entity-runs that reached the cap (all 359 had a SUSPENDED record in the live set).
- 13150 of the samples (86%) have at least one SUSPENDED project in the live set; 12360 (80%) have one older than 200 ticks; 9586 (62%) have two or more.
- 709 distinct (entity, project) SUSPENDED records older than 200 ticks seen at cap; 1051 distinct SUSPENDED records seen at cap in all, by kind: STABILIZE 218, RESOLVE_BLOCKER 178, COMBAT_ENGAGE 158, HUNGER 120, FATIGUE 120, GUILD 98, HARVESTING 64 (+1), TOWN_RETURN 32, RECOVER 31, COMBAT_RETREAT 15, SOCIAL 13, INVESTIGATE 3.
- Samples where the holder of the retreat is at cap: 339 (of those entity-samples).
These counts go to TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK and the :1610 follow-ups; not fixed or folded in here.

## Width baseline on main (AC1 definitions: Phase 1's; N counted from the last present threat)
15 runs: 14 with any retreat holder, 38 retreat projects. Stale: N=50 8 projects, N=200 4, N=1000 1. Open at run end 0.
- N=200 rows: frontier_living_world s43 e6 (792 ticks after the last threat, hp 1.00), urban_political s42 e18 (1202, hp 1.00), s43 e19 (223, hp 0.26), s46 e12 (268, hp 0.41). N=1000: urban s42 e18 only.
- N=50 only (50-199 ticks after the last threat): frontier_living_world s43 e19 (163, hp 0.20), s44 e36 (79, never threatened, hp 0.10), urban_political s45 e19 (197, hp 0.22) and e23 (126, hp 0.16). So 6 of the 8 N=50 rows end at hp < 0.5 (still hurt: ruling says these go to ordinary re-decision, RECOVER/REST) and 2 at hp 1.00 (fl s43 e6, urban s42 e18).
- Dead entities with an ACTIVE project: 231 of 344 dead (67%), as Phase 1 (death-closes-no-project, other ticket).
- Flapping (retreat -> complete -> retreat within a few selection calls) cannot be measured before the fix; AC1 reports it after.

## Src files the plan would touch (preliminary, for the planner)
`src/systems/strategic_systems/entity_target_objective.py` (retreat branch of `objective_outcome`), `src/systems/strategic_systems/intelligence.py` (only if the evaluator needs the project-kind/typed-end wiring), `src/core/strategic.py` (`ProjectEnd` widening, one-writer helper), `src/systems/strategic_systems/cognition_export.py` only if its output needs a change (it already copies the value). NOT touched: `src/core/state.py`, `src/engine/apply_plan.py`, the group store, the capacity gate (`intelligence.py:1768`) or the :1610 rules.
Docs/ledger: Bible 04 + tactical contract section 4 (a retreat ends when the threat is gone), parity ledger row, intentional-divergences entry (Enforced), mechanism registry entry if the retreat mechanism is cited.

## Disk and slot
Disk 8.2 GB before the runs, 6.9 GB after (above the 6 GB stop line); the probe deletes each run's scratch dir; logs are in scratch.
