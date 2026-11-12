---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT
phase: done
date: 2026-11-09
tags: [architecture, determinism, planning]
---

# TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT

## Title
ADR amendment: allow an opt-in experiment mode whose Collection workers run outside the engine process, with one writer kept and the default unchanged.

## Status
DONE

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
4. **Determinism rule:** a run in the mode must give an identical final hash under the current proof scheme (`PROOF_DIGEST_SCHEME`) and `TICK_END` trail to
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
- agent-working/stored_artifacts/TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- src/engine/kernel.py (selection at 193-198; validation at 556)
- src/engine/worker_manager.py (no-timeout rule at 192)

## Assumptions / Open Questions
- lead-planner may prefer a new ADR file over amending two docs; either satisfies this ticket.

## Implementation Notes
- Took the "new ADR file" route (Assumptions): the draft moved by `git mv` from `docs/plans/architecture/distributed_workers_adr_amendment_draft.md`
  to `docs/architecture/distributed_workers_adr.md`, rewritten as accepted. Header and Status cite the owner's acceptance (#715 6777076537), the
  §10 answers (6776551375) and the scale direction (6776564953). Decision 6 records the first-build choices (local recompute, CLI and harness
  only, gRPC, pickle with guards). "Not decided here" drops the two items the owner has now decided, and adds parallel Resolution (C-10, Gate B
  unchanged) and promotion. Risks add the two accepted first-build risks and the child-3 replay note.
- Applied §5.1 to `system_overview.md` (first bullet of "What is deliberately not distributed") and §5.2 to `devops_plan_amendment_proposal.md`
  ("What stays from the ADR"). The ADR quotes the applied text verbatim. The next-gen direction paragraph is untouched.
- Not applied: §5.3 (`worker_contract.md`, epic child 5, `docs/engine/**`) and §5.4 (Mode 5 pointer, architecture-planner-u24).
- Gate: the ticket's "after ubuntu's docs batch" gate covered the docs/architecture/kernel_concurrency file. This change does not edit that file,
  and docs-as-review-source PR 1 landed (#859), so the gate does not block.

## Test Summary
Doc only. `validate_frontmatter.py` passes on the ADR, this ticket and its three artifacts. `done_checker_static.py` passes. The five Scope points
were checked against the ADR text by hand (AC1): kept one writer (Decision 1), relaxed only for Collection under the profile (2), default
unchanged (3), determinism rule (4), why it reopens (5). Known gap: `make knowledge-index-update` was not run (the search model's load runs
out of memory on this host).

## Files Changed
- docs/architecture/distributed_workers_adr.md (moved from docs/plans/architecture/distributed_workers_adr_amendment_draft.md, rewritten as accepted)
- docs/architecture/system_overview.md
- docs/architecture/devops_plan_amendment_proposal.md
- agent-working/tickets/todos/distributed-workers-experiment/SEQUENCE.md
- this ticket, its stored artifacts, docs/REGISTRY.yaml, agent-working/agent-monitoring/

## Completion Summary
DONE. The owner accepted the design with this amendment (#715 6777076537). AC1: merged in `docs/architecture/**` with the five points, citing
#715 6731714291 (in Context and Decision 5). AC2: Decision 5 and §5.4 state that the owner's experiment choice replaces the Mode 5 reopen condition.
AC3: the devops amendment's bullet now reads "one writer and a single replica", which stays true. Known gap: the search index was not refreshed.
