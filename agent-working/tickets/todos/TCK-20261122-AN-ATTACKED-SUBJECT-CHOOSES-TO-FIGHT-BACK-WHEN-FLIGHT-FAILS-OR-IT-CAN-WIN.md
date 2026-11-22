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
2. Mechanic-scenario tests, with rpg-designer's REVISED invariants (2026-11-22, after the owner chose "Only if it judges it can win", relayed via lead-planner-u24 from #715). N = 2 property-chosen pairs × 3 seeds = 6 cases, all holding, each with a failing control.
   - The pre-registered can-win predicate: `can_win(subject, other)` = the SAME `can_overcome` judgement the engine's appraisal uses (src/engine/appraisal.py, the function behind PREDATION and WARY), evaluated by the subject about the other on the decision's state. No new formula. The plan cites its path and line. Any margin is a named constant in data, never inline.
   - B0 PERMISSION: a prey's strike on its predator between the predator's blows is LEGAL (dependency ticket, PR #992).
   - B1 CORNERED: with no legal retreat tile and under attack, it strikes back within 1 decision.
   - B2 CAN WIN, UNDER ATTACK: hit, and can_win true: it fights back and does not flee.
   - B3 OUTMATCHED WITH AN ESCAPE: can_win false, under attack, an open retreat: it flees, and doesn't turn while its flight succeeds.
   - B4 CAUGHT AGAIN AND AGAIN: hit 3 times inside its flight, it turns within 1 decision (3 is the scenario's threshold, in data if adopted).
   - B5 FIRST STRIKE ONLY IF IT CAN WIN (replaces the earlier B5 "no forced reflex" and B6 "no first strike, full tick"), both arms:
     - B5a: a subject facing a would-be predator that has NOT attacked it, with can_win FALSE, never strikes first: NO attack action over a full scheduler tick and a 50-tick window, run through the real kernel (lead-planner-u24's full-tick requirement, #715 7076325384, kept). It keeps distance or flees per Step A.
     - B5b: the same scene with can_win TRUE (a clearly stronger, healthy subject, neutral disposition): it strikes first within 2 decisions in all 6 cases. The fixture names its disposition so "may" is deterministic here. It is never forced: the choice follows appraisal, disposition and condition.
     - B5c: swapping the kind labels while keeping identical properties gives identical choices (no kind-name rule).
   - B6 NO STALE FEAR (rpg-designer, 2026-11-22, from #992's test_9): when no basis remains for either party to strike (no faction verdict, no PREDATION, no recent hit), the flight guard does not hold the subject; it may flee or carry on. Rule: the guard's free-swing fear (felt_lethal_attacker, src/engine/felt_swing.py:16-38) counts an attacker only if that attacker may legally strike the subject NOW, by the same attack_allowed as the subject's own strike, so guard and strike-back lapse together. This flips #992's test_9 (an 11-tick-old hit by a fed wolf), which is a further owner ask at that point.
   - The catalog text: a THIRD AGENCY-07 amendment, "A first strike when it judges it can win", proposed by rpg-designer. It's sent for the owner's word-for-word check (via lead-planner-u24) and lands with the catalog-text ticket only after the owner's yes.
3. AGENCY-07 amendment evidence updated to SUPPORTED; Bible, divergence and parity.
4. A re-trace for points 5 and 6 on top of Step A (R7 and R6), with its own S9.

## Out of Scope
- Permission (the dependency ticket) and Step A's flight hold.

## Acceptance Criteria
1. B1-B6 (B5 in all three arms) hold in all 6 cases, and each fails on its control.
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
