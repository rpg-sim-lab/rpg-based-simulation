---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS
phase: done
date: 2026-11-09
tags: []
---

# TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS

## Title
On an off-cadence tick, fused_strategic_pass's fast path sends a loaded entity with an entity-typed objective home (REGROUP), off its pursuit. The slow path does not.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Owner-approved as fix A of the fused_strategic_pass proposal (#715 6736224900; approval 6736269441, "Approve, after hit-wake (Recommended)"). B, the hygiene ride-along, rides in the same PR (see Scope). Slot: after the hit-wake re-measure. Hit-wake was parked on 2026-11-11 (#715 6776436829), so this is next.

The defect is in src/systems/strategic_systems/intelligence.py::fused_strategic_pass (line numbers on main 2ea0e4d8f).
- **Fast path (~:394, off-cadence ticks):** the "keep the objective's direction" guard tests only `getattr(active_obj, 'target_position', None) is not None`. An entity-typed objective (`target_entity_id` set, no `target_position`) fails the guard. A loaded entity then gets `target_set=town_target, movement_mode_set=REGROUP` and an interaction reset.
- **Slow path (~:663):** it treats `target_entity_id is not None` as owning the direction (`has_nav_update = True`, no point set), so it writes no regroup. That follows TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK.
- **Characterisation (C, #852):** tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py pins the bug.
  - `test_row1_current_behaviour_entity_objective_off_cadence_regroups_home` asserts REGROUP_HOME.
  - The differential row `entity_objective_loaded_entity` is a strict xfail on DEFECT_A.

## Scope
A (the fix, one condition):
- In the fast path's guard, treat an active objective with `target_entity_id is not None` the same as one with a `target_position`. It owns the direction, so no regroup is written. This matches the slow path at ~:663.
- Change nothing else in the function. The overwrite inconsistency is out of scope; see below.
- Tests:
  - flip `test_row1_current_behaviour_entity_objective_off_cadence_regroups_home` to "no walk decision" (`is None`), as the test's own comment asks;
  - remove the strict xfail on `entity_objective_loaded_entity`;
  - add one regression test that exercises the pipeline-wired path, not the function alone (owner prevention item 2). It sets up a loaded entity pursuing an entity-typed objective on an off-cadence tick, through the real kernel or authoritative pipeline, and asserts it keeps its pursuit and is not sent home.
- Divergence: none expected. This brings the fast path to the documented slow-path behaviour (Bug Fix). Check the STRAT entry in docs/parity_ledger/strategic_cognition.yaml for the fast-path parity text and update its v2_evidence.

B (hygiene ride-along, hash-neutral, its own commit AHEAD of A's fix commit):
- The STRAT-012 citation at ~:625 is the wrong id. Find the right Logic ID in the parity ledger and cite it. If none fits, report that and leave it.
- The "unconditional, every tick" comment at ~:621: make it say what the code actually does.
- The two bare `except: pass` in fused_strategic_pass (~:348 and ~:518; :650 is a third, so report the count you find). Narrow each one to the exception it actually guards, and log through the module logger only. No behaviour change, no new state, no event.

Measurement (pinned runner, PYTHONHASHSEED=0, 5000 ticks):
- B: one crowded s42 cell on the B commit. Its hash must equal main's base cell, or STOP.
- A: paired base vs fix on 7 seeds, 14 runs: crowded_frontier s42-46, urban_political s44, frontier_living_world s45.
- Bar: the standing Tier 1 death bar plus the extinction check on 5-seed sums, with the Tier 2 trace on any trip. Results go to rpg-designer to recount and rule.
- Total 15 runs.

Notes riding in this PR (docs only, on the named tickets):
- TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED: a scope note on the overwrite inconsistency. The fast path builds a new EntityUpdate when there is no ent_upd, but `replace`s it when there is one, so the two branches drop different fields.
- TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE: note D, that the restructure is folded into the next-gen kernel/logic contract after M1.

## Out of Scope
- The overwrite inconsistency (CLEAR-TARGET's).
- The restructure (D).
- Any other fast-path or slow-path disagreement in #852's differential. Those rows keep their marks.
- Owner prevention items 1, 3 and 4 (other seats).

## Acceptance Criteria
- Off cadence, a loaded entity with an active entity-typed objective gets no regroup and no interaction reset from the fast path. The flipped C row and the new wired-path test pin this.
- #852's `entity_objective_loaded_entity` differential row passes with no xfail. No other C row changes mark.
- B is hash-neutral: crowded s42 on the B commit equals the main base hash.
- The 14 A runs are reported and recounted by rpg-designer. A trip goes to the owner via lead-planner-u24, and nothing lands on a trip without a ruling.
- The parity ledger text and evidence match the code.
- Both scope notes are recorded on their tickets.

## Related Tickets
- TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH (C, #852)
- TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED
- TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE
- TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK (the slow-path rule)
- TCK-20261109-ONE-MUTATION-RUN-MEASURES-HOW-MANY-INJECTED-FAULTS-THE-FUSED-STRATEGIC-PASS-TESTS-CATCH (E)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/parity_ledger/strategic_cognition.yaml

## Related Stored Artifacts
- None.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py::fused_strategic_pass (fast path ~:380-410, slow path ~:655-680, ~:348, ~:518, ~:621-625, ~:650)
- tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py

## Assumptions / Open Questions
- The paired runs may move deaths: entities keep their pursuit instead of heading home. That is the point of the measurement.
- Filed by rpg-planner on 2026-11-11, from the owner-approved scope (#715 6736224900 and 6736269441).

## Implementation Notes

**Run count (2026-11-11, rpg-implementer-3; lead agreed via rpg-planner): 16 runs, not 15.** 16 = the 15 approved runs + 1 `frontier_living_world` s45 base cell on origin/main `2ea0e4d8f`. There was no fliving s45 base cell on 993400a52, so the seventh pair needed one. `git diff 993400a52 2ea0e4d8f -- src data config` is empty (#859 is docs and tooling only), so the other 6 base cells (crowded_frontier s42-46, urban_political s44) reuse the cells measured on 993400a52. The set: B = crowded s42 on c7607b6da (must equal d842c20983d7); A = the fix head on crowded s42-46, urban s44 and fliving s45; base = fliving s45 on 2ea0e4d8f. The push ask names both shas (2ea0e4d8f and 993400a52); the PR's evidence section says the same.

**What was built (2026-11-11).** B (c7607b6da): the capacity block cites STRAT-006/STRAT-007 and says it runs on every slow-path evaluation; three bare `except: pass` in `fused_strategic_pass` are line-for-line one-liners that log at debug through the module `logger` (cache store, access-blocker parse, material-lead parse). A (e3b3be09c, reshaped in c78d4c4b0): the fast-path guard counts a `target_entity_id` objective as owning the direction, as the slow path does (~:663). Two further bare excepts outside the function (~:775, ~:1251) are untouched. The parity text is COMB-329 in `combat_movement.yaml` (not a STRAT row, as the ticket assumed). Scope notes landed on CLEAR-TARGET and RESTRUCTURE (note D, plus the missing-status line). 26ca2c77c is a comment-only change on the :395 line.

**Code health.** Cognitive complexity of `fused_strategic_pass` went 437 to 438 and the ceiling was raised by one (c1c762a46, owner #715 6776776165). The `value` is unchanged. The ratchet is otherwise untouched.

**Staging artifacts: none.** The ticket's plan lives in its own Scope; there is no `staging_artifacts/<ticket>/` directory to migrate.

## Test Summary
- `tests/unit/strategic`: 523 passed (`-n 1`, `-p no:randomly`) at c632e0150.
- Row 1 flipped to `test_row1_entity_objective_off_cadence_does_not_regroup_home` (`is None`). The strict xfail and its `KNOWN_DISAGREEMENTS` entry for `entity_objective_loaded_entity` are removed; the table now holds exactly row 6 (`earlier_phase_target_set`).
- New wired-path test `test_pursuit_objective_survives_the_off_cadence_strategic_pass.py`: through `AuthoritativeApplyPipeline.refine` off cadence, no REGROUP target and no interaction reset; it failed before the fix (REGROUP to (50,50)). A control without a project still regroups.
- `codebase.health check`: OK, 0 worse. `mypy_gate`: rc 0.
- Measurement (pinned runner, PYTHONHASHSEED=0, 5000 ticks, 16 runs): B crowded s42 on c7607b6da = d842c20983d7 = base. Fix on c1c762a46 vs base, 7 pairs (crowded s42-46, urban_political s44, frontier_living_world s45): all 7 final hashes and result JSONs are identical. Crowded 5-seed deaths 160 to 160 (COMBAT 118, DEFEAT 26, HAZARD 16 on both sides); extinction check: stop [], base_state [blacksmith, scout], recovered []. Bases: 993400a52 (6 cells) and 2ea0e4d8f (fliving s45); `git diff 993400a52 2ea0e4d8f -- src data config` is empty. rpg-designer ruled A+B PASSES with no probe.

## Files Changed
- `src/systems/strategic_systems/intelligence.py` (B and A; one comment-only commit on :395)
- `tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py` (row 1 flipped, xfail removed)
- `tests/unit/strategic/test_pursuit_objective_survives_the_off_cadence_strategic_pass.py` (new)
- `docs/parity_ledger/combat_movement.yaml` (COMB-329)
- `codebase/baselines/code_health_exceptions.jsonl` (one ceiling, 437 to 438, owner-approved)
- `agent-working/tickets/todos/TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED.md`, `.../TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE.md` (scope notes)
- This ticket, moved to `done/`.
The branch also carries earlier commits from its merge of rpg-planner-seat-8 (filed tickets, `social_narrative.yaml` SOC-227, `docs/simulation/domains/party_contract.md`); they are not part of this ticket's change.

## Completion Summary
Fix A and the B hygiene ride-along are done. Three disclosures, in plain words:
1. **The fix shows in the tests only.** All 7 paired measurement cells are byte-identical to base, so no run in the measured set exercised the changed branch in a way that moved any trajectory.
2. **The guard never checked the objective's own status.** The fast-path guard (~:395) does not check `active_obj.status`, while the slow path (:657) requires `ObjectiveStatus.ACTIVE`. This fix extends that pre-existing leniency from point objectives to entity objectives. It is recorded on the RESTRUCTURE ticket to be folded into the restructure.
3. **The three narrowed excepts now let other exception types propagate.** Each one catches only the exceptions it guards (AttributeError/TypeError; ValueError/SyntaxError/TypeError; ValueError/AttributeError). Any other type now propagates instead of being swallowed. No measured run hit one.

The `fused_strategic_pass` complexipy ceiling went 437 to 438 (owner #715 6776776165). The restructure itself stays folded into the next-gen contract after M1 (note D); it is not done here.

The mechanism-registry advisory flagged `goal_hierarchy` and `strategic_intelligence_core` (cited code changed, entries did not); rpg-planner agreed no entry change is needed. The staging artifacts (plan, investigation, test_plan) were written retroactively at close. 2.68 in `docs/guidelines/intentional_divergences.md` gained one line.

Known gap: no measured run shows the fix's effect. All 7 base/fix pairs are byte-identical, so only the tests show it.
Known gap: the fast-path guard does not check the objective's own status, while the slow path does (`ObjectiveStatus.ACTIVE`); this is left for the RESTRUCTURE ticket (note D).
