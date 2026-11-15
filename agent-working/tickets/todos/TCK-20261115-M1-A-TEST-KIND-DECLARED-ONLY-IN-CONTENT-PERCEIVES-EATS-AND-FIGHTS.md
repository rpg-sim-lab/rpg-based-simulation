---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS
phase: open
date: 2026-11-15
tags: [testing]
---

# TCK-20261115-M1-A-TEST-KIND-DECLARED-ONLY-IN-CONTENT-PERCEIVES-EATS-AND-FIGHTS

## Title
Milestone 1's content-alone probe: a test kind declared only in test content, with no code change, perceives, eats and fights by its declarations through the real kernel

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Split on 2026-11-15 from TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE (its scope item 2). That ticket was filed by rpg-planner on 2026-11-09 under the milestone 1 epic (owner #715 6731822583). The owner gave it to testing-planner on #715 6883358041.

Roadmap §12.5 done item 1: "'Works from content alone' is proven by a named probe: a test kind declared only in content, with no code change, perceives, eats and fights by its declarations."

HELD (rpg-planner, 2026-11-15). This probe is the milestone's done-proof. It must pass on the M1 record commit and would only fail today, because #781 (the decision-73 step) is open and no retirement has landed. rpg-planner says when the retirements reach the stage where it can go green, and testing-planner dispatches then.

## Scope
- One test in tests/integration/, through the real kernel. A test kind is declared only in test content (a test content pack or fixture, nowhere under src/). The test checks that the kind perceives, eats and fights by its declarations.
- Each behaviour is asserted from typed records (perception, consumption, combat events), not from log strings.
- rpg-planner signs off on the test kind's declarations at dispatch.

## Out of Scope
- Any src/ change. If the kind can't be made to work without code, that is a finding for the retire ticket, not a fix here.
- The name-check probe (the parent ticket).

## Acceptance Criteria
- [ ] AC1: The content-alone probe passes on the milestone 1 record commit.
- [ ] AC2: The test kind and its declarations live only in test content. A check in the test asserts that the kind's id appears nowhere under src/.
- [ ] AC3: rpg-planner's sign-off on the declarations is recorded in the PR (comment id).

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE (parent, now the name-check probe only)
- TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3, §12.5)

## Related Stored Artifacts
None.

## Related Code Areas
tests/integration/, test content (read-only for src/)

## Assumptions / Open Questions
- Dispatch waits for rpg-planner's go, relayed to testing-planner.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
