---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261125-TWO-INFER-BLOCKERS-BRANCHES-COMPARE-LOWERCASE-REASON-CODES-WITH-UPPERCASE-STRINGS
phase: open
date: 2026-11-25
tags: [cognition]
---

# TCK-20261125-TWO-INFER-BLOCKERS-BRANCHES-COMPARE-LOWERCASE-REASON-CODES-WITH-UPPERCASE-STRINGS

## Title
Two infer_blockers branches can never fire: lowercase ReasonCode values are compared with uppercase strings.

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found by rpg-implementer during the K2 fix investigation (2026-11-25; plan question Q6, inspected). rpg-designer ruled it a separate ticket. Filed by rpg-planner to the cognition-rework backlog. It is NOT HARD: dead branches, no state stuck.
- ReasonCode.PATH_NOT_FOUND and ReasonCode.LIQUIDITY_EXHAUSTED have lowercase values, but infer_blockers compares them with uppercase strings. So those two blocker branches never match.

## Scope
- Confirm the mismatch with a test. Then either fix the comparison (typed enum compare) or delete the dead branches; rpg-designer rules which before any code.

## Out of Scope
- The K2 service blocker (phase 5), which is new and works.

## Acceptance Criteria
- A test showing the branch reached (if fixed) or removed (if deleted). The hash effect is measured if the fix wakes a branch.

## Related Tickets
- TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER (where it was found)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (STRAT-191-194)

## Related Stored Artifacts
- The K2 fix investigation.md (stored at the K2 close)

## Related Code Areas
- infer_blockers (src/systems/strategic_systems/), src/core ReasonCode

## Assumptions / Open Questions
- Waking a branch changes behaviour, so it would need a measured step.

## Durable state, lifecycle and clocks
- None.

## Implementation Notes
- Not started.

## Test Summary
- None.

## Files Changed
- None.

## Completion Summary
- Open.
