---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER

## Title
Distributed workers child 3: a RemoteWorkerManager behind the existing executor adapter, its transport, the slow or dead worker rule, and its tests (filing only, not built)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Design §9 child 3 of TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (docs/plans/architecture/distributed_workers_experiment_design.md). Its owner there is rpg-planner. The owner approved filing the remaining distributed children as tickets only, with nothing built (#715 6889947724, scoped in 6889952914, item D). Implementation stays gated by the owner's whole-plan review (#715 6731938042). All src/engine work under this epic is paused until after Milestone 1.

## Scope
1. A RemoteWorkerManager behind the existing adapter (design §3), using the wire format and transport of §4. Selection is the opt-in of §5; the default path never changes (kernel.py executor selection; `docker compose up` without a profile).
2. The slow or dead worker rule (§6, owner #715 6776551375):
   - a transport failure or a timeout recomputes that chunk locally through the same `_execute_locally` path;
   - a worker that raises is handled as the local path handles a raised chunk;
   - a late result is dropped;
   - each fallback is a typed counter or record in the run manifest, never a log line or a reason string;
   - a failed handshake refuses the run.
3. Before the transport is built, verify the §6 open check: does `default_simulation_worker` read nothing outside its packet, including process-global singletons (content catalog, registries)? Report the answer to rpg-planner before going on.
4. The tests of §8 for child 3, each at the place testing-planner gave:
   - unit: `test_executor_context_parity.py` extended with the remote manager;
   - unit: a chunk round trip, with negative decode cases that refuse loudly;
   - unit: the dead-worker rule, read from a typed counter;
   - unit: a late result is dropped;
   - kernel integration: loopback equivalence against LocalSequentialExecutor under the medium budget, wall time measured on the slow VM and stated;
   - extra_slow: a sibling file, starting with crowded_frontier s45. It needs testing-planner's sign-off with a measured wall time under 540 s.

## Out of Scope
- The container entry point and the `distributed` compose profile (child 4, platform-planner).
- API reach (§5).
- Multi-host networks, tail latency and any timing claim.
- The evidence guard (child 6, testing-planner with rpg-planner), and the contract docs (child 5).
- Behaviour evidence: the rpg gate, paired arms and the gate baseline stay on the pinned sequential runner.

## Acceptance Criteria
- Equivalence (DET-PORT-1 under PERF-D2): a field-by-field content compare is the primary check and the canonical hash the secondary one, with zero worker FAILURE no-ops on both arms.
- The dead-worker and late-result tests pass, reading a typed fallback record.
- The default executor selection and the default compose path are byte-unchanged.
- The §6 open check is answered with evidence.

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (parent)
- TCK-20261109-DISTRIBUTED-WORKERS-DESIGN
- TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE (#918; RunConditions already records the executor)
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ

## Related Docs
- docs/plans/architecture/distributed_workers_experiment_design.md (§3, §4, §5, §6, §8, §9)
- docs/architecture/distributed_workers_adr.md
- docs/engine/contracts/bounded_concurrency_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/kernel.py (executor selection, read only), src/engine/executor.py, worker_manager.py (`_execute_locally`, :192-194, :213-224), src/core/protocol_validator.py:41-50
- tests/unit/kernel/test_executor_context_parity.py, tests/integration/kernel/test_executor_equivalence_long.py

## Assumptions / Open Questions
- Gated: nothing starts before the owner's whole-plan review (#715 6731938042), and src/engine work under this epic waits until after Milestone 1 (#715 6889952914).
- The §6 open check (process-global reads by the worker function) may change the transport design. If it fails, this ticket returns to the owner with options before any build.
- The measurement tier and lanes are stated at dispatch.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
