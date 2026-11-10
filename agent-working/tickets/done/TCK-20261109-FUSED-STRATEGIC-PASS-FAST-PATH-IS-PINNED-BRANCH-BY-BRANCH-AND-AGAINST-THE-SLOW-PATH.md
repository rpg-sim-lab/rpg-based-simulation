---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH
phase: done
date: 2026-11-09
tags: [testing, regression]
---

# TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH

## Title
fused_strategic_pass's off-cadence fast path is pinned branch by branch (characterisation), and a fast-against-slow differential on the same entity state lists every known disagreement as a row

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Owner go on issue #715, comment 6736269441 (item 2, "E, C, (2) now"), on the proposal in comment 6736224900. That proposal came from a read-only review of `StrategicIntelligenceSystem.fused_strategic_pass` (src/systems/strategic_systems/intelligence.py, about lines 301-707 on main). Twelve test files call the function, but none targets the off-cadence fast path. The fast path is the block taken when neither concern nor intent evaluation is due, no strategic update is pending, and the entity has no blockers or leads (about lines 376-413).

This ticket pins today's behaviour before any change (Feathers characterisation). It also adds a differential test: for the same entity state, the off-cadence result must equal the forced-cadence result wherever the two paths are meant to agree. The executor parity tests use the same pattern.

Defect A (TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS, rpg-planner) is several measurement slots away. This ticket lands before A, as its own PR, and A's PR flips row 1.

## Scope
New tests under tests/unit/strategic/ (rpg-planner's tests route; rpg-planner signs off on the files). State is built by hand with V2EntityBuilder and tests/helpers, with no world compiler. Marked `domain("strategic_cognition")`, `level("unit")`.

Rows, in rpg-planner's risk order:
1. **Regroup home with items** (about :391-402 fast, :651-657 slow). Two objective kinds, a position objective and an entity objective, each run on and off cadence. In the differential, the entity objective off cadence is defect A: `xfail(strict=True, reason="TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS")`. The position-objective rows are plain asserts.
2. **proj_resolved early-out** (about :389-390). A craft or collect objective whose target item is in the pending inventory (has_item on pending_inventory, including an inventory update from an earlier phase).
3. **nav_changed** (about :392-394). The objective's target_position differs from the current nav target.
4. **lodged_stayer suppression**, on both paths.
5. **The position != (0, 0) guard and the state.town_center fallback** when no town tile is found. The row id cites the filed P3 town_center sentinel ticket (rpg-planner gives the id).
6. **The fast path overwrites an earlier phase's target_set** (and its interaction, with reset=True); the slow path does not (about :633/:672). Pin it as current behaviour, named `..._current_behaviour_fast_path_overwrites`. It is a known-disagreement differential row under TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED, not an xfail: nobody has ruled it a defect.
7. **Material-blocker lead redirection**, slow path only (about :640-650), plus the malformed-detail `except` row. Characterisation only, since there is no fast counterpart. The malformed row asserts behaviour only (no redirect, no raise) and nothing about logging, because B's hygiene change turns the bare excepts into narrow excepts with a logger call.

Also in scope:
- Differential form: one parameterized test, each row an id. Run the same state through fused_strategic_pass twice, with a cadence that makes the tick off-cadence for the entity and with one that makes it due. Compare the navigation outcome (target_set, movement_mode_set) and the interaction reset for that entity. Rows where the paths are designed to differ are listed in a table at the top of the test, each with its reason and owning ticket; any disagreement not in the table fails.
- Inactive and dead entities are skipped (one small row).
- Line numbers are for orientation only. Tests reach branches through state, never through line numbers or private helpers.

## Out of Scope
- Any src/ change, including defect A, B's hygiene, the CLEAR-TARGET overwrite fix, and D (the restructure).
- The mutation run (TCK-20261109-ONE-MUTATION-RUN-MEASURES-HOW-MANY-INJECTED-FAULTS-THE-FUSED-STRATEGIC-PASS-TESTS-CATCH). It re-runs on this ticket's PR as evidence, but that is the E ticket's work.
- Diff coverage (item 3, deferred by the owner).
- Tests through the full kernel or a compiled world.

## Acceptance Criteria
- [x] AC1: Each of rows 1-7, plus the inactive/dead skip, has at least one characterisation test that fails if that branch's output changes. Shown by a local revert-or-perturb check per row, recorded in the Test Summary (e.g. flip the branch condition in a scratch copy and the row goes red), with no src/ change committed.
- [x] AC2: The differential runs each shared-branch row on both paths, and the known-disagreement table holds exactly row 1 (strict xfail citing defect A) and row 6 (current behaviour, CLEAR-TARGET). Any other disagreement fails the test.
- [x] AC3: Row 1's entity-objective off-cadence case is `xfail(strict=True)`, so A's fix makes it XPASS and fails until A's PR turns it into a plain assert.
- [x] AC4: Row 7's malformed-detail case asserts no redirect and no raise, and nothing about logging.
- [x] AC5: The new tests run in the PR lane in under 5 s total, are deterministic (no wall clock, no unseeded randomness), and carry the domain and level markers.
- [ ] AC6 (rpg-planner signed off the file at 7197afc3d by message on 2026-11-09, 34 passed + 1 xfailed; the PR comment id is added to the PR once the PR exists): rpg-planner's sign-off on the files under tests/unit/strategic/ is recorded in the PR (comment id).

## Related Tickets
- TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS (defect A, rpg-planner; flips row 1)
- TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED (row 6's owner)
- TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE (D; these tests are its safety net)
- TCK-20261109-ONE-MUTATION-RUN-MEASURES-HOW-MANY-INJECTED-FAULTS-THE-FUSED-STRATEGIC-PASS-TESTS-CATCH (E; measures this ticket's gain)
- TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS (the differential pattern)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/testing/test_taxonomy.md (section 5 levels, section 10 markers)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH/

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (fused_strategic_pass)
- tests/unit/strategic/

## Assumptions / Open Questions
- rpg-planner chose landing before A, as its own PR closing this ticket (rpg-planner, 2026-11-09). Row 1's strict xfail sits on main until A's PR flips it.
- The P3 town_center sentinel ticket id for row 5 comes from rpg-planner.
- If a row can't be reached through state alone (only via a private helper), stop and tell testing-planner. Don't mock the function's internals.

## Implementation Notes
New file tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py (35 passed, 1 xfailed, 0.5 s). No src/ change.

- State is hand-built with V2EntityBuilder, tick 5, entity 1 the subject and entity 2 a live pursuit target. "Off cadence" = both cadences 1000; "due" = concern cadence 1 and intent cadence 1000. The intent cadence stays long on purpose: with it due, evaluate_strategic_intent abandons an entity-targeted project that has no real pursuit set up, which hides the redirection difference this ticket pins.
- Every row is reached through state alone. Nothing is mocked and no private helper is called.
- Objective kinds "craft"/"collect" are plain strings on ObjectiveState (they are not ObjectiveKind members); the guard compares against those strings, so the tests use them as such.
- Row 5 cites TCK-20261109-STATE-TOWN-CENTER-DEFAULT-IS-A-SENTINEL-A-RETREAT-CAN-AIM-AT (rpg-planner; filed in #851): with no town tile and the default town_center (0.0, 0.0), a loaded entity is sent to the map origin; pinned as current behaviour.
- Row 1 also has a plain pin of the fast path's current value (entity objective off cadence regroups home), added at testing-planner's review; defect A's PR changes that assert as well as removing the xfail.
- Differential: 13 rows, one parameterized test. KNOWN_DISAGREEMENTS holds exactly two entries: row 1's entity objective (strict xfail citing defect A) and row 6 (earlier phase's target_set overwritten, pinned as different, citing TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED). A guard test asserts the table has exactly those two keys.
- Inactive/dead skip: StrategicWorkQueue.build already drops such entities before the loop, so the in-function early exit is shadowed. The row pins the pass-level behaviour; removing only the in-function guard does not turn it red (see Test Summary).

## Test Summary
Local: tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py: 35 passed, 1 xfailed in 0.5 s (deterministic: no wall clock, no randomness).

AC1 perturbation checks (a one-line change to src/systems/strategic_systems/intelligence.py in the worktree, test file run, file restored by hand; nothing committed under src/). Failing tests per perturbation:
- row 1, flip the objective-position guard in the fast path: 4 failed (row 1 position-objective test; differential rows position_objective_walk_set, entity_objective_loaded_entity, craft_item_missing).
- row 2, proj_resolved forced False: 2 failed (both row 2 completion tests).
- row 3, nav_changed forced False: 2 failed (row 3 and differential position_objective_walk_differs).
- row 4, drop the lodged_stayer test from the fast regroup: 2 failed (row 4 and differential lodged_stayer).
- row 5a, drop the position != (0, 0) guard from the fast regroup: 2 failed (row 5 origin and differential origin_guard).
- row 5b, drop the state.town_center fallback from the fast regroup: 11 failed.
- row 6, make the fast regroup keep an earlier target_set: 2 failed (row 6 and differential earlier_phase_target_set).
- row 7, disable the material-blocker redirect: 1 failed. Make the malformed-detail except re-raise: 1 failed.
- Inactive/dead skip, remove the in-function early exit: 0 failed (equivalent mutant: StrategicWorkQueue.build filters the same entities first, work_queue.py:31). The row pins the pass-level result only.

Known gap: the in-function inactive/dead guard cannot be pinned by a test on the function alone while the work queue duplicates it.
AC6 (rpg-planner sign-off, PR comment id) is pending.

## Files Changed
- tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py (new)
- the three ticket files filed by testing-planner (this ticket, the E mutation-run ticket, the held advisory-guard ticket)

## Completion Summary
Added 36 tests (35 passed, 1 strict xfail) pinning the fused strategic pass's off-cadence fast path branch by branch and against the slow path, test-only. AC1-AC5 met; AC6 (comment id) is added in the PR. Known gap: the in-function inactive/dead guard is shadowed by StrategicWorkQueue and cannot be pinned alone.
