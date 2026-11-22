---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261122-WHAT-OBSERVABILITY-COSTS-THE-TICK-RECORDING-ON-VS-OFF-ON-MAIN
phase: open
date: 2026-11-22
tags: [performance]
---

# TCK-20261122-WHAT-OBSERVABILITY-COSTS-THE-TICK-RECORDING-ON-VS-OFF-ON-MAIN

## Title
Measure what the observability stack costs the tick: same code, `SIM_OBS_MODE` OFF against the default, `frontier_living_world`, 5000 ticks, on main

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Step 1 of deferred item D4 (`agent-working/lead/deferred_backlog.md` in the main checkout; owner direction #715 7074152618, relaunch #715 7075402333). `EventRecorder.record()` (`src/observability/event_recorder.py:180`) runs on the tick thread, and its drain worker is a thread in the same process (`src/observability/queue.py:87`), so it shares the GIL. Observed: 45-75 ms per tick with recording OFF (the O3 trace, older code) against 144-193 ms with recording ON (the births gate harness, births code). Code and recording are confounded, so nothing is split yet. This ticket measures the share on one frozen tree. An ADR comes only if the share is worth fixing; any `src/` change waits for the gate motive/ledger change to merge and for an owner-opened core window.

## What the arms are (found while planning)
`SIM_OBS_MODE=OFF` is not "event recording off". At `kernel.py:145-298` it also removes the SimQ hub, the run artifact repository and manifest, the metric, cognition, decision-trace and personality recorders, and `_phase_observability` (`kernel.py:946`: extract_events, the hard-law check, the shadow shapers). So OFF against the default mode (LIGHT) prices the **whole observability stack**. Isolating `record()` plus the drain thread needs the callee split of step 1b.

## Scope
- Step 1: ABBA series (OFF, LIGHT, LIGHT, OFF), `frontier_living_world`, seed 42, 5000 ticks after 20 warmup, audit_mode, `PinnedNormalGovernor`, `LocalSequentialExecutor`, one process at a time, `PYTHONHASHSEED=0`, `PYTHONDONTWRITEBYTECODE=1`, cpus 4-5, `MemoryMax=3G`, `MemorySwapMax=0`. The only difference between arms is `SIM_OBS_MODE` (`RPG_OBS_MODE` cleared). Tree: `git archive` of the main sha named in the run record, verified against `git ls-tree -r`.
- Per arm: mean, median, p95, p99 tick ms, first and second half means, loop wall, shutdown wall, peak RSS, run-dir bytes, steal and swap, the start and final `CanonicalStateHasher` hashes, and the recorder's counters (events recorded, dropped by backpressure mode, final mode).
- Step 1b (own go): py-spy 1000 ticks at LIGHT with threads, to split the ON cost into `record()`, `extract_events`, the drain thread under the GIL, and the other recorders.
- A 10-tick preflight of each arm first, on the frozen tree.
- Held until step 1 shows a gap: seed 43, NORMAL mode arms.

## Out of Scope
Any `src/` edit; any change in `src/observability`; `uv sync` or any `uv.lock` change (uv freeze); the ADR (lead-owned, only if the share is worth fixing); any quiet-host claim.

## Acceptance Criteria
- [ ] The frozen tree equals `git ls-tree -r` of the named sha (paths and blob hashes), and the launcher refuses a missing or unverified tree.
- [ ] Preflight of both arms passes (rc 0, the recorded fields present, no constant-default fields).
- [ ] The ABBA series completes, or stops with a stated reason.
- [ ] The report gives the ON/OFF ratio with the ABBA arm-to-arm spread, labelled "loaded host, pinned cpus 4-5, steal/swap recorded"; if the final hashes differ between OFF and ON, that is reported as a finding.
- [ ] The result is written into `docs/performance/tick_cost_growth.md` and the D4 entry gets the figure.

## Related Tickets
- TCK-20261122-THE-GATE-ATTACK-AND-UNEATEN-KILL-ROWS-SPLIT-VICTIMS-INTO-PEOPLE-AND-NON-PEOPLE (touches the same `src/observability` files; no src change from here until it merges)

## Related Docs
- docs/architecture/observability_hot_path_safety_contract.md
- docs/performance/tick_cost_growth.md (sections 10.x)

## Related Stored Artifacts
Kit: `/data/vboxuser/perf_runs/obs_kit/` (`obs_cost_arm.py`, `launch.sh`), outside the repo; the run record carries their sha256.

## Related Code Areas
- src/observability/event_recorder.py, src/observability/queue.py, src/engine/kernel.py (read-only)

## Assumptions / Open Questions
- The births gate harness runs with the default mode (LIGHT); no `OBS_MODE` appears in `tools/test_architecture` or `tools/rpg_measure`. To confirm in the preflight by reading `obs_mode` from each arm's json.
- The O3 trace holds the slot first; the series yields (HOLD file) when lead says so.

## Durable state, lifecycle and clocks
N/A: measurement only; no durable engine state.

## Implementation Notes
Run records and GO are on #715 (lead-planner). Nothing has run yet.

## Test Summary

## Files Changed

## Completion Summary
