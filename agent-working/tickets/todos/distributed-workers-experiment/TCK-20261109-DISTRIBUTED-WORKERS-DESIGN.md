---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-DISTRIBUTED-WORKERS-DESIGN
phase: open
date: 2026-11-09
tags: [architecture, engine, determinism, platform]
---

# TCK-20261109-DISTRIBUTED-WORKERS-DESIGN

## Title
Design the distributed-workers experiment mode: seam, wire format, selection, slow or dead worker rule, equivalence proof and compose profile.

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 1 of `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`. Blocked on child 0
(`TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`). Owner: architecture (architecture-planner-u24, or
architecture-implementer-u24 on dispatch). Output is one design doc in `docs/plans/architecture/`.

## Scope
Write `docs/plans/architecture/distributed_workers_experiment_design.md`, covering:
1. **Seam.** A new `IWorkExecutor` (working name `RemoteExecutionAdapter`) passed explicitly as `executor=`, so `kernel.py:193-198`
   is unchanged. Whether it reuses `WorkerManager` (it already has an unused process-pool path, `worker_manager.py:90-93`) or calls
   workers over the network directly.
2. **Wire format.** How a `WorkerPacket` and `WorkerResult` cross the boundary (`src/core/worker_protocol.py:55-151`), including
   the large world views (`:82-108`) and the private caches (`:93-98`, rebuilt on the worker, not sent). `tests/unit/kernel/test_executor_context_parity.py`
   (#837) must stay green and cover the new adapter as a third packet consumer.
3. **Selection.** How a run opts in. The cheaper default is the CLI and test harness only; reaching it from the API needs
   `V2EngineManager` to pass an executor (`engine_manager.py:139` passes none), which is a larger change.
4. **Slow or dead worker rule.** It must keep outcomes host-independent (`worker_manager.py:192`; contract §4). Proposed: after a
   bounded wait, the kernel computes that chunk locally from the same packets (a pure function, so the result is identical), counts
   it, and records it in the run manifest; it never answers with a FAILURE no-op, because that would make the outcome depend on speed.
   The design weighs this against failing the run loudly.
5. **Equivalence proof.** Same world and seed under `LocalSequentialExecutor` and the mode: identical final hash under the current proof scheme (`PROOF_DIGEST_SCHEME`) and
   `TICK_END` trail, on 3 gate worlds at seed 42, 300 ticks, plus a killed-worker case (the rule in 4 must still give the same hash).
6. **Compose profile.** A `distributed` profile adding one engine-worker service holding N workers; a name that cannot be confused
   with `ai_worker` (the anomaly consumer, `compose.yaml:81-89`); `docker compose up` with no profile unchanged.
7. **Testing strategy** (owner, #715 6731938042), reusing what exists rather than inventing: the `docs/testing/test_taxonomy.md`
   layers; `tests/unit/kernel/test_executor_context_parity.py` (#837) and `tests/integration/kernel/test_executor_equivalence_long.py`
   as the equivalence pattern; the gate worlds and the rpg gate baseline (`tests/simulation_quality/rpg_gate/baselines/rpg_gate_v1.json`);
   the pinned sequential runner (`tools/rpg_measure`) as the only behaviour evidence; the Slow regression lane
   (`.github/workflows/slow-regression.yml`); the PERF-D2 hash and `TICK_END`-trail claim rules; the existing CI lanes. For each of
   children 2-5: the layers it adds tests in, what is new and why no existing layer covers it, and which lane runs it. Layer
   placement is testing-planner's call, asked through its own route.
8. **Cut lines** for epic children 2-5: what each owner builds, its cost and what it leaves out, using the epic's table as the start.

**Cost:** one doc session, no runs. **Leaves out:** code, measurement (child 2), the contract text (child 5).

## Out of Scope
- Building anything; running anything on the heavy slot.
- The API/engine split, multi-host, k8s.
- `docs/engine/**` and `docs/architecture/**` edits.

## Acceptance Criteria
1. The design doc covers points 1-8, with each claim cited to a file and line on main at the time it is written.
2. It names the open choices that are owners' calls (selection reach, the dead-worker rule) with a recommendation for each.
3. It stays inside the amendment accepted in child 0.

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (parent)
- TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT (blocks this)

## Related Docs
- docs/engine/contracts/worker_contract.md
- docs/architecture/kernel_concurrency_design_philosophy.md
- docs/plans/architecture/conformance_suite_design.md (Mode 3 matrix; the same equivalence form)

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/executor.py
- src/engine/kernel.py
- src/engine/worker_manager.py
- src/core/worker_protocol.py
- src/api/engine_manager.py
- compose.yaml

## Assumptions / Open Questions
- None beyond the two owner calls in acceptance criterion 2.

## Implementation Notes
DRAFT written 2026-11-09 by owner leave (#715 6731956846): `docs/plans/architecture/distributed_workers_experiment_design.md`.
Testing placement from testing-planner (2026-11-09) folded into §8. Stops for the owner's review with child 0.

## Test Summary
Doc only.

## Files Changed
None yet.

## Completion Summary
Open.
