---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE
phase: done
date: 2026-11-15
tags: [testing, determinism, observability]
---

# TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE: test_plan

| AC | Test |
|---|---|
| 1a | `tests/unit/tools/test_rpg_gate_candidate.py`: NOT_PINNED seed and pooled document refuse naming the document and difference; no `runner` refuses; `runner_header` and `pooled_runner` unit tests; `test_rpg_gate_harness.py`: every real document carries PINNED |
| 1b | `tests/unit/tools/test_rpg_measure_collected.py`: `refuse_non_pinned` direct (None, NOT_PINNED, wrong case, empty); collected compare refuses base, new and repeat; neutral refuses |
| 1c | `tests/unit/tools/test_paired_arms.py`: assemble refuses NOT_PINNED, missing field, non-object, missing arm document |
| 1d | `tests/unit/kernel/test_run_conditions_record.py`: arm_child refuses a build on `ConcurrentExecutionAdapter` with pinned governor/budget/flags, naming executor only |
| 2 | same file: threads kernel records `src.engine.worker_manager.WorkerManager`, sequential records None, and dropping the record leaves `CanonicalStateHasher.get_hash` equal |
| 3 | No run (owner item A). AC2's hash test is the proof. |
| 5 | existing kernel, rpg_gate, paired_arms, known_reds and baseline tests |
