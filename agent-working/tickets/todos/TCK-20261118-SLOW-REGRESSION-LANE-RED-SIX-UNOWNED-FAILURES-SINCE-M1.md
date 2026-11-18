---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261118-SLOW-REGRESSION-LANE-RED-SIX-UNOWNED-FAILURES-SINCE-M1
phase: open
date: 2026-11-18
tags: [regression]
---

# TCK-20261118-SLOW-REGRESSION-LANE-RED-SIX-UNOWNED-FAILURES-SINCE-M1

## Title
The slow-regression lane is red on six failures with no known-reds entry, first seen after the M1 steps; attribution is pending, by rpg

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
The scheduled `slow-regression.yml` run failed on 3 of its last 4 runs (11-17 to 11-18). The step "Report failing-set changes" (`tools/test_architecture/slow_regression_report`) exits 1 by design: failing tests with no entry in `tools/test_architecture/slow_known_reds.yaml` (UNOWNED). This is a real test regression, not infrastructure, and not the parked determinism root cause. The failing set is identical in the three red runs read (44070835917, 44191853013, 44287724126).

Status: **attribution pending, by rpg (u24), under the M1 rule (a)**: a grade pin is re-pinned only by the PR whose own moves caused it, with a predicted direction. Testing takes no action on the rows until rpg attributes each one.

## Scope
Record the evidence and track attribution. After rpg attributes each row to a step, testing carries out the follow-up that rpg's ruling names for it: a known-reds entry (ticket, owner, expiry), a re-baseline through the PR that caused it, or nothing if the code is fixed.

The six failures (run 44287724126, head 2df2a59a6; expected is the pinned anchor, actual is live):

1. `tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_500t_cognition_grade_stability`: COGNITION anchor is no-data, live grade 'S' (score 3.61, event_count 200, raw 1000, loop_detected True). "pillar gained data: re-anchor under a ruling".
2. `...::test_simq_routing_test_seed42_1000t_cognition_grade_stability`: the same text and values as 1.
3. `...::test_urban_political_seed42_1000t_social_grade_stability`: SOCIAL anchor 51.887, live 24.838 (1 trial).
4. `...::test_urban_political_seed123_1000t_social_economy_grade_stability`: SOCIAL anchor 53.8, live 30.460.
5. `...::test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability`: PROGRESSION anchor 0.42405, live 0.29843.
6. `tests/integration/world/test_living_world_ph9.py::test_long_run_simulation_ph9` (line 93): `assert len(bosses) <= 1` fails with "Duplicate bosses at tick 200: 2" (both `kind='world_boss'`). An invariant failure, not a grade pin.

Onset window: last green scheduled run 43979729008 at f4ac858f9; first red run 44070835917 at 9d13a3356. Commits in range include the M1 steps #946, #949, #952 and the rpg gate re-baseline bb26e4e5f. Not bisected; the cause is unconfirmed.

Already known-red in the same runs and out of scope: `test_behavioral_5k*` (TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS), hero_guild_routing_1000t cognition, urban_political_selfmodel_probe_200t, arena_stress_50v50, perf_movement[5000], perf_passive_scaling[5000].

## Out of Scope
- Adding known-reds entries or re-baselining any pin before rpg attributes the row.
- Re-opening the parked slow-regression determinism root cause.
- Choosing stale-baseline versus real-behaviour-shift; that is rpg's call.
- Any `src/` change.

## Acceptance Criteria
1. Each of the six rows is attributed by rpg to a step (#946, #949, #952, bb26e4e5f or other), with a ruling recorded in this ticket.
2. For each row the ruled follow-up is done, or an explicit known-reds entry exists with ticket, owner and expiry.
3. A scheduled `slow-regression.yml` run on main passes "Report failing-set changes", or every remaining failure is known-red with an owner.
4. Pins are re-pinned only by the PR that caused them (M1 rule (a)); no testing-side re-baseline precedes attribution.
5. **Row 6 (ph9:93, duplicate world boss) is its own item and an invariant failure, not a pin.** It closes only when the test passes again with the `len(bosses) <= 1` assertion unchanged (a code fix by rpg), or when rpg rules in writing that the invariant no longer holds, with the assertion changed through that ruling. A re-anchor, a re-baseline or a known-reds entry alone does not close it.

## Related Tickets
- TCK-20261007-BEHAVIORAL-5K-REBASELINE-AFTER-THE-STARVATION-CHAIN-LANDS (known-red, same lane)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (the lane's known-reds ownership)
- TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND (lands on top of this red lane; its PR body cites this ticket)

## Related Docs
- `tools/test_architecture/slow_known_reds.yaml`
- `tests/unit/worldassembly/test_corpus_diversity.py`
- GitHub issue #631 (CI workflow owner thread)

## Related Stored Artifacts
- CI artifact `slow-junit-2df2a59a6281f7d5f03f1ec9137b75663909342f` of run 44287724126 (expires; the values above are copied from it)

## Related Code Areas
- `.github/workflows/slow-regression.yml`
- `tools/test_architecture/slow_regression_report.py`
- `tests/integration/world/test_living_world_ph9.py`

## Assumptions / Open Questions
- Whether #3, #4 and #5 are stale pins or real behaviour shifts: rpg's call. The drops (SOCIAL about 40-45%, PROGRESSION about 30%) read like real drift.
- Whether #6 comes from M1's `kind` / occupation change breaking the world-boss uniqueness read: rpg to check. ENABLE_WORLD_BOSS_SPAWN is a deliberately OFF site in the spawn-sites guard.
- Whether the first red really sits in the M1 steps: unbisected.

## Durable state, lifecycle and clocks
None. A ticket and CI evidence only.

## Implementation Notes
Read-only investigation on 2026-11-18 by testing-planner: job logs and the junit artifact of run 44287724126; failing sets compared across the three red runs.

## Test Summary
Not applicable until attribution.

## Files Changed
This ticket only.

## Completion Summary
Open. Attribution pending, by rpg (u24).
