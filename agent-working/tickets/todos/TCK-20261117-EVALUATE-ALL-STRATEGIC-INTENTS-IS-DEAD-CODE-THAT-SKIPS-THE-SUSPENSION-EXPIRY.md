---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-EVALUATE-ALL-STRATEGIC-INTENTS-IS-DEAD-CODE-THAT-SKIPS-THE-SUSPENSION-EXPIRY
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-EVALUATE-ALL-STRATEGIC-INTENTS-IS-DEAD-CODE-THAT-SKIPS-THE-SUSPENSION-EXPIRY

## Title
StrategicIntelligenceSystem.evaluate_all_strategic_intents has no production caller, and its direct call to evaluate_strategic_intent would skip N10's suspension expiry

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found by rpg-implementer-3 during N10 (TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK). intelligence.py:987 (evaluate_all_strategic_intents) is called only by tests (test_event_shapers_strategy.py, test_evaluate_all_strategic_intents_routing_family.py); the pipeline runs fused_strategic_pass. N10 runs the suspension expiry in the production caller through a helper, and a static test allows this dead path by name. If anyone revives it, subjects would skip the expiry. Same family as the designer's deeper issue 4 (uncalled intelligence.py paths). Filed for Phase 3 under owner #715 6936893143.

## Scope
1. Confirm there's no production caller.
2. Delete it and move its tests onto fused_strategic_pass, or route it through the expiry helper. The designer rules which.

## Out of Scope
- N10 itself.

## Acceptance Criteria
- No direct production-reachable call to evaluate_strategic_intent bypasses the expiry helper. The static caller test's allowlist entry for this path is removed.

## Related Tickets
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
- TCK-20261117-INTELLIGENCE-RAW-TIME-PATHS-ARE-UNCALLED

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- none

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (evaluate_all_strategic_intents)

## Assumptions / Open Questions
- 2026-11-17 (lane A's F2 code read): `StrategicRedirectionSystem` in src/systems/strategic_systems/redirection.py is also dead in production. Only its re-export (src/systems/redirection.py) and tests import it, and tests/architecture/test_unwired_subject_check.py:107-113 pins it as unwired. Its logic is a stale copy of the live bridge in intelligence.py (the comment at :632). Remove or retire it with the same care as evaluate_all_strategic_intents, and keep its tests' meaning where the bridge carries it.

- Line numbers are from N10's branch on 2026-11-17.

## Implementation Notes
- MOVED OUT of systemic_foundation (M1) to the cognition-rework backlog, 2026-11-25. Owner ruling #715 7157496515 Q2 (only HARD K1-K5 repairs stay); rpg-designer's classification posted as #715 7157686023 and recorded by the lead as 7157730160. Reason: dead code, with no live path and no behaviour. It may ride along as a dead-code removal if a lane is already in that file.
- Filed by rpg-planner.
- Also dead in the same family (rpg-implementer-3, blocker-churn fix): StrategicIntelligenceSystem.resolve_blockers (intelligence.py ~:845) has no caller and still completes a resolve_blocker project untyped (ended_by None). Delete it, or type its end (ProjectEnd.BLOCKER_CLEARED), with this ticket (rpg-designer, 2026-11-17).

## Test Summary

## Files Changed

## Completion Summary
