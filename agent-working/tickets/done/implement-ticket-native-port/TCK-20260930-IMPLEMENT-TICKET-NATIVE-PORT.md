---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT
phase: done
date: 2026-10-01
tags: [ai, agent-monitoring]
---

# TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT

## Title
Port implement-ticket.js to the native Workflow runtime in the classified order

## Status
DONE

## Tier
epic

## Type
refactor

## Priority
P2

## Request Summary
Follows the classification: advisory and bookkeeping sites first, then input sites, then gates with attestation, plus the dispatch-cost batching decision (13 writeSidecar and 11 captureTs invocations).

## Scope
- Children: advisory and bookkeeping sites via `runCommand`/`args`; input sites; gate and control sites using the attested route from the design ticket; per-phase timestamp and sidecar batching.
- Blocked by `TCK-20260930-IMPLEMENT-TICKET-PARSE-AND-NONDETERMINISM-FIX` and `TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN`.

## Out of Scope
- Any other workflow script.

## Acceptance Criteria
1. No `bash(` remains in implement-ticket.js. **MET** (`workflow_bash_sites.py` reports 0).
2. Every gate-class site uses the attested route or stays orchestrator-side by an explicit, recorded decision. **MET** (the attested gate sites and the orchestrator backstop).
3. One native run of a small ticket completes with correct gate outcomes. **PARTLY MET**: the fail path, the plan gate, and the attested gates through Test behaved correctly across three runs, but no run completed end to end.

## Related Tickets
- TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION (the classification this follows from)
- TCK-20260930-IMPLEMENT-EPIC-NATIVE-WORKFLOW-PORT (sibling)
- TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT (pattern and measurement)

## Related Docs
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/classification.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260930-IMPLEMENT-TICKET-GATE-VS-BOOKKEEPING-CLASSIFICATION/`

## Related Code Areas
- `.claude/workflows/implement-ticket.js`

## Assumptions / Open Questions
- **Parked 2026-10-18 (owner decision via lead-planner, #634 stale-epic triage): awaiting owner opt-in for one native Workflow run. The only open child is TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN (BLOCKED for the same reason); every other child is done.**
- Attestation design outcome (`agent-working/stored_artifacts/TCK-20260930-NATIVE-GATE-RESULT-ATTESTATION-DESIGN/design.md`): **adopt for gates only**. A nonce-hash attestation was forged on the first try by a cheat-instructed agent, so it is anti-misreport only; the unforgeable check is an orchestrator-side re-run of the static gates plus CI. AC2 is therefore met by "attested route + recorded orchestrator backstop", not by attestation alone.
- **Deliberate partial run (user decision, 2026-10-01):** only 3 of the 5 children run now (BOOKKEEPING-ADVISORY-SITES, INPUT-SITES, ORCHESTRATOR-BACKSTOP; all done and moved to `agent-working/tickets/done/`). `TCK-20260930-NATIVE-PORT-ATTESTED-GATE-SITES` and `TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN` are deferred and stay in this folder. Reason: the design measured about 450k tokens and about 3 minutes extra per run if all 9 gate sites are reached, so the user decides on the gate children after seeing the cheap children's measured cost. This is a recorded exception, not a breach of the epic all-or-nothing rule. The epic stays OPEN and is not moved to done.
- Children are in this folder; order in `SEQUENCE.md`. No child started in the scoping batch.

## Implementation Notes
Scoped 2026-10-01 into 5 children (see `SEQUENCE.md`). Epic closes when all children are done; 3 of 5 are done, 2 deferred by user decision (see Assumptions).

## Test Summary
Evidence is in TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN's Test Summary: wf_b59e5ed2-5d3 (`TAGS_NOT_REGISTERED` at Scope, as designed), wf_d6a35058-f5d (`NEEDS_HUMAN_INPUT` at the Plan gate, a correct stop) and wf_f48f4fae-569 (attested gates through Test, ended `TESTS_FAILED`).

## Files Changed
See the children. This ticket changes no files beyond its own move to `done/`.

## Completion Summary
Closed on the owner's answer to hand-finish the vehicle (#715 6894904885). AC1 and AC2 are met. AC3 is partly met and the gap is named below. Closing the epic drops the unmet part of AC3 from scope, so the closure itself rests on the owner's yes on the PR (#715 6875225978).

Known gap: no native run has completed end to end. Parity, Verify and Finalize have never run on the native path, so their attested gate sites are untested. The Test phase runs the whole of `tests/tools` in one uncapped process (filed: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS). Whether the pipeline is retired instead is OD-5, which agent-working-designer brings to the owner.

