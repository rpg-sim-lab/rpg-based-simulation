---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, engine, determinism, planning]
---

# ADR (DRAFT): the kernel/logic phase contract as the engine's direction

**Authored as DRAFT for lead-planner's review and adoption.** Authorship and the decision stay with lead-planner. This text is a
proposal, not a recorded decision.
- The owner had it drafted now (#715 6735920310, "Draft both ADRs now (Recommended)") while the ubuntu seat is away.
- Written by architecture-planner-u24 for `TCK-20261109-NEXT-GENERATION-ENGINE-ADR`, child 0 of
  `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`.
- Nothing is implemented.
- `system_overview.md`, `kernel_concurrency_design_philosophy.md` and the `docs/engine` contracts are in ubuntu's docs batch and are
  **not edited** here. "Proposed amended text" quotes what would change.

**Companion:** the distributed-workers ADR amendment draft (`docs/plans/architecture/distributed_workers_adr_amendment_draft.md`, on
branch `architecture-distributed-workers-epic`).
- Both touch the "one process" decision, and they carry the **same proposed `system_overview.md` bullet**, word for word. This ADR
  adds nothing to that bullet, because its serial and parallel executors stay in-process.
- They are separate ADRs because the tracks and gates differ: an experiment, and a direction. Lead-planner may combine them.

## Status

DRAFT. Proposed by architecture-planner-u24, 2026-11-09. To be decided by lead-planner, then accepted by the owner.

## Context

- **The investigation:** `docs/plans/architecture/next_generation_engine_feasibility_review.md` (§2, §2a, §5, §8a). It is
  code-derived on `main` `e755dc3d1`.
  - Resolution (`pipeline.py:136-444`) is one fold over a shared `StateUpdate`.
  - Its hot steps mostly compute per entity from tick-start state plus the entity's own entry.
  - The true ordering sits in a few chains.
  - RNG is keyed (`rng.py:65-105`).
- **Owner decisions** (#715 6735575831):
  - Level A by default;
  - both scaling dimensions, with the world farm first;
  - the split after M1, with an observe-only audit alongside it;
  - the depth rule kept;
  - a separate epic.
- **Delivery** (same comment): trunk, additive stages behind the existing selection; an equivalence test in every stage PR; `src/engine`
  stages sequenced by rpg-planner; spikes never merged.
- **Decisions in force:**
  - `system_overview.md` (one process, one writer);
  - C-10, "Resolution stays serial" (`performance_optimization_decisions.md`; reopened only for evaluation under PERF-M6-T05, Gate B);
  - PERF-D1 and PERF-D2 (DET-PORT tiers);
  - C-14 (sub-phase declarations are "not a presumed step toward concurrency").

## Decision

1. **Direction.** RPG logic runs as phases behind an explicit contract, and the kernel owns the plan, ordering, merge and commit.
   Executors are swappable. Today's serial order is the **first executor and the reference**.
2. **One writer is kept**, and so is one process. Multi-host is outside this ADR, reachable only through the recorded Mode 5 path.
3. **Level A by default:** identical results to today's engine. A Level B change (a versioned change of meaning) is its own owner
   decision, with an `intentional_divergences.md` entry and a new determinism tier beside PERF-D2.
4. **Delivery.** Trunk, additive stages behind the existing selection. The current path stays untouched and selected as today until
   equivalence is proven. Every stage PR carries the equivalence evidence of clarification 14. `src/engine` stages are sequenced by
   rpg-planner around M1. Spikes are never merged.
5. **The contract has four layers:**
   - (1) immutable tick-start state;
   - (2) a view per step: tick-start state plus exactly the earlier deltas the step declares;
   - (3) compute, which returns a typed delta and writes nothing else;
   - (4) merge and commit, done by the kernel: per-field rules in commit-key order, then the existing validate and single-writer apply.
   A step that needs sliding state declares it.
6. **Distributed readiness is a compatibility check only** (feasibility review §8a). This ADR includes no remote scheduling, no
   multiple writers and no multi-host work.
7. **The Gate B question (stage 5).** This ADR does **not** reopen C-10. It names the evidence that would justify opening the
   PERF-M6-T05 evaluation for a parallel executor:
   - child 2's access audit;
   - the contract-spec (child 4) merge rules;
   - a stage 3 prototype proven at Level A under the serial executor;
   - a Level A proof under a parallel executor that meets clarification 18;
   - a measured cost (no speed claim without data).
   Perf-planner proposes the T05 evaluation; lead-planner records it. Until then, stage 5 stays uncut.
8. **Fit with the distributed-workers experiment.** It shares the explicit-executor seam (`kernel.py:193-198`) and changes neither
   that seam nor the experiment's scope.

## Correctness clarifications

Each answer gives the rule, how Level A holds, and an evidence class:
- **G**, guaranteed by the contract;
- **S**, established by static inspection;
- **T**, supported only by runtime tests.

The detail is child 4's.

| # | Clarification | Rule | Level A argument | Class |
|---|---|---|---|---|
| 1 | Sliding state (`action_routing`, ascending id) | a declared **ordered** step; units run in ascending entity id; interaction groups only if proven to give the global order | the same order as today, by construction | G (order); T (groups, if used) |
| 2 | Evolving state within a tick | the layer-2 view holds exactly the declared earlier deltas; no step moves to tick-start state where today it reads this tick (for example the combat witness tier) | the view equals what the fold offers today at that point | S + T (audit) |
| 3 | Order-sensitive merges (sentiment clamp; staleness → contradiction; trust/grudge float sums; witness fold; whole-object cognition replace; list concatenation and float addition) | each field gets a declared merge rule that **replays today's order**: today's list order is the commit-key order of its producers; cognition becomes sub-field deltas applied in today's step order | reproducing today's order is the requirement; any rule that does not is a Level B change with its **own versioned decision** | G (rule declared); T (equivalence) |
| 4 | Contention (JOIN_PARTY on one offer; resource reservations; movement claims) | for each contended key, a declared winner rule equal to today's loop order (iteration over `state.entities` for JOIN_PARTY; sorted id for reservations; selection order for claims), and conflicts detected by the key | today's winner by construction; any other rule is Level B, with its own decision | G (detection); T (equivalence) |
| 5 | Spawn-id allocation | spawn requests are collected, sorted by today's issue order, then allocated from the counter; tiles in the same order | the same ids, tiles and RNG keys | G + T |
| 6 | The death chain | a declared ordered chain (action_routing → near_death_hardening → lifecycle → transfers); each death and transfer keyed by entity id and applied once | the same order; once-only by key | G (once-only); T |
| 7 | Hidden mutations of tick-start state | tick-start state is immutable during refine; timeline events, claims, `route_plans`, spatial and movement caches and the strategic flag move to deltas or to kernel- or phase-owned stores. The cooperation `< 150` gate reads the step's own pending events | the same values at each read point | S (inventory) + T (audit) |
| 8 | Process-global state and content identity | content is loaded once per process from a declared path (not the cwd), and fingerprinted; caches are owned per world or keyed by content fingerprint, not `id()` | the same content gives the same reads | G (fingerprint check); S |
| 9 | RNG key hygiene (XOR collisions past about 65k ids; quest keys without a building id) | keep today's keys under the contract; the repair (hashing the key tuple; adding building ids) is **its own versioned decision**, never in a contract PR | unchanged keys means unchanged draws | G (keyed draws); the repair is Level B |
| 10 | Event ids and order | event order equals today's emit order under the commit key; `uuid4` ids are **not** in hashed state (static check, 2026-11-09), so event-stream comparisons exclude the id. Deriving ids (tick, source, seq) is its own versioned decision | the state digest is unaffected; the stream compare excludes ids | S |
| 11 | Exception and failure semantics | a raised unit gives a FAILURE no-op per entity, recorded, as today; it is **never recomputed as an infrastructure failure**; a lost unit (transport, timeout) is recomputed from the same inputs; if a recomputed result differs from a late or remote one, the run fails loudly | identical to today for raised units; recompute is a pure function | G (classification); T |
| 12 | Floating point and platform | reductions keep today's order (clause 3); any change of order or value type is its own versioned decision; claims stay within PERF-D2 (one DET-PORT-1 row per executor, no DET-PORT-2) | same order, same floats | G (claim scope); T |
| 13 | When a step is parallel-safe | all of: static side-effect inspection; child 2's runtime audit; dependency-sensitive scenarios (deaths, contention, spawns, the JOIN_PARTY collision); hidden-mutation and global detection; **fail-loud on undeclared access** (modelled on `PacketFieldMissingError`); then clarification 18 | runtime evidence alone never makes a step safe | S + T; fail-loud is G |
| 14 | Evidence per stage PR | field-by-field content compare (primary); `flat-sha256-v3`; `TICK_END` trail; existing behaviour evidence; failure behaviour. A hash alone is insufficient (digest gaps, `TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ`) | — | T |
| 15 | Guaranteed, inspected or tested | every property in the contract and the spec carries G, S or T; a T property is never stated as a guarantee | — | — |
| 16 | Versioned contracts and replay | the contract version is in the run manifest; a contract change is a versioned decision; replay from declared state and inputs stays reproducible; distributed readiness is compatibility only | — | G |
| 17 | Task identity scope | task id = (run id, replay session or attempt, tick, step, unit). Dedup, retry and late-result rejection match within the same run and attempt only, so a result from another run or an earlier replay is rejected | ids cannot collide across concurrent worlds or replays | G |
| 18 | Independent determinism evidence | the proof matrix varies `PYTHONHASHSEED` (several values; every harness pins 0 today), arrival order (permuted), worker counts (1, 2 and 4), and failures (exceptions, lost or late units), with a full-state compare. A DET-PORT-1 row counts only if it passes all of these | — | T |

## Proposed amended text (not applied; for lead-planner to place)

**`docs/architecture/system_overview.md`, first bullet of "What is deliberately not distributed"** (shared with the companion ADR,
word for word):

> - **The engine has one writer.** That is a choice, not a gap: determinism and replay depend on it
>   (`docs/architecture/kernel_concurrency_design_philosophy.md`). Every result is validated, sorted and applied by the kernel alone.
>   **By default the engine is also one process.** One recorded exception exists: the opt-in distributed-workers experiment may run
>   the Collection pool in a separate container (ADR amendment, #715 6731714291), and it must give results identical to the
>   sequential run. Scaling is per run (many seeds in parallel), not per tick.

**A new paragraph after that list** (this ADR):

> **Execution kernels are swappable behind a phase contract** (ADR, #715 6735575831). RPG logic declares what each step reads and
> writes and returns typed deltas, and the kernel owns order, merge and commit. Today's serial order is the reference executor. Any
> other executor must give identical results, and may run Resolution in parallel only after the Gate B evaluation (C-10, PERF-M6-T05).

**`docs/architecture/kernel_concurrency_design_philosophy.md`, Part 2:** unchanged by this ADR. The sentence "Only COLLECTION runs
work in parallel" stays true until a Gate B decision. If one is made, that decision amends this sentence.

**`docs/architecture/performance_optimization_decisions.md`, C-10:** unchanged. Add a pointer: "Evidence route for the T05 evaluation:
next-generation engine ADR, Decision 7."

## Consequences

**Allowed once this is accepted:**
- child 2, the access audit, under rpg-planner's conditions;
- child 4, the contract spec;
- stages 3 and 4, cut by rpg-planner after M1.

The current engine stays the reference and stays selected throughout.

**Not allowed by this ADR:**
- parallel Resolution (Gate B);
- multiple writers, partitioned ownership, PDES or optimistic rollback, multi-host;
- adopting Ray, Dask or Spark.

**Costs:**
- every Resolution phase signature changes over time, behind the serial executor;
- the merge rules are the hard part (clarifications 3 to 7).

**Risks:**
- a within-world speed-up is unproven in CPython;
- the digest's blind spots, which is why the content compare is primary;
- whether the dependencies support free threading is unknown.

## Related

- `TCK-20261109-NEXT-GENERATION-ENGINE-ADR` (the ticket this drafts; its scope holds the clarification sources and the cross-check
  table)
- `docs/plans/architecture/next_generation_engine_feasibility_review.md`
- `docs/architecture/performance_optimization_decisions.md` (C-10, C-14, PERF-D1, PERF-D2)
- `docs/engine/deterministic_execution.md`
