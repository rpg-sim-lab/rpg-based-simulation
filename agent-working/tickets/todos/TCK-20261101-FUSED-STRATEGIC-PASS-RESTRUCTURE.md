---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE

## Title
Pay down the code-health debt in fused_strategic_pass and the files F3 grew: split the 408-line strategic pass into named stages

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
F3 (TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE, PR #823) landed six code-health "worse" rows that the owner accepted as ratchet debt (#715 6557046208, option (a)):

| function / file | old -> new | why |
|---|---|---|
| StrategicIntelligenceSystem.fused_strategic_pass, cognitive complexity | 433 -> 437 | three lodged-stayer guards inside one 408-line function |
| fused_strategic_pass, function length | 407 -> 408 | the is_lodged_stayer assignment |
| src/systems/strategic_systems/intelligence.py, module length | 1831 -> 1833 | import plus assignment |
| PhaseDependencyGraph.should_run_phase, cognitive complexity | 49 -> 50 | the lodging trigger joins an existing condition |
| src/core/state.py, module length | 1668 -> 1672 | two typed fields plus canonical lines |
| src/core/updates.py, module length | 1308 -> 1315 | two fields plus the merge helper |

fused_strategic_pass is already far above every ceiling (cognitive complexity 437). No change near it can return a row without a restructure.

## Scope
1. Split fused_strategic_pass into named, separately testable stages (for example: target writers, section-5 objective redirect and fallback, material lead), with no behaviour change.
2. Bring the six debt rows back to or under their pre-F3 values, and lower the function's ceiling as far as the split allows (tighten the ratchet).
3. should_run_phase: a table or predicate per trigger, if it pays down the row.

## Out of Scope
- Any behaviour change, including the ordering of target writers (the ~30 writers noted in F3's investigation).
- core/state.py and core/updates.py restructuring beyond F3's own lines.

## Acceptance Criteria
- Final state hashes and 25-tick chains are byte-equal to main on urban s44, crowded s46 and frontier s45 at 5000t, plus 3 worlds x s42 at 2000t.
- make code-health shows the six rows at or under their pre-F3 values (or removed), with no new or worse rows. make typecheck-py is clean.
- Scoped unit, engine, architecture and integration (-m 'not slow') pass.
- Hot-loop: yes (the fused strategic pass runs every tick for every entity).

## Related Tickets
- TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (source of the debt)
- TCK-20261101-CLEAR-TARGET-IS-NEVER-APPLIED (touches the same target writers)

## Related Docs
- docs/plans/codebase_health/handoffs/handoff_to_rpg.md (the 2026-10-05 debt precedent)
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE/

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (fused_strategic_pass)
- src/engine/phase_graph.py (should_run_phase)
- src/core/state.py, src/core/updates.py

## Assumptions / Open Questions
- The perf pause (#715 6556861718): this is a refactor with byte-equal acceptance, so no timing claim is made. Check whether the pause defers it.

## Implementation Notes
Filed by rpg-planner 2026-11-01 under the owner's option (a), #715 6557046208. HELD (lead-planner-u24, 2026-11-01): not dispatched until checkpoint (a) of the perf-pause replan has a base. Then it goes as a named hot-loop batch with its own timing pair; the ubuntu lead may take it to the owner with the replan.

## Test Summary

## Files Changed

## Completion Summary
