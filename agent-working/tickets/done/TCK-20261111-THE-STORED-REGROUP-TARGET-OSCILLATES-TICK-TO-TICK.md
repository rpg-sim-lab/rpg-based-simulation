---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK
phase: done
date: 2026-11-11
tags: []
---

# TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK

## Title
The REGROUP target that fused_strategic_pass stores (~:678) flips between neighbouring tiles tick to tick, walking the subject into contact and out of it

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
rpg-designer found this while checking the Scope 1 trace of TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING (lane B, free_swing_trace.py at sha256 7c22df89…, 5 hash-matched runs). rpg-planner filed it on 2026-11-11.

In the traced windows, the stored REGROUP navigation target written at intelligence.py ~:678 alternates:
- crowded s42 #3: 39↔38 on one axis;
- crowded s43 #12: 35↔34;
- def2 crowded s45 #5: around (25,25).

The movement phase walks each new target, so the subject steps toward the fight and back away from it, and each step off engagement pays the opportunity attack.

Raw data: /mnt/data2/scratch-b/fst_out/{flight_c42,flight_c43,def2_c45}.json; the readout is in the non-flight ticket's staging_artifacts/trace_readout.txt.

## Scope
1. Investigation first, read-only: what recomputes the REGROUP point each tick? Candidates: the nearest town tile from a moving position (`nearest_town_tile`), the slow/fast path alternating, or a group centroid. Name the writer and its inputs per tick, on main.
2. Then a fix proposal to rpg-designer. Whether a stored REGROUP point should be stable once chosen is a design question.

## Out of Scope
- The lethal free-swing step itself (TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING).
- Whether a stored target may step at all while engaged (TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE, widened).

## Acceptance Criteria
- The writer and its per-tick inputs are named, with a trace on main that hash-matches its cell.
- rpg-designer rules on the fix shape before any code.

## Related Tickets
- TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING
- TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
- TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE

## Related Docs
- docs/mechanics/04_strategic_cognition.md
- docs/mechanics/02_combat_laws.md §7

## Related Stored Artifacts
- None yet.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (~:670-:680 slow-path navigation writes)

## Assumptions / Open Questions
- intelligence.py is on the hands-off list for the COMBAT-RETREAT P2 and is the next-gen stage 3 slice. Any fix here is sequenced with both.

## Implementation Notes

## Test Summary
No code changed. Verification: the trace's end hash equals the plain cell (MATCH e0e20c2044d7).

## Files Changed
Tickets and stored artifacts only (plus the cherry-picked stored-target close, TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE, with its two doc notes). No src, tests, data or config.

## Completion Summary
Closed as MEASURED, NO CHANGE (hand-orchestrated, path-reason investigation_only). Owner approval to run: #715 6843004519. rpg-designer ruled (2026-11-13, session message): if the flip reproduces and pays no swing, no change; cosmetic churn on a town tile.

**Writer and inputs (main d1c9b3022).** `fused_strategic_pass` (src/systems/strategic_systems/intelligence.py: fast path :394-406, slow path :675-681) writes `target_set=nearest_town_tile(state.town_tiles, entity.navigation.position) or state.town_center` with `movement_mode_set=REGROUP` and `InteractionUpdate(reset=True)`, when `len(pending_inventory.items) > 0`, the position is not (0,0) and the stored target differs. `nearest_town_tile` (src/systems/strategic_systems/town_targeting.py:5-20) returns the subject's own tile when it stands on a town tile, so the stored point is where it stood a tick ago and the movement phase walks back to it.

**Trace on main.** free_swing_trace_win.py (61a181a5, args only), crowded_frontier s42, subject 3: end hash MATCH e0e20c2044d7, output /mnt/data2/rpg-measure/regroup/trace_c42_s3.json sha256 ab4c0c0ce2453bc545dc080699bea21670ee4b3f93e52f9b788da33f8618766c, peak RSS 213776 kB. The flip REPRODUCES: from t2048 to t2052 the target is rewritten every tick and the subject steps (30,27) <-> (31,27) (the cycle ended at t2052 with a failed step, reason LEGAL). The window is 8 ticks, so the full duration is not known. It pays no swing: no engaged or adjacent hostile on any tick, no opportunity-attack call, hp 22 to 23. The control window t2100-2107 is stationary.

**Ruling applied.** Reproduces, pays no swing in the traced window: NO CHANGE (cosmetic churn on a town tile). No fix, no spy, no src edit. Not established: whether another cell or window shows the flip beside a hostile; the designer's own spy-1 on main found every REGROUP step beside a hostile walks a FIXED town tile ((40,40) or (40,38); 29 swung at in frontier_marches, 17 in crowded_frontier), which is the stored-target gap the owner closed as no change (6842890741), not this flip.

**Findings, not tickets.** (a) The writer sends any item-carrier with no objective to town forever, because nothing discharges pending inventory on arrival (no arrival condition, the 2.113 arrival law is not applied): goes to the producer investigation. (b) def2 s45 #5 is a routing wobble with a fixed target (25,25): out of scope.

Known gap: knowledge-index-update not run: worktrees use main's index (lead-planner-u24, 2026-11-12).
