---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261101-A-CONGESTION-BLOCKER-RESOLUTION-SENDS-A-SUBJECT-TO-THE-TOWN-CENTRE
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-CONGESTION-BLOCKER-RESOLUTION-SENDS-A-SUBJECT-TO-THE-TOWN-CENTRE

## Title
A congestion blocker-resolution project sends its subject to the town centre, from inside town, right after a lodge

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
In urban_political s44 (F3 branch rpg-sleeper-lodges, f3r code), subject 17 left its inn bed (building 20006, (65,23), inside town_tiles / region trading_hometown). From t3187 to t3220 its target flipped every tick at the door (the leaver re-target churn, to N14). At t3222 a project of kind resolve_blocker ("resolve_blocker_blocker_congestion") replaced the finished fatigue project. Its reach_location objective has target_position (25,25), which is state.town_center. intelligence.py:670 (the section-5 active-objective redirect, `target_set=target_pos`) wrote that target at t3224, and the subject walked west across town. Facts come from lane B's entity-tagged re-run, reported 2026-11-01.

The town-return fallback (intelligence.py:678, REGROUP) was not the writer: it wrote (65,22), the subject's own tile. nearest_town_tile was not involved. The earlier "town-return sends an in-town subject to the centre" reading is withdrawn.

Designer hypothesis, to be tested by the counts: the leaver churn itself registered the blocker_congestion, and resolving it sent the subject to a fixed town point. If so, N14's re-lodge-cycle fix removes the trigger, and this ticket may close on N14's numbers.

## Scope
Counts first, with no fix shape before the counts and the designer's ruling. Take the counts on the N14-on-F3 runs, from the same runs as the N14 report, per world and seed, for the arms base, F3 and N14-on-F3:
1. blocker_congestion creations per run.
2. The share of those created within 50 ticks of a lodger leave, or at a building reach tile.
3. The resolution's target kind (town_center versus other) and walk length in tiles.
4. Deaths within 200 ticks of such a walk, with cause.
5. The writer of the resolution target, by file:line.

## Out of Scope
- Any fix before the counts. The designer's lean, which is not a ruling, is that a congestion resolution moves the subject to the nearest free tile out of the jam, not to a fixed town point.
- The leaver churn itself (N14).
- The town-return fallback (:678).
- Hazard exposure on the walk (H1).

## Acceptance Criteria
- The counts 1-5 are reported for base, F3 and N14-on-F3 on the same seeds, at or after the F3 base.
- The designer rules on the hypothesis: closed on N14's numbers, or a rule shape for where a congestion resolution sends its subject.

## Related Tickets
- TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3; subject 17 disclosure line)
- TCK-20261021-A-CROWDED-SERVICE-DOOR-BLOCKS-A-STARVING-SUBJECT (N14; the counts ride its F3 re-measure)
- TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK (STALEMATE/WANDER nav family)
- TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER (designer: not this; there a blocker never forms)

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/guidelines/intentional_divergences.md 2.155

## Related Stored Artifacts
- none yet; lane B's tagged-trace output (scratch) is summarised in Request Summary

## Related Code Areas
- src/systems/strategic_systems/intelligence.py:670 (active-objective redirect), :678 (town-return fallback)
- resolve_blocker project creation for blocker_congestion (writer to be named in the counts step)

## Assumptions / Open Questions
- Is town_center the only target a congestion resolution can pick, or one case among several? Answered by count 3.
- Does the blocker form from the churn (the hypothesis) or from real door crowding? Answered by count 2.

## Implementation Notes
Filed by rpg-planner, 2026-11-01, on a designer ruling (P3, own ticket, counts-first). Not dispatched.

## Test Summary

## Files Changed

## Completion Summary

## 2026-11-01 second named case (rpg-designer, via rpg-planner)
- frontier s45 churn-on-F3 e22: resolve_blocker_blocker_congestion toward [25,25] walked [49,40]->[34,33] into a hostile cluster around [25,25-30]; killed t891. It is the same redirect as subject 17. Source: ubuntu groups batch C rows (via the churn ticket's evidence folder on origin rpg-ubuntu-group-id-alloc-impl).
