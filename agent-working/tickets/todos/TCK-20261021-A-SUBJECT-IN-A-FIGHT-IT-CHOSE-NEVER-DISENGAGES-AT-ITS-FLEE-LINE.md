---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE
phase: open
date: 2026-10-21
tags: []
---

# TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE

## Title
A subject in a fight it chose never disengages at its flee line (crowded s44 merchant 12, hp 9 to 1 over about 200 ticks)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Lane A traced the crowded_frontier STOP cases for the corpse fix (TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT, 23fbe0ecf, 2026-10-21). On seed 44, new arm:
- Merchant 12 pursues raider 35 from t1851 at (25,24). The two attack each other every tick.
- The merchant loses about 9 hp per 21 ticks from t1856 and stays in ATTACK down to hp 1. It dies by COMBAT at t2066.
- The raider stays at about 25 hp throughout.
- The merchant's sleep_debt is 92.5 (context).

Bible 04 §1 puts flight (Tier 1) above any chosen goal, and the flee line exists for merchants: frontier merchant 37 panicked at hp 16 or below. So in a fight it chose, the merchant's flee line never fired.

The designer's ruling (2026-10-21): a defect independent of the corpse fix, since the same meeting would play out the same way in base. It does not block the STOP or v1, no V check catches it, and D78 keeps behaviour changes after v1. Disclosed in v1_disclosure.md as row C6.

## Scope
- Lane A's one-line cause, one of:
  - (a) the flee or retreat check isn't evaluated while pursuing or committed to ATTACK;
  - (b) it is evaluated, but the engagement's score beats retreat;
  - (c) appraisal rates the opponent as beatable.
  Cause letter: <pending>.
- Also: who started the pursuit, and why a merchant pursues a raider at all (which goal or scorer).
- The designer rules the shape, together with TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE and the D32 pursuing-hostile wake.
- Implement, add real-kernel tests (a subject in a chosen fight crosses its flee line and disengages), and measure paired against v1 (seeds 42-46, D76).

## Out of Scope
- The corpse fix and step 2 (before v1).
- Changing the flee line itself without a ruling.

## Acceptance Criteria
- The cause is named with evidence.
- A subject that chose a fight disengages at its flee line in a real-kernel test, and the s44 replay no longer shows ATTACK below the flee line.
- D76 shows no unexplained drift against v1, and C6 in v1_disclosure is closed with numbers.

## Related Tickets
- TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE
- TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET (D32)
- TCK-20261020-A-DEAD-BODY-IS-NOT-A-PERCEIVED-THREAT (which surfaced this)
- TCK-20261019-RECORD-BASELINE-V1

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1 (flight, Tier 1)
- docs/mechanics/02_combat_laws.md
- docs/plans/systemic_world/v1_disclosure.md (C6)

## Related Stored Artifacts
- Lane A traces: /mnt/data/scratch-rpg-implementer/paired_cn/traces/ (s44)

## Related Code Areas
- src/engine/tactical.py (panic and flee gate, emotion.is_fleeing)
- the combat engagement and pursuit scorers

## Assumptions / Open Questions
- Does sleep debt 92.5 change the flee line or the appraisal?

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
