---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261117-PAY-DOWN-THE-STEP-4-KIND-IS-SPECIES-CEILING-RAISES
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-PAY-DOWN-THE-STEP-4-KIND-IS-SPECIES-CEILING-RAISES

## Title
Pay down the code-health ceilings that M1 step 4 (kind is the species) raised

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Drafted by rpg-implementer-2 on the M1 step-4 branch (rpg-m1-kind-step4) for rpg-planner's review. Step 4 of TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD gave every spawner a separate `species` and `occupation` argument and added typed refusals where a code-chosen default species stood. The code-health check (tool numbers, head b4b43c3ae, `/mnt/data2/rpg-measure/m1step4/health/head.log`) then found 12 blocking rows over their ceiling. The five function-level-import rows were fixed (module-level imports); the comment lines were not trimmed (that is squeezing). The jscpd rows reported alongside are the same on clean origin/main and are not ours.

The rows (ceiling before → raised to):
- src/world/boss.py `BossService.check_for_boss_spawn` function-length 135 → 137; `BossService.check_for_lair_spawn` 97 → 98
- src/world/camp.py `CampService.process_camps` function-length 87 → 89
- src/worldassembly/resolver.py `CompileProfileResolver.resolve` function-length 154 → 157
- src/worldbuilding/compiler.py `WorldCompiler.compile` complexipy cognitive-complexity 142 → 143
- src/systems/world_systems/generator.py ruff PLR0913 (too many arguments) 1 → 2
Repeats, on the orchestrator and scenario_runner rows that TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED already owns (raised again, see that ticket's note): orchestrator.py module 1126 → 1128, `CampaignOrchestrator` 1004 → 1005, `_build_initial_state` function-length 420 → 421 and complexipy 47 → 49; scenario_runner.py `ScenarioRunner.execute` function-length 154 → 156 and complexipy 17 → 19.

## Scope
1. Pass the spawn identity (species, occupation) as one typed argument to the generator spawners, so the argument count falls back under its ceiling.
2. Move the species refusals into one helper that the compiler, resolver, orchestrator and scenario runner call, so each function sheds its refusal lines and complexity.
3. Extract the boss and camp spawn argument assembly so the three spawn functions shed their added lines (no line squeezing).
4. Then `python3 -m codebase.health tighten` to lower each row and clear its `retiring_ticket`.
5. Behaviour-neutral: whole-doc IDENTICAL on the 3 gate worlds at s42 (an owner run ask), plus the scoped unit tests.

## Out of Scope
- Any meaning change to kind, occupation or role.
- The jscpd duplicate-block rows (report-only, present on main).

## Acceptance Criteria
- Each row listed above is back at or below its pre-raise ceiling, or lowered by tighten with the reason stated, and none cites this ticket any more.
- The refusals go through one helper, with the existing K6d tests still passing unchanged.
- IDENTICAL proof on the 3 gate worlds at s42.

## Related Tickets
- TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD (raised them)
- TCK-20261117-PAY-DOWN-THE-NINE-LINE-CEILINGS-THE-OCCUPATION-FIELD-RAISED (the earlier raise on orchestrator and scenario_runner)

## Related Docs
- docs/guidelines/agent_working_environment.md ("Reading code-health results on a PR"); docs/guidelines/python_code_standard.md §4

## Related Stored Artifacts
None.

## Related Code Areas
src/world/, src/worldassembly/, src/worldbuilding/, src/systems/world_systems/generator.py, src/domains/campaigns/, src/testing/

## Assumptions / Open Questions
- The owner approves each ceiling raise (the ceiling rule); the numbers above are the code-health tool's, not estimates.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
