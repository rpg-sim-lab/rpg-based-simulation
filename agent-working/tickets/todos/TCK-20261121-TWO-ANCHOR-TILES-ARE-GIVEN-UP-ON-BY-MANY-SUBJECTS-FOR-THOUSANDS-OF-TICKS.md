---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261121-TWO-ANCHOR-TILES-ARE-GIVEN-UP-ON-BY-MANY-SUBJECTS-FOR-THOUSANDS-OF-TICKS
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-TWO-ANCHOR-TILES-ARE-GIVEN-UP-ON-BY-MANY-SUBJECTS-FOR-THOUSANDS-OF-TICKS

## Title
Two tiles, [40, 82] in frontier_living_world and [40, 31] in urban_political, are given up on again and again by many subjects for 4000+ ticks: check whether world content makes them unreachable

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
This is report-only finding D6 of the F2 v2.2 design (rpg-designer, main-checkout `.claude/handover/drafts/rpg-designer-f2-giveup-memory.md`, section "## v2.2", paragraph "D6 CONTENT FINDING"; draft sha256 e621ebeb at filing). The finding comes from the F1+F2 attempt-2 run (`/mnt/data2/rpg-measure/f2/cells_f1f2_b`, FAIL on record) and the v9.5 trace (`/mnt/data2/rpg-measure/f2/cells_trace_b`, #715 S9 7060424598, VALID 7060853408). Both runs are on tree 562067080 (rpg-stalemate-nav), seed 42, 5000 ticks.
- frontier_living_world: the way-round give-ups gather at anchor [40, 82]. Its G3 rows (subject, anchor) carry 27, 22 and 11 give-ups, and the anchor shows up in every flw UNCLASSED reset run. The T4 rows at those reset ticks are same-tile re-sets of [40, 82].
- urban_political: the same pattern at anchor [40, 31].
- Both anchors repeat across subjects for 4000+ ticks.
F2 v2.2 stops a subject from re-choosing a tile it just gave up on. It does not explain why so many subjects pick these two tiles in the first place, or why they can't reach them. This ticket asks that question of world content, not of movement code.

## Scope
1. Read, without running anything new first, what lies at and around [40, 82] (frontier_living_world) and [40, 31] (urban_political) in the world specs and the assembled maps at 562067080. Look at the terrain or building footprint, the passability of the four neighbours, and any wall, door, water or region edge.
2. Name what draws subjects there: the objective, lead, building or town-centre target that resolves to that tile. Use the trace's T1 site chains in `cells_trace_b` (report-only; the rows are capped at 4000).
3. Decide whether the tile is (a) unreachable by content (a fix in the world spec or assembly), (b) reachable but only by a path longer than the local way-round ladder can find (a movement limit, disclosed in divergence 2.213 item (3)), or (c) something else. Report it with file:line evidence.

## Out of Scope
- Any change to the F1/F2 movement or give-up code. That is the F2 ticket's job, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON.
- Changing a bar, a threshold or a measured result of the F2 runs.
- A pathfinding redesign. If (b) holds, file it as its own ticket.

## Acceptance Criteria
1. Each anchor has a recorded verdict, (a), (b) or (c), with the evidence that supports it (inspected or executed, labelled).
2. If (a): a world-content fix ticket exists, or the fix lands here with a test that the tile is reachable from its region.
3. If (b): the 2.213 disclosure cites this ticket.
4. rpg-designer has read the verdict before the next F2 full run is read.

## Related Tickets
- TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON (F2; v2.2 D6 is the source of this ticket)
- TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER

## Related Docs
- `docs/guidelines/intentional_divergences.md` 2.213 (the way-round ladder, item (3): local and memoryless)
- `docs/mechanics/06_worldbuilding_foundation.md` (declarative topology, integrity validation)

## Related Stored Artifacts
None yet. The evidence is in `/mnt/data2/rpg-measure/f2/cells_f1f2_b` and `/mnt/data2/rpg-measure/f2/cells_trace_b` (kept as v2.2's evidence base).

## Related Code Areas
- World specs and assembly for frontier_living_world and urban_political (`src/worldassembly/`, world content data)
- `src/engine/tactical_destinations.py`, `src/systems/strategic_systems/intelligence.py` (where targets resolve)

## Assumptions / Open Questions
- That both anchors are the same kind of problem is an assumption. Each gets its own verdict.

## Durable state, lifecycle and clocks
None expected. This is a read-first content check.

## Implementation Notes
- CARRIED G3 ITEM from F2 (owner ruling, #715 ask 7078451773, answer 7078467940: "Land, carry to D6"): F2 (TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON) lands with its G3 bar (a subject-anchor given up on 5 or more times since its last DESTINATION_GIVEN_UP) not 0 in the post-fix full run (crowded / flw / up = 1 / 6 / 12). The scoped, EXPIRING item names these (subject, anchor) tiles: up (25,25), (40,31), (38,30), (35,27); flw (40,82), (87,50); crowded (110,37). It expires when this ticket's fix lands; G3 is re-judged then and stays a HARD bar after. Evidence: F2's evidence_v22b/g3_up_read.out (the up rows, approximate reconstruction: of the new run's 12 rows, 24 give-ups fall inside the reconstructed suppression window and 37 at or after expiry; the old run's 4 rows 10 and 12).

## Test Summary

## Files Changed

## Completion Summary
