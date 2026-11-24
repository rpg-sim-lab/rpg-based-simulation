---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261124-A-WALL-CLOCK-TIMER-IN-THE-REPLAY-STREAM-MAKES-REPLAY-FILES-NON-REPRODUCIBLE
phase: done
date: 2026-11-24
tags: []
---

# TCK-20261124-A-WALL-CLOCK-TIMER-IN-THE-REPLAY-STREAM-MAKES-REPLAY-FILES-NON-REPRODUCIBLE

## Title
A wall-clock timer inside every replay update makes replay files differ byte for byte between two runs of the same world and seed

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by lead-planner while reviewing the AC2 record set of TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK (session message 2026-11-24). Every tick's replay update carries `payload.update.metric_counters.cooperation_phase_ms`, a float wall-clock duration. Lead-planner counted it in 2020 of 2020 updates of perf's /data/vboxuser/perf_runs/obs_out_613a8365bcd1_s42_attr/tree-data-runs/1_OFF_replay, for example 0.302696 in chunk_0000. The source is src/domains/cooperation/phase.py:266-272 (origin/main 4f2f284cb): `t_duration_ms = (time.perf_counter_ns() - t_start) / 1e6`, written into `metric_counters`. The kernel then copies `metric_counters` into `_metrics` (kernel.py:637), and the replay stream records it. So the raw chunk bytes of two runs of the same world and seed can never be equal, and a byte-level replay comparison needs a key filter. The final state hash is unaffected: metric_counters is not authoritative state.

## Scope
- Keep wall-clock durations out of the replay payload: move `cooperation_phase_ms` to the timing path the kernel already has for phase costs (sub_phase_costs / phase_costs, which the replay does not record per tick), or drop it from `metric_counters`. Keep `cooperation_evaluations`, which is a count.
- Search src/ for any other `perf_counter`/`time.time` value written into `metric_counters` or any other replayed field, and handle each the same way.
- A test: two runs of the same small world and seed give replay chunks that are byte-equal once nothing but the run id is masked, or equal raw if the chunks carry no run-specific field.
- Note: `StateUpdate.metric_counters` is typed `Dict[str, int]` (updates.py:360), but this value is a float.

## Out of Scope
- The replay digest work (TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK): its AC2 compare removes only the pre-registered wall-clock keys.
- Replay schema or chunking changes beyond removing wall-clock values.

## Acceptance Criteria
1. No wall-clock value is written into any replayed field. The search is listed in the ticket.
2. The new reproducibility test passes, and it fails on the current code.
3. Any reader of `cooperation_phase_ms` (perf kits, tools, frontend) is found and moved, or listed as having none.

## Related Tickets
- TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK

## Related Docs
- docs/engine/contracts/replay_contract.md
- docs/engine/deterministic_execution.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261124-A-WALL-CLOCK-TIMER-IN-THE-REPLAY-STREAM-MAKES-REPLAY-FILES-NON-REPRODUCIBLE/approach_note.md, pr_notes.md

## Related Code Areas
- src/domains/cooperation/phase.py
- src/core/updates.py (metric_counters)
- src/engine/kernel.py (_metrics)
- src/engine/replay_manager.py

## Assumptions / Open Questions
- Not verified yet: whether perf or a dashboard reads cooperation_phase_ms from the replay. AC3 answers it before the change.

## Durable state, lifecycle and clocks
N/A: nothing durable is added. `replay_form()` returns a short-lived copy of the tick's update for the replay emit; the replay chunks lose their timer values (they were never authoritative state), and no clock is added or read differently: the phases still read `perf_counter_ns` and the kernel still keeps those values in `_phase_costs` and `_metrics`.

## Implementation Notes
- 2026-11-24, from the replay-digest AC2 key scan (BASE 36a7e2089 smoke, #715 7132066246, proven complete by a second smoke): a SECOND wall-clock field is in every REFINED_UPDATE: `payload.update.sub_phase_costs.<23 phase names>` (src/core/updates.py:359 `sub_phase_costs: Dict[str, float]`, per-phase durations such as combat_engagement 17.316701). It is not named *_ms and is not in metric_counters. Scope covers it too: both timer groups leave the replayed payload. Frozen list: tools/rpg_measure/replay_digest_wall_clock_keys.jsonl on rpg-ubuntu-replay-digest.

- 2026-11-24, approved approach (rpg-planner-ubuntu, option A): `Kernel` emits `refined_update.replay_form()` (kernel.py:656); `StateUpdate.replay_form` empties `sub_phase_costs` and drops `WALL_CLOCK_METRIC_KEYS` (src/core/updates.py) from `metric_counters`, never mutating self. `metric_counters` is typed `Dict[str, float]`. The kernel's own update, `_phase_costs`, `_metrics` and the governor input are unchanged (perf baselines read `_metrics`).
- Found and ruled out of scope (run metadata by design, not replayed simulation content; planner ruling 2026-11-24): `src/engine/replay_manager.py:64` and `:173` (`manifest.json` `start_time`/`end_time`, `time.time()`), `src/engine/kernel.py:173` and `:1241` (run manifest `started_at`/`ended_at`), `src/engine/run_identity.py:21` (run id). No ticket is needed.
- The sealed AC2 kit (tools/rpg_measure/replay_digest_*) is unchanged; its mask is a no-op on new chunks and still correct on old ones.

## Test Summary
- New: tests/unit/engine/test_replay_chunks_are_reproducible.py (16 tests; 13 red on main, all green now): byte-equal chunks with and without ENABLE_WORLD_EMERGENCE, no float timer leaf, counts kept, the kernel keeps `_metrics` and `_phase_costs`, TICK_END hashes and the final digest equal between the new emit and the old (replay_form patched to self), `replay_form` drops exactly WALL_CLOCK_METRIC_KEYS, handles None and empty, never mutates self, leaves is_noop alone.
- Pre-push set: unit/engine 1329, unit/core+kernel+replay 567, perf cooperation budget 1, integration 12, architecture 260, static 176, tests/tools all pass except 4 live docs-index build timeouts in test_knowledge_search.py on this host (environmental). code-health OK, import contracts 17 kept 0 broken.

## Files Changed
src/core/updates.py (WALL_CLOCK_METRIC_KEYS, StateUpdate.replay_form, metric_counters typed Dict[str, float]), src/engine/kernel.py (emit replay_form), tests/unit/engine/test_replay_chunks_are_reproducible.py, docs/engine/contracts/replay_contract.md, docs/engine/deterministic_execution.md, docs/performance/wall_clock_inventory.md (T8, T10), this ticket and its stored artifacts.

## Completion Summary
Replay chunks carry no wall-clock value: two runs of one world and seed write byte-equal chunk_*.json, with the world-emergence flag on and off. The kernel's own update, `_metrics`, `_phase_costs`, the governor input, the final hash and the TICK_END hashes are unchanged. Known gaps are in pr_notes.md.
