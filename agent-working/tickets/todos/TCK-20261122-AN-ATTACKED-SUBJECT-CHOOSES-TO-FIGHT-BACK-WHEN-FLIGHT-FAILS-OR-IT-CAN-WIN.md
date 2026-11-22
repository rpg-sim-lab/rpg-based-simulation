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
ORDER (rpg-designer, 2026-11-22): Step A → decision-62 slice 1 (TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS) → this ticket → TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM.
Owner point 4 (#715 7076062275), with its wording approved as the AGENCY-07 amendment "when to fight back" (#715 7076096298). The owner's order is to measure it as its own step after Step A (#715, "fix 1-3 first, point 4 as separate step").
BLOCKED on TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS: a prey can't fight back while its strike is illegal. Also after Step A, TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT.

## Scope
1. The decision layer weighs fighting back against fleeing for a subject under attack. It fights when its flight is failing (cornered, outpaced, or caught again and again) or when its own appraisal says it can win (the CONFLICT-03 appraisal). Kind-neutral; any threshold goes in data.
2. RE-SCOPED 2026-11-22 after the owner's directions (#715 7078469868: ONE power-judgement component; fight dispositions declared per kind), from rpg-designer's text.
   - THE SEAM: `judge_power(observer, other, state) -> PowerJudgement`, typed {can_overcome: bool, basis: OBSERVED | REMEMBERED | DEFAULT, confidence: float}.
     - It lives in the perception layer, next to OpponentPerceptionService (src/domains/combat_engagement/perception.py).
     - v1 MAY delegate to the existing can_overcome judgement (basis DEFAULT, disclosed). Later versions use OpponentPerceptionService's observation and memory without callers changing.
     - Step B's can_win reads ONLY this seam. A source test asserts no inline power comparison in Step B's code, listing the two known bypasses (CONFLICT-03's PREDATION/WARY can_overcome; tactical_threat.py:93-94 apparent_power) as the allowed exceptions until TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM lands.
     - Those two do NOT move here: moving them is hash-moving and has its own ticket.
   - WAYS OF FIGHTING: read from the kind's DECLARED fight_disposition (decision 62's slice 1, a dependency; Step B does not introduce the declaration). Values: ALWAYS_FLEES, FIGHTS_BACK (the visible default), STRIKES_FIRST_IF_CAN_WIN. AGGRESSIVE and GUARDS/TERRITORIAL are later decision-62 slices and don't exist in Step B's code.
   - INVARIANTS: N = 2 property-chosen pairs × 3 seeds, all must hold, each with a failing control. Every fixture DECLARES its disposition.
     - B0 PERMISSION: a prey's strike on its predator between the predator's blows is LEGAL (PR #992); it's a fact about the pair, never about disposition.
     - B1 CORNERED, under attack, no legal retreat tile: FIGHTS_BACK and STRIKES_FIRST_IF_CAN_WIN strike back within 1 decision; ALWAYS_FLEES does not strike (it keeps trying to flee, or holds).
     - B2 CAN WIN, under attack: FIGHTS_BACK and STRIKES_FIRST fight back and do not flee; ALWAYS_FLEES flees.
     - B3 OUTMATCHED WITH AN ESCAPE: every disposition flees and does not turn while flight succeeds.
     - B4 CAUGHT AGAIN AND AGAIN (3 hits in flight; 3 in data if adopted): FIGHTS_BACK and STRIKES_FIRST turn within 1 decision; ALWAYS_FLEES keeps fleeing.
     - B5 FIRST STRIKE, not attacked, over a full scheduler tick + 50t through the real kernel (lead-planner-u24, #715 7076325384):
       - B5a: can_win false: no disposition strikes first;
       - B5b: can_win true: STRIKES_FIRST_IF_CAN_WIN strikes first within 2 decisions; FIGHTS_BACK and ALWAYS_FLEES never do;
       - B5c: identical properties AND an identical declared disposition give identical choices; changing only the kind label changes nothing.
     - B6 NO STALE FEAR (from #992's test_9): when no basis remains for either party to strike (no faction verdict, no PREDATION, no recent hit), the flight guard does not hold the subject. The guard's free-swing fear (felt_lethal_attacker, src/engine/felt_swing.py:16-38) counts an attacker only if it may legally strike the subject NOW, by the same attack_allowed. This flips #992's test_9, which is a further owner ask at that point.
     - B7 ONE SEAM: can_win is read only through judge_power. Control: a stub seam returning the opposite flips B5b's outcome.
   - THE CATALOG TEXT: the third AGENCY-07 amendment. The owner approved a first version (7078442937). rpg-designer then revised it for declared ways of fighting ("If its kind's declared way of fighting allows a first strike, …"), and that revision is APPROVED by the owner word for word (ask 7078497229, answer 7078502579; it replaces 7078442937's text). It lands with the catalog-text ticket.
3. AGENCY-07 amendment evidence updated to SUPPORTED; Bible, divergence and parity.
4. A re-trace for points 5 and 6 on top of Step A (R7 and R6), with its own S9.

## Out of Scope
- Permission (the dependency ticket) and Step A's flight hold.

## Acceptance Criteria
1. B0-B7 (B5 in all three arms, every disposition named in each) hold in all 6 cases, and each fails on its control.
2. The re-trace is reported against Step A's.
3. Docs updated; hash change disclosed.

## Related Tickets
- TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS (depends on)
- TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT (Step A)
- TCK-20261122-A-FLEEING-SUBJECT-KEEPS-FLEEING-AND-AN-ATTACKED-ONE-WEIGHS-FIGHTING-BACK (the rules text)
- TCK-20261109-M1-EACH-MONSTER-KIND-DECLARES-WHY-IT-FIGHTS (depends on its slice 1: the declared fight_disposition)
- TCK-20261122-EVERY-CAN-I-WIN-JUDGEMENT-GOES-THROUGH-ONE-POWER-SEAM (follow-up: routes the two known bypasses)

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
