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

# Approach note (stage 1, no src change): keep wall-clock values out of the replay chunk bytes

Base: origin/main 2adee5a6c. Everything below was read on that tree. Only a draft test was written.

## Pick: option A, strip at the kernel's replay emit, not at the sink
`Kernel._phase_resolution` emits `REFINED_UPDATE` with the whole `refined_update` as `payload["update"]` (kernel.py:648-659). The kernel's own `refined_update` stays untouched: it still feeds `_phase_costs` (kernel.py:637-638), `_metrics` (:640), `_current_update` (:661) and `resolution_overhead` (:443). Only the object handed to `self._replay.emit` becomes a replay form of the update, with the timers removed. Why A and not B:
- perf-planner's constraint: `kernel._metrics`, `_phase_costs`, the governor input and `cooperation_evaluations` must not change, because tests/perf/baselines/*.v0001.json record `cooperation_phase_ms` from `kernel._metrics` (tools/perf/profile_sweep.py:304,372; _profiling_common.py:536). A leaves them byte for byte as they are. B would change `_metrics` and force perf to re-record.
- B moves 3 writers and the merge rule (`updates.py:467-581`) for no reader that exists.
- Strip at the kernel emit, not in `ReplaySink._clean_for_json`: the sink is generic over any dataclass and must not know field names.
Shape: one pure method on `StateUpdate`, `replay_form()`, returning `dataclasses.replace(self, sub_phase_costs={}, metric_counters={k: v for k, v in self.metric_counters.items() if not k.endswith("_ms")})`, and the emit passes `refined_update.replay_form()`. Fields removed from the chunk bytes: `payload.update.sub_phase_costs.*` (the ticket counts 23 phase keys) and the `*_ms` keys of `payload.update.metric_counters`: `cooperation_phase_ms`, `world_emergence_ms`. Counts stay: `cooperation_evaluations`, `aggregates_generated`, `quest_opportunities_rejected`, `phase_runs`, `run_*`/`skip_*`, `raw_entity_updates`, `compacted_entity_updates`, `movement_candidates`, `strategic_candidates`. Chunk files keep the keys `sub_phase_costs` and `metric_counters` (empty / counts only), so the schema shape does not change.
A rule on the key suffix `_ms` is brittle: a future timer without the suffix would leak. The guard is a test that no float leaf exists under `payload.update.metric_counters`, run with the world-emergence flag on.

## 1. The exact write site and the fields removed
- Write site: `ReplaySink.persist_chunk` (src/engine/replay_sink.py:61-84; `json.dumps(self._clean_for_json(e))` at :73-75, file at `chunk_NNNN.json`), reached from `ReplayManager._execute_persistence` (replay_manager.py:235-241). The data enters at kernel.py:648-659 (`REFINED_UPDATE`) and :1124 (`TICK_END`, payload is hash / scheme / digest_status only, no timer).
- Changed site: kernel.py:656, `"update": refined_update` becomes `"update": refined_update.replay_form()`.
- Chunk event fields: `tick, system, event_type, payload, causal_id`; `REFINED_UPDATE` payload: `tick, world_time, seed, update, fingerprint`. A probe of two same-seed runs (12 ticks, frontier_living_world, 573 595 bytes) found them equal after masking `sub_phase_costs` and the `*_ms` counters, and no run id anywhere in a chunk, so no run-id mask is needed.

## The wall-clock search (src/, excluding src/observability which never builds a StateUpdate)
Search: `perf_counter|time\.time\(|monotonic|process_time|datetime\.(now|utcnow)` over src/ gives 138 lines outside src/observability. Classified by sink:
- REACHES a replayed field (3 sources):
  - `src/engine/pipeline.py`: 54 `perf_counter_ns` stamps (first :97, last :461) into `costs`, returned as `update.sub_phase_costs` (:468).
  - `src/domains/cooperation/phase.py:101,267,272`: `metric_counters["cooperation_phase_ms"]`.
  - `src/domains/world_emergence/phase.py:35,128,130`: `metric_counters["world_emergence_ms"]`, flag-gated (pipeline.py:351), so absent from the AC2 worlds.
  - `pipeline_phases/movement.py:238,320` and `town_resolution.py:71-76` only pass the dicts through.
- Does NOT reach the chunks (control/telemetry only): kernel.py:233,402-470,602,749 (phase costs, `_final_compute_ms`, frame pacing :456-460), worker_manager.py:46-49,243-246, engine/observability.py:47,131.
- Reaches the run directory but not the chunks: `replay_manager.py:64,173` writes `start_time` and `end_time` (`time.time()`) into `manifest.json`; kernel.py:173,1241 `started_at` / `ended_at`; `run_identity.py:21` run id. FINDING (not in this fix unless you say so): `manifest.json` is non-reproducible too, and so is the run manifest; the ticket says "chunk files".
- Not run-time sinks: src/lab, src/perf, src/api, src/certification, src/cli, src/worldbuilding, src/worldgeneration, src/testing, src/rendering, src/logging, src/simulation_quality, src/ai/life_stage.py (a comment: "monotonic"). They write no StateUpdate field.
Limit: the static trace covers the three sources above; a runtime probe (12 ticks, one world) found no other differing byte. A flag-on or other-world run could still show a leaf this does not; the float-leaf test is the guard.

## 2. Readers
- Replay chunks, the two fields: `tools/rpg_measure/replay_digest_compare.py:73-75` and the key list `tools/rpg_measure/replay_digest_wall_clock_keys.jsonl` (the AC2 mask), plus `tests/tools/test_replay_digest_kit.py:25,54`. These mask or compare the keys; with the keys gone the mask is a no-op on new chunks and still correct on old ones. No change needed; I will say so in the test docstring.
- In src/, tools/, frontend/src: none read these fields from replay chunks (searched `cooperation_phase_ms|world_emergence_ms|sub_phase_costs|metric_counters`).
- Readers of the in-memory values (all stay unchanged under A): `kernel.py:443` (`_current_update.sub_phase_costs`), :637-640, `phase_governor.py:109-135` via `signal_source.py:71,94,173`, tools/perf/_profiling_common.py:534-536, profile_sweep.py:304,372, tests/perf/baselines.
- perf-planner: the AC5 kit never reads chunk_*.json.

## 3. Final hash and checkpoint are unchanged
`metric_counters` and `sub_phase_costs` appear in neither src/engine/checkpoint.py nor src/engine/apply.py nor src/core/state.py (searched). `replay_form()` runs on the emit copy after the kernel has already applied `refined_update`. Pin: a test that runs one seed with the old and new emit and asserts the final canonical digest equal and the per-tick TICK_END hashes equal (the AC2 and equality files already prove digest independence; I will add one `final_hash(seed)` constant-style equality test between a run and a run with `replay_form` patched to identity).

## 4. `is_noop`
`StateUpdate.is_noop` includes both fields (updates.py:391). `replay_form()` creates a new object and nobody calls `is_noop` on it; the kernel's `refined_update` is unchanged, so no `is_noop` result changes. A test pins `refined_update.is_noop` equal before and after on a tick that carries only timers.

## 5. Tests
- tests/unit/engine/test_replay_chunks_are_reproducible.py (drafted, on this commit): (a) two runs of one world and seed give byte-equal chunk_*.json; (b) no float leaf under `metric_counters` or `sub_phase_costs`. Both FAIL on main (2 failed in 3.9 s). No run-id mask is needed.
- The world-emergence path (lead's point 2): add a flag-on kernel run (`ENABLE_WORLD_EMERGENCE` on through the flags the world-emergence integration test uses, tests/integration/domains/test_fused_loop.py:69-84) and a unit test on `WorldEmergencePhase.execute`'s returned update: it carries `world_emergence_ms`, and `replay_form()` drops it. Fails on main (no `replay_form`).
- Governor still gets phase costs: after `tick_once`, `kernel._phase_costs` is non-empty with the 23 sub-phase keys and `status.signal_history[-1].phase_costs_ms` carries them, and `_metrics["cooperation_phase_ms"]` is still present. The draft asserts `_phase_costs` non-empty.
- The replay digest kit tests still pass unchanged (no key removed from the compare).
- Typing: `StateUpdate.metric_counters: Dict[str, int]` (updates.py:360) holds floats. Fix: type it `Dict[str, float]` (mypy accepts ints), with a one-line comment that `*_ms` keys are timers and are not replayed. Splitting counters from durations is option B territory (changes `_metrics`), so I do not do it.

## 6. Docs
replay_contract.md (a limit: chunks carry no wall-clock value; where it is stripped), deterministic_execution.md (the replay-form line), wall_clock_inventory.md rows T8 and T10 (add "stripped from the replayed copy at kernel.py:656"), parity ledger: one entry mentions `metric_counters` (world_dynamics.yaml:1250, the count `quest_opportunities_rejected`); none names a timer, so no ledger change. Note in pr_notes: the PR merges only after perf's AC5 after-arm.

## Separate question: can a wall-clock value change what the sim does outside audit_mode? (NOT part of this fix)
Yes, and it is already documented. Trace: `sub_phase_costs` (pipeline.py:468) -> `_phase_costs` (kernel.py:637-638) -> `MeasuredCosts.phase_costs` -> `LiveSignalSource.tick_end_signals` (signal_source.py:94) -> `status.signal_history[-1].phase_costs_ms` -> `tick_start_signals` (signal_source.py:71) -> `PressureSignals.effective_phase_cost` -> `PhaseBudgetGovernor` (phase_governor.py:109-135: locomotion and final_integrity above 10 / 15 ms or 0.3 / 0.5 of the tick budget lowers `move_b`, `strat_b`, `sweep_int`, scan policy) and :140 (tick cost over 0.8 of budget: AGGRESSIVE compaction). `tick_compute_ms` feeds `ResourceGovernor._get_indicated_mode` (cadence, LOD, scan policy, budgets). The tick-5 clamp is signal_source.py:59-60. `ZeroedSignalSource` (audit_mode) zeroes all of it; `CanonicalSignalSource` replaces it with a modelled cost and an empty `phase_cost`.
Documented: docs/engine/deterministic_execution.md:62 "**Today's runs satisfy neither contract fully.** One wall-clock input still changes what is computed, in every execution mode unless `audit_mode` is on"; :63 item 1 (`ResourceGovernor._get_indicated_mode()` chooses `RuntimeMode` from `tick_compute_ms` ... cadence, LOD, scan policy, and phase budgets); :69 ("`audit_mode` zeroes the timing and resource signals"); :184 limit 4 (the phase-cost governor `PhaseBudgetGovernor` is neutralised by `audit_mode`). The T1/T2 budget paths (kernel `_phase_resolution` / end-of-tick overrun) are report-only since TCK-20261006-PERF-TICK-BUDGET-THROTTLE-REPORT-ONLY (:65-66). No new FINDING.

## What I need from you
1. Approve A with `replay_form()` and the `_ms`-suffix rule, plus the `Dict[str, float]` typing.
2. Say whether the `manifest.json` / run-manifest timestamps are in scope (I say no: a separate ticket).
