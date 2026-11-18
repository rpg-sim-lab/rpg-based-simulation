---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261118-PREFLIGHT-FAILS-A-PROCESS-THAT-WRITES-NO-OUTPUT-FILE
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-PREFLIGHT-FAILS-A-PROCESS-THAT-WRITES-NO-OUTPUT-FILE

## Title
A unit test pins that the kit preflight fails a process that writes no output file

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Check (d) fails "the entry wrote no output file" when a process declares output fields or a count_path hook and writes none (the step-5 probe prints nothing to stdout, so that is its only signal). The branch was inspected in code only; no test covered it. Hotfix tier; owner-directed origin (#715 6971915608 follow-up) via rpg-planner.

## Scope
One unit test in tests/unit/tools/test_kit_preflight.py.

## Out of Scope
Any change to kit_preflight.py.

## Acceptance Criteria
A probe that writes no output file, with declared fields, gives a check-d FAIL "wrote no output file" while the fixture run (c) itself passes.

## Related Tickets
TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN, TCK-20261118-PREFLIGHT-CHECK-B-MIRRORS-THE-RUNS-INTERPRETER-FLAGS

## Related Docs
tools/rpg_measure/README.md

## Related Stored Artifacts
None.

## Related Code Areas
tools/rpg_measure/kit_preflight.py (check_fixture_run), tests/unit/tools/test_kit_preflight.py

## Assumptions / Open Questions
Tooling only, no src; dated before 2026-11-19, so no durable-state section is required.

## Implementation Notes
The test reuses the clean probe with its json.dump line removed.

## Test Summary
Pending the host run.

## Files Changed
tests/unit/tools/test_kit_preflight.py, this ticket.

## Completion Summary
Pending.
