---
status: historical
layer: combat
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER
phase: done
date: 2026-11-15
tags: []
---

# Plan: past the starving line, a swing left behind no longer counts as an act

Implements rpg-designer's FINAL design v1 as written (owner #715 6894693356). Branch `rpg-d1-starving-hit-reach` (worktree /mnt/data2/rpg-wt/d1hit, off origin/main f94417e6f). Plan only until rpg-designer reviews it. No push, no heavy run, no delete.

## Change 1: one predicate (src/engine/tactical_threat.py)
`_hit_acts_on(hostile, subject, tick)`: keep the existing window test; add, when `subject.biological.hunger >= STARVING_LINE`, the reach test `abs(hx - sx) + abs(hy - sy) <= max(1, hostile.combat.range)`.
```
hit_tick = subject.combat.last_hit_tick
if hit_tick is None or subject.combat.last_attacker_id != hostile.id or tick - hit_tick > NEED_WAKE_CADENCE:
    return False
if subject.biological.hunger >= STARVING_LINE:      # past the starving line only
    return _distance(subject, hostile.navigation.position) <= max(1, hostile.combat.range)
return True
```
- `STARVING_LINE` imported from `src.engine.starvation` (module has only a dataclass import: no cycle, no layer change expected; the import-layers check will confirm). No new constant. `_distance` already exists in the file (takes an entity and a position).
- `hostile_acts_on`, `need_yields`, `_panic_holds`, `_need_path_first`, `_panic_yields_to_need` and `acting_threat_to` are untouched: they all reach the predicate through `hostile_acts_on`, so the rule stays "one predicate pair, re-derived nowhere". Term (a) `_task_acts_on` is untouched (a pursuing or attacking task still counts at any distance).
- Docstrings of `_hit_acts_on` and `need_yields` get the past-line sentence.
- Not changed: engagement ordering (ubuntu ticket 2), the hp<15% branch order, the sleep-debt side of `_panic_holds`.

## Change 2: tests (the designer's 7)
Unit, tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py (same file/fixtures, subject hunger set through the builder):
1. past the line, last attacker at distance 5, task None, within 10 ticks -> not acting;
2. same but adjacent -> acting;
3. same at distance 5 with a PURSUE task on the subject -> acting (term a);
4. below the line at distance 5 within 10 ticks -> acting (unchanged);
5. a ranged hitter (range 4) at distance 3 past the line -> acting.
Tactical, tests/unit/tactical/ (beside test_held_panic_falls_through.py):
6. a starving subject with a held panic and the hitter out of reach falls through to the need path (the A shape); with the hitter adjacent the panic stands.
Integration (real kernel, built fixture), tests/integration/... (modelled on test_starving_wounded_merchant_eats_through_the_real_kernel.py):
7. a starving wounded subject one tile from an inn, hit by a hostile that then moves >= 3 tiles away, eats within 2 ticks; the old code flees. I will run it on the old predicate first to show it fails there (red), then on the fix.

## Change 3: docs, ledger, divergence (same change)
- docs/mechanics/04_strategic_cognition.md, the LAW P paragraph: add "past the starving line, a hit acts only while its hitter can still reach the subject (Manhattan <= max(1, range)) or pursues or attacks it; below the line the 10-tick window stands".
- docs/guidelines/intentional_divergences.md: new entry, rationale class **Bug Fix**, cross-referencing 2.135 and memo row 88, with the Verification test path. Number: **2.207**. 2.206 is RESERVED by lane A's HOLD branch (local, not yet on main; rpg-planner, 2026-11-15), so D1 does not use it. If HOLD or another PR lands a 2.207 first, I merge origin/main and renumber.
- docs/parity_ledger/strategic_cognition.yaml: a new row (id: the next free one in that shard at write time; COMB-353 is taken by HOLD and is not reused, ids checked against origin/main and the HOLD branch's reservation before I write it) beside the LAW P rows (4675/4685), status verified, test_path = the unit file, divergence_note pointing at the new section; checked with `python3 tools/parity_ledger_writer.py --check <shard> --base origin/main` (the tool is check-only now, the entry is hand-written).
- docs/world_rules/life-body/survival-needs.md SURV-07 text only if it states the 10-tick hit window without the line (to check while writing; otherwise untouched).
- mechanism registry: `registries/mechanisms.yaml` binds `tactical_decision` to `hostile_acts_on` / `acting_threat_to`; no entry is added or retargeted. Its content is rpg-planner's, so if the changed-code advisory (`mechanism_registry_changed_code_check.py`) names an entry I will report it to rpg-planner rather than edit it.
- Ticket close: Test Summary, Files Changed, Completion Summary; working_log through `record_hand_orchestrated_closure.py` (hotfix-style monitoring is not used: tier is standard, so the staging artifacts move to stored_artifacts at close).

## Verification before any report
- New tests green; the whole of tests/unit/tactical, tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py, test_survival/need tests that touch `last_hit_tick` (listed in test_plan.md) green, single process only (`-n 0`), >= 3500 MB available and no measurement running.
- Fixtures that already put a starving subject beside a far past hitter may change meaning; any such existing test is read and reported to rpg-designer/rpg-planner, never edited to pass (CLAUDE.md gate rule).
- Gates the diff can touch: mypy baseline, code-health registry, import layers (engine -> engine, none expected), mechanism registry advisory, docs registry regeneration, divergence/ledger validators. Each run only on a free host.
- Measurement (paired 3 worlds x s42-46 x 5000 ticks, rows r1 and r2, the V3 cells re-read, rpg_gate_known.yaml) is NOT part of this build: it waits for HOLD stage 2 and rpg-planner's slot. Landing is a later owner ask.

## Questions for rpg-designer before Implement
1. Past-line trigger: the design says hunger >= STARVING_LINE; `_panic_holds` itself uses `hunger >= HUNGER_LINE or sleep_debt >= SLEEP_LINE`. I read the fix as hunger only (sleep-debt-collapsed subjects keep the 10-tick window). Confirm.
2. `max(1, hostile.combat.range)` uses the hitter's CURRENT range attribute with plain Manhattan distance and no line-of-sight test (a ranged hitter behind a wall still "reaches"). Confirm that is the intended cheap reading.
3. Range comparison uses the positions at the decision tick (hitter's current position), not the hit position. Confirm.
