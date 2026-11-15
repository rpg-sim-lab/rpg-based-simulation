---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE
phase: done
date: 2026-11-15
tags: [testing, architecture]
---

# TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE

## Title
A run on a non-sequential executor is refused by the gate candidate, the paired arms and rpg_measure, and its manifest says which worker manager it ran on

## Status
DONE

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
1. [x] **Gate candidate (testing).**
   - `tools/test_architecture/rpg_gate_run.run` reads the run's `data/runs/<run_id>/run_manifest.json` after shutdown. It writes the pinned verdict into the metric document header as `runner: {verdict, differences}`, using `pinned_runner.classify_manifest`.
   - `rpg_gate_candidate.build_candidate` refuses (`CandidateRefused`, naming the document) any `ok` document whose `runner.verdict` is not `PINNED`, or that has no `runner` field.
   - The report path is unchanged.
2. [x] **Paired arms (rpg's tools, rpg-planner's ruling).**
   - `arm_child.py` writes `runner: "PINNED"` (the `require_pinned` verdict) into its arm document.
   - `tools/rpg_measure/paired.py` refuses to compare an arm document that is missing it or has another value; that covers local and `--collected` results.
   - `tools/test_architecture/paired_arms.assemble` refuses the same at assembly.
   - **Pre-record arm trees** (rpg-planner (u24) ruling, accepted by rpg-planner-ubuntu, 2026-11-15; ubuntu twin TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE): `arm_child.py` loads `pinned_runner` by file path from the tool checkout (never from the arm tree, which is on PYTHONPATH; the module is stdlib-only). The path is chosen by the ARM TREE's contents: a tree with `RunConditions` in `src/observability/reporting/artifact_repository.py` must have its kernel's manifest record (`run_conditions_source: "manifest"`); a tree without it (older than b6ac7dabb) is classified from its live kernel (governor and executor as module.qualname, the profile's `max_tick_budget_ms`, `_audit_mode`, `_no_frame_pacing`), same `require_pinned` (`run_conditions_source: "derived_from_kernel"`). A tree that has the model but whose manifest lacks the record, or is not pinned, is refused. No new `runner` label value. `paired.py` accepts either source, prints each arm's source in its report, and refuses only an arm not marked PINNED.
   - Changing arm_child moves paired's child hash, so cached results are not reused. That is expected.
3. [x] **Manifest (src, rpg-planner's ruling 2026-11-15).**
   - Add `worker_manager: Optional[str]` (class qualname) to `RunConditions`. It is None when the executor is sequential, and is written at the same kernel.py `update_manifest` call.
   - The reason: the design's remote manager sits behind `ConcurrentExecutionAdapter`, so the executor class alone cannot tell a threads run from a remote run.
   - No mode enum. The classifier is unchanged: anything other than `LocalSequentialExecutor` is NOT_PINNED.
   - The rules from #918 apply: typed, Optional, outside hashed state and the event stream, no behaviour change. `docs/engine/kernel.md` and the `docs/parity_ledger/infrastructure.yaml` line (INFRA-440) are updated in the same PR.
4. [x] **Docs, so later sessions are not given conflicting information** (owner 6889947724). The design §8 row 6 and the epic's child-6 row say "the run manifest gets an executor-mode field". Each gets one line saying the record is `RunConditions.executor` plus `worker_manager`, read by `pinned_runner.classify`, citing this ticket. That wording needs its owner's OK at review (architecture-planner-u24 for the design doc, the epic owner for the epic).

## Out of Scope
- Anything beyond refusing (design child 6 cut line). No remote manager (child 3, TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER), no mode enum, and no change to the classifier's PINNED definition.
- Re-recording the gate baseline.

## Acceptance Criteria
1. [x] Unit tests, one per refusal:
   - (a) the gate candidate refuses a document whose runner is NOT_PINNED, and one with no runner;
   - (b) `paired.py` refuses an arm document that is not pinned, tested directly rather than through arm_child;
   - (c) `paired_arms.assemble` refuses one;
   - (d) `arm_child` refuses a manifest whose executor is `ConcurrentExecutionAdapter`. The existing governor test does not count for this; the executor case needs its own test.
2. [x] A unit test that a threads-built kernel records its `worker_manager` qualname and a sequential one records None, and that the record does not move `CanonicalStateHasher.get_hash`.
3. [x] No run (owner #715 6889952914 item A: "Small, no runs"; rpg-planner withdrew its run ask, 2026-11-15). The proof is AC2's unit test: a threads-built kernel records its `worker_manager`, and `CanonicalStateHasher.get_hash` is unmoved by the record (#918's hash-equal runs already showed writing RunConditions is hash-neutral).
4. [x] Harness hash: `rpg_gate_run.py` is a `_HARNESS_SOURCES` file, so this ticket moves `harness_hash`. The PR states that, and the gate baseline's drift comparison treats the move as declared (per the gate-baseline rule: hash-moving edits are declared at review).
5. [x] The existing tests pass: `tests/unit/kernel/test_run_conditions_record.py`, `test_executor_context_parity.py`, the rpg_gate and paired_arms tool tests, and `tests/unit/tools` for known_reds and rpg_gate_baseline.
6. [x] `arm_child` runs an arm tree older than b6ac7dabb (pre-record path), proven by one byte-identical base-vs-base repeat, the single short run approved by the owner at #715 6891712419 and ordered first by 6892133979 (urban_political s42, 200 ticks, base 5ba65854c02ec9d132adb985a30b945fa8525d29, arm then `-repeat` through `paired.run_arm` on a `prepare_tree`, fresh empty cache, one process, tool head fdb803dbd, child hash c4726f3c, 2026-11-15 09:10:46Z to 09:11:09Z, wall 23.2 s, children max RSS 186 MB, min host MemAvailable 4477 MB). Both arm documents have sha256 3e88144322362a1d66a98be7766eac68d1ebb45bac0364d261267234373434c9 (byte-equal); `runner: PINNED`, `run_conditions_source: derived_from_kernel`; start_hash 61483d5868d598e78a30112e64c92f79e6552b29693c916023792f0b1cec1f7d, final_hash b0bb86cc93327cc70b84838578d1da65f2b5a2799bb88a2d8895e126b2254efd in both. No second run.

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
- agent-working/stored_artifacts/TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE/ (plan, investigation, test_plan)

## Related Code Areas
- tools/test_architecture/{rpg_gate_run,rpg_gate_candidate,paired_arms,pinned_runner}.py
- tools/rpg_measure/{arm_child,paired}.py
- src/observability/reporting/artifact_repository.py (RunConditions), src/engine/kernel.py (the one write)

## Assumptions / Open Questions
- `kernel._worker_manager` is built even when the executor is sequential (kernel.py:139). The record is None when the executor is sequential, regardless of that object; rpg-planner ruled this.
- An `ok` gate document from before this change has no `runner` field, so the candidate refuses it. Candidates are built only from the same run's fresh documents, so nothing that is valid today is lost.

## Implementation Notes
Follow-up (arm_child, 2026-11-15, found by testing-planner's review of this ticket): `arm_child.py` imported `tools.test_architecture.pinned_runner` from the arm tree, which raises ModuleNotFoundError on any arm older than b6ac7dabb, and an older kernel writes no record either. Fixed as in Scope item 2 (pre-record arm trees). Import audit of arm_child's path for `tools.*` modules an older arm tree lacks: only `tools.test_architecture.rpg_gate_run`, present in both 5ba65854c and 96db1f5e8 (the `src.*` imports and `tests.helpers.kernel_pinning` too). The child hash, and so the paired cache keys, move. `tests/unit/tools/test_arm_child_pinned_check.py`: 5ba65854c and 96db1f5e8 archives pass by the pre-record path, each with a threads-executor negative; this tree passes by its manifest; this tree with the record withheld is refused.
Built as filed. `RunConditions.worker_manager` (Optional str, None for `LocalSequentialExecutor`; for another executor, the class of its own `_worker_manager` if it has one, else the kernel's) is written in the one existing `update_manifest` call. Gate: `rpg_gate_run.run` writes `runner: {verdict, differences}` from the run's manifest (a missing manifest is NOT_PINNED); `pool` is PINNED only if every pooled document is; `build_candidate` refuses a document without a PINNED runner. Paired arms: `arm_child` writes `runner: "PINNED"`; `paired.refuse_non_pinned` runs on the base, new and repeat documents (local and `--collected`) and in the neutral report; `paired_arms.assemble` refuses an arm document not marked PINNED, or a cost.json with no document beside it. `harness_hash` moves because `rpg_gate_run.py` is a harness source: declared here for the baseline drift comparison. The design §8 row 6 and epic child-6 lines (scope item 4) are not edited in this change: their owners add them (testing-planner, 2026-11-15). No evidence run (AC3 as ruled, owner #715 6889952914 item A).

## Test Summary
- tests/unit/tools/test_arm_child_pinned_check.py 11 passed (see Implementation Notes); test_rpg_measure, test_rpg_measure_collected, test_paired_arms re-run after the follow-up.
- tests/unit/kernel/test_run_conditions_record.py 20 passed (worker_manager recorded for threads and None for sequential; hash unmoved by the record; threads run NOT_PINNED by executor alone; arm_child refuses the concurrent executor).
- tests/unit/tools: test_rpg_gate_candidate (NOT_PINNED and no-runner refuse, runner_header, pooled_runner), test_rpg_gate_harness 24 passed (real documents carry PINNED), test_paired_arms 29 passed, test_rpg_measure_collected (refuse_non_pinned direct; collected and neutral refuse), test_rpg_gate_baseline, test_rpg_gate_report, test_rpg_measure, test_known_reds.
- A wide single-process run (kernel, observability, architecture and the tool files) gave 1952 passed, 3 failed, 1 error (test_worker_equivalence::test_authoritative_equivalence; 3 in test_rpg_gate_harness) during a host OOM window (14:09); those two files passed when rerun alone (24 and 2 passed). The cause of the four failures is not established. The wide scope was then re-verified file by file (list in the PR).

## Files Changed
src/engine/kernel.py; src/observability/reporting/artifact_repository.py; tools/test_architecture/{rpg_gate_run,rpg_gate_candidate,paired_arms}.py; tools/rpg_measure/{arm_child,paired}.py; docs/engine/kernel.md; docs/parity_ledger/infrastructure.yaml (INFRA-440); tests/unit/kernel/test_run_conditions_record.py; tests/unit/tools/{test_rpg_gate_candidate,test_rpg_gate_harness,test_paired_arms,test_rpg_measure_collected}.py; stored artifacts.

## Completion Summary
(Reopened 2026-11-15 for the arm_child follow-up; closed again with AC6's proof run, see AC6.)
The gate candidate, the paired arms (local and collected), the neutral compare and the arm assembly refuse a run that was not on the pinned runner, and a manifest names the worker manager. No run, by ruling. Two items remain with their owners: the design §8 row 6 and epic child-6 lines; AC4's baseline drift declaration is made in the PR.
