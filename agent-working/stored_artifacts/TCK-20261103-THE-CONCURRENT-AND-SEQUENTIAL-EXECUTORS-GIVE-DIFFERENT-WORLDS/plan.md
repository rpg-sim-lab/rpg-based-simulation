---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS
tags: []
---

# plan - TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS

Owner go #715 6593491826 (build), #715 6593673717 (failure answers). Branch `rpg-ubuntu-executor-parity` off origin/main 9eeb0fd97 (#833: no src change since 0e7b1030c).

1. `src/core/worker_protocol.py`: `WorkerPacket` gains `feature_flags`, `building_tiles`, `town_center`, `clans` (real values set by the executor; no None placeholders). `seed` keeps its name and carries the WORLD seed.
2. `src/engine/executor.py`: the adapter stops deriving `packet_seed`; it passes `state.seed`, `ReadOnlyDict(state.feature_flags)`, `state.building_tiles`, `state.town_center`, `state.clans` (the readonly view already freezes the last two).
3. Guard: `WorkerPacket.__getattr__` (called only when a lookup fails): a name that is an `AuthoritativeState` field/property but neither a packet field nor on a named allow-list raises `PacketFieldMissingError(RuntimeError)`; any other name raises `AttributeError` as before. The allow-list (lazily derived caches, one reason each) lives beside the class.
4. `src/engine/worker_manager.py`: `PacketFieldMissingError` passes through the four handlers (`_process_chunk_wrapper`, the submission fallback, `_collect`, `_wrap_work`); every other worker exception keeps Failure-to-No-Op (contract section 4) and is counted by wrapping `failure_no_op` in tests.
5. Docs: bounded_concurrency_contract.md section 4 gets the one written exception; deterministic_execution.md probe line corrected; certification matrix / parity ledger (infrastructure.yaml) state the law with its horizon; divergence entry (Bug Fix).
6. Tests: unit (kernel) per field, the guard, pass-through on the thread pool, the no-op pin and counter positive control, clans join/leave on both executors; long test in tests/integration/kernel (extra_slow), horizon agreed with testing-planner (floor 3000 ticks, not below t2100).
