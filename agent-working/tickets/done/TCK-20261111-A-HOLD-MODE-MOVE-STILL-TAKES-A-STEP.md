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

### CI fix round (PR #931; owner #715 6908596468 "(a) Land, mark test, P1 ticket"; landing approved 6906654192)
CI on f49118c66 failed 5 jobs. Cause and ruling for each:
- Import contract (Code health, Architecture): `systems do not import engine outside the pinned exceptions (phase18)`: intelligence.py and redirection.py imported `src.engine.hold_mode`. Fix: `src/engine/hold_mode.py` moved to `src/core/hold_mode.py` (it needs only `MovementMode` from core; core already holds such pure rule helpers, `lodging_rules.py` and `social_counts.py`), a pure move: the 4 src importers, the test import, COMB-353 v2_evidence, divergence 2.206, the mechanisms.yaml implemented_by path and the pin text. Wider scope stays 369 / unbound 262 from the check's own output. Removing the dead function-local `should_run` import from intelligence.py (to keep its module-length ceiling) also removed a grandfathered systems -> engine pin: un-pinned in tests/architecture/test_phase18_import_boundaries.py and docs/audits/D14_coupling_depth.md (13 -> 12 sites) with testing-planner ok.
- Diagonal melee control (Unit core/world): the completion-tick overshoot is now stopped by two independent rules (the completion-tick guard and P1, `movement_target` returns no target for a pending `target_clear`); the control disabled only the guard (first strike tick 31 on main, 11 on the fix). Designer ruling: the control now disables the guard AND P1 (and CONFLICT-04) and keeps its expectation; a new test pins P1 alone; the MAIN test is unchanged.
- Extractor characterization (Unit infra/observability): 176 pinned outputs moved, all `lifecycle_full_coverage_world:42`, calls 103 to 199 (97 rows). First divergence call 103: entity 29 takes an AVOID_NO_ROUTE wait beside entity 34 and holds instead of stepping into its free swing (hp 150 -> 143 avoided); one downstream class; the default `as_built` output is unchanged; the second-hash-seed twin equals the first seed. Re-pinned with the test file's own command (`python -m tests.unit.observability.extractor_characterization.corpus`); only kernel_runs.jsonl changed.
- Hunting kill-to-meal (Perf/cert/arena), a real behaviour finding: the wolf eats the first portion of its kill at tick 15 in both trees, then the region_stabilization goal (utility 100.0 against the scavenge step's 63.99) opens an investigate wolf_den project and it walks off; on main the HOLD bug's priced stray steps kept it within two tiles and it ate again at tick 25. Owner: test `xfail(strict=True)` citing the new P1 `TCK-20261116-A-HUNGRY-HUNTER-EATS-ONE-PORTION-OF-ITS-KILL-THEN-WALKS-OFF-TO-AN-UNRELATED-PROJECT`; parity TOWN-205 -> `divergent` with its divergence_note extended (2.107 text kept).
- RSS guard (Architecture): passes locally (1 passed); classified environmental/flaky on the runner, to be checked by the next CI run.
Also filed: `TCK-20261116-A-CORNERED-HOLD-ENDS-ON-A-LIVE-ACTION-TASK-AND-WALKS-BACK-INTO-THE-FIGHT` (the one death the fix caused, s43 e12).

Main merges: dc2f4c07e (#929, no conflicts), then 3bfdb038b (with #933 group combat at 7bf4a5670): 4 conflicts, no src: combat_movement.yaml kept COMB-353 then #933's COMB-354/355; mechanisms.yaml tactical_decision: #933's note first, ours after, our implemented_by entry kept; REGISTRY and the verification view regenerated, not hand-merged. src is unchanged by main since c9279925b (`git diff 7bf4a5670 3bfdb038b -- src` empty).

Proof after the fix round:
- Hash equality at head 852325043 (git archive, ls-tree verified, 19744 files, 0 mismatches), PLAIN 5000-tick cells, each equal to the stage-2 fix cell: fix frontier_marches s44 `1fa7a16c85446f576e74219d304303bc13a109d76b96650daaa4969564126b6c`, fix urban_political s43 `c8d788c6d44617938b4fbe2de5a43c43858c7f544e6a814fd2b7a6ad134bc5e4` (scripts run_head_hash.sh a2b00cb4 for the earlier head 3a7ea995d, run_head_hash2.sh 80cc3eff, run_head_hash2b.sh 53ce8721 and run_head_hash2c.sh e8ba6b9a, which narrows the gate to this project's paths). Two earlier stops (06:18 and 06:21 UTC) were host-gate trips by outside algo-ai tests, not results.
- Patch identity at the merged head e1dc568bc: ordered +/- lines of `git diff 3bfdb038b e1dc568bc -- src tests` equal the HOLD patch `git diff dc2f4c07e 852325043 -- src tests` (15 of 15 files); src alone 8 of 8 files against `git diff f94417e6f 852325043 -- src`.
- Local CI set: `python3 -m tools.delivery.ci_lanes --run --all` at 852325043, 06:33 to 07:21 UTC (47 min), one process at -n 1 via PYTEST_ADDOPTS. PASS: unit-core-world 3139 passed/3 skipped, unit-gameplay 1988/1, integration 1131/6, tools-f-z 4236/26/1 xfailed, agent-orchestration 453/5, simulation-quality 541/64, arch-docs 546/2/2 xfailed (+ mechanism-registry-validate), perf-cert-arena 275/1/2 xfailed, migration-lanes 493/1 (+ gate-expansion 12). Four local artifacts, none ours: (1) unit-infra/observability: the 2 unit-corpus tests failed because PYTEST_ADDOPTS "-n 1" reached the corpus sub-pytest (confirmed: the same 2 pass on the head without it, and fail on the base tree with it); (2) tools-a-e: `test_codebase_health_snapshot` needs ruff, absent from the checkout .venv; (3) api-cli-engine: `test_http_surface_matches_the_recorded_snapshot` fails the same on the base tree (passed in #931 CI); (4) typecheck, code-health and code-health-sarif crashed on an empty `$GITHUB_STEP_SUMMARY` (IsADirectoryError); their direct verdicts: `codebase.gates.mypy_gate` rc 0, `make code-health` OK. The informational simq-grade-drift lane printed 28 failing grade-anchor tests (informational, skipped in CI). The rest is checked by CI on the push.
- Individual files at the merged head (12 files + phase18, -n 1 on the command line): all passed.
- Interaction smoke #931 x #933 (owner #715 6910017023; the approved driver smoke_driver.sh 9c12d18b with smoke_wrapcount.py 6fdfaa35 over hold_spy_v7 69e529f9): merged e1dc568bc vs main 7bf4a5670, frontier_marches and crowded_frontier seed 42, 5000 ticks, PLAIN twin then pinned spied run, 8 runs rc 0, all 9 wrap targets hit and v7 on top, hash plain == spied in all four. Designer ruling: PASS. Merged: typed-wait steps 0, free swings 0 in both worlds, collapse-live 12 (fm) / 0, kill 0 / 2, no never-ending hold. Disclosed: fm s42 ends with roles 4 and 5 at 0 alive on the merged head against 3 and 6 on main (deaths 50 vs 43, combat 38 vs 29), untraced.

## Test Summary
- New tests: `tests/unit/engine/test_hold_wait_takes_no_step.py` and `tests/unit/engine/test_hold_mode_reset.py`. Ratchet `tests/architecture/test_no_name_switches_in_decision_paths.py` passes. Scoped run at `-n 1` on the final head `3a7ea995d`: 147 passed (the two hold tests, the ratchet, and the neighbours listed in divergence 2.206's Verification). `make code-health` OK, `make parity-ledger-schema-check` OK, `codebase.gates.mypy_gate` rc 0.
- Stage 1 (`frontier_marches`, `crowded_frontier`, seed 42, 5000 ticks): HOLD steps 59 to 12 and 20 to 2; base plain hashes equal the pins `908eb3bb` and `e0e20c20`; fix plain hashes `8ba8c3a5` and `14b7244c`.
- Stage 2 (3 worlds, seeds 42-46, {base, fix}, 5000 ticks, spy `hold_spy_v7` `69e529f9`, checker `94ca9b14`): 34 of 34 runs rc 0. `frontier_marches`: no limit tripped. `crowded_frontier`: seed 46 hero (role 0) loss, fix 0 against base 3 on the 5-seed sums, waived once by the owner (#715 6899865649); role 4 alive fell from 4 to 2. `urban_political`: Tier 1 tripped for COMBAT deaths (fix 40, base 34, bar +4) and HAZARD deaths (fix 15, base 11, bar +2).
- Tier 2 read (`dying_window_v8` `3828af12`; cells fix s42 `6daf3802`, fix s43 `c085c86b`, fix s45 `14735c06`, base s43 `7fd61d77`): 1 FED (s43 e12) and 4 NOT FED. Owner: "(a) Land + new ticket", #715 6906654192.
- A behaviour-identical extraction after measurement (commits `e93102691`, `3a7ea995d`: `_collapse_hold_ends` out of `ActionRoutingPhase.route`, two typing fixes, one dead function-local import removed from `intelligence.py`), proven hash-equal: head `3a7ea995d` extracted with `git archive` (19692 files, 0 mismatches against `git ls-tree`), two PLAIN 5000-tick runs, `frontier_marches` s44 `1fa7a16c…` and `urban_political` s43 `c8d788c6…`, each equal to the stage-2 fix cell's `final_hash`. `make code-health` OK, `codebase.gates.mypy_gate` rc 0.
- `tests/codebase/test_codebase_health_snapshot.py::test_make_target_runs_successfully_end_to_end` fails locally only because the checkout `.venv` has no ruff ("No module named ruff"); CI is its check.
- Timing NOT MEASURED (perf pause).
- Known gap: the Tier 2 spy does not wrap `resolve_attack` and its `hold_writer` is the last copy site; the other arm-only urban COMBAT/HAZARD deaths were selected out by "no HOLD episode of their own within 40 ticks before death" and not traced; base s42 and base s45 Tier 2 runs were dropped.
- CI fix round (PR #931): scoped and individual files pass at the merged head e1dc568bc (diagonal 4; hunting 4 passed + 1 xfailed; extractor 12; RSS guard 1; phase18 13; ratchet 58; hold_wait 9; hold_mode_reset 21; mechanism registry 87, completeness 14, changed-code 17, summary shape 15); `ci_lanes --run --all` at 852325043: see Implementation Notes for the per-lane counts and the 4 local artifacts; hash equality at 852325043 on fm s44 and urban s43; smoke #931 x #933 PASS (owner 6910017023).

## Files Changed
`src/core/hold_mode.py` (new; first landed as `src/engine/hold_mode.py`, moved in the CI fix round), `src/engine/candidate_selector.py`, `src/engine/tactical_hold.py`, `src/engine/tactical.py`, `src/engine/pipeline_phases/actions.py`, `src/engine/intent/action_intent.py`, `src/systems/strategic_systems/intelligence.py`, `src/systems/strategic_systems/redirection.py`; `tests/unit/engine/test_hold_wait_takes_no_step.py`, `tests/unit/engine/test_hold_mode_reset.py`, `tests/unit/engine/test_diagonal_melee_pair_strikes.py` (control re-worded, P1-alone test), `tests/mechanic_scenarios/test_hunting_kill_to_meat.py` (xfail strict), `tests/fixtures/event_extractor_characterization/kernel_runs.jsonl` (re-pin), `tests/architecture/test_phase18_import_boundaries.py` and `docs/audits/D14_coupling_depth.md` (un-pin), `tests/unit/tools/test_mechanism_registry_completeness_check.py` (pin text), `registries/mechanisms.yaml` (notes and implemented_by), `docs/parity_ledger/town_resource.yaml` (TOWN-205 divergent); `docs/mechanics/02_combat_laws.md`, `docs/engine/contracts/tactical_contract.md`, `docs/guidelines/intentional_divergences.md` (2.206), `docs/parity_ledger/combat_movement.yaml` (COMB-353, COMB-015). See `git log origin/main..HEAD` on branch `rpg-hold-mode-move-step`.

## Completion Summary
A hold now holds. A typed wait (WATCH_HOSTILE, AVOID_NO_ROUTE, HOLD_CHOKEPOINT) clears the stored navigation target in the same update that sets HOLD, and the movement check honours a pending clear, so the subject takes no step on its deciding tick and none before its next decision. HOLD ends at the subject's next walk decision (every mode-less target writer resets the mode through `hold_reset_kwargs`, unless an action task is live) and a collapse's HOLD ends with its sleep. The legality price of HOLD (the 0.1 clamp) is unchanged. Docs: Bible 02, `tactical_contract.md`, divergence 2.206 (Bug Fix; Measured and Disclosed filled), parity COMB-353 and COMB-015. Follow-up filed: `TCK-20261116-A-CORNERED-HOLD-ENDS-ON-A-LIVE-ACTION-TASK-AND-WALKS-BACK-INTO-THE-FIGHT` (the one death the fix caused, s43 e12). The ticket was filed as hotfix and run as standard (staging artifacts, two measurement stages).
