---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-EPIC-NEXT-GENERATION-ENGINE
phase: open
date: 2026-11-09
tags: [architecture, engine, determinism, performance, planning]
---

# TCK-20261109-EPIC-NEXT-GENERATION-ENGINE

## Title
Separate the kernel from the RPG logic behind an explicit phase contract, so execution kernels can be swapped (serial first, then a
measured parallel one), with exact legacy equivalence and the current engine kept as the reference.

## Status
EPIC_SCOPED

## Tier
epic

## Type
refactor

## Priority
P2

## Request Summary
The owner's longer-term aim, from two owner-shared external reviews (`tmp/distributed_workers_experiment_design_review_2.md`,
`tmp/next_generation_engine_feasibility_review_review.md`, untracked) and the owner's own idea: split the kernel from the RPG logic so
the kernel can be swapped, from today's approach up to fully distributed. The investigation is
`docs/plans/architecture/next_generation_engine_feasibility_review.md`.

Owner decisions (#715 6735575831, "Confirm all five (Recommended)"):
- Q1 (a): a separate strategic epic now. It authorises **no implementation**.
- Q2 (a): Level A, exact legacy equivalence, by default. Each Level B (versioned semantic) change is its own owner decision.
- Q3 (c): both scaling dimensions, with many worlds (the world farm) first.
- Q4 (a): the kernel/logic split comes after M1. The observe-only dependency audit may run alongside M1.
- Q5 (a): the depth rule (#715 6731764470) is kept. Perf items come in only on a measured hard issue; there is no
  compile-the-hot-loops stage.

Delivery model (same comment, "Trunk, additive stages (Recommended)"):
- no long-lived integration branch;
- each stage lands on `main` as small additive PRs behind the existing selection, with the current engine path untouched and
  selected as today, not switched until equivalence is proven;
- every stage PR carries an equivalence test;
- stages that touch `src/engine` are sequenced by rpg-planner around M1;
- throwaway spike branches are allowed, never merged.

## Scope
Scoping only. Nothing is built under this epic until child 0 (the ADR) is accepted and each child's own gate passes.

**What the investigation found** (feasibility review §2, §2a, §5; code-derived on main `e755dc3d1`):
1. Resolution (`src/engine/pipeline.py:136-444`) is one fold over a shared `StateUpdate`. Its hot steps (combat_engagement,
   cooperation, fused_strategic_pass) mostly compute per entity from tick-start state plus the entity's own entry. Their serial order
   comes from the fold, not from the mechanics.
2. Some exceptions are real:
   - cooperation's JOIN_PARTY contention on the offerer's contract, and its in-place `timeline.append` on tick-start state;
   - combat's witness fold;
   - the true chains: action_routing's sliding state, movement and occupancy, resource reservations, the death chain, spawn-id
     allocation, clamped faction-sentiment accumulation, and last-writer-wins staleness → contradiction.
   No step is claimed parallel-safe yet.
3. RNG is keyed, not streamed (`src/platform/rng.py:65-105`).
4. A one-world-per-process farm already exists in the gate, paired and capacity tooling.

**Children** (the feasibility review's §12). Children 0, 2 and 4 are filed here; the others are cut by their owning planners:

| # | Child | Owner | Filed | Gate |
|---|---|---|---|---|
| 0 | `TCK-20261109-NEXT-GENERATION-ENGINE-ADR` | lead-planner (ubuntu); may be combined with the distributed-workers ADR (`TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`), which touches the same "one process" decision | yes | the ubuntu lead reachable; ubuntu's `lead-docs-review-source` batch landed |
| 1 | stage 0: re-measure after H1 (#751) and H2 (#771) on a quiet host; per-phase ms with denominators; Resolution profile incl. `fused_strategic_pass`. Measurement only | perf-planner | to be cut by perf-planner | none |
| 2 | `TCK-20261109-NEXT-GENERATION-ENGINE-ACCESS-AUDIT`: stage 1, declarations plus a shadow access audit; observe-only, off by default, hash-neutral; rpg-planner's conditions (2026-11-09) in the ticket | architecture's implementer, reviewed by rpg-planner (the implementer's write scope must grow first) | yes | design now; code after child 0, after the three RPG heads are pushed, in a gap rpg-planner names |
| 3 | world farm: a Redis stream per world (`SIM_STREAM_NAME`), unique lab run ids (`src/lab/orchestrator.py:171-174`), process-safe ledger appends, N worlds per host measured | platform-planner; perf-planner for the measurement | to be cut by platform-planner | none (first in priority) |
| 4 | `TCK-20261109-NEXT-GENERATION-ENGINE-CONTRACT-SPEC` | architecture | yes | child 0 accepted; children 1 and 2 results |
| 5 | stages 3 to 5: serial prototype (`fused_strategic_pass` slice), migration, measured parallel executor | rpg-planner; perf-planner for the executor | **not cut** | M1 complete; child 4 accepted; for the executor, Gate B (C-10, PERF-M6-T05) |

**Decisions this runs into** (feasibility review §10):
- `docs/architecture/system_overview.md` "What is deliberately not distributed": the single writer is kept, so this epic does not
  change it. Multi-host is outside this epic; the Mode 5 reopen path is recorded.
- C-10 / Gate B (PERF-M6-T05): parallel Resolution, stage 5 only. The question goes in child 0's scope.
- PERF-D2 tiers: an executor's claim is a DET-PORT-1 row; any Level B change needs a new tier.
- Section F, C-14: declarations are fine as declarations; using them for concurrency is the Gate B question.

## Out of Scope
- Any implementation before its gate; stages 3 to 5 are not cut.
- Distributed writers, partitioned state ownership, PDES or optimistic rollback, multi-host, and adopting Ray, Dask or Spark, each
  without a separate architectural justification.
- Changing the distributed-workers experiment (`TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`). Its executor seam is the one
  point of contact, and child 4 states how they fit.
- Mixing E's refactor into M1's PRs.
- Option A perf work, except on a measured hard issue (depth rule).

## Acceptance Criteria
1. Child 0 is accepted before children 2 and 4 start, and before anything under child 5 is cut.
2. Every stage PR is additive on `main`, behind the existing selection: the current path is untouched and selected as today, and
   existing gate and paired hashes are unchanged.
3. Every stage PR carries a Level A equivalence test: the field-by-field content compare (primary), `flat-sha256-v3`, the
   `TICK_END` trail, and, for an executor, worker-count and arrival-order independence.
4. No step is called parallel-safe before child 2's access audit and a Level A proof under a parallel executor both pass.
5. Each child records its cost and what it leaves out.

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (separate; shares the executor seam and the "one process" decision)
- TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE (open; the prototype slice's step)
- TCK-20261026-COMBAT-ENGAGEMENT-CONSIDER-PER-PAIR-COST-AFTER-H1 (open)
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ (open; why the content compare is primary)
- TCK-20261031-SIMULATION-EVENT-ID-IS-A-RANDOM-UUID (open; event ids for the contract)

## Related Docs
- docs/plans/architecture/next_generation_engine_feasibility_review.md
- docs/plans/architecture/engine_execution_modes_proposal.md
- docs/architecture/system_overview.md
- docs/architecture/kernel_concurrency_design_philosophy.md
- docs/architecture/performance_optimization_decisions.md
- docs/engine/deterministic_execution.md
- docs/plans/design_enhancement/subphase_domain_contracts_epic.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/engine/pipeline.py
- src/engine/kernel.py
- src/core/updates.py
- src/platform/rng.py
- src/domains/cooperation/phase.py
- src/domains/combat_engagement/phase.py
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- A within-world speed-up is unproven in CPython. E's value (testable phases, a swappable kernel) does not depend on it.
- Whether the dependencies support free-threaded CPython is unknown (stage 5's question).

## Implementation Notes
Filing rides in a later implementation PR on this track (owner rule, #715 6697748243), not a PR of its own.

## Test Summary
Not applicable at epic level.

## Files Changed
- agent-working/tickets/todos/next-generation-engine/
- docs/plans/architecture/next_generation_engine_feasibility_review.md

## Completion Summary
Open.
