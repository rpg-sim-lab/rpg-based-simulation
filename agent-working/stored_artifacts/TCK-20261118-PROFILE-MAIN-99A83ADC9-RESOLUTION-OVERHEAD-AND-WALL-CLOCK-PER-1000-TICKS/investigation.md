---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261118-PROFILE-MAIN-99A83ADC9-RESOLUTION-OVERHEAD-AND-WALL-CLOCK-PER-1000-TICKS
date: 2026-11-18
tags: [performance]
---

# Investigation

TCK-20261015 and section 9 had already attributed `resolution_overhead` to `fused_strategic_pass`; the work was the finer split, the H1-H3 re-check and wall-clock by entity count. Findings and limits: `tick_cost_growth.md` section 10. Raw run files: `/data/vboxuser/perf_runs/r1` to `r4` (outside the repo).
