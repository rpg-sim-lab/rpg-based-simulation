---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS
date: 2026-11-18
tags: [performance]
---

# Plan

Measurement only. R1 per-phase ms (3 gate worlds x 3 runs, unprofiled), R2 py-spy per world, R3 synthetic scenarios, R4 1000-tick runs with peak RSS. Cores 2-3, MemoryMax=1G, serial, gated on births load and MemAvailable. Output: `docs/performance/tick_cost_growth.md` section 10. No `src/` change.
