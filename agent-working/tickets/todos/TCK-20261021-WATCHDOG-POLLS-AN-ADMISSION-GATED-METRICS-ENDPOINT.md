---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-WATCHDOG-POLLS-AN-ADMISSION-GATED-METRICS-ENDPOINT

## Title
The watchdog GETs backend:8000/metrics, which is behind require_admission (401), so with admission on, check_metrics fails every 10 s and WatchdogTrip fires continuously

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Lead-planner-u24 found this on 2026-10-21 by reading the code on origin/main; it was not run. It does not block v1.
- src/observability/watchdog.py:47 GETs BACKEND_URL/metrics (default http://backend:8000).
- server.py:176 puts /metrics behind Depends(require_admission). The comment in docker/prometheus.yml says it returns 401.
- If admission is enforced in compose, check_metrics fails every 10 s, so WatchdogTrip fires continuously, limited only by the 60 s dedup.
- tests/unit/observability/test_watchdog.py mocks check_metrics, so no test sees it.

## Scope
- Confirm the compose behaviour (admission enforced or not).
- Fix direction:
  - read the R1 metrics port (backend:9109); or
  - retire the watchdog in favour of a Prometheus stall rule. That part is platform's, so coordinate with platform-planner.
- Add a test against the real endpoint shape: an admission-gated 401 must not count as a stall.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The watchdog reads an endpoint it is allowed to read, or is retired with platform's OK.
- A test covers the 401 case.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- src/observability/watchdog.py, src/api/server.py:176, docker/prometheus.yml, tests/unit/observability/test_watchdog.py

## Assumptions / Open Questions
- This was read from code, not reproduced. Re-verify it before any fix.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
