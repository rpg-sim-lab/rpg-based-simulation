---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261101-SLOW-KNOWN-RED-FOR-THE-BRAVERY-QUARTILE-TEST
phase: done
date: 2026-11-01
tags: [testing]
---

# TCK-20261101-SLOW-KNOWN-RED-FOR-THE-BRAVERY-QUARTILE-TEST

## Title
The bravery quartile test gets a slow_known_reds entry owned by rpg-planner until its kernel is pinned

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Scheduled run 41230865672 at e523f92b2 failed because tests.integration.scenarios.test_entity_differentiation::test_bravery_quartile_combat_rate_2x had no owner (1.48x against the 1.5x floor). rpg-planner ruled it most likely host-speed noise, not established, took ownership, filed TCK-20261101-BRAVERY-QUARTILE-TEST-RUNS-HOST-SPEED-DEPENDENT and asked for this entry.

## Scope
One exact-id entry, kind flaky, expiring 2026-11-30.

## Out of Scope
- The pin and the ratio check: rpg's ticket. Below 1.5x once deterministic is a STOP to the designer, never a re-tuned floor.
- A sweep of other tests using neither audit_mode nor the pinned governor.

## Acceptance Criteria
- [x] AC1: the entry resolves the failing id to rpg's ticket; nothing else in the registry changes.
- [x] AC2: the registry lint tests pass.

## Related Tickets
TCK-20261101-BRAVERY-QUARTILE-TEST-RUNS-HOST-SPEED-DEPENDENT, TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Related Docs
None

## Related Stored Artifacts
None

## Related Code Areas
tools/test_architecture/slow_known_reds.yaml

## Assumptions / Open Questions
The entry masks a real drift too, if there is one, until rpg's ticket reads the deterministic ratio. The expiry forces that read. rpg's ticket was not on main when this was written.

## Implementation Notes
Exact id, so the rest of that file stays unowned if it fails.

## Test Summary
tests/unit/tools/test_slow_regression_report.py and test_known_reds.py.

## Files Changed
tools/test_architecture/slow_known_reds.yaml

## Completion Summary
Entry added. The test stays red when it flaps; only its ownership changes.
