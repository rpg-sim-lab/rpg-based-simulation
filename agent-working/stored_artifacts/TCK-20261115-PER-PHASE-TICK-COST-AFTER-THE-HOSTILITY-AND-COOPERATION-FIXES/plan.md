---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-PER-PHASE-TICK-COST-AFTER-THE-HOSTILITY-AND-COOPERATION-FIXES
phase: open
artifact_type: plan
date: 2026-11-16
tags: [performance]
---

# Plan: stage 0 per-phase re-measure

Spec as accepted by lead-planner (2026-11-15) and run on the go of 2026-11-16: 3 gate worlds, seed 42, PROD_SMALL, `profile_tick.py --contract pinned`, warmup 20, 200 measured ticks; per world 3 `--sampler none` runs and 1 `--sampler py-spy` run at 250 Hz; quiet gate before each; 3G cap on CPUs 4-5; origin/main detached at a recorded sha. Frontier re-run (3 more timed runs, swap counters before and after) on lead's second go. Results into `docs/performance/tick_cost_growth.md` §9. Existing tools only; no `src/` edit.
