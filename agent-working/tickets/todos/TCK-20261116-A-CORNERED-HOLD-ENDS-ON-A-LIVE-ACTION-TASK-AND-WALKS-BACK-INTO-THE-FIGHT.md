---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261116-A-CORNERED-HOLD-ENDS-ON-A-LIVE-ACTION-TASK-AND-WALKS-BACK-INTO-THE-FIGHT
phase: open
date: 2026-11-16
tags: []
---

# TCK-20261116-A-CORNERED-HOLD-ENDS-ON-A-LIVE-ACTION-TASK-AND-WALKS-BACK-INTO-THE-FIGHT

## Title
A cornered (AVOID_NO_ROUTE) hold ends one tick later on a live action task, and the subject walks back into the fight

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed by rpg-planner on 2026-11-16. The owner chose "(a) Land + new ticket (Recommended)" on the HOLD stage-2 Tier 2 FED stop, #715 6906654192 (row `.claude/handover/drafts/rpg-designer-hold-tier2-fed-owner-row.md`, sha256 2b0073146f0f). rpg-designer read the evidence and named the ticket.

The Tier 2 read for TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP found 1 death the HOLD fix caused (FED) and 4 it did not. The FED death is urban_political s43 e12:
- The arms are identical up to t279. At t280 both choose an AVOID_NO_ROUTE HOLD: e12 is cornered and has no route.
- Base (f94417e6f): the step-under-HOLD bug moves e12 to (40,41) and then (40,40), a hometown tile with hazard 0. It takes free hits (hp 53 to 33), holds there to t291, and survives the window.
- Fix (b9d78c427): e12 correctly takes no step at t280. At t281 its HOLD ends with an ENTITY_ACT task live (mode REGROUP) while base is still holding. It REGROUPs into e17 and dies COMBAT at t291 on (41,40), killer 17. That is 10 ticks after the hold the fix ended, on the edge of the 10-tick FED window.

Mechanism (designer) [I]: the fix ends an AVOID_NO_ROUTE hold as soon as a self-decided action task is live, and the subject walks back into the fight. In base, the subject survived only because of the step the fix rightly removes.

Evidence: spy `dying_window_v8.py` 3828af12 (docstring-only revision 082e99e8). Cells `/mnt/data2/rpg-measure/holdmove/dying/cells/fix_urban_political_s43_v8.json` (c085c86b) and `base_urban_political_s43_v8.json` (7fd61d77). Spy limits: ordinary hits (`resolve_attack`) are not recorded, and `hold_writer` records the capacity_enforcement copy site rather than the originating writer. The designer judged on task and mode.

## Scope
1. Design (rpg-designer, after the HOLD fix lands): should a typed AVOID_NO_ROUTE hold, which the subject chose because it had no route, end on a live self-decided action task? Or only when a route reappears or the engagement changes? Candidate: for AVOID_NO_ROUTE, a live action task does not break the hold unless the action's target is adjacent and attackable. In that case the subject attacks in place and does not walk.
2. Implement the ruled design with real-kernel tests: cornered with a non-adjacent target, cornered with an adjacent attackable target, and a route reappearing.
3. Measure against the landed HOLD fix as base: the standing bar, plus a row counting AVOID_NO_ROUTE holds that end on an action task and are followed by a death within 10 ticks.
4. Bible / parity / divergence updates for the ruled behaviour.

## Out of Scope
- The WATCH re-choose loop (TCK-20261115-A-WATCHING-CHARACTER-RE-CHOOSES-WATCH-HOSTILE-BESIDE-A-QUIET-ENEMY-FOR-80-TICKS).
- The HOLD step suppression itself (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP).
- A cornered PANIC_RETREAT with no flight destination (TCK-20261021-FLIGHT-OSCILLATION-COUNTS-NO-DECISION-TICKS-AND-A-CORNERED-SUBJECT-HOLDS (b)). That one is related, but it is a different entry path.

## Acceptance Criteria
- The designer's ruling is recorded in Bible 04 (or the HOLD section it lives in), with a test for each case in Scope 2.
- In the measurement, the AVOID_NO_ROUTE-hold-ends-on-action-then-death-within-10 count does not rise against the landed HOLD base, and the standing bar holds.
- A parity row and a divergence entry exist for the changed rule.

## Related Tickets
- TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP (source; this FED is disclosed in its PR)
- TCK-20261115-A-WATCHING-CHARACTER-RE-CHOOSES-WATCH-HOSTILE-BESIDE-A-QUIET-ENEMY-FOR-80-TICKS
- TCK-20261021-FLIGHT-OSCILLATION-COUNTS-NO-DECISION-TICKS-AND-A-CORNERED-SUBJECT-HOLDS

## Related Docs
- docs/mechanics/04_strategic_cognition.md; docs/mechanics/02_combat_laws.md; docs/guidelines/intentional_divergences.md (2.206)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/holdmove/dying/ (cells, spy, checkers; kept until the HOLD PR merges)

## Related Code Areas
- The HOLD-end path changed by the HOLD fix (b9d78c427 vs f94417e6f). Exact site to be located at design; the spy did not record the originating writer.

## Assumptions / Open Questions
- Dispatch needs an owner yes. Planning starts after the HOLD fix lands.
- The death sits exactly on the 10-tick window edge, and it is 1 of the 6 extra urban COMBAT deaths.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
