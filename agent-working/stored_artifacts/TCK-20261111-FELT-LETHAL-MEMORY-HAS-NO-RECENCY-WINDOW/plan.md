---
status: historical
layer: combat
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW
phase: done
date: 2026-11-12
tags: []
---

# Plan

Investigation first; no fix in this phase.

1. Read-only code read (investigation.md).
2. First trace: `free_swing_trace_win.py` sha 61a181a5, unchanged, args only, on main frontier_marches s42, subjects e31 and e49 over about t1950-2000, and e31 over about t2395-2407. Its end hash must equal the plain cell 908eb3bb1441, else STOP.
3. Send rpg-planner the code read and the trace rows, with no classing.
4. rpg-designer rules on the shape: expire after N ticks, expire on hostile inactivity, the stalemate break, or no change.
5. Any fix is a separate ticket that re-measures both 2.202 and 2.204.

No src edits until the ruling.
