---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261119-INTEGRATION-CLI-EXPORT-TEST-MISSING-MANIFEST-ONCE
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-INTEGRATION-CLI-EXPORT-TEST-MISSING-MANIFEST-ONCE

## Title
`test_cli_export_command_success` failed once on the Integration job with a missing `export_manifest.json`, and passed on the rerun; cause unexplained

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Recorded as an **unexplained intermittent failure**. No cause is claimed. Filed at lead-planner's request on 2026-11-19; it found no existing ticket or issue for it.

Evidence (PR #966, branch `testing-implementer-gate-rerun-only-new-rows`, head 962b8b3ca, workflow `test.yml`):
- Run 44456343941, attempt 1, job **135332351192** ("Integration"), failed at 2026-11-19 04:15:45Z: `1 failed, 1133 passed, 6 skipped` in 334.77 s.
- The failing test: `tests/integration/observability/test_export_flow.py::test_cli_export_command_success` (assertion `assert 1 == 0` at line 117, on the CLI's exit code).
- The logged error: `FileNotFoundError: [Errno 2] No such file or directory: '<workspace>/data/exports/4091d43498b1429abfa1379c9f96de55/export_manifest.json'`, logged by `src.observability.analytics.exporter` (exporter.py:653, "Export Job 4091d43498b1429abfa1379c9f96de55 failed").
- The same run, attempt 2, job **135335223336**, passed on the same sha.
- Run 44455067844 (head 62166f44b, an earlier commit on the same PR) passed. PR #966 touched no code on this path.

## Scope
Record the intermittent failure, watch for a recurrence, and (if it recurs) collect the evidence below. No root-cause hypothesis is recorded here, and none should be assumed.

If it recurs: record the run id, job id, head sha and the full failure traceback; whether the path was the test's own `data/exports/<id>` or another process's; whether other tests ran concurrently in the same job and shared `data/exports`; and the test's temp-directory and cleanup behaviour for that run.

Routing: the code path is `src/observability/analytics/exporter.py` and the test is under `tests/integration/observability/`. `python3 -m tools.sessions.route` returns `rpg-planner` for both (`src/**` and `tests/**`); neither is a testing-owned path (testing owns `tests/architecture` and `tests/mutation`). Lead-planner routes the diagnosis if it recurs.

## Out of Scope
- Guessing a cause, adding a retry, or skipping or marking the test flaky before a recurrence is understood.
- Any `src/` change.

## Acceptance Criteria
1. The failure above is recorded with the run, job and sha ids (done by this ticket).
2. On a recurrence, the evidence listed in Scope is added here and the ticket is routed to its owner.
3. If it does not recur across a stated window (14 days of `test.yml` runs on main and PR branches), lead-planner may close the ticket as "not reproduced".

## Related Tickets
- PR #966, TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN (where it was seen; unrelated to its change)

## Related Docs
None.

## Related Stored Artifacts
- CI job logs of run 44456343941, attempts 1 and 2 (they expire).

## Related Code Areas
- `src/observability/analytics/exporter.py`
- `tests/integration/observability/test_export_flow.py`

## Assumptions / Open Questions
- Whether this is a shared-directory race, a cleanup race or something else: unknown.
- Whether it has happened before on other runs: not checked beyond the two runs above; lead-planner found no ticket or issue.

## Durable state, lifecycle and clocks
None: a CI observation.

## Implementation Notes
Filing only.

## Test Summary
Not applicable.

## Files Changed
This ticket only.

## Completion Summary
Open.
