---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN

## Title
Step B of the goblin-30 fix: an attacked subject chooses to fight back when its flight fails or it judges it can win (AGENCY-07 amendment "when to fight back")

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner point 4 (#715 7076062275), with its wording approved as the AGENCY-07 amendment "when to fight back" (#715 7076096298). The owner's order is to measure it as its own step after Step A (#715, "fix 1-3 first, point 4 as separate step").
BLOCKED on TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS: a prey can't fight back while its strike is illegal. Also after Step A, TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT.

## Scope
1. The decision layer weighs fighting back against fleeing for a subject under attack. It fights when its flight is failing (cornered, outpaced, or caught again and again) or when its own appraisal says it can win (the CONFLICT-03 appraisal). Kind-neutral; any threshold goes in data.
2. Mechanic-scenario tests, with the designer's invariants verbatim (drafts/rpg-planner-goblin-fix-invariants.md), N = 2 kind pairs by properties × 3 seeds, all holding, each with a failing control:
   - B1 cornered;
   - B2 can win;
   - B3 outmatched with an escape;
   - B4 caught again and again (3 is the test parameter, kept in data if adopted);
   - B5 no forced reflex.
   B0 permission lives in the dependency ticket (PR #992).
   - B6 NO FIRST STRIKE, FULL TICK (lead-planner-u24, #715 7076325384): a prey beside an idle hunting predator emits NO attack action over a full scheduler tick and a 50-tick window, run through the real kernel. #992's B5 pins only the appraisal that feeds the decision.
3. AGENCY-07 amendment evidence updated to SUPPORTED; Bible, divergence and parity.
4. A re-trace for points 5 and 6 on top of Step A (R7 and R6), with its own S9.

## Out of Scope
- Permission (the dependency ticket) and Step A's flight hold.

## Acceptance Criteria
1. B1-B5 hold in all 6 cases, and each fails on its control.
2. The re-trace is reported against Step A's.
3. Docs updated; hash change disclosed.

## Related Tickets
- TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS (depends on)
- TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT (Step A)
- TCK-20261122-A-FLEEING-SUBJECT-KEEPS-FLEEING-AND-AN-ATTACKED-ONE-WEIGHS-FIGHTING-BACK (the rules text)

## Related Docs
- docs/world_rules/knowledge-agency/agency-decision.md AGENCY-07 amendment "when to fight back"
- docs/world_rules/capability-progression/conflict-combat.md CONFLICT-03

## Related Stored Artifacts
- /mnt/data2/rpg-measure/o3prime_stage2_83a752cd_designer_read/read_notes.txt

## Related Code Areas
- src/engine/tactical.py, src/engine/tactical_flight_guard.py, src/engine/tactical_threat.py, the appraisal

## Assumptions / Open Questions
- How "flight is failing" is detected is engineering, ruled by rpg-designer at plan time.

## Durable state, lifecycle and clocks
Any "caught N times in this flight" counter must be typed, scoped to one flight, and end with it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
