---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP
phase: open
date: 2026-11-15
tags: [performance]
---

# TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP

## Title
Measure what a Collection chunk costs to encode and decode, and Collection's internal split, on the 3 gate worlds (cheap form)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 2 (packet-cost measurement) of `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`, specified in `docs/plans/architecture/distributed_workers_experiment_design.md` §9.

The owner exempted this item from the perf pause (#715 6556861718), and only this measurement; the pause stays for everything else. Record: #715 6889952914; the owner's words: 6889947724. Relayed by lead-planner on 2026-11-15. The exemption covers the cheap form first. The full form runs only if the cheap one is inconclusive.

The design encodes per chunk, not per packet: the adapter freezes the large world views once per batch and shares them across packets (`ConcurrentExecutionAdapter._batch_views`, `src/engine/executor.py:221`; design §4). Whether a remote worker is worth building depends on what one chunk costs to pickle and unpickle, against the compute it carries.

## Scope
- **Cheap form**, in-process, with no containers or network, about minutes on the heavy slot:
  - On the 3 gate worlds (`frontier_living_world`, `urban_political`, `crowded_frontier`; `tools/rpg_measure/paired.py:45`) at seed 42, with the chunking the adapter uses today.
  - Per chunk: pickled size in bytes (packets plus the shared views), encode time and decode time.
  - Collection's internal split per chunk: packet build, encode, compute, decode, validate. Any item that cannot be measured without a `src/` edit is marked **unknown**, not estimated (design §12).
  - Each figure carries its denominator: the chunk's compute time and Collection's share of the tick, plus the sha, warmup and measured ticks.
- The measurement is a probe that drives the existing adapter code paths and times `pickle` around them, with no `src/` edit. Where it lives (a perf test helper or under `tools/perf/`), and whether it is kept, is settled with lead-planner before the run (see Open Questions).
- **Full form** (loopback round trip through one worker container, about an hour) only if the cheap form is inconclusive, and only after a fresh go. It is not started by this ticket's cheap-form slot.
- Quiet host under `docs/performance/perf_baseline_policy.md` §2.2, one run at a time, under the 3G cap, on the slot lead-planner grants. lead-planner-u24 is told before it runs (epic SEQUENCE rule).
- Results go into the design doc's §9 child 2 row and a short evidence note.

## Out of Scope
- `RemoteWorkerManager`, transport, the worker entry point, the compose profile (children 3 and 4).
- Multi-host networks, contention with other containers, tail latency (design §9).
- Any change to the default path (`kernel.py` selection, `docker compose up` without a profile).
- Collection's growth attribution (`TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION`, still paused).

## Acceptance Criteria
- [ ] Per-chunk pickled size and encode/decode time on all 3 gate worlds at seed 42, with denominators and the sha.
- [ ] Collection's internal split per chunk, each item measured or marked unknown with the reason.
- [ ] A stated verdict: conclusive (the cost against compute is clear either way) or inconclusive with what the full form would settle.
- [ ] Design §9's child 2 row cites the result; child 3 can read it.
- [ ] Run data cleaned by id.

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (parent, child 2)
- TCK-20261109-DISTRIBUTED-WORKERS-DESIGN
- TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT (done; the ADR)
- TCK-20261026-PERF-COLLECTION-PHASE-GROWTH-ATTRIBUTION (paused; overlaps on Collection, not covered by the exemption)
- TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE (where the pause and this exemption are recorded)

## Related Docs
- docs/plans/architecture/distributed_workers_experiment_design.md (§4, §9, §12)
- docs/architecture/distributed_workers_adr.md
- docs/performance/perf_baseline_policy.md (§2.2)
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/executor.py (read only: `ConcurrentExecutionAdapter`, `_batch_views`)
- tools/perf/quiet_gate.py

## Assumptions / Open Questions
- **Settled (lead-planner, 2026-11-15, citing #715 6889952914 item C): the probe is inside the exemption, on conditions.** It lives in this ticket's staging artifacts (`agent-working/staging_artifacts/TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP/`), which move to stored_artifacts as evidence. It does not go in `tools/`, and there is no `src/` edit. If it needs a permanent home in `tools/` or a `src` hook, that is new perf tooling: stop and bring it to lead-planner for the owner.
- **Settled, corrected by lead-planner the same day:** the pinned-runner rule (`delivery_process.md`, "Behaviour evidence comes from the pinned runner") covers behaviour evidence, not timing. Timing follows `docs/engine/performance_contract.md`. The probe still drives the pinned kernel, by choice: packet contents should come from the reference sequential state, and the final-hash match is the positive control. Its executor, `LocalSequentialExecutor`, builds no packets or chunks. So the probe drives the pinned kernel (`tools/test_architecture/rpg_gate_run.build_kernel`), and on each measured tick it builds, off the run, what `ConcurrentExecutionAdapter.execute` would build (`_batch_views` plus the `WorkerPacket`s, `executor.py:221-330`). It then chunks them the way the worker manager does and times pickle and unpickle around them. That side path reads state only and must not change the run: the probe checks the final hash against a probe-free run. The part of Collection's split that only a concurrent run has (dispatch, worker compute per chunk) is marked unknown or taken from the full form.
- **Settled:** item C supersedes the epic SEQUENCE's "no heavy-slot run until the owner has reviewed the whole plan" for this cheap form only. lead-planner tells lead-planner-u24 when it queues the run.
- Whether the chunking today (chunk size, worker count) is the one the experiment would use: design §4 decides. This ticket measures today's.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
