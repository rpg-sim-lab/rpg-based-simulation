---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261021-OBSERVABILITY-DETERMINISM-TEST-NEVER-HASHES
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-OBSERVABILITY-DETERMINISM-TEST-NEVER-HASHES

## Title
test_phase28_observability_determinism is named "same authoritative hash" but only toggles the observability mode and never compares a hash

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Lead-planner-u24's read-only pass on origin/main (2026-10-21): the test is named for the same authoritative hash across observability modes, but it only toggles the mode and never hashes. This is a test-strength gap. Testing-planner was copied and may take it; tests/integration is rpg-planner's path, so either lane can do it with the other's OK. After v1.

## Scope
- Run the same world, seed and ticks under each observability mode.
- Assert that the final authoritative state hash is identical, using the existing hash helper.
- Keep the test's name, so the frozen-name rule holds if it applies.

## Out of Scope
- Anything before v1. The simulation-behaviour freeze holds until the v1 record lands.

## Acceptance Criteria
- The test fails if an observability mode changes authoritative state.
- It passes on main.

## Related Tickets
- TCK-20261019-RECORD-BASELINE-V1 (do after it)

## Related Docs
- docs/engine/

## Related Stored Artifacts
- none

## Related Code Areas
- tests/integration/observability/test_phase28_observability_determinism.py

## Assumptions / Open Questions
- Lead-planner-u24 reported this; it has not been re-verified here yet.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
