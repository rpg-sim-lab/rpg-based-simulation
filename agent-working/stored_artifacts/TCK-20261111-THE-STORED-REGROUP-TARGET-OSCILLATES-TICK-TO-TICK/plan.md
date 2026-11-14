---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261111-THE-STORED-REGROUP-TARGET-OSCILLATES-TICK-TO-TICK
phase: done
date: 2026-11-13
tags: []
---

# Plan

Investigation first, no fix (owner approval #715 6843004519).
1. Read-only code read on main (investigation.md): the writer, its per-tick inputs, the cause of the two-tile cycle.
2. Confirm on main with one trace if rpg-planner gives HOST FREE: free_swing_trace_win.py (sha 61a181a5, args only), crowded_frontier s42, subject 3, a window around t2047-2050, hash-matched to the plain cell (e0e20c2044d7). One run under a 1G cap and at least 1.5 GB MemAvailable.
3. Send the read to rpg-planner; rpg-designer rules whether a stored REGROUP point should be stable once chosen.
4. Any fix is a separate step after that ruling and sequenced with the stage-3 hands-off list for intelligence.py; no src edit before it.
5. The stored-target close (bc3532e7e on rpg-stored-target-close) is cherry-picked into this branch and rides this PR.
