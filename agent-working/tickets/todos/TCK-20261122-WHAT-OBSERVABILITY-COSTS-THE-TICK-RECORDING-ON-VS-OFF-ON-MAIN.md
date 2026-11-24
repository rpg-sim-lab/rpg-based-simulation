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

## Finding 2026-11-22: replay was ON in the first kit, so the first OFF arm and the gate-harness ON figure both include replay work
- Run 1 (kit v1, tree 613a8365b, `obs_out_613a8365bcd1_s42`): preflight passed; the series was started, then stopped at HOLD after arm 1_OFF (rc 0, 1058 s) so O3 stage 2 could have the slot. Arm 1_OFF read 210 ms per tick against 45-75 ms for the O3 kit's recording-OFF runs. It is one arm and is not used as a result.
- Cause (read-only comparison of the two kits): both use `tools.test_architecture.rpg_gate_run.build_kernel` (PROD_SMALL, PinnedNormalGovernor, LocalSequentialExecutor, audit_mode, no frame pacing) and time `tick_once`. The difference: `person_attack_spy.py` (`inject_no_replay_if_recording_off`, line 438) wraps `Kernel.__init__` to force `flags["no_replay"]=True` under `SIM_OBS_MODE=OFF`, because the observability variables alone leave replay on. Kit v1 did not. Proof: the 1_OFF run dir holds 50 replay `chunk_N.json` files (333 MB) and a manifest.
- Consequence: `build_kernel` in the births gate harness also leaves replay on, so the 144-193 ms "recording ON" figure in D4 mixes replay work with observability work. The gap in D4 is not a recording cost until replay is held fixed.
- Kit change (v2): `obs_cost_arm.py` injects `no_replay=True` in every mode by the same wrapper (`OBS_COST_NO_REPLAY=1` default), refuses to run if `kernel._no_replay` or `_audit_mode` differs from the spec, and records `no_replay`. `launch.sh` passes `NO_REPLAY` (default 1; 0 keeps replay on). v2 sha256: `obs_cost_arm.py` 138ff16ab05e75c9ba64bc0044e049525eb7b3a9c72d7e9adce43b8aa82dc4a7, `launch.sh` 2ab8e68eaa65be0a3df451004b72fb87068b9b36858814de6836d686e80fcd22 (v1 files kept as `*.v1`). Not yet run.

## Corrected plan
1. Preflight v2 (10 ticks, OFF and LIGHT) on the same frozen tree, after O3 stage 2 seals.
2. ABBA series with `no_replay` on in both arms (isolates observability; same as the O3 kit), fresh OUT directory, own GO.
3. Separate later GO: a 2x2 pass with replay ON (`NO_REPLAY=0`) to price replay on its own; each arm is about 1000+ s.
4. Step 1b (py-spy callee split of the ON cost), seed 43 and NORMAL arms stay held until step 1 shows a gap.
The D4 entry should say the 144-193 ms figure includes replay.

## Findings 2026-11-22 (loaded host, pinned cpus 4-5, steal/swap recorded; main 613a8365b; `frontier_living_world`, seed 42, 5000 ticks, ABBA; one world, one seed)
Run files under `/data/vboxuser/perf_runs/` (kept for the owner's delete list, 1.5 GB in all). Result files and sha256: `obs_series_v2_result.md` 8f266332ed29cfd299568f9973a8df75da66080a3e80e200fdbf1d188abe3814; `obs_replay_pair_result.md` d65f409c8c9a749d071da2a50fba37b3d95b6c31ffd90e09d771416545d3c482. Logged on #715 by lead-planner (replay result 7077235935).

| question | OFF arm | ON arm | cost |
|---|---|---|---|
| observability stack (SIM_OBS_MODE OFF vs LIGHT, replay off in both) | 44.0 ms/tick (arm spread 1.2 %) | 50.5 ms/tick (spread 15 %) | about 6.5 ms, about 15 % (6 to 22 % by statistic); 9.5 events per tick, 0 dropped; +25 MB RSS, 29 MB files |
| replay (no_replay vs replay on, observability OFF in both) | 39.5 ms/tick (spread 3.9 %) | 111.0 ms/tick (spread 0.4 %) | about 71.5 ms, 2.8x; 349 MB of chunk files per 5000 ticks; +85-97 MB RSS; second half 31 % above the first half |

- All eight final state hashes of the two series are equal (the two series use the same 5000 ticks, tree and seed): neither the observability mode nor replay changes the simulation.
- Replay costs about 11 times what the observability stack costs. D4's 144-193 ms "recording ON" figure (births gate harness) is mostly replay, which `build_kernel` leaves on; it was never an event-recording cost alone. Whether the replay write path is worth moving out of the tick (the direction D4 describes for recording) is for the owner to decide; no ADR is warranted for observability alone at about 6.5 ms.
- Not done and still held: the py-spy callee split of the observability stack (step 1b), seed 43, NORMAL mode. The LIGHT arms disagree by 15 %, so the observability figure is the less certain of the two.
- OPEN: the first (v1) kit's 1_OFF arm had replay on and observability OFF, the same configuration as the replay-on arms, yet read 210 ms per tick (1058 s) against 111 ms here. It was one arm on a host with light desktop load; the cause is not known and the arm is not used. It is a reminder that a single arm on this host can read 1.9x high. Not investigated further.

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
Run records and GO are on #715 (lead-planner). Run 1 (kit v1) was stopped at HOLD after arm 1_OFF and is not a result; see the finding above. HOLD file stays in place until lead says O3 stage 2 has sealed.

## Test Summary

## Files Changed

## Completion Summary
