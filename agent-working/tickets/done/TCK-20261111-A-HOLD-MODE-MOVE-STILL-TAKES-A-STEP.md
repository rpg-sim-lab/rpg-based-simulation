---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP
phase: done
date: 2026-11-11
tags: []
---

# TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP

## Title
A subject whose movement mode is HOLD still takes a step toward its stored target

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
rpg-designer found this in the Scope 1 trace of TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING. rpg-planner filed it on 2026-11-11.

def2 crowded s43 #1, t2942 (tree 3300928e8, hash-matched): `resolve_move` ran with mode HOLD toward the stored target (25,25), written at t2939 by intelligence.py ~:670. The subject stepped and took the opportunity attack (attacker 30, hp 9, damage 23).

Raw data: /mnt/data2/scratch-b/fst_out/def2_c43.json.

## Scope
1. Read-only check on main 5c6990e51: what HOLD means in MovementSystem.resolve_move and route_movement_intent, and in the docs (Bible 02, docs/engine movement contracts). Is a HOLD step intended?
2. If it isn't intended, the fix is that HOLD takes no step. rpg-designer rules first, with a paired measurement only if the rule moves any outcome.

## Out of Scope
- The lethal free-swing hold (the non-flight P2 ticket).
- The stored-target-while-engaged question (COMBAT-RETREAT P2, widened).

## Acceptance Criteria
- HOLD's meaning is cited from the docs and the code, with a verdict.
- If it's a defect, a unit test pins "HOLD takes no step".

## Related Tickets
- TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
- TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/engine/contracts/tactical_contract.md

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP/` (plan, investigation, test plan, and `evidence/`: stage 1 cells, stage 2 cell summaries, the four Tier 2 cells, the spies, checkers, drivers and logs).

## Related Code Areas
- src/systems/movement.py (resolve_move)
- src/engine/pipeline_phases/movement.py (route_movement_intent)

## Assumptions / Open Questions
- The answer may simply be that HOLD is a mode for speed or terrain, not a "don't move" instruction. If so, close it with the citation.

## Implementation Notes

Design approval (rpg-designer, 2026-11-14, session message): HOLD plan v3 at d7b872287 (plan.md sha256 1e71d299…, test_plan.md 71d0407f…) is approved as a DESIGN only. The build waits for the owner's answer on the HOLD row (lead-planner-u24 carries it); no src edit and no push before then. BUILD CONDITION: the limit stated at plan.md line 43 ("Limit, said plainly: the predicate is 'an action task is live', not 'THE task that entered the HOLD is live': the state does not store which task entered the HOLD. It errs toward keeping HOLD: a typed-wait HOLD that persists while the subject has since started an unrelated live action (e.g. an ATTACK) is not reset by a walk decision until that action ends. That is the safe direction (it never makes a walk cheaper than today), and it costs at most the time until that action ends.") is written in the same words into the Disclosed line of divergence 2.206 and into the tactical_contract.md :89 note; no ledger row may claim "the entering task" anywhere.

## Test Summary
- New tests: `tests/unit/engine/test_hold_wait_takes_no_step.py` and `tests/unit/engine/test_hold_mode_reset.py`. Ratchet `tests/architecture/test_no_name_switches_in_decision_paths.py` passes. Scoped run at `-n 1` on the merged head: see the PR body for the counts of this final head.
- Stage 1 (`frontier_marches`, `crowded_frontier`, seed 42, 5000 ticks): HOLD steps 59 to 12 and 20 to 2; base plain hashes equal the pins `908eb3bb` and `e0e20c20`; fix plain hashes `8ba8c3a5` and `14b7244c`.
- Stage 2 (3 worlds, seeds 42-46, {base, fix}, 5000 ticks, spy `hold_spy_v7` `69e529f9`, checker `94ca9b14`): 34 of 34 runs rc 0. `frontier_marches`: no limit tripped. `crowded_frontier`: seed 46 hero (role 0) loss, fix 0 against base 3 on the 5-seed sums, waived once by the owner (#715 6899865649); role 4 alive fell from 4 to 2. `urban_political`: Tier 1 tripped for COMBAT deaths (fix 40, base 34, bar +4) and HAZARD deaths (fix 15, base 11, bar +2).
- Tier 2 read (`dying_window_v8` `3828af12`; cells fix s42 `6daf3802`, fix s43 `c085c86b`, fix s45 `14735c06`, base s43 `7fd61d77`): 1 FED (s43 e12) and 4 NOT FED. Owner: "(a) Land + new ticket", #715 6906654192.
- A behaviour-identical extraction after measurement (commits `e93102691`, `3a7ea995d`: `_collapse_hold_ends` out of `ActionRoutingPhase.route`, two typing fixes, one dead function-local import removed from `intelligence.py`), proven hash-equal: head `3a7ea995d` extracted with `git archive` (19692 files, 0 mismatches against `git ls-tree`), two PLAIN 5000-tick runs, `frontier_marches` s44 `1fa7a16c…` and `urban_political` s43 `c8d788c6…`, each equal to the stage-2 fix cell's `final_hash`. `make code-health` OK, `codebase.gates.mypy_gate` rc 0.
- `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` fails locally only because the checkout `.venv` has no ruff ("No module named ruff"); CI is its check.
- Timing NOT MEASURED (perf pause).
- Known gaps: the Tier 2 spy does not wrap `resolve_attack` and its `hold_writer` is the last copy site; the other arm-only urban COMBAT/HAZARD deaths were selected out by "no HOLD episode of their own within 40 ticks before death" and not traced; base s42 and base s45 Tier 2 runs were dropped.

## Files Changed
`src/engine/hold_mode.py` (new), `src/engine/candidate_selector.py`, `src/engine/tactical_hold.py`, `src/engine/tactical.py`, `src/engine/pipeline_phases/actions.py`, `src/engine/intent/action_intent.py`, `src/systems/strategic_systems/intelligence.py`, `src/systems/strategic_systems/redirection.py`; `tests/unit/engine/test_hold_wait_takes_no_step.py`, `tests/unit/engine/test_hold_mode_reset.py`; `docs/mechanics/02_combat_laws.md`, `docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md` (2.206), `docs/parity_ledger/combat_movement.yaml` (COMB-353, COMB-015). See `git log origin/main..HEAD` on branch `rpg-hold-mode-move-step`.

## Completion Summary
A hold now holds. A typed wait (WATCH_HOSTILE, AVOID_NO_ROUTE, HOLD_CHOKEPOINT) clears the stored navigation target in the same update that sets HOLD, and the movement check honours a pending clear, so the subject takes no step on its deciding tick and none before its next decision. HOLD ends at the subject's next walk decision (every mode-less target writer resets the mode through `hold_reset_kwargs`, unless an action task is live) and a collapse's HOLD ends with its sleep. The legality price of HOLD (the 0.1 clamp) is unchanged. Docs: Bible 02, `tactical_contract.md`, divergence 2.206 (Bug Fix; Measured and Disclosed filled), parity COMB-353 and COMB-015. Follow-up filed: `TCK-20261116-A-CORNERED-HOLD-ENDS-ON-A-LIVE-ACTION-TASK-AND-WALKS-BACK-INTO-THE-FIGHT` (the one death the fix caused, s43 e12). The ticket was filed as hotfix and run as standard (staging artifacts, two measurement stages).
