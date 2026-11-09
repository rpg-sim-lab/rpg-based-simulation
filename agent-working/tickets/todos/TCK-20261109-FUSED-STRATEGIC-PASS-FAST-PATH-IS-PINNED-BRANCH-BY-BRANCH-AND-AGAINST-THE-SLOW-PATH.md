---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH
phase: open
date: 2026-11-09
tags: [testing, regression]
---

# TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH

## Title
fused_strategic_pass's off-cadence fast path is pinned branch by branch (characterisation), and a fast-against-slow differential on the same entity state lists every known disagreement as a row

## Status
OPEN

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
- [ ] AC1: Each of rows 1-7, plus the inactive/dead skip, has at least one characterisation test that fails if that branch's output changes. Shown by a local revert-or-perturb check per row, recorded in the Test Summary (e.g. flip the branch condition in a scratch copy and the row goes red), with no src/ change committed.
- [ ] AC2: The differential runs each shared-branch row on both paths, and the known-disagreement table holds exactly row 1 (strict xfail citing defect A) and row 6 (current behaviour, CLEAR-TARGET). Any other disagreement fails the test.
- [ ] AC3: Row 1's entity-objective off-cadence case is `xfail(strict=True)`, so A's fix makes it XPASS and fails until A's PR turns it into a plain assert.
- [ ] AC4: Row 7's malformed-detail case asserts no redirect and no raise, and nothing about logging.
- [ ] AC5: The new tests run in the PR lane in under 5 s total, are deterministic (no wall clock, no unseeded randomness), and carry the domain and level markers.
- [ ] AC6: rpg-planner's sign-off on the files under tests/unit/strategic/ is recorded in the PR (comment id).

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
- none

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (fused_strategic_pass)
- tests/unit/strategic/

## Assumptions / Open Questions
- rpg-planner chose landing before A, as its own PR closing this ticket (rpg-planner, 2026-11-09). Row 1's strict xfail sits on main until A's PR flips it.
- The P3 town_center sentinel ticket id for row 5 comes from rpg-planner.
- If a row can't be reached through state alone (only via a private helper), stop and tell testing-planner. Don't mock the function's internals.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
