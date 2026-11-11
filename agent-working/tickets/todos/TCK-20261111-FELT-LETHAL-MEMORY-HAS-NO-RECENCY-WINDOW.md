---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW
phase: open
date: 2026-11-11
tags: []
---

# TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW

## Title
A single felt-lethal hit keeps an engaged subject pinned for 65-71 ticks while the hostile strikes nothing, because the felt-lethal memory has no recency window

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
rpg-designer found this on 2026-11-11 while ruling on the PIN STOP in the P2 S1 measurement of TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING. rpg-planner filed it the same day. It is investigation first; there is no fix now. It comes after the current batch.

The setup: fix 824483949, held_step_spy sha256 84e78113…125d. Raw data in /mnt/data2/rpg-measure/results/824483949cec-72320cac-5000/spy_crowded_frontier_{42,43}.json. These rows are provisional until the s42 plain twin hash-matches.

- **crowded s42, entity 3.** Held at t2740-2810, 71 consecutive ticks. Every row names last_attacker 30 with last_hit_damage 23. hp climbs 17→21 with no drop on any held tick, so 30 lands nothing during the hold. Regen ends the hold. Entity 3 survives the run.
- **crowded s43, entity 33.** Held at t1440, then t1449-1513: a run of 65, 66 ticks in all. Again attacker 30, damage 23, with hp flat at 23, so the test 23 ≥ 23 holds. There is no drop. Entity 33 dies at t2774 (COMBAT), 1261 ticks later.

`felt_swing.felt_lethal_attacker` stays true off one remembered hit (the last attacker and its damage), however long ago it landed and whether or not the hostile is still acting on the subject. The predicate is shared by the merged 2.202 flight guard and by the P2 S1 step guard, so both pin.

- **crowded s45, worker 5** (rpg-designer recount, 2026-11-11; this is the designer's def2 evidence subject s45 #5). In base it dies by DEFEAT. In fix it is held at t2117-2150 (34 ticks), then dies of STARVATION at t2161. That is 11 ticks after the hold, just outside the t−10 link window. It is not a stop and not a trip. It is the first sign that a pin may keep a hungry subject away from food. The other fix-arm starvation, s46 worker 4, was never held (COMBAT in base, so drift).

The s42 plain twin hash-matched (e0e20c2044d7), as did s43 (609683ccdf2b), so the rows above count. The designer ruled this a standoff: it ends by regen or a hit. It is an accepted cost of S1 and not a defect of that ticket. The open question is whether that memory should expire.

## Scope
1. A read-only code read on the then-current main. What feeds felt_lethal_attacker? The last attacker, the last-hit damage and the last-hit tick, with the write site and the clear site. Does anything clear it apart from a new hit? How does tactical_hold.stalemate_break_update interact with a held subject?
2. Measurement, only if the code read leaves it open. Pin counts and lengths, plus the share of pins where the hostile strikes during the hold, on a designer-approved, hash-matched spy. Include whether a held subject's hunger rises during the pin, and whether it reaches food after the pin (the s45 worker 5 case).
3. Then rpg-designer rules on the shape: expire the felt hit after N ticks without a new hit, expire it once the hostile stops acting on the subject, leave it to the stalemate break, or no change.
4. Any fix touches the shared predicate, so it re-opens and re-measures both the 2.202 flight guard and P2 S1.

## Out of Scope
- The P2 S1 step guard itself (its own ticket).
- Any change to 2.202 before the designer rules.

## Acceptance Criteria
- The predicate's inputs and their lifecycle are cited with file:line on main.
- The designer's ruling is recorded. If it calls for a fix, that is a separate ticket with a paired measurement of both guards.

## Related Tickets
- TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
- the flight-guard ticket (divergence 2.202)

## Related Docs
- docs/mechanics/02_combat_laws.md §7
- docs/guidelines/intentional_divergences.md (2.202, 2.204)

## Related Stored Artifacts
- None yet.

## Related Code Areas
- src/engine/felt_swing.py (felt_lethal_attacker)
- src/engine/tactical_flight_guard.py
- src/engine/tactical_hold.py (stalemate_break_update)
- src/systems/movement.py (resolve_move free-swing site)

## Assumptions / Open Questions
- The rows are from the spied fix cells. The s42 and s43 plain twins hash-matched on 2026-11-11, so the rows count.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
