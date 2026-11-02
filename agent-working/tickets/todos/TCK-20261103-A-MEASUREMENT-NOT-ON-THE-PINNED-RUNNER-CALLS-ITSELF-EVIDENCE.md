---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
phase: open
date: 2026-11-03
tags: []
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

## Test Summary

## Files Changed

## Completion Summary
