---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261118-ACTION-OUTCOMES-ARE-WRITTEN-INTO-THE-NAVIGATION-FAILURE-REASON
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-ACTION-OUTCOMES-ARE-WRITTEN-INTO-THE-NAVIGATION-FAILURE-REASON

## Title
About twenty action handlers write their failure outcome into NavigationUpdate.failure_reason, so last_failure_reason mixes movement-step outcomes with action outcomes; give action outcomes their own typed field and keep the navigation field step-only

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Found by the stale failure-reason fix's own-job (S9 #715 6957082783 and continuation 6966311308; tree 2b6ee3123). Lane A's read-only writer list traced the cause, and rpg-designer ruled it (2026-11-18, ruling (c), point 2).
- `navigation.last_failure_reason` is meant to be the outcome of the LAST movement step (F2 v2 ruling; TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE).
- Action writers also write that field through NavigationUpdate.failure_reason, at these sites (file:line at 2b6ee3123):
  - src/engine/core_actions.py :43, :98 (SOURCE_MISSING / SOURCE_DEPLETED, eat at corpse), :158, :231, :306, :369, :402, :418, :485, :556, :561, :569, :591, :612;
  - action_router.py :30, :125;
  - combat_actions.py :51, :61;
  - skill_actions.py :44, :52, :60, :76, :83, :101;
  - aoe_actions.py :52;
  - lodging.py :126 (NO_BED_FREE).
- In the own-job, 74 SOURCE_DEPLETED rows (frontier 73, crowded 1) were action codes sitting in the navigation field.
- Ruled precedence until this lands: a code written in the same tick wins over the movement clear. The fix's rerun bar M2 attributes each such row to its writer.
- Readers of the navigation field: intelligence.py:495 (infer_blockers maps only PATH_NOT_FOUND / STUCK / OSCILLATING), state_presenter.py:187, domains/information/phase.py:130 and observability/live/entity_inspector.py:123.

## Scope
1. Evidence: the stale-reason fix rerun's "action-code rows per writer" report (its spy v2). Use it to size the move.
2. rpg-designer rules the field: a typed `last_action_failure` (or similar) on the right component with a defined lifecycle (written by an action outcome; cleared by a successful action, or by an aging rule), and which readers move to it.
3. Move every action writer off NavigationUpdate.failure_reason onto the new typed update. Then navigation.failure_reason is written only by the movement path and its refiners (occupancy, trust, actor_validity).
4. FIELD_RULES row, checkpoint and canonical hash, presenter. Tests: an action failure never sets last_failure_reason; the new field round-trips. Bible ch. 04 text, parity and divergence.

## Out of Scope
- The movement clear and the yield/swap move law (the stale-reason fix, ruling (c) point 1).
- The bare-string OCCUPANCY_CONFLICT at pipeline_phases/occupancy.py:140 (noted in the stale-reason fix; it could ride here as a ReasonCode member if rpg-designer wants).

## Acceptance Criteria
- No action handler writes NavigationUpdate.failure_reason. A source-scan test pins it, with the movement path and the three refiners as the only allowed writers.
- Action outcomes live in a typed field with a defined lifecycle and a test.

## Related Tickets
- TCK-20261117-A-NAVIGATION-FAILURE-REASON-IS-NEVER-CLEARED-AND-KEEPS-FEEDING-BLOCKER-INFERENCE (the step-only law; the fix that found this)
- TCK-20261118-MOVED-RECENTLY-IS-SET-TRUE-ON-THE-FIRST-STEP-AND-NEVER-CLEARED (another NavigationComponent field without a lifecycle)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (blocker inference)
- docs/core/state.md (NavigationComponent)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/failreason/cells_fail_all (the own-job rows)

## Related Code Areas
- src/engine/core_actions.py, action_router.py, combat_actions.py, skill_actions.py, aoe_actions.py, lodging.py; src/core/updates.py (NavigationUpdate); src/engine/patches.py:290

## Assumptions / Open Questions
- Which readers, if any, rely on action codes in the navigation field today is unchecked beyond the four listed.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
