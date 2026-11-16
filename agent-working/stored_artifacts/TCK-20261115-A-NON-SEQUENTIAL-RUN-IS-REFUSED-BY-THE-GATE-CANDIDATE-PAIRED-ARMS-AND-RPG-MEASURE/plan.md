---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE
phase: done
date: 2026-11-15
tags: [testing, determinism, observability]
---

# TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE: plan

## Order
1. `RunConditions.worker_manager: Optional[str] = None`; `kernel.py` writes the class of the manager behind a non-sequential executor (`None` when the executor is `LocalSequentialExecutor`) in the one existing `update_manifest` call. Rules from #918: typed, Optional, outside hashed state and events.
2. `rpg_gate_run.run` writes `runner: {verdict, differences}` from the run's manifest (`pinned_runner.classify_manifest`); `pool` writes PINNED only if every pooled document is. `rpg_gate_candidate._load` refuses a document with no `runner` or a verdict other than PINNED.
3. `arm_child` writes `runner: "PINNED"`; `paired.refuse_non_pinned` (local, `--collected`, repeat and neutral paths); `paired_arms.assemble` refuses a result whose document is not `runner: PINNED`.
4. Docs: `docs/engine/kernel.md` line, INFRA-440 text and evidence. The design §8 row 6 and epic child-6 lines are NOT edited here: their owners add them (testing-planner, 2026-11-15).

## Out of scope (kept)
No remote manager, no mode enum, no classifier change, no baseline re-record, no evidence run (owner #715 6889952914 item A, "Small, no runs").

## Harness hash
`rpg_gate_run.py` is a `_HARNESS_SOURCES` file, so `harness_hash` moves. The PR states it; the baseline drift comparison treats it as declared.
