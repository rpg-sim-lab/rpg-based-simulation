---
status: historical
layer: observability
authority: P2
audience: agent
artifact_type: report
ticket_id: TCK-20261124-A-WALL-CLOCK-TIMER-IN-THE-REPLAY-STREAM-MAKES-REPLAY-FILES-NON-REPRODUCIBLE
date: 2026-11-24
tags: []
---

# PR notes: replay chunks carry no wall-clock value

## What and why
Every replayed `REFINED_UPDATE` carried `payload.update.sub_phase_costs.*` (about 23 per-phase durations) and `metric_counters.cooperation_phase_ms` (and `world_emergence_ms` when that flag is on), so two runs of one world and seed wrote different `chunk_*.json` bytes. The kernel now emits `refined_update.replay_form()` (kernel.py:656): `sub_phase_costs` empty, the keys in `WALL_CLOCK_METRIC_KEYS` (src/core/updates.py) absent from `metric_counters`, counts kept. The kernel's own update still feeds `_phase_costs`, `_metrics` (the perf baselines) and the governor, so none of those change. The final hash, every `TICK_END` hash and `is_noop` are unchanged. Approach approved by rpg-planner-ubuntu (option A); the note is approach_note.md beside this file.

## Evidence
- 16 new tests in tests/unit/engine/test_replay_chunks_are_reproducible.py, written first: 13 FAILED on main (byte inequality with and without ENABLE_WORLD_EMERGENCE, float timer leaves, the missing `replay_form` and `WALL_CLOCK_METRIC_KEYS`); the 3 that pass on main pin what must not change (the flag really ran the phase, counts stay, the kernel keeps its timers). All 16 pass now.
- Hash pin: the same seed run with and without `replay_form` (monkeypatched to return self, the old emit) gives equal TICK_END hashes and an equal final canonical digest; this compares the two arms of one run only, not AC2's or perf's hashes.
- Pre-push set on this head: tests/unit/engine 1329 passed 3 skipped; unit/core+kernel+replay 567; tests/perf/test_phase7_social_cooperation_budget.py 1; integration authoritative_outcome_truth + fused_loop 12; tests/architecture 260; tests/static 176; tests/tools in 25-file chunks (a single 3G run hits MemoryError, as before): all pass except 4 in test_knowledge_search.py TestLiveQueryDocsMechanics, which time out building the live docs index (360 s) on this host. code-health OK (the 2 new and 2 worse rows are report-only jscpd in src/observability, not touched here); import contracts 17 kept 0 broken; docs-registry in sync.
- tools/rpg_measure/replay_digest_* (the sealed AC2 kit) is unchanged and its tests pass.

## Known gaps
- The strip is by a named key set: a new timer written into `metric_counters` leaks until it is added; the float-leaf test fails on it.
- manifest.json `start_time`/`end_time`, the run manifest `started_at`/`ended_at` and the run id differ between runs: run metadata, ruled out of scope by the planner.
- The wall-clock search is static for three sources plus a 12-tick probe on one world.
- AC5 finished before this PR (lead-planner).
