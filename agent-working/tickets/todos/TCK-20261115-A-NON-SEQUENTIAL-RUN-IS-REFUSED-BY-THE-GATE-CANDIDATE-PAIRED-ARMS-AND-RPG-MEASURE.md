---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE
phase: open
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE

## Title
A run on a non-sequential executor is refused by the gate candidate, the paired arms and rpg_measure, and its manifest says which worker manager it ran on

## Status
OPEN (owner approved filing and building: #715 6889947724 / 6889952914 item A; dispatched in the digest-light batch)

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
This is distributed-workers design §8 row 6 / §9 child 6 (`docs/plans/architecture/distributed_workers_experiment_design.md`; epic `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT` child row 6). Behaviour evidence comes only from the pinned sequential runner. Today, only some of the tools that produce evidence enforce that, and the rest rely on policy. #918 (TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE) already did most of the work:
- `RunConditions.executor` records the executor class.
- `tools/test_architecture/pinned_runner.py` classifies anything other than `LocalSequentialExecutor` as NOT_PINNED.
- `tools/rpg_measure/arm_child.py` calls `require_pinned`.

This ticket closes the rest of child 6, as scoped by testing-planner and rpg-planner on 2026-11-15.

## Scope
1. **Gate candidate (testing).**
   - `tools/test_architecture/rpg_gate_run.run` reads the run's `data/runs/<run_id>/run_manifest.json` after shutdown. It writes the pinned verdict into the metric document header as `runner: {verdict, differences}`, using `pinned_runner.classify_manifest`.
   - `rpg_gate_candidate.build_candidate` refuses (`CandidateRefused`, naming the document) any `ok` document whose `runner.verdict` is not `PINNED`, or that has no `runner` field.
   - The report path is unchanged.
2. **Paired arms (rpg's tools, rpg-planner's ruling).**
   - `arm_child.py` writes `runner: "PINNED"` (the `require_pinned` verdict) into its arm document.
   - `tools/rpg_measure/paired.py` refuses to compare an arm document that is missing it or has another value; that covers local and `--collected` results.
   - `tools/test_architecture/paired_arms.assemble` refuses the same at assembly.
   - Changing arm_child moves paired's child hash, so cached results are not reused. That is expected.
3. **Manifest (src, rpg-planner's ruling 2026-11-15).**
   - Add `worker_manager: Optional[str]` (class qualname) to `RunConditions`. It is None when the executor is sequential, and is written at the same kernel.py `update_manifest` call.
   - The reason: the design's remote manager sits behind `ConcurrentExecutionAdapter`, so the executor class alone cannot tell a threads run from a remote run.
   - No mode enum. The classifier is unchanged: anything other than `LocalSequentialExecutor` is NOT_PINNED.
   - The rules from #918 apply: typed, Optional, outside hashed state and the event stream, no behaviour change. `docs/engine/kernel.md` and the `docs/parity_ledger/infrastructure.yaml` line (INFRA-440) are updated in the same PR.
4. **Docs, so later sessions are not given conflicting information** (owner 6889947724). The design §8 row 6 and the epic's child-6 row say "the run manifest gets an executor-mode field". Each gets one line saying the record is `RunConditions.executor` plus `worker_manager`, read by `pinned_runner.classify`, citing this ticket. That wording needs its owner's OK at review (architecture-planner-u24 for the design doc, the epic owner for the epic).

## Out of Scope
- Anything beyond refusing (design child 6 cut line). No remote manager (child 3, TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER), no mode enum, and no change to the classifier's PINNED definition.
- Re-recording the gate baseline.

## Acceptance Criteria
1. Unit tests, one per refusal:
   - (a) the gate candidate refuses a document whose runner is NOT_PINNED, and one with no runner;
   - (b) `paired.py` refuses an arm document that is not pinned, tested directly rather than through arm_child;
   - (c) `paired_arms.assemble` refuses one;
   - (d) `arm_child` refuses a manifest whose executor is `ConcurrentExecutionAdapter`. The existing governor test does not count for this; the executor case needs its own test.
2. A unit test that a threads-built kernel records its `worker_manager` qualname and a sequential one records None, and that the record does not move `CanonicalStateHasher.get_hash`.
3. Evidence: one `frontier_marches` s42 pinned run of about 200 ticks, hash-equal to main, in a slot rpg-planner names. Run data is cleaned by run id.
4. Harness hash: `rpg_gate_run.py` is a `_HARNESS_SOURCES` file, so this ticket moves `harness_hash`. The PR states that, and the gate baseline's drift comparison treats the move as declared (per the gate-baseline rule: hash-moving edits are declared at review).
5. The existing tests pass: `tests/unit/kernel/test_run_conditions_record.py`, `test_executor_context_parity.py`, the rpg_gate and paired_arms tool tests, and `tests/unit/tools` for known_reds and rpg_gate_baseline.

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (child 6)
- TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE (#918, the base)
- TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER (child 3, filing only)

## Related Docs
- docs/plans/architecture/distributed_workers_experiment_design.md §8 (row 6), §9
- docs/guides/delivery_process.md (behaviour evidence comes from the pinned runner)
- docs/engine/kernel.md (manifest line)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE/

## Related Code Areas
- tools/test_architecture/{rpg_gate_run,rpg_gate_candidate,paired_arms,pinned_runner}.py
- tools/rpg_measure/{arm_child,paired}.py
- src/observability/reporting/artifact_repository.py (RunConditions), src/engine/kernel.py (the one write)

## Assumptions / Open Questions
- `kernel._worker_manager` is built even when the executor is sequential (kernel.py:139). The record is None when the executor is sequential, regardless of that object; rpg-planner ruled this.
- An `ok` gate document from before this change has no `runner` field, so the candidate refuses it. Candidates are built only from the same run's fresh documents, so nothing that is valid today is lost.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
