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

# Measurement: does the stored REGROUP target flip tick to tick on main?

Trace: free_swing_trace_win.py sha256 61a181a5a430ac61aac25f5a1207be974c6b383bd3ae42682a1f640e5a50794e (args only, approved), main d1c9b3022, crowded_frontier s42, 5000 ticks, pinned runner (PYTHONHASHSEED=0), MemoryMax=1G (peak RSS 213776 kB). End hash MATCH e0e20c2044d7 vs the plain cell. Output /mnt/data2/rpg-measure/regroup/trace_c42_s3.json sha256 ab4c0c0ce2453bc545dc080699bea21670ee4b3f93e52f9b788da33f8618766c. Owner approval #715 6843004519; rpg-designer ruled the scope-2 rule (2026-11-13, session message).

## Rows: subject 3 (position, stored target, engagement, outcome per tick)

| tick | start pos -> end pos | stored target start -> end | writer at end | engaged / adjacent | resolve_move |
|---|---|---|---|---|---|
| 2045 | (29,27) -> (29,27) | (29,27) -> (29,27) | fused_strategic_pass:678 (written t2042) | none / none | none |
| 2046 | (29,27) -> (29,27) | same | same | none / none | none |
| 2047 | (29,27) -> (30,27) | (29,27) -> (40,31) | updates.py merge (a decision, WANDER) | none / none | WANDER to (30,27) |
| 2048 | (30,27) -> (31,27) | (40,31) -> (30,27) | fused_strategic_pass:678 | none / none | WANDER to (31,27) |
| 2049 | (31,27) -> (30,27) | (30,27) -> (31,27) | fused_strategic_pass:678 | none / none | REGROUP to (30,27) |
| 2050 | (30,27) -> (31,27) | (31,27) -> (30,27) | fused_strategic_pass:678 | none / none | REGROUP to (31,27) |
| 2051 | (31,27) -> (30,27) | (30,27) -> (31,27) | fused_strategic_pass:678 | none / none | REGROUP to (30,27) |
| 2052 | (30,27) -> (30,27) | (31,27) -> (30,27) | fused_strategic_pass:678 | none / none | REGROUP to (31,27) fails, reason LEGAL |

Control window t2100-2107: subject 3 stands at (34,27) with a stored target (34,27) written at t2098; no writes and no steps until a decision at t2107 sets (40,31).

## Reading (raw, as the designer asked)

- The flip REPRODUCES on main in this window: from t2048 to t2052 the stored target is rewritten every tick to the position the subject stood on at the start of the tick (the fast/slow REGROUP town write, intelligence.py:678 on this tree), and the subject steps between (30,27) and (31,27). Five consecutive ticks are in the trace (t2048-2052); the cycle stopped at t2052 with a failed step (LEGAL). The window is eight ticks, so the full duration is not known from this trace.
- No flip step is beside a hostile or pays a swing in this window: engaged and adjacent lists are empty on every tick, no opportunity-attack call, and hp does not fall (22, then 23).
- The cause named in `investigation.md` holds: the written point is the nearest town tile to the subject's own position, which is the subject's own tile.

## Designer's measurement of spy-1 on main (relayed, not re-run here)

Every REGROUP step beside a hostile walks a FIXED town tile, (40,40) or (40,38). In frontier_marches 29 of those were hit by a swing, in crowded_frontier 17. That is the stored-target gap the owner closed as (b) (TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE), not this flip.
