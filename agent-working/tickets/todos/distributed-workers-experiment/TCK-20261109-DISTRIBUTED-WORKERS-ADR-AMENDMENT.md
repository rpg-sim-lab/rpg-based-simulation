---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT
phase: open
date: 2026-11-09
tags: [architecture, determinism, planning]
---

# TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT

## Title
ADR amendment: allow an opt-in experiment mode whose Collection workers run outside the engine process, with one writer kept and the default unchanged.

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Child 0 of `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`. The owner chose "Epic + ADR first" (#715 6731714291); every other
child is gated on this one. Author: lead-planner (ubuntu seat), the ADR owner. Filed by architecture-planner-u24; lead-planner-u24
carries it to lead-planner when that seat is back. **Gate:** ubuntu's `lead-docs-review-source` batch must land first: it
edits `docs/architecture/kernel_concurrency_design_philosophy.md`, and this amendment touches `system_overview.md` and may cite that file.

## Scope
Amend the recorded decisions so that one opt-in mode may run the Collection pool outside the engine process. The amendment states:
1. **What is kept:** the engine is one writer. Workers only compute `WorkerResult`s from a `WorkerPacket`; the kernel validates
   (`kernel.py:556`), sorts (`worker_contract.md` §3) and applies every result through `ApplyPath` alone. Scaling stays per run.
2. **What is relaxed, and only where:** "one process" is relaxed for the Collection pool, only under the opt-in experiment profile.
   Every other phase, and every run without the profile, stays one process.
3. **The default is unchanged:** no change to the executor selection at `kernel.py:193-198`, to `LocalSequentialExecutor`,
   `ConcurrentExecutionAdapter`, or to `docker compose up` without a profile.
4. **Determinism rule:** a run in the mode must give an identical `flat-sha256-v3` final hash and `TICK_END` trail to
   `LocalSequentialExecutor` on the same world and seed, or the mode is unclaimed for it (PERF-D2: anything but DET-PORT-0
   sequential needs a passing parity matrix). Outcomes must not depend on worker speed (`worker_manager.py:192`, contract §4).
5. **Why it reopens:** it is an experiment the owner chose (#715 6731714291), not a speed-up; this replaces the Mode 5 condition
   "only if the owner names a world one machine cannot hold" (`engine_execution_modes_proposal.md`, Mode 5). Collection was 6 to 26 %
   of a tick (`tick_cost_growth.md`), so the expected result may be slower than sequential.

Where it lands is lead-planner's call: likely `docs/architecture/system_overview.md` ("What is deliberately not distributed") and
`docs/architecture/devops_plan_amendment_proposal.md` ("What stays from the ADR"), plus a pointer from the Mode 5 section of
`engine_execution_modes_proposal.md` (architecture-planner-u24 edits that file once the amendment is accepted).

**Cost:** one doc session, no runs. **Leaves out:** anything built; the `worker_contract.md` and `infrastructure_overview.md`
edits (epic child 5, gated on ubuntu's docs batch).

## Out of Scope
- More than one writer, engine replicas, an API/engine split, brokers beyond Redis Streams, multi-host or k8s deploys.
- Any claim of speed.
- `docs/engine/**` edits.

## Acceptance Criteria
1. The amendment is merged in `docs/architecture/**` with the five points above, citing #715 6731714291.
2. It states that the Mode 5 reopen condition is replaced by the owner's experiment choice.
3. The devops amendment's "single replica" stays true as written (the engine remains one writer, one replica).

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (parent)
- TCK-20261109-DISTRIBUTED-WORKERS-DESIGN (gated on this)

## Related Docs
- docs/architecture/system_overview.md
- docs/architecture/devops_plan_amendment_proposal.md
- docs/architecture/kernel_concurrency_design_philosophy.md
- docs/plans/architecture/engine_execution_modes_proposal.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/kernel.py (selection at 193-198; validation at 556)
- src/engine/worker_manager.py (no-timeout rule at 192)

## Assumptions / Open Questions
- lead-planner may prefer a new ADR file over amending two docs; either satisfies this ticket.

## Implementation Notes
None yet.

## Test Summary
Doc only.

## Files Changed
None yet.

## Completion Summary
Open.
