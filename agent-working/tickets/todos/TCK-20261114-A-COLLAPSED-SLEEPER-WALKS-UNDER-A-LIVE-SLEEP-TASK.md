---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261114-A-COLLAPSED-SLEEPER-WALKS-UNDER-A-LIVE-SLEEP-TASK
phase: open
date: 2026-11-14
tags: []
---

# TCK-20261114-A-COLLAPSED-SLEEPER-WALKS-UNDER-A-LIVE-SLEEP-TASK

## Title
A collapsed sleeper with a live SLEEP task walks, under HOLD, to a MOVE_TO target

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by the HOLD spy (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, finding (b), lane A 2026-11-14). In frontier_marches s42 (5000t), 12 HOLD steps were taken by collapse-class subjects whose SLEEP task was still live (status hold_task_live), branch target_set_no_move_task, target written by a MOVE_TO intent at src/engine/intent/action_intent.py:137. They provoked no OA. They passed the 10x HOLD price only through the reroute rung (TCK-20261114-REROUTE-RUNG-STEPS-PAST-THE-READINESS-GATE-AND-STATUS-BLOCK). The collapse law (divergence 2.105 / SURV-02 amendment, decision 41; 2.115 "a collapse holds until below the collapse line") says a collapsed subject stays where it stands.

Designer (rpg-designer, 2026-11-14, session message): P2, breaks the collapse law; the open question is who issues the action_intent.py:137 MOVE_TO to a collapsed sleeper.

## Scope
1. Read-only first: name the issuer of the MOVE_TO to a collapsed sleeper (call site, decision source, cadence), from the HOLD cell rows and code; count such intents per world.
2. Designer rules the meaning and fix shape after the read.

## Out of Scope
- HOLD lifecycle (HOLD ticket); the reroute bypass (reroute ticket).

## Acceptance Criteria
- Issuer named with evidence; designer ruling recorded; then fix or close per ruling.

## Related Tickets
- TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP (found by)
- TCK-20261114-REROUTE-RUNG-STEPS-PAST-THE-READINESS-GATE-AND-STATUS-BLOCK (12 fm rows shared)
- TCK-20261011-HUNGER-WAKES-A-SLEEPER, TCK-20261009-SLEEP-DEBT-WEAKENS-THEN-COLLAPSES-THE-SUBJECT-WHERE-IT-STANDS-NO-HP-LOSS

## Related Docs
- docs/guidelines/intentional_divergences.md 2.105, 2.115
- docs/mechanics/04_strategic_cognition.md (Standing Needs Escalate)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/briefs/hold-cells-report.md (off-repo)

## Related Code Areas
- src/engine/intent/action_intent.py:137 (MOVE_TO), src/engine/sleep_debt.py:71 (collapse HOLD writer)

## Assumptions / Open Questions
- Who issues the MOVE_TO?

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
