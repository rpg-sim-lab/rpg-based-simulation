---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-ROUTINE-BOOSTS-KEYED-SLEEP-AND-EATING-NEVER-MATCH-A-GOAL-KIND
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-ROUTINE-BOOSTS-KEYED-SLEEP-AND-EATING-NEVER-MATCH-A-GOAL-KIND

## Title
The routine boosts keyed "sleep" and "eating" never match a GoalKind value, so they are dead

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Deeper issue 3. The routine boosts in src/systems/world_systems/routine.py are keyed by the strings "sleep" and "eating", which never equal a GoalKind value, so the boosts never apply.

Source: rpg-designer M1 items 2-6 rule text (main-checkout .claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md, sha256 800027b5), section 'Deeper issues'. Filed by rpg-planner under owner ruling #715 6936893143 (deeper issues found in Phase 1 are filed now and fixed in Phase 3 unless they are hard errors).

## Scope
1. Confirm read-only (GoalKind values vs the keys).
2. Rule, through the designer: remove the dead boosts, or key them to the real GoalKinds (a behaviour change).

## Out of Scope
- Retuning the routine.

## Acceptance Criteria
- A test pins the decision: no unmatched key exists, or the boost applies to its GoalKind.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/mechanics/ (the chapter for this subsystem)

## Related Stored Artifacts
- none yet

## Related Code Areas
- as named in the Request Summary

## Assumptions / Open Questions
- The line numbers are on main bb26e4e5f, from the designer's reading; re-check them before acting.

## Implementation Notes
- Phase 3.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
