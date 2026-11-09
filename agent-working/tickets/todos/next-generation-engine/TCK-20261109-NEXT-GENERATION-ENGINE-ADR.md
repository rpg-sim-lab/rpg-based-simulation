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
6735575831. Lead-planner-u24 carries it over together with `TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`. **Both ADRs touch the
same "one process" decision** (`system_overview.md`). Ubuntu review R1 ruled a split: this ADR proposes no edit to that bullet,
and the distributed ADR carries the bullet's edit alone.

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

### Correctness clarifications the ADR must answer

The owner relayed the external AI's final verdict on 2026-11-09, via lead-planner-u24: "Approve direction and staged plan. Require
targeted correctness clarifications in the contract ADR." **The verdict's own list was not provided.** The list below is assembled
from the two reviews the owner did share (both untracked):
- `tmp/next_generation_engine_feasibility_review_review.md` §3.1 to §3.3, §5 and §8;
- `tmp/distributed_workers_experiment_design_review_2.md` §7.2, §9 and §14.

Each item is matched to the code facts in the feasibility review. If the verdict's own list differs, it replaces this one.

For each item, the ADR states:
- the rule;
- how the rule reproduces today's result exactly (Level A);
- whether architecture guarantees it, or only a test establishes it.

The detail goes to child 4.

1. **Sliding state.** `action_routing` runs actors in ascending id, and later actors see earlier kills (`actions.py:197-350`). The
   contract must express this as a declared, ordered step: does it run as a whole, or as ordered interaction groups (`:263`)? If
   groups are used, the ADR must show the groups reproduce the global ascending-id result. (Reviews: 3.2; review_2 §7.2.)
2. **Evolving state within a tick.** The per-step view is tick-start state plus the earlier deltas the step declares. The ADR must
   say how a step's view is built, and that no step silently moves onto tick-start state when today it reads this tick's deltas (for
   example, the combat witness tier reading action_routing's `CombatUpdate`s). (3.2.)
3. **Order-sensitive merges.** Each needs a rule that reproduces today's order exactly. If it does not, it is a Level B change,
   with its **own versioned owner decision**; it is never folded into a contract PR:
   - (a) the faction-sentiment clamped accumulation, `max(-1, min(1, prior + delta))` in list order (`apply.py:406-434`);
   - (b) staleness → contradiction, where last writer wins (`pipeline.py:395-404`);
   - (c) trust and grudge float sums across groups (`cooperation/phase.py:252-265`);
   - (d) the combat witness fold, in `entity_updates` insertion order;
   - (e) the whole-object replace of `cognition_bundle_set` (`updates.py:799`);
   - (f) list concatenation (`intent_results`, `world_events_add`) and float addition in `EntityUpdate.merge`.
   (3.1; review_2 §9, conflict handling and floating point.)
4. **Cross-entity writes and contention.** Covers:
   - JOIN_PARTY writing the offerer's contract promotion, where two joiners in one tick collide (`cooperation/phase.py:175-196`);
   - resource reservations in sorted id order (`economy.py:49-57`);
   - first-come movement claims (`movement.py:188-204`).
   The ADR must state who wins, why that equals today's result, and how a conflict is detected. Any contention rule that differs
   from today's loop order is a Level B change, with its own versioned decision. (3.1; review_2 §9.)
5. **Id allocation.** Spawn ids come from one sequential counter, and tiles are first-come (`world_systems/generator.py:96-119`).
   RNG keys and tiles derive from that id. The ADR must define deterministic allocation (for example, sort requests, then allocate)
   equal to today's order. (review_2 §9, task identity.)
6. **The death chain.** action_routing → near_death_hardening → lifecycle → death transfers and inheritance
   (`pipeline.py:405-409, 570-578`), with lifecycle re-running its own transfers. The ADR must state its ordering, and that each death
   and transfer applies exactly once. (3.1.)
7. **Hidden mutations of tick-start state.** Covers:
   - cooperation's `timeline.append`, which the `< 150` gates read back in the same pass;
   - movement's claims and occupancy cache;
   - `route_plans` and spatial caches set through `object.__setattr__`;
   - the strategic cache flag;
   - the `movement_cache` invalidation.
   The ADR must state where these live under the contract, and that tick-start state is immutable during refine. (3.1.)
8. **Process-global state and content identity.** Registries, the `behavior_consumers` catalog (auto-loaded from a cwd-relative path),
   the terrain cache and id-keyed caches. The ADR must state how a unit gets content: loaded once per process, or owned per world. It
   must also state how identity is checked (a content fingerprint). (3.1; review_2 §14, content identity and initialization.)
9. **RNG.** Draws are keyed, which is guaranteed today (`src/platform/rng.py:65-105`). The keys need repair:
   - XOR composition collides once entity ids pass about 65k;
   - quest keys lack a building id.
   The fix moves pinned hashes, so it is **its own versioned decision** and never rides a contract PR. Draws must never depend on
   the worker, the process count or completion order. (review_2 §9, randomness.)
10. **Event ordering and identity.** Covers:
    - `uuid4` event ids (`observability/events.py:56`). Checked 2026-11-09 [C, static only]. They do **not** enter hashed state:
      - `recent_world_events` holds `WorldEvent`s (`world_emergence/schema.py:64`), which have no id field;
      - the `source_event_id`s stored in state are deterministic strings (`world_emergence/services.py:196,232`);
      - the scar path that takes an event id (`world/consequences.py:62-75`) has no live caller found;
      - `CausalMemoryEntry.event_id` (`src/core/cognition.py:237`, ubuntu review R3) is derived, `combat_loss_{tick}_{subject}`
        (`src/engine/pipeline.py:151`, read by `src/domains/memory/phase.py:101`), not a uuid, and is not hashed: `CausalMemory`
        hashes only `entries_count` and `capacity` (`cognition.py:252-256`), reached through the entity's `cognition`
        (`src/core/state.py:985`, `src/engine/checkpoint.py:151`). Rechecked on `main` `1fb40ac76`. The uuid4 minting is
        `src/observability/events.py:56`, the `SimulationEvent` envelope sent to the recorder, never `AuthoritativeState`.
      They **do** make the observability event stream unreproducible, so any comparison of event streams must exclude the id, or the
      contract must derive it (from tick, source and seq). Changing the id derivation is its own versioned decision;
    - the ordered `world_events_add` and `recent_world_events` in hashed state;
    - the recorder's sampling counter, which depends on emit order (`event_recorder.py:214`).
    The ADR must define event ids and order under the contract. (review_2 §9, event ordering.)
11. **Exception and failure semantics.** Today a unit that raises gives a FAILURE no-op per entity. The ADR must say:
    - that this is kept per unit;
    - how an infrastructure failure differs from a computation exception;
    - that a lost unit is recomputed, never dropped, and never changes the outcome;
    - that **recompute never hides a real computation error**. A unit that raises is a computation failure, and is handled as today
      (a FAILURE no-op, recorded). It is never retried or recomputed as if the infrastructure had failed. If a recomputed result
      differs from a late or remote one for the same task, the run fails loudly instead of choosing one.
    (§5; review_2 §9, worker failures; §14 item 5.)
12. **Floating point and platform.** Order-dependent float reductions, and the DET-PORT tiers. The ADR must state:
    - which reductions get a fixed order, or integer or fixed-point values. A reduction order or value type that differs from today's
      is its own versioned decision;
    - that the claim scope stays within PERF-D2 (a DET-PORT-1 row per executor; no DET-PORT-2 claim).
    (review_2 §9.)
13. **When a step counts as parallel-safe.** Declared read/write sets are necessary, not sufficient. A runtime audit sees only the
    branches that ran, so it can never prove a step safe on its own. The ADR must name the evidence, in all of these forms:
    - static inspection of the step's side effects: writes to state, `object.__setattr__`, globals, caches;
    - child 2's runtime access audit;
    - dependency-sensitive scenarios that exercise the rare branches (deaths, contention, spawns, the JOIN_PARTY collision);
    - hidden-mutation and global-access detection;
    - **fail-loud on undeclared access** under the contract (the packet's `PacketFieldMissingError` is the model,
      `worker_protocol.py:110-116`);
    - then a Level A proof under a parallel executor (item 18).
    (3.1; §5.)
14. **The evidence standard** for every stage PR:
    - the field-by-field content compare, which is primary because of the digest's known gaps
      (`TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ`);
    - the current proof scheme (`PROOF_DIGEST_SCHEME`);
    - the `TICK_END` trail;
    - the existing behaviour evidence;
    - schedule and worker-count independence;
    - exception semantics.
    A matching hash alone is insufficient. (§5.)
15. **Guaranteed, inspected or tested.** The ADR must label each property with one of three evidence classes:
    - **guaranteed by the contract:** keyed RNG, a unique commit key, the duplicate check, a sorted digest, fail-loud on undeclared
      access;
    - **established by static inspection:** for example "uuid4 ids do not enter hashed state" (item 10), and "this step writes only
      its own key";
    - **supported only by runtime tests:** the executor equivalence cases, arrival permutation, the frozen-view cache, the access audit.
    A runtime-only property is never stated as a guarantee. (§5; review_2 §9.)
16. **Versioned contracts and replay.** The contract version is recorded in the run manifest, and a contract change is a versioned
    decision. Replay from declared state and inputs must stay reproducible. Distributed readiness (feasibility review §8a) is a
    **compatibility check only**, with no multi-host, remote-scheduling or multi-writer work. (3.3; review_2 §9, replay and recovery.)
17. **Task identity namespace.** A task id (tick, step, unit) is unique only inside one world's run. Several worlds, runs and replays
    execute at once (the world farm; the gate's subprocesses). So the ADR must scope the id as (run id, replay session or attempt,
    tick, step, unit). Retries, dedup and late-result rejection then match only within the same run and attempt: a late result from a
    different run, or from an earlier replay, is rejected, never merged.
    - Run ids already exist (`src/engine/run_identity.py:20`).
    - Today's `ProtocolValidator` dedup works per batch only (`protocol_validator.py:41-50`).
    (Consolidated clarification 3; review_2 §9, task identity.)
18. **Independent determinism evidence.** The proof matrix varies these independently:
    - **`PYTHONHASHSEED`:** several values, not only the pinned 0. The measurement harnesses pin 0 (`rpg_gate_harness.py:158`,
      `paired.py:102`), which can hide iteration-order dependence. Reuse the existing subprocess hash-seed tests as the pattern:
      `tests/unit/engine/test_set_order_follows_no_hash_seed.py`, `tests/unit/domains/faction/test_squad_group_id_hashseed.py` and `tests/unit/domains/perception/test_filter_ids_hashseed.py`;
    - **scheduling:** permuted arrival order;
    - **worker counts:** 1, 2 and 4;
    - **state:** a full-state, field-by-field compare;
    - **failure behaviour:** exceptions, and lost or late units.
    Only DET-PORT-1 rows that pass under all of these count. Hash-seed variation is a **new** requirement: no executor proof varies
    it today. (Consolidated clarification 4; §5.)

**Cross-check against the external AI's consolidated clarifications** (pasted by the owner via lead-planner-u24, 2026-11-09). Per
that input, there is no separate canonical list. The 16 points are kept, and only genuine gaps were added.

| Consolidated issue | Status | Where |
|---|---|---|
| 1. No silent Level A violations (the RNG-collision fix, event ids, float reduction order, contention semantics, each its own versioned decision); verify how uuid4 ids enter hashed state | **Accepted.** Partly covered already; the wording is sharpened. The uuid4 check found the ids are **not** in hashed state [C, static], but they make event streams unreproducible | items 3, 4, 9, 10, 12 |
| 2. No overclaim from dynamic auditing (contract vs static vs runtime evidence; static inspection, runtime audit, dependency-sensitive scenarios, mutation and global detection, fail-loud) | **Accepted.** Mostly covered; the evidence forms and three evidence classes are now explicit | items 13, 15 |
| 3. Task identity namespace | **Accepted, a genuine gap** | new item 17 |
| 4. Independent determinism evidence (hash seeds, scheduling, worker counts, full state, failures) | **Accepted.** Hash-seed variation was a **genuine gap**; the rest was already covered | new item 18 (folds in 13 and 14) |
| C-3. Local recompute must not hide a deterministic computation error | **Accepted, a clarification** | item 11 |
| C-8. Distributed-ready means compatibility only | **Already covered** (feasibility review §8a, scope point 6); restated | item 16 |

**Cost:** one doc session, no runs. **Leaves out:** the contract's detail (child 4), code, measurement.

## Out of Scope
- Code; the merge-rule spec in detail (child 4).
- Distributed writers, partitioning, PDES, multi-host.

## Acceptance Criteria
1. The ADR records points 1 to 8, citing #715 6735575831, and answers each of the 18 correctness clarifications with a rule, its Level A argument, and whether it is guaranteed or tested.
2. It keeps every decision it does not change, and names every one it changes with its owner.
3. The owner accepts it.

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (parent)
- TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT (same "one process" decision; kept separate, review R1)

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
- It depends only on ubuntu's review and the owner's acceptance (ubuntu review R5). Ubuntu's docs batch (row A) touches different
  lines and is not a gate. On adoption, ubuntu writes `docs/architecture/next_generation_engine_adr.md` from a lead branch after the
  owner's yes; the feasibility review stays in `docs/plans/architecture/` (R6).

## Implementation Notes
Filed by architecture-planner-u24. The filing rides a later implementation PR (#715 6697748243).

## Test Summary
Doc only.

## Files Changed
None yet.

## Completion Summary
Open.
