---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261101-BRAVERY-QUARTILE-TEST-RUNS-HOST-SPEED-DEPENDENT
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-BRAVERY-QUARTILE-TEST-RUNS-HOST-SPEED-DEPENDENT

## Title
The bravery-quartile behaviour test runs a host-speed-dependent kernel, so it flaps near its floor

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
testing-planner finding 2026-11-01: `test_bravery_quartile_combat_rate_2x` (tests/integration/scenarios/test_entity_differentiation.py) is red on main e523f92b2 (Slow regression run 41230865672): top 0.2519 vs bottom 0.1698 = 1.48x, under the 1.5x floor (calibrated about 1.74x by TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION). Tracker #390 shows it flapping: NEW 10-18, NEW and FIXED 10-24, NEW 10-31. It passed at 6fdfdf555. The only src change between the two runs is #803 (the OFF-mode import move), which is behaviour-neutral by its own hash check.
Cause (planner reading, to be verified): the test builds `Kernel(_test_profile(), ...)` with neither `audit_mode` nor `PinnedNormalGovernor`, so the PhaseBudgetGovernor reads live wall-clock signals and the world diverges with host load (TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR, investigation: normal mode diverges by tick 9). The test avoids audit_mode on purpose (transaction_trace growth).

## Scope
- Make the test host-independent without audit_mode: build its Kernel with the pinned governor (`tests/helpers/kernel_pinning.py::PinnedNormalGovernor`, which zeroes signals since TCK-20261014), plus `PYTHONHASHSEED`-independent ordering if the test needs it.
- Run it twice on a loaded host and once idle: the ratio must be identical.
- Read the deterministic ratio. If it is at or above 1.5x, done. If it is below, STOP: that is a behaviour question for the rpg designer, not a re-tune of the floor.

## Out of Scope
Changing the 1.5x floor. Any src change.

## Acceptance Criteria
- AC1: the test's Kernel is signal-zeroed (pinned governor), asserted in the test (manifest `signals_zeroed` or the governor flag).
- AC2: the same ratio on three runs under different host load.
- AC3: the deterministic ratio reported; a pass, or a STOP to the designer.

## Related Tickets
TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION; TCK-20261005-BRAVERY-QUARTILE-GUARD-RED-ON-MAIN-UNOWNED; TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR; TCK-20261031-ADVENTURE-SCORER-LOADS-THE-COGNITION-PACKAGE-IN-OFF-MODE.

## Related Docs
docs/testing/test_taxonomy.md.

## Related Stored Artifacts
agent-working/stored_artifacts/TCK-20261014-UNAUDITED-RUNS-DEPEND-ON-HOST-SPEED-THROUGH-PHASE-BUDGETS-EVEN-WITH-THE-PINNED-NORMAL-GOVERNOR/investigation.md

## Related Code Areas
tests/integration/scenarios/test_entity_differentiation.py; tests/helpers/kernel_pinning.py.

## Assumptions / Open Questions
Owner: rpg-planner. A known_reds entry is allowed until this lands: owner rpg-planner, ticket this, expiry 2026-11-30. About 22 other files use PinnedNormalGovernor; tests that use neither it nor audit_mode are a wider sweep for testing-planner, not this ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
