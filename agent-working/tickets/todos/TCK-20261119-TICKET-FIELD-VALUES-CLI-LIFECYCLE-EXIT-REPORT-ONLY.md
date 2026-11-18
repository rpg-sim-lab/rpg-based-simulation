---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-TICKET-FIELD-VALUES-CLI-LIFECYCLE-EXIT-REPORT-ONLY
phase: open
date: 2026-11-19
tags: [process-improvement]
---

# TCK-20261119-TICKET-FIELD-VALUES-CLI-LIFECYCLE-EXIT-REPORT-ONLY

## Title
`tools/ticket_field_values.py` CLI must not exit 1 on a lifecycle-section FAIL (report-only per owner)

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
PR #960 (merged 291cfdd04, owner "merge now, fix after", #715 6974746591) made the `## Durable state, lifecycle and clocks` checks advisory (#715 6972698325). `done_checker_static` and `pr_body_lint` are report-only, but `main()` in `tools/ticket_field_values.py` still returns 1 when `check_lifecycle_section` returns FAIL (`return 1 if any_fail or lifecycle_status == "FAIL" else 0`). Found in the planner review of #960 (comment 6974727818). No gate or workflow calls the CLI today, so nothing blocks; it contradicts report-only if anyone wires it in.

## Scope
- In `main()`, print the lifecycle line as before but leave the exit code driven by `check_ticket_field_values` results only; label a lifecycle FAIL `[advisory]` in the output.
- Add or adjust a test in `tests/tools/test_lifecycle_section.py` (or `test_ticket_field_values.py`) pinning: lifecycle FAIL alone gives exit 0 and still prints the line; a real field-value FAIL still gives exit 1.

## Out of Scope
- Promoting the check to blocking (a later owner decision after the fill-rate baseline).
- Any change to done_checker_static or pr_body_lint.

## Acceptance Criteria
1. `python3 tools/ticket_field_values.py <ticket dated >= 2026-11-19 with no lifecycle section>` prints the lifecycle FAIL line and exits 0.
2. A ticket with an invalid Tier/Status/Priority value still exits 1.
3. The scoped tests pass.

## Related Tickets
- TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES

## Related Docs
- `docs/guides/delivery_process.md` ("Durable state, lifecycle and clocks section")

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES/`

## Related Code Areas
- `tools/ticket_field_values.py` (`main`)
- `tests/tools/test_lifecycle_section.py`

## Assumptions / Open Questions
- Assumes no caller depends on the exit-1 behaviour (grep found none outside tests; the implementer re-checks).

## Durable state, lifecycle and clocks
N/A: no src change; a tools CLI exit code only.

## Implementation Notes
For agent-working-implementer's next batch on a fresh branch off main (lead-planner relay 2026-11-19).

## Test Summary

## Files Changed

## Completion Summary
