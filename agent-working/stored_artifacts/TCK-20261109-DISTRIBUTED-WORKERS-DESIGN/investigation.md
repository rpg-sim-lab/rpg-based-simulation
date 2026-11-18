---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-DISTRIBUTED-WORKERS-DESIGN
artifact_type: investigation
---

# Investigation — TCK-20261109-DISTRIBUTED-WORKERS-DESIGN

**Reconstructed at close from design §2-§3; no tests run (doc deliverable).** This file was written on 2026-11-16, when the ticket
closed. It was not written as pre-work. The investigation itself is in the design doc,
`docs/plans/architecture/distributed_workers_experiment_design.md`, where every code fact is cited to a file and line on `main` at
`e755dc3d1`. This file summarises them.

## Code facts the design rests on (design §2, §3)
- **One writer.** `ProtocolValidator.validate_result_batch` checks results against the source packets (`kernel.py:556`, and
  `executor.py:367` inside the adapter). Results are sorted before apply (`worker_contract.md` §3).
- **Selection** is at `kernel.py:193-198`: an explicit `executor`, else `ConcurrentExecutionAdapter` when `max_worker_count > 0`,
  else `LocalSequentialExecutor`.
- **The seam.** `ConcurrentExecutionAdapter(worker_manager=...)` (`executor.py:213`) takes any manager with
  `WorkerManager.execute_batch`'s contract (`worker_manager.py:107`). The adapter is the only packet builder
  (`test_executor_context_parity.py:141`).
- **Shared views.** The adapter freezes the world views once per batch (`_batch_views`, `executor.py:221-232`). The worker
  function is module-level (`default_simulation_worker`, `executor.py:341-345`).
- **No timeout** on `result()` (`worker_manager.py:192`). A raised chunk is answered with FAILURE no-ops (`:192-194`).
- **The API passes no executor** (`src/api/engine_manager.py:139`).
- `ai_worker` in `compose.yaml:81-89` is the anomaly consumer, not an engine worker.

## Finding that changed the ticket's scope
Scope item 1 proposed a new `IWorkExecutor`. The design chose a `RemoteWorkerManager` behind the existing adapter instead (§3).
That keeps packet building and validation in one place, which is the drift #837 guards against.

## Later evidence, after acceptance
Child 2 (`5c9496a33`): the per-chunk pickle round trip is 34-60 ms against 0.2-1.2 ms of compute. So child 3 as designed is a
no-go (design §14).
