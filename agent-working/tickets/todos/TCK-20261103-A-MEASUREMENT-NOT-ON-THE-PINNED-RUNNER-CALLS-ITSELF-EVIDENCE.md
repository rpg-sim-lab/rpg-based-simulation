---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
phase: open
date: 2026-11-03
tags: [testing, determinism, observability]
---

# TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE

## Title
A behaviour measurement run on the unpinned `_run_engine` can be presented as evidence: such a run should refuse to call itself evidence

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Requested by rpg-designer on 2026-11-03: "a run that isn't pinned refuses to call itself evidence".

On 2026-11-03, rpg-planner-ubuntu found that `tools.calibrate_simq._run_engine` (plain PROD_SMALL, default governor and executor, profile feature flags) and `tools.test_architecture.rpg_gate_run.build_kernel` (raised tick budget, PinnedNormalGovernor, LocalSequentialExecutor) give different worlds. On crowded s45 base they split between t2000 and t2100; the #828 arm differs by t2000. Those results are relayed and the cause is open. The #828 composition set and the #826 (2.156) tables used `_run_engine`, and a V3 red on #828 turned out to belong to that runner alone. It cost about a day.

rpg-designer's ruling: pinned build_kernel is the evidence standard for every measurement. Pinned is the measurement ruler, not a claim about what players get.

Standing rule for rpg-planner's lanes until this lands: measure on the pinned runner only.

## Scope
1. Every run written by `_run_engine` carries a typed runner marker in its output (the run manifest), and the pinned build carries its own.
2. A helper that lane probes use to report evidence refuses, or labels NOT EVIDENCE, a run whose marker is not pinned. The paired tool (tools/rpg_measure/arm_child.py) already refuses a tree that doesn't force audit_mode and no_frame_pacing; extend the same idea to the governor, executor and budget.
3. A close-time advisory or check: scripts in a ticket's evidence that call `_run_engine` for behaviour counts are flagged.
4. The delivery rule text. docs/guides/delivery_process.md is outside rpg-planner's seat (route says unowned), so the wording goes through lead-planner-u24.

## Out of Scope
- The cause of the runner difference, and whether production should change (a separate ticket on ubuntu's control results; rpg-designer's framing: an executor difference is a defect, a governor or budget under load is a legitimate degraded world judged separately, a budget or adapter changing results with no load is a defect).
- SIMQ grade anchors and calibration, which use `_run_engine` by design. Whether they should is a question for that later ticket; this one must not break them.
- Re-measuring #826 (rpg-designer's call) or #828 (already ruled to re-run pinned).

## Acceptance Criteria
- Tests: a `_run_engine` run is labelled not pinned; a build_kernel run is labelled pinned; the report helper refuses the former; SIMQ tools still run.
- The run hash does not change (marker is outside hashed state), shown by a hash-equal run.
- Hot-loop: no (run setup and report only).

## Related Tickets
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ
- TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS (done)
- TCK-20261004-MEASUREMENTS-TAKEN-VIA-A-NON-RUNNING-WORLD-DEFINITION (done)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (#828)
- TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT (#826)

## Related Docs
- docs/guides/delivery_process.md
- docs/engine/deterministic_execution.md
- docs/engine/performance_contract.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT/evidence/probe12.py (a `_run_engine` probe)

## Related Code Areas
- tools/calibrate_simq.py (`_run_engine`), tools/test_architecture/rpg_gate_run.py (`build_kernel`), tools/rpg_measure/arm_child.py, src/engine/kernel.py (manifest)

## Assumptions / Open Questions
- Lane scratch scripts outside the repo can't be checked by a close-time scan. F3's were in lane scratch, so the marker in the output is the real guard.
- tools/calibrate_simq.py and delivery_process.md route as unowned: who holds them is for the lead.
- Dispatch needs an owner yes.

## Implementation Notes
2026-11-03 delivery rule, state: text agreed by rpg-designer, sent to agent-working-planner-u24, which holds it until this ticket, the executor ticket and the digest ticket are all on main, since the text cites them. docs/guides/delivery_process.md is unowned; it would carry it as a short subsection, and that needs the owner's yes because the rule binds every session's verdicts. Its wording notes, for rpg-planner and rpg-designer to settle: "Applies from 2026-11-03" vs from the rule's merge; name the hash the pinned run reports; the older-claims sentence (including intentional_divergences.md entries) should be explicit to the owner. Open: whether the rule closes on this ticket's batch.

The rule lands in docs/guides/delivery_process.md via PR #834 (agent-working-planner-u24, hotfix TCK-20261103-DELIVERY-GUIDE-PINNED-RUNNER-EVIDENCE-RULE, head c4e9af4f2; rpg-planner's review 834#issuecomment-6594083847). This ticket keeps its code scope: runner marker, refuse-or-label helper, close-time flag.

Final rule text (rpg-designer, 2026-11-03):
"Behaviour evidence (a paired table, a probe count, a trace row used in a verdict or disclosure) comes from the pinned runner: `tools/rpg_measure` or `rpg_gate_run.build_kernel`. A run on another runner is labelled as such, backs no verdict, and is not re-labelled after the fact. A trace or probe used as evidence states its hash check against a plain pinned run at its own end tick, using `CanonicalStateHasher.get_hash` (the same value as the manifest `state_hash` when the end tick is the run's last). A hash check covers the state digest only; fields outside it are listed in TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ until that closes. Until TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS closes, the pinned runner is the measuring ruler, not a claim about what the concurrent production path gives. Applies from 2026-11-03, the date the standard was ruled. Older claims, including entries in `intentional_divergences.md`, stand as their era's and are re-checked only if a new ruling cites them."

Planner rulings (testing-planner, 2026-11-15; owner dispatch #715 6883358041; rpg-planner sign-off 2026-11-15 on the src lines, with the conditions below):
- **Scope item 4 is already done.** The rule text landed in docs/guides/delivery_process.md "Behaviour evidence comes from the pinned runner" via #834 (36d4fd78e). The only doc edit here: line 170's "which also owns the runner marker and refuse-or-label helper that will enforce this" becomes a sentence naming the helper and the record that now enforce it. The implementer drafts that exact sentence; testing-planner sends it to lead-planner-u24 before any push, for the owner's #715 log.
- **Design.**
  - Kernel record: the kernel writes a typed `run_conditions` record into the RunManifest. It records the governor class qualname, the executor class qualname, max_tick_budget_ms, audit_mode and no_frame_pacing, with signals_zeroed kept as it is.
  - Classifier: a testing classifier derives PINNED / NOT_PINNED from that record only, never from a runner-written label or kernel private fields.
  - Refusal: the evidence/report helper refuses NOT_PINNED.
  - arm_child.py: its existing refusal is extended to the governor, executor and budget (approved by rpg-planner).
  - Close-time advisory: flags `_run_engine` in a ticket's evidence scripts.
  - Not touched: tools/calibrate_simq.py and the SIMQ tools.
- **rpg-planner's conditions (all binding):**
  1. Write the record AFTER the executor is chosen. Add one `update_manifest(run_id, run_conditions=...)` right after executor selection (~kernel.py:193-198). Do NOT move executor selection above `create_run_directory` (it takes the rng; keep the order).
  2. A pydantic sub-model on RunManifest, `Optional[...] = None`, so old manifests load. Not a Dict[str, str].
  3. Kept out of hashed state and the event stream. Tests: same state hash and same events with and without the record, a manifest round-trip, and an old manifest without the field loading.
  4. Docs in the same PR: a manifest line in docs/engine/kernel.md, and an infrastructure.yaml parity-ledger entry via tools/parity_ledger_writer.py. No Bible change.
  5. One PINNED definition, read by both arm_child.py and the classifier: `tools/test_architecture/pinned_runner.py` (testing-owned; arm_child imports it). No second copy.
- **Test plan must include (lead C5):** tests/unit/kernel/test_executor_context_parity.py stays green, since kernel.py is touched.
- **Evidence run (rpg-planner):** fm and crowded at s42 for 1000 ticks, each hash-equal to main. The new runs classify PINNED. One `_run_engine` run classifies NOT_PINNED, and the helper refuses it. It runs only on rpg-planner's HOST FREE (queued after HOLD stage 1 and the V3 trace). Single process, no pytest -n>1 while cells run, 8 GB host.
- No behaviour re-measure (observability only; rpg-planner agrees).

## Test Summary

## Files Changed

## Completion Summary
