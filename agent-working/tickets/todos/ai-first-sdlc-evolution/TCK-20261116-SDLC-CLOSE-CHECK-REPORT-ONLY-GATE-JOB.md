---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB
phase: open
date: 2026-11-16
tags: [ai, delivery, governance, testing]
---

# TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB

## Title
One always-run CI gate job runs a post-close check on every PR that closes a ticket, report-only, covering the project tests, the agent-working tool tests and the gate ledger.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
SDLC Phase 2, filed by agent-working-planner on 2026-11-16. Filing only: dispatch needs a separate owner go.

The owner's decisions on the SDLC decision pack are recorded at #715 6910853925:
- OD-4, in the owner's words: "the test (deep layer testings, not just the project tests but the agent working gates". agent-working-designer confirmed lead-planner's reading of it as three layers.
- OD-13: one always-run gate job, the designer's recommendation.
- OD-12: advisory claims, plus detection of a ticket closed in two open PRs.

Plan: `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`:
- §28: the post-close condition set;
- §28a: the always-run gate job;
- §39: Phase 2, items 3, 8 and 10.

Under the owner's 11-15 rescope (#715 6889309909, 6889318166), Phase 1 (authority separation) is deferred. It is no longer a prerequisite. Instead, "required" means **required by owner practice**: the owner has bypass and M1 is deferred, so a red gate job is information for the owner, not a barrier. This ticket must say so wherever it uses "required".

## Scope
1. **Post-close condition set.** Add a set to `tools/gate_checks/done_checker_static.py` (or a sibling) that judges a ticket already in `done/`. The existing Part A assumes the ticket is still in progress. The set covers §28 conditions 1-5, 7 and 8:
   - in `done/` with `status: historical` and `phase: done`, and no copy in `todos/` or `inprogress/`;
   - standard-tier artifacts complete in `stored_artifacts/<id>/`;
   - exactly one working-log row;
   - Tier and Priority canonical;
   - docs-to-update coverage;
   - src paths changed imply their test lanes ran and passed in this PR;
   - no unresolved blocking `gate_verdict` for the ticket.

   Condition 6 (a closure record exists) stays off until TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS lands, and is listed as such.
2. **The three OD-4 layers,** each reported as its own line:
   - (1) the project test lanes for the paths the PR touches (condition 7);
     - a sub-line under (1), the **test-scope floor**, **required** (OD-5 condition 1, #715 6911091662). For each ticket the PR closes, it reports whether the tests that ran cover every test directory the changed paths require (reuse `tools/gate_checks/test_scope_coverage_static.py::expected_test_dirs_for`). It is a finding line in the step summary. The pipeline enforces this floor, but the hand path does not; rpg's #931 is the one real miss on record;
   - an **architecture verdict line**, **required** (OD-5 condition 2), for PRs that touch `src/`. It reports whether an architecture verdict is recorded for the PR, as `recorded` or `missing`, and does not judge the diff. Decide the record's form in this ticket's plan, from what exists: the gate ledger, `record_review`, the architecture-reviewer agent's output. Architecture-Verify has no hand-path stand-in;
   - (2) the agent-working tool tests (`tools-a-e`, `tools-f-z`, `agent-orchestration`) when `tools/`, `.claude/workflows/` or `.claude/agents/` change;
   - (3) the gate ledger: no unresolved blocking gate verdict for any ticket the PR closes (condition 8).
3. **OD-12 detection line:** a ticket closed by this PR that another open PR also closes is reported, not blocked.
4. **One always-run gate job** in `.github/workflows/test.yml`:
   - It has no path filter and no job-level `if`, so it never reports Success by being skipped (§28a).
   - It reads the other lanes' results and runs the condition set on the tickets the PR adds to `done/`. Legacy tickets the PR merely touches are out of scope.
   - It is **report-only**: it writes the step summary and does not fail the PR on a close-check finding. A crash of the check itself is shown as a crash.
   - The workflow-file edit is a governing change, so the exact diff goes to the owner through lead-planner before commit.
5. **E1-replay:**
   - Run the condition set read-only over the last 50 merged PRs that closed a ticket.
   - Report per condition and per layer: flags, the ones judged false positives (with the reason), and the expected ~5 unresolved verdicts and 1-2 premature closes (§39 Phase 2 item 8).
   - For each flagged close, also record which of the pipeline-only checks the hand close lacked: the test-scope floor, the capped-pytest enforcement, an independent review verdict, and an architecture verdict on `src` PRs. Report how often the floor line and the verdict line would have fired, and which firings were false positives. The 2-week clock and the Phase 4 gate rest on these counts.
   - The replay is a read-only tool run, not a heavy run.

## Out of Scope
- Making the gate job blocking or a named required check. After a report-only window of at least 2 weeks, the owner decides from the measured false-positive rate (§39 Phase 2 item 9). That needs its own ask.
- Rulesets and M1/M2 (deferred).
- The `work close` CLI: TCK-20261116-SDLC-WORK-CLOSE-CLI.
- The outcome-movement condition (OD-4 option C). It is not in the owner's decision. Raise it with the RPG seats if wanted.
- Dropping any of the three layers. If the owner meant only one, the others drop at the end of the report-only window, by the owner's decision on the replay report.

## Acceptance Criteria
1. The post-close set exists with tests for each condition, pass and fail, using temp trees. Existing done_checker tests pass unchanged.
2. The gate job runs on every PR (shown by one PR that touches only docs and one that touches only `tools/`), reports the three layers and the OD-12 line, and never fails the PR on a finding.
3. The E1-replay report over 50 merged closing PRs is committed as a stored artifact. It gives counts per condition and layer, and lists every flag judged a false positive with its reason. It also gives the per-close count of missing pipeline-only checks.
4. The ticket and the docs (`docs/guides/delivery_process.md`, "PR Lifecycle") say plainly that the job is report-only, and that "required" means owner practice while M1 is deferred.
5. Both OD-5 lines, the test-scope floor and the architecture verdict, appear in the gate job's step summary on a PR that touches `src/` and tests.
6. The E1-replay reports, per flagged close, how often the floor line and the verdict line would have fired, and which firings were false positives.
7. The ticket states the Phase 4 clock rule: the 2 weeks start on the first day the check carries both lines (`SDLC_DECISION_RECORD.md`, "2026-11-16 (later)"), and the close records that date.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS (switches on condition 6)
- TCK-20261116-SDLC-WORK-CLOSE-CLI
- TCK-20260705-GATE-DET-DONE-CHECKER (Part A)
- TCK-20261116-SDLC-RETIRE-PIPELINE-WORKFLOWS (Phase 4, gated on this ticket's two OD-5 lines)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (§28, §28a, §39 Phase 2)
- docs/plans/agent_infrastructure/SDLC_DECISION_RECORD.md
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- tools/agent-monitoring/gate_ledger.py
- .github/workflows/test.yml (the `changed-files` and `resync-gate` jobs show the existing patterns)

## Assumptions / Open Questions
- Whether the org repo offers an organization-level required workflow (OD-13 C) is not checked. It matters only if M1 or M2 is reopened.
- A sync-only push skips lanes as `pr_content_unchanged`. The job must read a skip as "ran on the prior content head", not as a pass, and say which it was.
- OD-4, OD-6, OD-11, OD-12 and OD-13 are recorded in `docs/plans/agent_infrastructure/SDLC_DECISION_RECORD.md` (section "2026-11-16"), filed with this ticket.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
