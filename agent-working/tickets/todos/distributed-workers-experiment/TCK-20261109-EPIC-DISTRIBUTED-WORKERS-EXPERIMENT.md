---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT
phase: open
date: 2026-11-09
tags: [architecture, engine, determinism, platform, planning]
---

# TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT

## Title
An opt-in experiment mode that runs Collection work in separate worker containers, with one writer kept and the default path unchanged.

## Status
EPIC_SCOPED

## Tier
epic

## Type
feature

## Priority
P2

## Request Summary
The owner's idea, raised through the read-only Q&A session: an opt-in experiment mode for a distributed deploy, with several docker
containers, one holding N engine workers, plus the other components. The default path must keep working with no change to existing
logic. Routed to architecture-planner-u24 (#715 6731692652). Shape chosen by the owner (#715 6731714291, "Epic + ADR first"): file
the epic now, scoping only; child 0 is an ADR amendment by lead-planner; every other child is gated on it.

**This is an experiment, not a speed-up.** The owner chose it knowing that. The workers would run only Collection, which was 6 to
26 % of a tick (Amdahl ceiling 1.06 to 1.35x; `docs/performance/tick_cost_growth.md`). The per-tick cost of moving a `WorkerPacket`
across a container boundary is unmeasured, so the mode may well be slower than `LocalSequentialExecutor`.

## Scope
Scoping only. Nothing is built under this epic until child 0 is accepted.

**Decisions this runs into** (all re-read on main at `55d6ee703`, 2026-11-09):
- `docs/architecture/system_overview.md`, "What is deliberately not distributed": "The engine is one process and one writer.
  ... determinism and replay depend on it. Scaling is per run (many seeds in parallel), not per tick."
- `docs/architecture/devops_plan_amendment_proposal.md:35-37`: "The engine stays one process with one writer ... a single replica."
- `docs/plans/architecture/engine_execution_modes_proposal.md`, Mode 5 (dropped 2026-10-26): distributed execution reopens only by an
  ADR amendment (lead-planner), and only if the owner names a world one machine cannot hold. The owner's choice of an experiment
  mode (#715 6731714291) stands in for that condition; child 0 records it.
- `docs/engine/contracts/worker_contract.md` §5 (`:41-44`): "No distributed workers (network boundaries)" is a non-goal.
- `src/engine/worker_manager.py:192`: no timeout on `result()`, so a chunk's outcome never depends on how fast the host is
  (contract §4; PR #713). A remote worker needs a timeout, so the slow or dead worker rule must keep outcomes host-independent.

**What the mode keeps and what it relaxes.** It keeps one writer: workers only compute `WorkerResult`s from a `WorkerPacket`; the
kernel still validates them (`kernel.py:556`, `ProtocolValidator.validate_result_batch`), sorts them before apply
(`_phase_resolution`; `worker_contract.md` §3) and commits through `ApplyPath` alone. It relaxes "one process" for the Collection
pool only, and only under the opt-in profile.

**Facts the children build on** (re-verified on main, 2026-11-09):
1. The API runs one Kernel in-process: `V2EngineManager` runs `tick_once()` on thread `v2-engine-loop`
   (`src/api/engine_manager.py:247`) and builds `Kernel(profile=..., state=..., rng=...)` with **no executor**
   (`engine_manager.py:139`). Splitting the API from the engine is a separate, larger job and is out of scope.
2. The seam is `IWorkExecutor` (`src/engine/executor.py:64-80`). Selection is at `kernel.py:193-198`: an explicit `executor`, else
   `ConcurrentExecutionAdapter` when `max_worker_count > 0`, else `LocalSequentialExecutor`. A new adapter passed explicitly adds the
   mode without touching the other two branches.
3. The protocol exists: `WorkerPacket` and `WorkerResult` (`src/core/worker_protocol.py:55-151`). The packet carries large world
   views (`regions`, `buildings`, `all_entities`, `spatial_grid`, `terrain`, `building_tiles`, `clans` and more, `:82-108`).
   `WorkerManager` already has an unused `ProcessPoolExecutor` path (`worker_manager.py:70,90-93`), so packets crossing a process
   boundary is not new in principle; it has never been enabled or proven.
4. Packet field parity across executors broke before (`TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES`);
   `tests/unit/kernel/test_executor_context_parity.py` (#837) is the guard now and must cover the new adapter.
5. `ai_worker` in `compose.yaml:81-89` is the anomaly consumer (`python -m src.observability.anomaly.worker`), not an engine worker.
   `docs/engine/contracts/infrastructure_overview.md:159` calls it a pool "executing computationally intense AI predictions", which
   disagrees with the code. The new engine-worker service needs a name that cannot be confused with it.
6. `docs/audits/D23_architecture_resilience.md` describes RabbitMQ, Kafka and a `docker-compose.yml`; `compose.yaml` has none of them.
   That audit is stale; it is reported to lead-planner-u24 and is not a child here.

**Children.** Filed now: child 0 and child 1 (see SEQUENCE.md). The rest are cut by their owning planners after child 0 lands,
because each is another domain's ticket:

| # | Child | Owner | Cost (measurement included) | Leaves out | Gate |
|---|---|---|---|---|---|
| 0 | `TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT` (filed) | lead-planner (ubuntu) | one doc session, no runs | anything built; the engine-side contract text (child 5) | owner choice recorded (#715 6731714291); ubuntu's `lead-docs-review-source` batch landing (it edits `kernel_concurrency_design_philosophy.md`; its topic map covers `system_overview.md`'s neighbours, `kernel.md` and `worker_contract.md`) |
| 1 | `TCK-20261109-DISTRIBUTED-WORKERS-DESIGN` (filed) | architecture (planner-u24 / implementer-u24) | one doc session, no runs | code, measurement, compose | child 0 |
| 2 | packet-cost measurement | perf-planner | **cheap form first:** pickled packet size and encode/decode time on 3 worlds at seed 42, in-process, no containers (minutes on the heavy slot). Full form only if the cheap one is inconclusive: loopback round trip through one worker container (about an hour) | real multi-host networks; contention with other containers; tail latency | child 1 (wire format); u24 heavy slot behind the RPG queue, lead-planner-u24 told before it runs |
| 3 | remote executor | rpg-planner (src/engine) | code + unit tests; equivalence on 3 gate worlds at seed 42, 300 ticks, remote (loopback) vs `LocalSequentialExecutor`: identical `flat-sha256-v3` final hash and `TICK_END` trail; `tests/unit/kernel/test_executor_context_parity.py` (#837) stays green and covers the new adapter as a third packet consumer. About 6 short runs | real container deploy (child 4); multi-host | child 1; child 2's cheap form |
| 4 | worker entry point + `distributed` compose profile | platform-planner | image + profile; one containerized smoke run repeating child 3's equivalence on one world; `docker compose up` with no profile unchanged | k8s/Helm; scaling beyond one host; the API/engine split | child 3 |
| 5 | `worker_contract.md` §5 and `infrastructure_overview.md` (the new mode, and the `ai_worker` wording of fact 5); `intentional_divergences.md` only if behaviour differs | docs/engine owner via lead-planner | doc only | everything else | child 0; ubuntu's docs-as-review-source batch (#715 6720445592) |

The equivalence proof lives in children 3 and 4 as acceptance criteria rather than its own child (the simpler shape: it tests the
code those children write).

## Out of Scope
- Splitting the API from the engine (fact 1), engine replicas, or more than one writer.
- Any change to the default selection at `kernel.py:193-198` or to `docker compose up` with no profile.
- Multi-host deploys, k8s/Helm (devops step 4 keeps the engine single replica), message brokers (system_overview: none beyond Redis
  Streams).
- Any speed-up claim. A result slower than sequential is a valid outcome of the experiment.
- Editing `docs/engine/**` or `docs/architecture/**` from this seat, and any file in ubuntu's docs-as-review-source batch
  (`lead-docs-review-source`, #715 6720445592): every child that edits `system_overview.md`, `kernel_concurrency_design_philosophy.md`,
  `kernel.md` or `worker_contract.md` (children 0 and 5) waits for that batch to land.

## Acceptance Criteria
1. Child 0 is accepted, or the owner withdraws the idea; nothing under children 1-5 is built before child 0.
2. With the mode off, the default path is untouched: no change to `kernel.py:193-198` selection, to `LocalSequentialExecutor`,
   `ConcurrentExecutionAdapter` or `docker compose up`, and existing gate and paired hashes are unchanged.
3. With the mode on, the same world and seed give an identical `flat-sha256-v3` final hash and `TICK_END` trail to
   `LocalSequentialExecutor` (children 3 and 4).
4. A slow or dead worker never changes the outcome: the rule from child 1 is implemented and has a test.
5. Every child records its cost and what it leaves out; children 2-5 are cut by their owners after child 0.

## Related Tickets
- TCK-20261008-SERVICE-LOOKUP-CRASHES-UNDER-THE-CONCURRENT-EXECUTOR-WORKERPACKET-HAS-NO-BUILDING-TILES (packet parity precedent)
- TCK-20261023-ARCHITECTURE-ENGINE-MODES-PROPOSAL-UPDATE (Mode 5 dropped)
- TCK-20261024-PROOF-DIGEST-HASHES-THE-CARRIED-STATE-IT-OMITS (`flat-sha256-v3`, the equivalence hash)

## Related Docs
- docs/architecture/system_overview.md
- docs/architecture/devops_plan_amendment_proposal.md
- docs/architecture/kernel_concurrency_design_philosophy.md
- docs/engine/contracts/worker_contract.md
- docs/engine/contracts/infrastructure_overview.md
- docs/plans/architecture/engine_execution_modes_proposal.md
- docs/performance/tick_cost_growth.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/executor.py
- src/engine/kernel.py
- src/engine/worker_manager.py
- src/core/worker_protocol.py
- src/api/engine_manager.py
- compose.yaml
- tests/unit/kernel/test_executor_context_parity.py

## Assumptions / Open Questions
- graphify was not run for this scoping: the new worktree has no linked graph. Facts were read directly on main and cited above.
- Whether the mode is reachable from the API (fact 1: the manager passes no executor) or only from the CLI and test harness is
  child 1's question; the cheaper answer (CLI and harness only) is the default.

## Implementation Notes
Filing rides in a later implementation PR on this track (owner rule, #715 6697748243), not a PR of its own.

## Test Summary
Not applicable at epic level.

## Files Changed
- agent-working/tickets/todos/distributed-workers-experiment/

## Completion Summary
Open.
