---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE

## Title
NavigationComponent.last_failure_reason is written only when a failure carries a code and is never cleared, so a stale PATH_NOT_FOUND/STUCK/OSCILLATING keeps being read by infer_blockers on every strategic pass

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by lane A's read-only F2 code read (2026-11-17, F1 head 46ac46e40; the cited files are identical on main 3aafdb383 apart from F1's own movement.py hunks).
- patches.py:288: `last_failure_reason = u_nav.failure_reason if u_nav.failure_reason is not None else new_nav.last_failure_reason`. An update with None keeps the old value.
- The only assignments are patches.py:288 and the builder default (core/builder.py:388/407). Nothing ever sets it back to None, including a successful move, a new target or a give-up.
- infer_blockers reads it on every strategic pass (intelligence.py:495), and files an ACCESS blocker for PATH_NOT_FOUND, STUCK or OSCILLATING keyed on the task payload's target_position (intelligence.py:190-191).
- So one old failure can keep re-inferring an access blocker long after the failure, against whatever target the task holds now. That defeats a lifecycle which expects a blocker to stop being re-inferred once its cause is gone (the churn fix's merge and quiet-spell rules).
- The way-round give-up itself sets failure_reason None (movement.py:362-365, :459), so it leaves the stale value in place and writes no code of its own.

## Scope
1. RULED by rpg-designer (F2 v2, 2026-11-17): last_failure_reason = the outcome of the LAST step. A successful step clears it with an explicit typed NavigationUpdate.failure_reason_clear, and a None never carries it forward. F2 does not use last_failure_reason.
   SCHEDULE: land before or with the churn fix, because a stale reason re-infers blockers against the churn lifecycle.
2. A typed clear in NavigationUpdate, applied in patches.py; tests; parity and Bible text.
3. Measure whether stale re-inference happens today: count access blockers inferred while the current failure is more than N ticks old.

## Out of Scope
- F2's giveup_records design (TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON), though it should be designed together with this.

## Acceptance Criteria
- last_failure_reason has a defined lifecycle: written, cleared, with a documented owner.
- Blocker inference never acts on a failure older than the rule allows. A test pins it.

## Related Tickets
- TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON (F2)
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION (churn lifecycle)
- TCK-20261117-MATERIAL-AND-PARTNER-BLOCKERS-NAME-A-SUBJECT-NOTHING-CAN-MATCH (subject format: intelligence.py:192 builds "(25.0, 25.0)" float strings, which score_modifiers.py:58 matches against target_id)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (blocker inference)

## Related Stored Artifacts
- Lane A's V2-V5 code read (relayed to rpg-designer, 2026-11-17)

## Related Code Areas
- src/engine/patches.py:288, src/systems/strategic_systems/intelligence.py:176-202 and :495, src/engine/movement.py:362-365 and :456-472

## Assumptions / Open Questions
- Whether a stale reason has ever filed a wrong blocker in a real run is unmeasured.
- Any fix touching intelligence.py waits for the intelligence.py split (owner schedule).

## Durable state, lifecycle and clocks

- Record: `NavigationState.last_failure_reason` (entity navigation, authoritative state; read by `information/phase.py` `claim_failed_search` and by `infer_blockers`).
- Creator: a failed step (movement routing) or a failed action (action routing) writes a code through `NavigationUpdate.failure_reason`. Ender: any MOVE (own step, swap, yield displacement) carries `failure_reason_clear` and no code; before this ticket a yield or swap wrote YIELDING / POSITION_SWAP and nothing cleared it.
- Update semantics: `NavigationPatch.apply` is replace-by-precedence: a code beats a clear, a bare None leaves the old value. `NavigationUpdate.merge` keeps the later code. Within movement routing a code the phase itself wrote for a body is dropped when that body is then displaced, and the pre-phase (action) code is restored; a code from an earlier phase survives; a code written later still wins.
- Clock: state.tick only (phase order action_routing, position_swaps, movement_routing within one tick; guarded by a test). No world_time / is_night read; no new stored field and no new clock.
- Visibility: the observation stream changes (fewer `claim_failed_search` after a move); noted in information_contract.md and divergence 2.215.

## Implementation Notes

**Ruled move law (rpg-designer, owner #715 6967356642 and 6967398421, after the first own-job tripped R1/R3):** any position change by the movement apply path is a MOVE: the subject's own step, a swap, or a yield displacement (lodge entry and exit are not). A move carries `failure_reason_clear` and NO failure code. The yield (`movement.py` `_yield_update`) drops `YIELDING`; the position-swap update (`pipeline_phases/movement.py`) drops `POSITION_SWAP`; both carry the clear. A failure code the movement-routing phase itself wrote for a body earlier in the tick is dropped when the body is then displaced (`_merge_move_update`, provenance-tracked per phase); codes from earlier phases (action routing runs BEFORE position swaps and movement routing, so the body's existing update may hold an action code) survive, and a code written later still wins at the patch. `OCCUPANCY_CONFLICT` becomes a `ReasonCode` member (same value). The swap merge in the swap phase is unchanged: swaps run before movement routing, so a swapped body has no prior movement code, only possibly an action code, which survives.

## Test Summary
- Own-job (S9 #715, designer-accepted after recounting from the raw cells): tree fixtree_merged2 (git archive of b2898eb24, stream sha256 3dace138b5647706a22474cfe372208bd1d01e17e440f2f2ea24244469c1353d), spy v2 9c0b7c56, runner 528a7548, summarizer 7140a02c, manifest 488582e9; 3 cells (frontier_living_world, urban_political, crowded_frontier), s42, 5000 ticks, spy plus plain twin. summary.txt sha256 a073160db807cc2f546e37632362e77651912b7dc647cedd0a596f530beed9d0, `driver_rc=0`: ALL HARD BARS HOLD (L1 = M1 = M2 = R2 = 0; PINNED; logging_errors 0; exceptions {}; spy hash == plain hash; reasons set/cleared 2894/2882, 2623/2610, 1012/991; moves step 91093, swap 428, yield 33).
- Reported, not bars: v1 (resolve_move-only) R1 1, 1, 0 (SOURCE_DEPLETED from an earlier-phase action, which survives a later move by the ruled law); v1 R3 0, 1, 1 (occupancy_violation steps, see next line). Blockers filed: congestion only.
- Inspected (code read, not executed per row): an `occupancy_violation` failed step (v1 R3 rows, urban e6 t1130, crowded e2 t763) is a real failed step: `resolve_move` returns the code only when no sidestep, yield or reroute succeeded. The code is merged into the update (`_merge_move_update` records it as the phase's own code). If another body's yield displaces that same body later in the same movement phase, the displacement is a move: the clear replaces the phase's own code and the pre-phase code is restored, so the stored reason ends None. The reason is superseded by the move, not lost; a failed step with no later displacement keeps its code. Not traced per row; if the designer wants the two rows traced it is a separate read-only job.
- Preflight (kit_preflight, manifest 488582e9, one tree, ticks 10): 0 FAIL of 31 checks, preflight sha256 f81e5100dd782429d4104367100b741ad0ef79dcbf6e998dd1572a896255eb59; check (b) skipped for the spy (the run uses PYTHONPATH, not -I); the L1 wrap hook hit 67 times; other writer hooks not hit-checked.
- Statics on b2898eb24: make code-health rc 0 (`OK: 2 new, 2 worse, 96 improved, 22 gone, 3417 unchanged (4 report-only)`; report-only jscpd rows in untouched observability files), lint-imports 17 kept, mypy baseline-filtered rc 0.
- Targeted tests (one file per process, -n 1, not slow): move_carries_clear_not_code 9, failure_reason_lifecycle 8, swaps_and_yields_pay_step_time 5, movement_spatial_regression 8, migration_proof 4, position_swap 3, perc02a_senses_signals_night 43, checkpoint_fields 11, checkpoint_group_fields 14, checkpoint_schema 34: all passed.
- Owner-approved test-expectation edits (#715 6967398421): the four assertions that named YIELDING / POSITION_SWAP now assert None plus the clear; no assertion weakened otherwise.
- Evidence: agent-working/stored_artifacts/TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE/evidence/ (summary, driver log, manifest, preflight table, kit files).
- Delete list (the owner deletes; I never do): /mnt/data2/rpg-measure/failreason/{fixtree_move,fixtree_fix,fixtree_fix2,fixtree_merged,cells_fail,cells_fail_cf,cells_fail_all}, the older v6/v7/v8 dirs and f2_probe/. Keep fixtree_merged2 and diag2/cells_move until the PR merges.

## Files Changed
src: core/enums.py (OCCUPANCY_CONFLICT), core/updates.py (NavigationUpdate.failure_reason_clear in merge and is_noop), engine/patches.py (NavigationPatch clear), engine/movement.py (success step and yield carry the clear), engine/pipeline_phases/movement.py (swap carries the clear; `_merge_move_update`), engine/pipeline_phases/occupancy.py (typed code). tests: unit/movement/test_failure_reason_lifecycle.py and test_move_carries_clear_not_code.py (new); test_swaps_and_yields_pay_step_time, test_movement_spatial_regression, test_migration_proof, test_position_swap (assertion edits). docs: guidelines/intentional_divergences.md (2.215), parity_ledger/combat_movement.yaml (COMB-357), mechanics/04_strategic_cognition.md, simulation/domains/information_contract.md, registries/mechanisms.yaml (summary line). ticket and stored artifacts.

## Completion Summary
A reason now holds the outcome of the last step: a successful step or any move (own step, swap, yield displacement) clears it and carries no code, so blocker inference no longer acts on an old failure and a moved body no longer emits claim_failed_search. Own-job bars all hold on three worlds. Disclosed: the observation stream changes; the oscillation replan still reports LEGAL (F1 replaces that path); whether a stale reason ever filed a wrong blocker in a real run was not measured before the change.
