---
status: active
layer: testing
authority: P2
audience: agent
tags: []
---

# #992 wolf-starvation read kit: note for the sha review

Author: rpg-implementer-ubuntu, 2026-11-22, on rpg-planner-ubuntu's dispatch (owner dispatch GO #715 7080441579). Ticket (the spec): `TCK-20261122-TRACE-WHY-TWO-WOLVES-STARVE-ON-THE-PREY-STRIKE-BACK-FIX`, on rpg-planner-ubuntu's seat branch `rpg-ubuntu-planner-filings` at `8b86cc4d3`.
BUILD ONLY: nothing here has been run against a world. The real kernel is first met by the smoke, under its own lead GO.

## What it reads
Two NEW-arm starvations that the main arm does not have (frontier_living_world s42 wolf 47 at t3553, s45 wolf 49 at t3969; gate read of #992 at `dffe0a6e1`, #715 7079655858), side by side with main `67c65321`, per tick inside each wolf's window.
The kit records evidence and never judges: the summary has no verdict line and says which reading (exposed / regression) holds nowhere.

## Files (this kit)
| file | what |
|---|---|
| `subject_trace_run.py` | + `plan`, `plan-check`, `summarize`; the death/plan-sha VOID reasons; `items_for("wolf")` (plain then spy per arm and seed); `check --plan --arm` |
| `subject_trace_spy.py` | + `WayReads`, `read_view`, the need/hit/death fields, per-tick `counterparts`, `hits_taken`, `death_records`; bytecode guard first in `main` |
| `subject_trace_summary.py` | new: the side-by-side tables, the FRIENDLY_FIRE_ILLEGAL NEW-only rows, the hunt-end classifier |
| `wolf_starve_launch.sh` | new: the launcher for this read (8 processes; smoke = 2). `subject_trace_launch.sh` stays for the O3 trace |
| `pinned_check.py` | new: refuse to start while any other process is pinned to cpus 4-5 |
| `person_attack_summary.py`, `person_attack_spy.py`, `person_attack_launch.sh`, `subject_trace_launch.sh` | the folded fixes only (below) |
| `tests/tools/test_wolf_starve_kit.py` | 43 new controls; the 35 + 92 earlier controls are unchanged and green |

## How a run goes (each step under its own GO)
1. `cd $KIT && PYTHONPATH=$KIT python3 -B tools/rpg_measure/subject_trace_run.py plan --world frontier_living_world --subject 42:47:2953:3653 --subject 45:49:3369:4069 --expect-death 42:47:3553:STARVATION --expect-death 45:49:3969:STARVATION --out subjects.json`; its `plan_sha256` and the file's sha256 go into the record set (`PLAN_SHA256`, `PLAN_FILE_SHA256`).
2. SMOKE: its OWN plan whose window lies inside the 300 ticks (for example `--subject 42:47:0:300`, no `--expect-death`), `wolf_starve_launch.sh <record.env> <GO> smoke`: NEW s42 plain then spy at 300t, the twin hash compared with the same run's plain.
3. FULL: `wolf_starve_launch.sh <record.env> <GO> wolf`: for each arm (NEW first) and seed, plain THEN spy, 4100t, one process at a time in its own scope (3G, cpus 4-5), watcher per process, the checks, `summary/summary.md` + `summary.json`, `runner.json`, the seal last.
Trees: `git archive` into `/data/vboxuser/o3-trace-trees/<sha>` (NEW `dffe0a6e14e98369d272135108ead954a5e0a536`, BASE `67c65321996642fb9c8f98b06e740839fc5fbd11`), verified EQUAL to `git ls-tree` by `person_attack_tree_check.py`; the launcher re-checks both before the first process. Before the run the kit sha file (the shas of the kit files and `git status --porcelain`) is written beside OUT as in the earlier runs.

## Why each read is pure
Every read runs in the spy's `observe` on the PRIOR state of the tick, through `read_view(state)` = `copy.copy(state)`: a shallow copy of the frozen state. The only writes the reads can cause are cache attributes written with `object.__setattr__(state, ...)` (`WorldIndexService.get_indexes` writes `world_indexes` and the `_index_hits/_index_misses` counters; `SpatialQueryService` writes `_occupancy_map_cache`, `_building_map_cache` and the like). Those land on the COPY, never on the state the kernel keeps. Control: `test_the_reads_run_on_a_copy_so_a_cache_write_never_reaches_the_kernels_state` (real `AuthoritativeState`: a direct `get_indexes` call writes the cache onto the state, a call on `read_view` does not; mutated to `return state` it fails).
| call | what it does (read from the source) | RNG | writes |
|---|---|---|---|
| `ways_in_reach` (ways.py) | `food_hunger_recovery`, `can_eat_item`, `inn_in_reach`, `admits`, `open_food_step_kinds`, `shop_sale_in_reach`, `work_in_reach` | none | none besides the index cache (copy) |
| `open_food_step_kinds`, `opening_steps` (opening_steps.py) | `_forage_step` (loops `state.resource_nodes`), `_scavenge_step` (loops `state.corpses`), `_hunt_step` (`nearby_entities`, `relation`, `is_night`), `_earn_then_buy_step`, `_ask_step`: each returns a new frozen `OpeningStep` | none | index cache (copy) |
| `relation` / `appraise` / `faction_hostile` (hostility.py, appraisal.py) | compares species, properties, faction ids, night and tick | none (grepped: no random, no setattr, no append) | none |
| `nearest_sale`, `plan_sale`, `nearest_work`, `shift_takeable`, `meal_position_after` | loop `state.buildings`, build new intent objects | none | none besides the building index cache (copy) |
| `LeashService.way_in_range`, `can_eat_item`, `food_hunger_recovery`, `is_night` | arithmetic on the entity's own fields; a registry lookup | none | none |
| the kit's own reads (needs, hit record, death record, carcasses) | attribute reads; `copy.copy` | none | none |
The run itself proves it again: the spy's final hash must equal the SAME run's plain twin (`check`; unequal = VOID). The cost of the reads is not measured by the kit (the runs are about the trace, not about speed).

## VOID rules
The existing ones: spy exception or fatal (exit 8), twin hash unequal, ticks unequal, offset drift, 0 rows in a window; plus the plan sha256 not equal to the pinned value (either document), plus NEW s42 wolf 47 not dead of STARVATION at t3553 or NEW s45 wolf 49 not at t3969 in the run's own typed death record (`death_records`: cause and tick). BASE alive is context and is never judged. The stage-2 rule "NEW s42 has no legality call" is OFF for a hand-written plan (the ticket's VOID list does not contain it).

## The folded fixes (TCK-20261122-TRACE-KIT-CALENDAR-LOAD-WRITES-BYTECODE-INTO-A-FROZEN-TREE)
- `load_is_night` sets `sys.dont_write_bytecode = True` around the frozen-tree load and restores the caller's value. The spy child sets it before its first import from the tree, and `child_env` sets `PYTHONDONTWRITEBYTECODE=1`. Control `test_load_is_night_leaves_the_frozen_tree_byte_identical_whatever_the_callers_bytecode_setting` (a positive control in the same run shows the environment would have written a `.pyc`); mutated back to the old loader it FAILS.
- The heavy check also refuses on any other process pinned to cpus 4-5 (`pinned_check.py`, called as `pinned_elsewhere` in the preflight and before every process, in `wolf_starve_launch.sh`, `subject_trace_launch.sh` and `person_attack_launch.sh`). Pinned = `Cpus_allowed_list` shares a cpu with 4-5 and is not the whole machine. Skipped: the checker, its whole ancestor chain (the launcher shell, `kitpy`), kernel threads, empty command lines. It checks the claim on the cpus, not a name, so perf's `obs_cost_arm.py` is caught.
- The END `wall=` line in `subject_trace_launch.sh` is the process's own time (`P0`); the stop rules keep the run's `T0` on purpose. (`person_attack_launch.sh` already used a per-process start.)
- The MotiveReads docstring now says `source` is the entity's own `source_identity`, recorded per row.

## Choices the ticket does not fix
1. A NEW launcher `wolf_starve_launch.sh` (a copy of the stage-2 launcher with the sealed-O3 steps replaced by the plan steps) instead of editing `subject_trace_launch.sh`, so the O3 trace flow and its controls stay as approved; only the folded fixes touch the old launchers.
2. The plan carries `kind: hand_written`, `way_reads: true` (switches the spy's way reads on), `derived_from: {}`, `pad: 0` and the NEW-arm `expect_deaths`; `plan_sha256` = sha256 of the body as in `derive`. The launcher checks the file sha256 AND that `plan_sha256` recomputes.
3. `opening_steps` is called too (beside `ways_in_reach` and `open_food_step_kinds`): it gives each step's own reason string and the HUNT candidate; `steps_consistent` flags a disagreement with `open_food_step_kinds`.
4. Carcasses "within the way range": every carcass within the tree's own `SCAVENGE_RADIUS` (20, Manhattan), each with `in_way_range` (the leash rule), `edible` (the diet gate on its items) and `own_species`.
5. A hit event = the typed `last_hit_tick` changing between the two states; `hp_delta` = hp before minus hp after the apply of that tick (it also contains a drain in the same tick); the typed record holds only the last hit of a tick.
6. The death VOID compares the typed `death_record` (`cause`, `tick`) with the expectation exactly. If the gate's "t3553" is the tick the death was first seen rather than the record's tick, a legitimate run would be VOID: the reason text lists the record tick, the first-seen tick and the passive cause tick so the call can be made from the run.
7. "A hunt" at a tick = the HUNT step's candidate is available AND the subject's own task payload `target_id` or its objective's `target_entity_id` names that same creature (prior state). Last hunt = the last such tick.
8. The hunt-end order: prey dead or absent (any later row) > the last legality call at that target within 20 ticks of the last hunt tick was illegal (`hunt_refused`) > the prey hit the subject within 20 ticks (`prey_struck_back`) > the prey's Manhattan distance on the next row is beyond the hunt radius 10 (`out_of_range_or_fled`) > unknown. Every flag is listed so a reader can apply another order. 20 and 10 are mine; 10 is the tree's `HUNT_RADIUS`.
9. Curves are sampled every 25 ticks (plus the first and last row); the raw rows are all in the cells.
10. FRIENDLY_FIRE_ILLEGAL "absent on BASE at the same (target, tick)" is matched on (attacker, target, tick); the two arms diverge, so a NEW row often has no BASE call at that key at all: the count of those is shown apart.
11. The summary is written into `OUT/summary/` by the launcher even when a cell is VOID; a COMPLETE run without it ends `SUMMARY_NOT_WRITTEN` with RC 7.
12. The per-tick row also carries `counterparts`: every body met this tick (legality targets, the sources of a hit, the HUNT candidate, the task and objective targets) with presence, alive, hp, kind, position and distances.
13. The smoke needs its own plan (a window inside 300 ticks); the smoke's check judges NEW only.

## Not done / limits
- No world was run: the new reads were exercised on fake states and on the real `AuthoritativeState` copy only. Both frozen trees import `WayReads.from_tree()` cleanly and remain EQUAL to `ls-tree` afterwards.
- `ruff` is not applied to the kit (the project's lint scan covers `src/` only).
- The bytecode ticket is not moved to `done/` by this build; it closes with this kit's PR.
