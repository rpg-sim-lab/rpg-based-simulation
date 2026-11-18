---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION

## Title
In urban_political s42, half the survivors re-create a resolve_blocker project about every 80 ticks after t≈550 (each one times out and is abandoned), and cooperation stops

## Status
OPEN

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

## Test Summary

## Files Changed

## Completion Summary
