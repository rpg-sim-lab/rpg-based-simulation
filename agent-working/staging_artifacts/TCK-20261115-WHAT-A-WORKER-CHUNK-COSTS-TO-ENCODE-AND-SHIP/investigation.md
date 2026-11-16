---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP
phase: open
artifact_type: investigation
date: 2026-11-16
tags: [performance]
---

# Investigation: chunk cost probe

- Packet build: `ConcurrentExecutionAdapter.execute` (`src/engine/executor.py`) builds one `WorkerPacket` per ENTITY_MOVE/ACT/BRAIN item. Every packet references the same batch views (`_batch_views`) plus `all_entities=state.entities`, the tile maps and caches. One `pickle.dumps` per chunk writes each shared object once (memo); per-packet encoding copies them into each packet.
- Chunking: `WorkerManager.execute_batch` (`src/engine/worker_manager.py`). Threads (PROD_SMALL, 2 workers, the default the kernel builds at `kernel.py:139`): `min(50, n // 4)`. Processes: `n // workers`. Process mode is not wired by any profile.
- Compute: `_process_chunk_wrapper` is the process-path chunk body; under threads `_wrap_work` does the same per packet. The probe calls `_process_chunk_wrapper` on the decoded copy.
- Pickling: the packets pickle as the code stands. The smoke run (5 ticks) needed no reducer, so `--reducers none` is the default; the `mappingproxy` option stays only as a fallback and is named in the result if used.
- The proof digest (`CheckpointManager.compute_digest`) and `CanonicalStateHasher` read state only; the side path writes nothing to state. The probe's adapter has its own `_freeze_cache`.

## Smoke (2026-11-16, local, NOT a measurement: CPU 3, not the quiet gate, 2 warmup + 3 ticks, frontier_living_world)
- `final_hash` identical across probe (thread), probe (process) and `--no-probe`: fdc12732...
- About 470 KB per chunk at early ticks (7-8 packets per tick); private caches about 0.5 KB of it.
- Encode about 14 ms and decode about 12 ms per chunk against compute about 0.5 ms (thread chunking, 1-2 packets per chunk). Early-tick shape only; the real run decides.
- Smoke run dirs cleaned by id.
