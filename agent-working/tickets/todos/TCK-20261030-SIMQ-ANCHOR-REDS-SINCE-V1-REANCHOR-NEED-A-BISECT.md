---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT
phase: open
date: 2026-10-30
tags: [simulation-quality, regression, determinism]
---

# TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT

## Title
Two SimQ grade-stability tests went red on main after the v1 re-anchor. Bisect them to the commit and mechanism that moved each score.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
codebase-implementer measured these on a clean `git archive` of origin/main de5a223ca, with no M7 code; codebase-planner relayed them on 2026-10-30. rpg-planner-ubuntu checked them against `tools/test_architecture/slow_known_reds.yaml` and `tests/simulation_quality/fixtures/grade_anchors.json`. Two `@pytest.mark.slow` tests in `tests/unit/worldassembly/test_corpus_diversity.py` fail, and neither is registered:

1. `test_urban_political_seed123_500t_cognition_grade_stability`. The anchor (from #747, cb4f95015) is `{"status": "no-data", "reason": "below_min_events", "min_events": 3}`. The run now fails against it, which suggests COGNITION now has enough events to get a grade.
2. `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability`. WORLD scores 0.25 against anchor B 0.32 (-22%, past the shared 20% tolerance).

A third red, `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`, is already a known red under TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE. Its measured 2.6506 equals the v1 value that entry names, so it is out of scope here.

These tests run under `audit_mode`, so host load cannot move the scores. codebase-planner saw both reds on 33da13604 as well. So the change landed between #747 (cb4f95015) and 33da13604; it is not, or not only, #785 or #790.

rpg-planner ruled on 2026-10-30, relayed via lead-planner-u24 and lead-planner: file this as a SEPARATE measurement-only ticket in the ubuntu queue, cross-linked to the held-rows ticket. Report to rpg-planner-ubuntu first, then to rpg-planner, which rules re-anchor or fix with the designer.

## Scope
1. Positive control: run both tests at cb4f95015 and confirm they pass there (the anchor commit). Then run at de5a223ca and confirm they fail with the values above.
   - If either one does not pass at cb4f95015, STOP and report: the window is wrong.
2. Bisect over the src commits in `cb4f95015..33da13604`. Test the candidates first:
   - 3533fde71 (#753 hostile acts by an act, not a state)
   - 35e80fb56 (#751 hostility lookups indexed)
   - 6e3ffea3f (#757 semantic foundation batch 1)
   - 2afdba653 (#760 dead systems classes deleted)
   - 792a6b439 (#762 unknown craft recipe refused)
   - 957caf8f6 (#758 proof digest)
   - f34d8254d (#765 squad group_id hash)
   - d914bace7 (#769 retreat step A)
   - dc059c49e (#771 cooperation candidates per tick)
   Use `git log --oneline cb4f95015..33da13604 -- src/` as the full list. Name the first commit where each test's score moves.
3. For each named commit, give the mechanism: which events or pillar inputs change, with event counts for the pillar before and after on that world, seed and tick count. Test 1 needs the COGNITION event count against `min_events` 3. Test 2 needs the WORLD inputs behind 0.32 -> 0.25.
4. Report the table to rpg-planner-ubuntu, which relays it to rpg-planner. rpg-planner rules re-anchor (intended behaviour, via testing's re-anchor tool) or fix (a separate ticket with the designer).

Run settings: `PYTHONHASHSEED=0`, `audit_mode` as the tests set it, and an explicit `RPG_MEASURE_CACHE` on ubuntu. Run sequentially on an idle host, and only in a heavy slot granted through lead-planner.

## Out of Scope
- Changing any anchor, test, tolerance or known-red entry. The known-red entries for these two tests are handled separately, under rpg-planner's conditions.
- The 36 held rows of TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE, including hero_guild_routing_seed42_1000t.
- Any src fix.

## Acceptance Criteria
1. The positive control is recorded: both tests pass at cb4f95015 and fail at de5a223ca, with the measured values.
2. For each test: the first moving commit, its PR, the measured score at its parent and at the commit, and the mechanism with event counts.
3. Every run records its commit, world, seed, ticks, PYTHONHASHSEED and wall time.
4. The report reaches rpg-planner-ubuntu, and the ruling (comment id) is recorded here before closure.
5. Run data written by this ticket is cleaned by run id.

## Related Tickets
- TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE (held rows; separate scope)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (#747, the anchor commit cb4f95015)

## Related Docs
- docs/simulation_quality/eval_matrix_results.md
- docs/guidelines/intentional_divergences.md (if the mover carries a divergence)

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/worldassembly/test_corpus_diversity.py
- tests/simulation_quality/fixtures/grade_anchors.json
- tools/test_architecture/slow_known_reds.yaml
- src/ (whatever the bisect names)

## Assumptions / Open Questions
- Standard tier, so dispatch needs the ubuntu owner's go through lead-planner. Heavy-slot order is also the owner's call. The current queue is perf movement, then B's paired run, then (b) hunger part 1.
- Assumed: the slow job runs both tests. Confirm in the slow-regression report.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
