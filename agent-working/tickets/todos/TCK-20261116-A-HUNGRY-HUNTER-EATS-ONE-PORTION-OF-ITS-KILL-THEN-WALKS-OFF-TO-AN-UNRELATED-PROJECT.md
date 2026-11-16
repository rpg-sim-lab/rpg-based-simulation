---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261116-A-HUNGRY-HUNTER-EATS-ONE-PORTION-OF-ITS-KILL-THEN-WALKS-OFF-TO-AN-UNRELATED-PROJECT
phase: open
date: 2026-11-16
tags: []
---

# TCK-20261116-A-HUNGRY-HUNTER-EATS-ONE-PORTION-OF-ITS-KILL-THEN-WALKS-OFF-TO-AN-UNRELATED-PROJECT

## Title
A hungry hunter eats one portion of its kill, then walks off to an unrelated project and leaves the rest

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Filed by rpg-planner on 2026-11-16. The owner chose "(a) Land, mark test, P1 ticket (Recommended)" on the #931 hunting row, #715 6908596468 (row `.claude/handover/drafts/rpg-designer-hold-pr931-hunting-owner-row.md`, sha256 4a28365d14fc). rpg-designer named the ticket.

CI on #931 (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, head f49118c66) failed `tests/mechanic_scenarios/test_hunting_kill_to_meat.py::test_a_kill_leads_to_the_meal_at_the_same_hunger_the_hunt_starts_at`. The test asserts that raw_meat is gone from the carcass within 40 ticks of the kill. The test passes on main (f94417e6f) and fails with the fix.

Lane A's read-only trace (both trees, t5-t40; raw `probe_out/wolf_{base,head}.json` and `goals_head.json` in lane A's scratchpad):
- The wolf (hunger 60) kills a goblin at t7. The carcass 1000022 is at (87,36) and the wolf is at (89,36).
- At t15, both trees eat one portion in place (`tactical_rest.eat_at_corpse_in_place_update`: hunger ≥ `EAT_CARRIED_MIN_HUNGER` 40, carcass within `CARCASS_NEAR` 2.0, brain ticks only). Hunger goes 60.5 → 40.5.
- At the t15 strategic pass, both trees see the scavenge opening step as AVAILABLE: the carcass is 2.0 from the wolf, within `SCAVENGE_RADIUS` 20, and raw_meat is edible for it. Hunger utility is 63.99. But `region_stabilization` scores 100.00 (target wolf_den (87.5,50)) and wins. A stabilize/investigate project opens, and no hunger project ever exists. At t35: region_stabilization 100.00 (bandit_road), hunger 41.05. Modifiers touch neither.
- Base: the HOLD bug's priced steps keep the wolf within 2 tiles, so at the t25 brain tick it eats the rest (hunger 40.8 → 20.8) by chance.
- Fix: the kill's HOLD ends at the t15 project walk (the P3 reset). The wolf walks south at full speed and the meat is left. The carcass vanishes at t107.
- `tactical_avoid.eat_at_hunger_corpse`, the project or objective path, is never called in either tree.

There are two gaps here, and both already exist on main; the HOLD bug was papering over them:
- (i) scavenging its own fresh kill loses to an unrelated project while the hunter is hungry and 2 tiles from the kill;
- (ii) the in-place meal has no "keep eating my kill". After one portion it relies on standing within 2 tiles at a brain tick.

Generalisation: on #931's head, CI's quick set failed only 3 tests, and the 26 slow scenario tests (mechanic_scenarios and integration/scenarios) gave 24 passed, 1 skipped, 1 xfailed, 0 failed. This is the only flow found that relied on the HOLD linger. Not covered by any test: looting or gathering after a kill. Stage 2 counted no meals or carcasses. Starvation deaths there were fix 0 vs base 1 (a crowded worker).

## Scope
1. Check first whether region_stabilization should be eligible for wild_creature at all (t15 table: 100.00 for wolf_den; t35: 100.00 for bandit_road; lane A probe_out/goals_head.json). If it is a person goal reaching creatures, that fix may resolve (i) on its own.
2. Design (rpg-designer): how a hungry subject treats its own fresh kill within reach against opening or continuing an unrelated project, and whether the in-place meal continues until sated or the carcass is empty. The likely shape: a hungry subject's own fresh kill within reach outranks opening an unrelated project.
3. Implement the ruled design with real-kernel tests. Then remove the `xfail(strict=True)` on `test_a_kill_leads_to_the_meal_at_the_same_hunger_the_hunt_starts_at`, which must pass.
4. Measure paired against the landed HOLD base: the standing bar, plus a row counting kills followed by carcass meat finished by the killer within 40 ticks, base vs new.
5. Return TOWN-205 (town_resource.yaml) from `divergent` to `verified`, and update Bible 03 §3.1/3.2 and the divergence entry as the ruling requires.

## Out of Scope
- The HOLD step suppression (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP).
- A cornered hold ending on a live action task (TCK-20261116-A-CORNERED-HOLD-ENDS-ON-A-LIVE-ACTION-TASK-AND-WALKS-BACK-INTO-THE-FIGHT).
- Cooking, people hunting for sale, births of game (TOWN-205 support_boundary).

## Acceptance Criteria
- The hunting scenario passes without the xfail on the landed HOLD base.
- The designer's ruling is recorded in the Bible, with tests for: own kill within reach while hungry; own kill out of reach; sated subject; and, if Scope 1 finds it, a creature-eligibility test.
- In the measurement, the kill-to-meal row does not fall against base, and the standing bar holds.
- TOWN-205 is back to `verified`, with a passing `test_path`.

## Related Tickets
- TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP (source; #931 lands with this test xfail(strict) and TOWN-205 divergent)
- TCK-20261116-A-CORNERED-HOLD-ENDS-ON-A-LIVE-ACTION-TASK-AND-WALKS-BACK-INTO-THE-FIGHT
- TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH

## Related Docs
- docs/mechanics/03_economic_laws.md §3.1-3.2 (decision 44); docs/mechanics/04_strategic_cognition.md; docs/parity_ledger/town_resource.yaml TOWN-205; docs/guidelines/intentional_divergences.md 2.107

## Related Stored Artifacts
- Lane A scratchpad probes (wolf trace and goal table), referenced by the owner row; copy them into this ticket's staging evidence at design time.

## Related Code Areas
- src/ai/goals/opening_steps.py (`_scavenge_step`); src/systems/strategic_systems/intelligence.py (goal table, region_stabilization scoring); src/engine/tactical_rest.py (`eat_at_corpse_in_place_update`); src/engine/tactical_avoid.py (`eat_at_hunger_corpse`)

## Assumptions / Open Questions
- Dispatch needs an owner yes. The design starts after #931 lands.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
