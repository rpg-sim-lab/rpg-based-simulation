---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS

## Title
Split src/systems/strategic_systems/intelligence.py so its module and StrategicIntelligenceSystem class fall back below their line ceilings

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
The paydown ticket that retires the intelligence.py line-ceiling raises of M1 Phase 1.
- N10 (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK) adds the suspension-expiry helper and wrapper: module length 1833 → 1880 and class length 1671 → 1717.
- The blocker-churn fix (TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION) adds the quiet-spell and merge passes to the same file.
- PERC-02b moves about 13 perception sites, some of them in this file.
The split is a mechanical move (no behaviour change), proven by an AST name + body comparison and a hash-equal run.

## Scope
1. Move cohesive groups (project lifecycle, blocker lifecycle, routing helpers) into sibling modules. StrategicIntelligenceSystem keeps thin delegates where callers need them.
2. Bring the module and class below their ORIGINAL ceilings (1833 / 1671), and lower the ceilings.
3. Re-key any path-keyed baselines (mypy, import layers) with a ruling, and check the mechanism-registry implemented_by entries.

## Out of Scope
- Any behaviour change.

## Acceptance Criteria
- intelligence.py module and class are at or below 1833 / 1671 lines, and the ceilings are lowered to the new values.
- Hash-equal on the 3 gate worlds at s42; the AST comparison shows only moves.

## Related Tickets
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
- TCK-20261117-SPLIT-EVENT-SHAPERS-BELOW-ITS-LINE-CEILINGS (the same pattern)

## Related Docs
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- Schedule: after N10 and the churn fix land, before run-2 items that touch the file (PERC-02b). The owner decides.

## Implementation Notes
- Filed by rpg-planner.

## Test Summary

## Files Changed

## Completion Summary
