---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
phase: done
date: 2026-11-17
tags: []
---

# TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION

## Title
In urban_political s42, half the survivors re-create a resolve_blocker project about every 80 ticks after t≈550 (each one times out and is abandoned), and cooperation stops

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
HARD liveness (M1 Phase 1), found by rpg-implementer-3 in N10's cap-tail row (urban_political s42 1000t, main bb26e4e5f vs N10 67b507f8c). N10 clears the cap tail: subjects at cap with a SUSPENDED record are 0 from t700. But the cooperation stall does not clear. The last cooperation_event is t550 on main and t569 with N10. The current project stays resolve_blocker for 10-16 of 20 survivors from t600 to t999, while only 2 are at cap. It's pre-existing on main. rpg-designer ruled it a separate HARD-liveness defect, to be read and ruled BEFORE the run-1 boundary measurement.

EVIDENCE (lane C, rb_table.py on the N10 s42 run): it is CHURN, not one long-lived record. Each subject builds a new resolve_blocker about every 80 ticks (e.g. entity 1: projects created at t259, 439, 519, 599, 679, 759). Each earlier one ends ABANDONED through the existing 50-tick timeout. At t700/t800/t900, 17 subjects hold resolve_blocker records; 10/9/13 are ACTIVE (ages under ~48), with 89/112/131 abandoned in total. So resolve_blocker wins goal selection every cycle after t≈550: the blocker it targets is never resolved, the timeout ends the project, and the next cycle builds another. Not yet traced: the blockers themselves (REFINED_UPDATE blockers_add_or_update, readable without the host).

rpg-designer's pointer: the 50-tick resolve_blocker timeout (intelligence.py, inside the current-and-ACTIVE branch) should end an ACTIVE current resolve_blocker within ~50 ticks. Holding it for 300+ ticks means the project is either re-created each time it ends (the TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK family) or the timeout branch isn't reached.

## Scope
1. Evidence (lane C, from the N10 artefacts): a per-subject table for s42 after t600, covering project ids and created ticks, re-creation chains, the blocker kind and target, whether the timeout fired, and end reasons.
2. The designer rules the cause class and the fix shape before code.
3. Fix, own-job counts, docs and divergence, in the run-1 segment.

## Out of Scope
- N10's suspension expiry (merged on its own job).

## Acceptance Criteria
- The per-subject evidence table is delivered and the cause is named.
- After the fix, on urban_political s42 1000t: no subject holds resolve_blocker as the current kind for more than the timeout + cadence without the project ending or the blocker changing (the exact bar is fixed by the designer before data).
- Cooperation is not stalled by it (reported).

## Related Tickets
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (N10; found while reading its cap-tail row)
- TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK
- TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER
- TCK-20261101-A-CONGESTION-BLOCKER-RESOLUTION-SENDS-A-SUBJECT-TO-THE-TOWN-CENTRE
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- N10 worktree data/runs/urban_political_42_1000_3661521_e3fced34; base /mnt/data2/rpg-wt/mainref/data/runs/urban_political_42_1000_3352484_7cca1b5c; reader /mnt/data2/rpg-measure/n10/capread/capread_n10.py

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (the resolve_blocker timeout), the blocker creation paths

## Assumptions / Open Questions
- One trial per side (deterministic).

## Implementation Notes
- Filed by rpg-planner on rpg-designer's ruling (2026-11-17).
- Cause: re-inference replaced the stored congestion blocker and a quiet blocker was removed on first sight, so each 50-tick timeout was followed by a fresh blocker with no suppression and a new resolve_blocker.
- Fix (divergence 2.214, STRAT-355): re-inference merges into the stored blocker; a congestion blocker is removed only after 200 ticks of observable quiet; `ProjectState.ended_tick` and the blocker-owned `BlockerState.last_project_end_tick` (stamped by the same update that ends the project, one helper `ended_blocker_stamps`; needed because capacity_enforcement, phase 42, runs before apply and can trim a just-ended record).
- Disclosed gap: a resolve_blocker that completes via typed_completion does not stamp the blocker (moot per designer).
- Gate version: the busy gate was v3 (ef5020fc) for the whole rerun; it became v4 (b1b1bafc, python executables only) after the cells finished.

## Test Summary
Own-job cells_fix2b (tree_fix2, 5000t, spy + plain twin, S9 #715 6972088075), designer-accepted after recounting all four cells from the raw chunks: every end typed, B3 = 0, no quiet removal inside the bound, rebuild gaps follow the 100/200/400/800 backoff. Claim: "churn reduced, no untyped ends".
- B1-B6 = 0, twin hash match, PINNED, logging_errors 0, exceptions {} in frontier_living_world s42 (146 timeout ends), urban_political s42 (267), crowded_frontier s42 (101); urban_political s123 report cell 191.
- Builds vs main: urban s42 429 -> 274 (-36%); s123 339 -> 207 (-39%).
- Urban s42 rose vs the first fix (190 -> 274 builds, timeouts 183 -> 267): the first fix removed the blocker early; now there is no early removal, so the honest backoff re-attempts happen (gaps 100/200/400/800).
- Crowded inventory removals (27) are the resolved path.
- Perf: plain twin times are approximate (log and json mtimes, load unknown); urban s42 about +22% (planner figure), no flag.
- B3 was corrected (owner-recorded omission, #715 6971764418).
- S8 test-fixture edits: 10915fa79 (old-shape N10 project tests drop the whole appended tail) and 638e3a67b (assertion on the fused-pass end tick); no assertion weakened.
- Scoped unit run, mypy and tests/architecture green on 8f38e313f; later commits changed tests only (36 passed after 16f4908b2).
- Separate HARD ticket: urban_political s123 last cooperation tick stays at 1926 (t=4400-4900), mostly fatigue; not part of this fix.
- Fixture re-record: #715 6948845825. Order-dependent observability failures: TCK-20261117-TWO-OBSERVABILITY-TESTS-FAIL-ONLY-AFTER-A-LONG-SAME-PROCESS-RUN.

## Files Changed
src: core/strategic.py, core/state.py, core/update_models/strategic.py, ai/goals/live_record_route.py, engine/{building_arrival,building_services,lodging,checkpoint_fields}.py, observability/{event_shapers,extraction/strategy}.py, systems/strategic_systems/{blocker_lifecycle,cognition_export,entity_target_objective,intelligence}.py. Docs: Bible 04, intentional_divergences 2.214, parity STRAT-355, event_type_coverage, registries/mechanisms.yaml. Tests: unit/strategic (4 files), unit/engine (3), unit/observability, unit/tools mechanism completeness, event extractor fixture.

## Completion Summary
The resolve_blocker churn is reduced with no untyped ends; the stall in urban s123 is a separate HARD ticket.
