---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261116-LIVE-HEALTH-API-TEST-WAITS-A-FIXED-FOUR-SECONDS-ON-A-FIXED-PORT
phase: open
date: 2026-11-16
tags: []
---

# TCK-20261116-LIVE-HEALTH-API-TEST-WAITS-A-FIXED-FOUR-SECONDS-ON-A-FIXED-PORT

## Title
The live-health API test starts uvicorn on fixed port 8021, waits a fixed 4 s and then requests, and deletes its own server log even on failure, so an xdist failure leaves no evidence

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Seen during the restore-id hotfix's local passes on 2026-11-15/16 (TCK-20261115-A-RESTORED-SCENARIO-SHARES-ONE-RUN-DIRECTORY-PER-SPEC, branch head 943a3323b). Recorded by rpg-planner-ubuntu.

The failure:
- tests/api/test_live_health_api.py::test_live_health_api_suite[asyncio] failed ONCE, in pass 2: -n 2 --dist loadgroup over tests/integration/scenarios, tests/unit/engine and tests/api, on 2 capped cores (3G scope, CPUs 4-5).
- It passed in pass 1 (serial) and in pass 3 (-n 2).
- No traceback survives: the pass script kept only the summary line.

Controls (rpg-planner-ubuntu, lead-planner go), on clean git archives of the branch (943a3323b) and main (f94417e6f) under /data/vboxuser/Work/restore_ctrl:
- the single test under -n 2, 3x per tree: 6 of 6 passed, about 5.4 s each;
- tests/api in full, not slow, under -n 2: branch 192 passed in 49 s, main 192 passed in 82 s.
Not reproduced in 8 control runs on either tree. Cause unproven.

From the test's code on origin/main:
- l.16: a FIXED port, 8021;
- l.33: a fixed  before the first request, with no readiness poll;
- l.105-108: the finally block closes and , also after a failure, so the server's own startup and bind lines are gone exactly when they are needed.
In the controls' read-only copies of that log, startup completed and bound 127.0.0.1:8021 well inside 4 s on an idle slot. The same may not hold on 2 loaded cores; that is not measured.

## Scope
1. Replace the fixed sleep with a readiness poll: GET the health URL, or connect to the port, with a bounded timeout of about 30 s and a clear failure message that includes the server log tail.
2. A free port per run: bind port 0 to pick one, then pass it via --port, so two xdist workers or a stray server can never collide.
3. Keep the server log on failure: delete it only on success, or write it under tmp_path. Print its tail in the failure message.

## Out of Scope
Any change to the live-health endpoints themselves.

## Acceptance Criteria
1. The test passes serial and under -n 2 --dist loadgroup over tests/api.
2. On a forced failure (e.g. a server command that exits at once), the test fails within the timeout and its message shows the server log tail.
3. No fixed port remains in the test.

## Related Tickets
TCK-20261115-A-RESTORED-SCENARIO-SHARES-ONE-RUN-DIRECTORY-PER-SPEC (where it was seen; that change is imported by the server process but its changed path runs only on restore, which this test never calls).

## Related Docs
docs/testing/test_taxonomy.md

## Related Stored Artifacts
None. The control logs are in /data/vboxuser/Work/restore_ctrl/out on ubuntu, which is on the owner's delete list.

## Related Code Areas
tests/api/test_live_health_api.py

## Assumptions / Open Questions
Q1: do other tests/api tests start servers on fixed ports? Grep for --port and Popen in tests/api, and list them.

## Implementation Notes
Unscheduled; dispatch needs a go. Rides rpg-planner-ubuntu's next PR as a ticket filing.

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
