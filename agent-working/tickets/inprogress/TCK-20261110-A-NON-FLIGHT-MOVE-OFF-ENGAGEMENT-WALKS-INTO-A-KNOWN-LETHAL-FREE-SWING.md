---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
phase: in_progress
date: 2026-11-10
tags: []
---

# TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING

## Title
A subject with no flight decision moves off engagement and walks into a free swing it has felt will finish it (the CONFLICT-04 "neither" shape)

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Requested by rpg-designer on 2026-11-09/10, in its def2 and flight Tier 2 rulings.

The flight guard (TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE, divergence 2.202) weighs the felt free swing only at the 6 flight sites. Some subjects have no decision on the death tick and an ENTITY_ACT task at tick start, yet they still leave engagement and take a lethal movement opportunity attack (DEFEAT). The guard never reaches them. This is the old "moved with no move task" class, and rpg-designer reads it as the CONFLICT-04 "neither" defect still standing.

Evidence (pinned traces; each hash-matches its cell):
- Flight Tier 2, fix arm on 83004a122. Each row: opp=True call on the death tick, no decision that tick, ENTITY_ACT task, call lethal flag false.
  - crowded s42 #14: t323, hp 6, swing 11, attacker 34, DEFEAT.
  - crowded s42 #3: t2050, hp 26, swing 40, attackers 30 and 38, DEFEAT.
  - crowded s42 #12: t4971, hp 2, swing 21, attacker 30, DEFEAT.
  - crowded s43 #37: t1632, hp 11, swing 12, attacker 30, DEFEAT.
  - crowded s43 #12: t3053, hp 13, swing 21, attacker 30, DEFEAT.
  - urban s46: no rows.
- Hardening def2, fix arm 3300928e88c4: crowded s43 #1 and #8, crowded s45 #5, all with no decision on t, an ENTITY_ACT task, and the OA.
- Hit-wake trace, urban s46 (B e755dc3d1 vs W aa209f2d6; defeat_{B,W}_5000.json in /mnt/data2/scratch-c3/): subject e24's fatal move off engagement was an engage BRACKETING step into the free swing, not a flight. So the same shape also arises from an engage move, not only from a no-decision ENTITY_ACT.
- Attacker 30 lands most of these blows. Across def2, killer 30 landed 8 of 10 fatal swings.
- Rows are in /mnt/data2/rpg-measure/flight/rows/*.json and /mnt/data2/scratch-c3/def2/rows.txt. They are copied into this ticket's evidence at scoping.

## Scope
1. Investigate first: which code path moves an ENTITY_ACT subject with no decision on the tick (a carried move task, a nav continuation, or a group or bracketing move), and why the movement OA fires on it. Name the writer.
2. Then rpg-designer rules on the fix: extend the felt-swing weighing to that path, or stop the move, without stacking more tactical goal scoring.
3. Tests: a kernel row reproducing one evidence case; a unit row for the named path.
4. A paired measurement on the pinned runner, after the current heads. rpg-designer sets the bar.

## Out of Scope
- The 6 flight sites already guarded (2.202).
- Swaps off engagement being free (rpg-designer's parked tension; urban swaps 23→53 under the guard).
- Hazard-cluster bracketing (TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER), related but a different harm.

## Acceptance Criteria
- The moving writer is named, with a trace row.
- Tests in Scope 3 pass, and the measurement passes rpg-designer's bar or goes to the owner.
- Bible 02 §7 / CONFLICT-04 text, the parity ledger and a divergence entry (u24 block) are updated.
- Hot-loop: maybe. Timing is NOT MEASURED under the perf pause (#715 6556861718).

## Related Tickets
- TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE
- TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT (def2 evidence)
- TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER (related)

## Related Docs
- docs/mechanics/02_combat_laws.md §7; docs/guidelines/intentional_divergences.md 2.202

## Related Stored Artifacts
- Pending: the flight ticket's evidence (Tier 2 rows).

## Related Code Areas
- src/engine/movement.py (opportunity attack, :324)
- src/engine/tactical.py, src/engine/tactical_flight_guard.py

## Assumptions / Open Questions
- rpg-designer, 2026-11-10: the BRACKETING ticket TCK-20261020 is related only (a different harm). The hit-wake subject e24's bracketing step is an evidence row here.
- rpg-designer, 2026-11-10, priority: not dispatchable until its design is done. The response for a non-flight move (hold the move, swap the target?) is open. It drafts the design after the owner's scout ruling and the hit-wake re-measure, since hit-wake changes how often engaged hit subjects re-decide. Queue: after flight, hardening and hit-wake, ahead of the rejection-count fix (it's on the death path). The measurement is a separate run on its own base, under the same bar.
- rpg-planner, 2026-11-10, place: after next-gen child 2's cells and A+B. Both are already queued, and this ticket's design lands later anyway. It sits ahead of TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
