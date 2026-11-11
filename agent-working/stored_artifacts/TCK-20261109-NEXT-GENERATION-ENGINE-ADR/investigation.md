---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-NEXT-GENERATION-ENGINE-ADR
tags: []
---

# investigation - TCK-20261109-NEXT-GENERATION-ENGINE-ADR

The investigation is `docs/plans/architecture/next_generation_engine_feasibility_review.md`, by architecture-planner-u24. It is
code-derived on `main` e755dc3d1.

lead-planner re-verified the draft's citations at `main` 1fb40ac76:
- the executor seam is at `src/engine/kernel.py:193-198`; results are validated at `:556` and sorted by commit key at `:580`;
- `PacketFieldMissingError` is at `src/core/worker_protocol.py:15`;
- the RNG key is the XOR layout in `src/platform/rng.py:65-105` (`entity_id << 16` reaches the tick bits past 65,535 ids, as row 9
  says);
- the cooperation `< 150` gates are at `src/domains/cooperation/phase.py:110` and `:158`;
- the measurement harnesses pin `PYTHONHASHSEED=0` (`tools/rpg_measure/paired.py:102`, `tools/perf/rerun_baselines.py:427`). Three
  subprocess hash-seed tests already vary it; they are named in row 18;
- row 10: uuid4 is minted at `src/observability/events.py:56` (the `SimulationEvent` envelope). `CausalMemoryEntry.event_id`
  (`src/core/cognition.py:237`) is derived as `combat_loss_{tick}_{subject}` (`src/engine/pipeline.py:151`), and `CausalMemory`
  hashes only `entries_count` and `capacity` (`cognition.py:252-256`);
- the C-10 and C-14 wording (`performance_optimization_decisions.md`) and "Only COLLECTION runs work in parallel"
  (`kernel_concurrency_design_philosophy.md:47`) are unchanged.

Side finding (lead-planner-u24): causal-memory content is not in the digest. It is a digest blind spot, which supports the ADR's rule
that the content compare is primary.
