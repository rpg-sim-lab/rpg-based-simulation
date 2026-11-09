---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ADR
phase: open
date: 2026-11-09
tags: [architecture, engine, determinism, planning]
---

# TCK-20261109-NEXT-GENERATION-ENGINE-ADR

## Title
ADR: the kernel/logic phase contract as the engine's direction, with one writer kept, Level A by default and trunk-additive delivery.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 0 of `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`. Author: lead-planner (ubuntu). Owner decisions and delivery model: #715
6735575831. It waits until the ubuntu lead is reachable; lead-planner-u24 carries it over together with
`TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`. **Both ADRs touch the same "one process" decision** (`system_overview.md`), so
lead-planner may combine them into one ADR.

## Scope
Record, as an ADR under `docs/architecture/`:
1. **Direction:** RPG logic is expressed as phases behind an explicit contract, and the kernel owns planning, ordering, merge and
   commit. Executors are swappable. Today's serial kernel is the first implementation and the reference.
2. **The single writer is kept.** The contract does not relax "one writer". Multi-host stays outside, reachable only via the Mode 5
   reopen path.
3. **Level A by default** (exact legacy equivalence). A Level B change is a separate owner decision, with an
   `intentional_divergences.md` entry and a new determinism tier beside PERF-D2.
4. **Delivery model:** trunk, additive stages, behind the existing selection; an equivalence test in every stage PR; `src/engine`
   stages sequenced by rpg-planner around M1; spikes never merged.
5. **The four contract layers** (feasibility review §5): immutable tick-start state; a per-step view with declared earlier deltas;
   compute returning a typed delta; merge and commit by the kernel. Sliding state is declared, not hidden.
6. **Distributed readiness** (feasibility review §8a) as a compatibility check, not as built scope.
7. **The Gate B question for stage 5:** parallel Resolution under C-10 / PERF-M6-T05 (`docs/architecture/performance_optimization_decisions.md`).
   Record whether this ADR opens the T05 evaluation, or names the evidence that would.
8. How it relates to the distributed-workers ADR, and the shared executor seam (`kernel.py:193-198`).

**Cost:** one doc session, no runs. **Leaves out:** the contract's detail (child 4), code, measurement.

## Out of Scope
- Code; the merge-rule spec in detail (child 4).
- Distributed writers, partitioning, PDES, multi-host.

## Acceptance Criteria
1. The ADR records points 1 to 8, citing #715 6735575831.
2. It keeps every decision it does not change, and names every one it changes with its owner.
3. The owner accepts it.

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (parent)
- TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT (same "one process" decision; may be combined)

## Related Docs
- docs/plans/architecture/next_generation_engine_feasibility_review.md
- docs/architecture/system_overview.md
- docs/architecture/kernel_concurrency_design_philosophy.md
- docs/architecture/performance_optimization_decisions.md
- docs/engine/deterministic_execution.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/pipeline.py
- src/engine/kernel.py

## Assumptions / Open Questions
- It is gated on ubuntu's `lead-docs-review-source` batch landing (#715 6720445592), as the distributed-workers ADR is.

## Implementation Notes
Filed by architecture-planner-u24. The filing rides a later implementation PR (#715 6697748243).

## Test Summary
Doc only.

## Files Changed
None yet.

## Completion Summary
Open.
