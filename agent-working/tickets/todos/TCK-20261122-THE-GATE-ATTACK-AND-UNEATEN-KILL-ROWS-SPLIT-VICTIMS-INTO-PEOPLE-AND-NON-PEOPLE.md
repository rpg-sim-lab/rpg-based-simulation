---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261122-THE-GATE-ATTACK-AND-UNEATEN-KILL-ROWS-SPLIT-VICTIMS-INTO-PEOPLE-AND-NON-PEOPLE
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-THE-GATE-ATTACK-AND-UNEATEN-KILL-ROWS-SPLIT-VICTIMS-INTO-PEOPLE-AND-NON-PEOPLE

## Title
The gate's O3 attack row and O6 uneaten-kill row split attackers and victims into people and non-people: redefine both by attacker diet group, over any living victim

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P1

## Request Summary
Owner direction on #715, 7074277591: "No 'person' class at all". All kinds and races are treated equally in the code and differ only by their properties, so a measure must not split people from non-people. The owner then answered the two gate readings (#715 7074345722, owner account, 2026-11-22T04:44:05Z):
- A1, O3: "Yes, every group (Recommended)". One O3 row per exact attacker diet group, for EVERY group declared with t0 population > 0. The value is that group's hits on any living victim, summed over both ledger person flags. An undeclared group stays an error.
- A2, O6.kills_not_eaten: "Any diet with meat (Recommended)". One row per exact diet group that contains meat (meat, meat+plant+prepared, …). The value is that group's kills on any living victim minus eaten kills, with no person filter. Groups without meat get no O6 row. This clarifies 7074315999.
- A3: the person fields in the ledger keys (run_ledger, death_ledger) stay for now. Removing them is a later, separate owner ask.

The designer's reading is the rpg-designer FINAL combined scope, part A (relayed 2026-11-22). Its evidence is the O3 trace run accepted as #715 7074244442 (kit cd3a76430; seal 336487df; copy at /mnt/data2/rpg-measure/o3_trace_cd3a7643_run/). In frontier_living_world, every NEW O3 hit lands on one goblin per seed. Under the new definition the meat move is about 3.4x on s42/s43/s45, and a new meat+plant+prepared context row moves about 1.6x.

## Scope
Read-only list from testing-planner, spot-checked by the ubuntu lead at 613a8365b. The rows that read a person flag in `src/observability/rpg_gate_metrics.py`:
1. O3 (now attacks_on_people):
   - drop the attacker-side wild filter `_is_wild_meat_eater` (:141-143) and the victim flag test (:404);
   - replace the row set `declared_wild_meat_eaters` (:265-271) and `_tick0_persons` (:223-229) with "declared diet groups with t0 population > 0";
   - keep the `_require_declared` guard (:407) so an undeclared group is an error, not a silent row;
   - rename the row id to `O3.attacks_by_group` (testing-planner's name, 2026-11-22).
2. O6.kills_not_eaten: drop the attacker flag (:402), and emit one row per exact diet group containing meat, under the new id `O6.kills_not_eaten_by_group` (testing-planner's name; today's row has group "*", so its keys change either way).
3. O1/O2 already drop the person field through `_split`, so they need no change. Confirm that by test.
4. A before/after table of the O3 and O6 rows, under the old and the new definition, for the 20 saved reports (or v2). It goes to the owner through lead-planner-u24 BEFORE this lands.
5. Docs: the gate's metric description and any parity-ledger or observability doc that names "attacks on people".
6. Row identity (testing-planner, 2026-11-22):
   - Renaming the O3 id (and any O6 id) changes row identity. The baseline diff shows every old row removed and every new row added, and the v3 re-record must carry that as a rename, not as rows lost and found.
   - The per-row thresholds keyed by id (the table at `rpg_gate_metrics.py` :99 "O3.attacks_on_people" and :102 "O6.kills_not_eaten") move with the rename.
   - The O3 rationale text ("three more bites on villagers…") names people and is reworded.
   - Whether the (2.0, 3.0) floor still fits a total over every victim and every group (the BASE trace cells hold meat about 15 and meat+plant+prepared about 155 hits a seed) is a rpg-designer question. Any change to the value is an owner ask, and a rename alone keeps it.
7. The 'none' group (owner #715 7074477873, "Yes, include 'none' (Recommended)"): the non-eating group (for example FLW's 6 undead) gets an O3.attacks_by_group row like any other group, because non-eaters can still attack. It gets no O6 row, because it has no meat. This flips the existing expectation at tests/unit/observability/test_rpg_gate_metrics.py:406 (today: no O3 row for 'none').
8. Changed existing test expectations (testing-planner's read-only plan, 2026-11-22). Each goes in the owner's before/after packet under the standing rule:
   - tests/unit/observability/test_rpg_gate_metrics.py:
     - :160, people-on-people is not O3: flips;
     - :164, the O6 id and rows;
     - :197-202, rewritten as person-flag-insensitive (AC1);
     - :213, the _tick0_persons patch dropped;
     - :311, the O3 group set becomes every declared group with t0 > 0;
     - :330, the error stays and its match text changes;
     - :406, the 'none' row, now yes.
   - tests/simulation_quality/rpg_gate/test_v8_fires.py:41: the _tick0_persons patch is removed.
   - New tests for AC3 and AC4a.
   The test edits ride the SAME branch and PR as the rpg_gate_metrics.py change, so the suite is never red between them (testing-planner's proposal).
9. Row count: A1/A2 add a row for every group, so the number of baseline rows grows. The owner's before/after table shows a per-world row count (old vs new) as well as the values.

## Out of Scope
- Removing `attacker_person`/`victim_person` from the run_ledger or death_ledger keys (A3, a later owner ask).
- Every gameplay use of `keeps_coin` / `is_person` (lodging, building services, trade). The owner's direction is about measures.
- The baseline re-record (v3) itself. It follows this ticket and the #953/#954 bug ruling, under its own GO and owner yes.
- Gate tests (`tests/simulation_quality/rpg_gate/`, for example test_v8_fires.py:41, which patches `_tick0_persons`, and the non-eating pin tests). testing-planner owns them and changes them in step. Any changed existing expectation is an owner ask.

## Acceptance Criteria
1. No gate row reads a person flag. A unit test shows that the same ledger with person flags int 1, str "1" or absent gives identical O3/O6 rows.
2. O3 has one row per declared diet group with t0 population > 0, and an undeclared group raises an error.
3. O6 has one row per meat-containing diet group and none for other groups.
4. The before/after table is shown to the owner and the yes is recorded on #715 before merge. It lists the values and a per-world row count, old vs new; marks each renamed row as a rename; shows the new 'none' O3 row; and lists every changed existing test expectation (scope 8).
4a. The threshold table carries the new ids. No orphaned old-id entry remains, and a test fails on a row id that has no threshold.
5. Docs and the parity ledger name the new definitions; a divergence entry is added if the gate's documented meaning changes.

## Related Tickets
- TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES (the O3 trace; its evidence is the input here)
- TCK-20261121-THE-GATE-PERSON-FLAG-CHECK-SILENTLY-TREATS-A-NON-STRING-FLAG-AS-A-NON-PERSON (P3): this ticket removes the gate's person-flag reads, which makes that one moot for the gate. Close it as superseded when this lands, unless a non-gate reader remains.
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC (systemic_foundation; kinds by properties)

## Related Docs
- docs/plans/systemic_world/roadmap.md §12 (systemic_foundation)
- docs/observability/ (gate metric docs)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/o3_trace_cd3a7643_run/ (sealed O3 trace copy; the designer's recount sits next to it)

## Related Code Areas
- src/observability/rpg_gate_metrics.py; src/ai/goals/kind_group.py (`is_person`, read only); src/observability/run_ledger.py (key layout, unchanged)

## Assumptions / Open Questions
- Row ids are settled by testing-planner: O3.attacks_on_people -> O3.attacks_by_group and O6.kills_not_eaten -> O6.kills_not_eaten_by_group, both recorded as renames in the v3 diff (scope 6) and both covered by the AC4a test.
- The O3' re-trace (FINAL combined scope, stage 1) may refine the before/after numbers. It does not change the definition.

## Durable state, lifecycle and clocks
None. This is a read-only measure over the existing ledger keys, with no new durable field.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
