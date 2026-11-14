---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK
phase: done
date: 2026-11-13
tags: []
---

# Investigation: what recomputes the stored REGROUP point each tick? (read-only, main d1c9b3022)

Owner approval: #715 6843004519. No src edits until rpg-designer rules whether a stored REGROUP point should be stable once chosen.

## The writer and its inputs

The REGROUP target is written in two places in `StrategicIntelligenceSystem.fused_strategic_pass` (src/systems/strategic_systems/intelligence.py), both with `movement_mode_set=REGROUP` and an `InteractionUpdate(reset=True)`:
- the fast path, intelligence.py:394-406 (`not nav_changed and not proj_resolved`, no cadence tick for concerns or intents);
- the slow path, intelligence.py:675-681, used when no earlier writer in the pass set a navigation update (`not has_nav_update`).

Both compute, every pass the entity is a candidate:
- `town_target = nearest_town_tile(state.town_tiles, entity.navigation.position) or state.town_center`
  (src/systems/strategic_systems/town_targeting.py:5-20: the town tile with the smallest squared distance to the entity's CURRENT position, ties by lowest (x, y); state.town_tiles is built in src/worldbuilding/compiler.py:500, 899);
- they write it only when `len(pending_inventory.items) > 0`, `entity.navigation.position != (0.0, 0.0)`, and `entity.navigation.target != town_target`. The fast path additionally requires no ACTIVE project objective that carries a target position or target entity.

So the stored point is a function of the entity's current position, recomputed on every pass.

## Why it flips (from the traced rows, not yet re-traced on main)

`nearest_town_tile` returns the entity's OWN tile whenever that tile is a town tile (squared distance 0). The pass runs at the start of tick u and writes `target = position at the start of u`. The movement phase reads the target stored at the START of u, which is the tile the entity stood on at the start of u-1 (written on tick u-1), and walks there. So the entity steps back to where it was a tick ago, and the next pass writes its new position again:

- crowded s42 subject 3, t2049-2050 (/mnt/data2/scratch-b/fst_out/flight_c42.json): u2049 position (38,30) -> (39,30), stored target at start (39,30), the pass wrote (38,30); u2050 position (39,30) -> (38,30), stored target (38,30), the pass wrote (39,30). The writes are `target_set` at tick 2049 and 2050 from the REGROUP town write (intelligence.py:678 on the traced tree).
- crowded s43 subject 12, t3052-3053 (flight_c43.json): positions (34,40) <-> (35,40), the same pattern; the pass writes the position the entity starts the tick on.

The two-tile cycle persists as long as the entity stands on a town tile and holds pending inventory. In those rows the REGROUP moves are made without a decision, so each step off an engagement pays the opportunity attack.

## The third row is a different cause

def2 crowded s45 subject 5, t1297-1300 (def2_c45.json): the stored target stays at (25,25) the whole window (written at tick 1295, never rewritten); the position goes (26,24) -> (26,25) -> (26,26) -> (26,25) -> (26,26). The target is stable; the step oscillates, which is the movement system's route around an obstacle or an occupied tile, not a target recompute. It is not this ticket's writer.

## Trace on main (2026-11-13): the flip REPRODUCES at the window, pays no swing

free_swing_trace_win.py (sha256 61a181a5a430ac61aac25f5a1207be974c6b383bd3ae42682a1f640e5a50794e, args only) on main d1c9b3022 (src/data/config differ from the plain cell's tree cd83111c5 only in src/api/{admission_control,server,tracing}.py and src/logging/formatter.py, none on the run path), crowded_frontier s42, 5000 ticks, subject 3 over t2045-2052 and a control window t2100-2107. End hash MATCH e0e20c2044d7 vs the plain cell. Output /mnt/data2/rpg-measure/regroup/trace_c42_s3.json, sha256 ab4c0c0ce2453bc545dc080699bea21670ee4b3f93e52f9b788da33f8618766c; run under MemoryMax=1G, peak RSS 213776 kB, rc 0. Rows are summarised in `measurement.md`.

## Findings recorded (not tickets)

(a) The writer sends any item-carrier with no objective to town forever, because nothing discharges pending inventory on arrival: the REGROUP write has no arrival condition (the 2.113 arrival law is not applied to it). Goes to the producer investigation.
(b) def2 s45 #5 is a routing wobble with a fixed target, so it is out of scope of this ticket.
