---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE
phase: open
date: 2026-10-28
tags: []
---

# TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE

## Title
A low-hp subject near a hostile that neither engages nor acts gets a no-op PANIC_RETREAT every 10th tick, and its step toward food one tile away is refused, so it starves (gate V3, frontier_living_world s43 merchant 38)

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Main gate run 40653115297 (2c4869d61) has an unowned V3 at frontier_living_world s43: merchant 38 starves at t2518 with every way untried. Cached paired arms show it first appears with step A's R build (358f4cb7f); F4 has no effect and H2 is neutral. Three pure traces on d914bace7 (final hash 10b2e767a9ac equal with and without the probe; files /mnt/data/scratch-rpg-implementer/n15trace/out/trace{,2,3}.json) show:
- t2319-2341: hostile 30 acts on 38 (hp 40 -> 5), CombatRetreat is top, and 38 reaches (31,41).
- From t2342 no hostile acts and none is engaged with 38 (is_engaged, hostile_acts_on and engaged_adjacent_hostile are all False for hostiles 30 and 49). Hunger is the top goal with the inn way open (NeedAccess way_within_reach) until t2454; fatigue and then town_return from t2455.
- Every 10th tick, tactical.py:536-544 (the "pure retreat if hp is very low and engaged" branch of evaluate_entity_intent) is reached with a perceived-hostile list and hp_percent < 0.15. It has no engaged or acts-on gate and no hunger-line yield. retreat_destination returns None, so _destination_or_hold returns the subject's own tile: a no-op ENTITY_MOVE PANIC_RETREAT, which ends at once on the next tick (the task falls back to idle ENTITY_ACT).
- The current hunger project's objective targets (31,40), one tile north, which is unoccupied. candidate_selector.movement_target returns (31,40) on 7 of 19 ticks (t2342-2360), but the position never changes: the step is refused downstream of movement_target. The refusing line and ReasonCode are not traced yet. The stored nav target also flips between (31,40), (31,41) and None.
- 38 dies at t2518 with hunger 100 and hp 0.

## Scope
1. Trace the refusal: the movement phase's resolution for 38 at t2345 (file:line and ReasonCode), and the reset of the stored nav target between panic ticks.
2. Decide and fix, as one measured behaviour step:
   (a) tactical.py:536: what gates the low-hp pure retreat. The name says "engaged", but the code reads only perceived hostiles. Align it with step A's rule (retreat only against a hostile that acts) or with the engagement predicate, and handle a None retreat destination without stamping a no-op move.
   (b) the downstream refusal of the step to (31,40), if it is a defect of its own.
   Any semantic choice in (a), i.e. which predicate gates a low-hp retreat, goes to rpg-designer before code.
3. Measured as a behaviour step (decision 76) against its parent; report fls s43 merchant 38 and V3 on the gate worlds.

## Out of Scope
- The held flight and the REGROUP->RETREAT relabel step (post-M1, row 91).
- D73 (free meal).

## Acceptance Criteria
- A unit or scene test: a low-hp subject with a perceived but non-acting, non-engaged hostile and a reachable eat objective steps toward and eats. Its tactical intent is not a no-op PANIC_RETREAT.
- The refusal reason found in Scope 1 is named in the ticket with file:line.
- Paired step report; frontier_living_world s43 V3 entity 38 gone, or the reason it is not.
- Divergence entry (Bug Fix), Bible 04 / combat rulebook sentence for the low-hp retreat gate, parity entry.
- SimQ criterion (row 82): the outcome is already carried by the movement and task records, so no new event type.
- Known entry: this ticket's fix PR deletes the V3 entry for crowded_frontier seed 42 entity 30 from tools/test_architecture/rpg_gate_known.yaml (owner, #715 6692734974 item 2; the file takes only a date expiry, `expires_on: 2026-11-30`, so the delete is the PR's job, per testing-planner). If e30 still starves on the fix's pinned run, keep the entry and bring that to the owner; don't extend the date here.

## Related Tickets
- TCK-20261028-N15-KNOWN-V3-STARVATIONS-RECHECK-ON-THE-GATE-AFTER-STEP-A (where it was found)
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE (step A)

## Related Docs
- docs/plans/systemic_world/owner_decision_memo.md row 91
- docs/mechanics/02_combat_laws.md, docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer/n15trace/out/ (scratch, not in the repo)

## Related Code Areas
- src/engine/tactical.py (:214-229 panic, :536-544 low-hp retreat, _destination_or_hold, retreat_destination)
- src/engine/candidate_selector.py (movement_target)
- the movement phase resolution (to be located)

## Assumptions / Open Questions
- Owner question pending (via lead-planner-u24): own the s43 V3 as a scoped known entry until this lands, or hold M1 for the fix.
- Why step A exposes it (hypothesis: before step A, 38's hp never fell below 0.15 here) is untested.

## Implementation Notes
2026-11-03 named case (rpg-designer), crowded s42 base 65d43dfa9, pinned, e30 leader: a starving body beside a serving inn, held off by retreat with no acting hostile. rpg-planner-ubuntu's rows (out_e30pin/rows.jsonl, rows only, checked by no one else): all 9 present-not-acting retreats beside the inn are past the line, so they come from the hp-under-15% writer (tactical.py :531), not :216. Ticks t2050, 2060, 2110, 2120, 2170, 2196, 2198, 2200, 2202; hunger 100.0 on each; hp 1-5 of max hp 205-220. Support: from t2050 every direct `_panic_holds` call returned False, so :216 couldn't return, and the sampled t2100 returned :532. The 9 ticks' return lines weren't logged, so this is rpg-designer's rule plus that support, not a per-tick read. So this case is the second, ungated writer's cost. Hardening's max-hp growth raises the 15% line, so TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT bears on it too.
- 2026-10-31 DESIGNER RULING (SURV-07 family, from the F3-base family table). THE ONE PRECEDENCE LAW P: at every decision site choosing between a need past its escalation onset and any other goal or act, the need wins unless acting_threat_to(subject) holds (memo row 88: a perceived hostile attacking or pursuing the subject, or one that hit it within the window). No owner row is needed. Whether to flee at all stays on present_threat_to (AGENCY-07); where flight is warranted but the hostile is not acting, a pressing need still wins. ONE shared predicate pair, both reads: need_is_pressing(subject) (need_pull ESCALATION_ONSET line) and need_yields(subject, state) = acting_threat_to. Every site calls them; none re-derives them. ONE PRECEDENCE GRID test: {need pressing y/n} x {no hostile / perceived only / present-not-acting / acting} x site -> winner; each site's ticket adds its rows. Provisional order until harm-per-tag is counted: ENGAGEMENT -> LOW-HP-RETREAT -> TOWN-RETURN -> ESCALATED-SWITCH -> FLEE-LINE.
- THIS SITE (tactical.py:536-544): flight on present_threat_to only (consistent with retention ruling A); with no present threat there is no tactical retreat and the pressing need runs. Uses the predicates landed by ENGAGEMENT-OVERRIDES. F3 base: 4963 ticks / 40 subjects / longest 270 (crowded 4694).
## Test Summary
## Files Changed
## Completion Summary

- **2026-11-01 evidence (F3 f3r, urban s44, subject 17; rpg-designer):** from t3250 to t3306 the subject halted in REGROUP at (43-45,23) with hostile 24 (faction 0) adjacent. Its hp fell 70 to 0, and it did not flee even at hp 16 (REGROUP/ENTITY_ACT). The designer ruled this death the pre-existing no-flee-at-low-hp gap (law P family), not F3. Trace: lane B n14/out/tr17.json.

## 2026-11-01 rows from groups batch C (rpg-designer ruling, via rpg-planner)
- A cornered low-hp subject with no home region holds and dies. urban s42 e23 (churn-on-F3): AVOID_NO_ROUTE at tactical_hold.py:117 fires when retreat_destination (tactical_destinations.py:80) returns None. That function is pure region geometry: a point away from threats clamped to the region, else the home_region centre, else None, with no occupancy or route_search. e23 held at hp<=32 beside e17 and died t1687. It is the same gap as e9's "why no town_center" (TCK-20261101-A-RETREAT-WALKS-TOWARD-THE-THREAT).
- Rename the AVOID_NO_ROUTE reason to NO_RETREAT_DESTINATION: it is not a route failure.
- e23 final (ubuntu probe): retreat_destination is None from both [41,31] and [41,30]. It was not boxed in. The t1680/1681 moves came from a non-group writer.
- Named case for the precedence chain's ENG -> LOW-HP step (rpg-designer): "an inventory errand does not walk a subject that is under attack at low hp". e23 at low hp under attack took the strategic carry-pending-inventory-to-the-nearest-town-tile step (intelligence.py:400/406/678, nav reason REGROUP) while its tactical decision said HOLD. The two layers disagree, and the strategic walk wins.
- Rename row: the REGROUP reason on a town-carry walk should name the errand (for example CARRY_TO_TOWN). REGROUP should mean regrouping with a group.
- Counts row: tiles beside the inn are in NO region (containing_region None), so retreat_destination has no geometry at all there. This is wider than the no-home gap. Count per world the share of walkable tiles in no region, and the share of NO_RETREAT_DESTINATION holds in no region versus inside a region with no home. Answered (rpg-planner, Bible 06 section 2 'Unclaimed space', docs/mechanics/06_worldbuilding_foundation.md:42): a point inside no region legitimately has no region (None). It is not an assembly error, so no region-coverage ticket. The gap is retreat_destination having no fallback for an unclaimed position. It belongs to this ticket (the fallback shape, e.g. the nearest region or town tile, is for the designer to rule after the counts). Per NO_RETREAT_DESTINATION hold, the counts row also records: (a) the distance to the nearest region boundary; (b) the distance to the nearest town building or service, with the threat side noted (behind the threat or away from it). rpg-designer lean, not a ruling: "away from the threats, unclamped, a bounded step, in unclaimed space", else the nearest region's edge away from the threat. The counts decide. No inn-surroundings claim and no owner row (rpg-designer 2026-11-01).
- Ungated hold counter on main (lane A, 2026-11-02; base 15a8f5893, 3 worlds x s42-44, 5000t, 9/9, hash-neutral): 0 NO_RETREAT_DESTINATION (AVOID_NO_ROUTE) holds, 0 subjects, in all 9 runs. The scan works: PANIC_RETREAT 3835 and AVOID_HOSTILE 3279 subject-ticks seen. e23's holds were on the churn arm only. The boundary/town/threat-side fields are therefore empty, and the unclaimed-space fallback ruling waits for this counter to be re-run after churn lands (lane A branch rpg-eng-overrides-need, hold_probe.py).
- Post-churn re-run of hold_probe.py (rpg-designer 2026-11-02): read the main result as 0 holds on 9 of 15 seeds with the scan shown working, not as the gap being gone. The re-run also answers why holds appear on the churn arm and not on main: split holds by group membership and role, and see what puts a subject on the notice_unengaged_hostile path (posture "avoid" toward an adjacent target). If the post-churn count is about 0 again, report it and rpg-designer closes the fallback as guard-only (one unit test, no behaviour work).
