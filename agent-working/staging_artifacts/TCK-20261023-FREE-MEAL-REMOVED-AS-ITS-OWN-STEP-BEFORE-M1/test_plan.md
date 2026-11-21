---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1
artifact_type: test_plan
tags: []
---

# Test plan (D73)
Constructed (tests/unit/engine, new file `test_free_meal_removed.py`):
- A broke subject beside an inn issues EAT: hunger unchanged, gold unchanged, transfer rejected (ACTION_EXHAUSTION), building purse unchanged.
- A subject holding exactly 5 gold: hunger -60, gold -5, building +5, `last_meal_tick_set`, ONE accepted transfer (atomic: no state where hunger fell and gold did not; assert via the resolver, not by hand).
- A subject holding 4 gold: refused, nothing moves (no clamp).
- REST: broke gets no bed, no hp, no readiness; 10 gold pays in full and gets hp +5, readiness +10; held sleep repeat pays once (existing rule).
- EAT with nothing carried, no inn: no hunger change, typed failure, task ends, no readiness burn.
- Carried food and corpse meals unchanged (existing tests stay green: `test_eat_carried_before_travel.py`, corpse-meal tests).
- Scorers: EatScorer/FatigueScorer do not offer the inn to a subject under the price; do offer it at the price; the under-price subject takes `_hunger_without_open_way`.
- Conservation: total coin conserved on a paid meal and on a refused one (Bible 03); `HardLawMonitor` clean.
- Gate: V4 test `test_v4_counts_a_forbidden_meal_through_the_real_kernel.py` stays meaningful (forbidden diet meal still counted); a 1500-tick gate compute shows V1 = 0 and the known entry is removed in the same change (registry lint green) per Q4.
- Existing tests to re-run and update where they assert free meals or 20+40: grep `INN_MEAL_HUNGER`, `hunger_delta=-40`, `EAT_PRICE_GOLD` in tests/ (scope pytest to tests/unit/engine, tests/unit/ai, tests/mechanic_scenarios, tests/integration/observability); no full suite.
- Determinism: two-run digests (paired --self-check spread 0) and cross-hashseed unaffected (no new hash).
- Measurement as in plan.md (paired step after the planner's "host free").

## written at close (2026-11-21): the tests as landed (the text above is the 2026-10-28 v1 test plan, kept as history)
- New tests (new files need no owner ask): tests/unit/ai/test_seek_work_step.py (17 cases, executed green at abcf86774 and in the sweep), tests/unit/actions/test_held_eat_failure_ends_task.py (8 cases), plus the worker-index and price_fields/terms tests with their commits.
- Executed at 261b5600a (2026-11-21): parity-schema OK (0 rose, 0 new); code-health OK (2 new, 2 worse, 4 report-only, same as fb116ef3); typecheck rc 0; lint-imports 17 kept; tests/unit/** by directory: 85 red = 77 rows of freemeal-logs/d73_per_test_table_fb116ef3_abcf867.tsv + 8 corpus_diversity grade rows (5 known lane-B rows + hero_guild_routing / unit_selfmodel_pilot / urban_political s42 1000t), nothing newly red vs fb116ef3, 3 stopped being red (the amended seek tests). Map: freemeal-logs/red_at_261b5600_map.tsv.
- The 77 table rows are existing MAIN tests that pin the old free-meal behaviour or the CLAMP law (classes REWRITE per law 23, A FUND 21, BEHAVIOUR 13, B RESHAPE 12, C REMOVED LAW 6, the `test_service_admission.py:51` law-constant pin 1, D NEW STEP 1 = `test_project_end_sites` adds engine/tactical_objective.py). They are NOT edited in this PR before the single owner ask clears them.
- Not yet run: the grade rows re-pinned at the final head (rule (a)), the forced-broke and seek controls and the digest proof carry over from the approved kit v3.5 runs recorded in the ticket, the W cells.
