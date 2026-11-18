---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES
phase: open
artifact_type: investigation
date: 2026-11-16
tags: [performance]
---

# Investigation: stage 0 per-phase re-measure

- `fused_strategic_pass` (`pipeline.py:394`) runs inside `run_phase("strategic_intelligence", ...)` but has no sub-phase timer of its own, so its time is inside `resolution_overhead` (`kernel.py:441`: Resolution total minus recorded sub-phase costs). The share is therefore read from py-spy folded stacks (frames under `_phase_resolution` containing `fused_strategic_pass`), not from the kernel's costs; no wrapper was needed.
- `final_integrity` has its own timer on this tree (about 0.1 ms per tick), so the H5 timer fix is on main.
- Swap was checked as a cause of the frontier spread (lead-planner): ruled out for runs 4-6.
- Full figures, run list and gate readings: `evidence.md`.
