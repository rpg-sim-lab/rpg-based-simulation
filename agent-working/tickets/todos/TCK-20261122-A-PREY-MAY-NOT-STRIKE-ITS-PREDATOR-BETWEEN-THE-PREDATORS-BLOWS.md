---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS

## Title
Attack permission is asymmetric and transient for wild pairs: a prey may strike its predator only on the tick the predator's task names it, breaking CONFLICT-03

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
rpg-designer's ruling on motive stage 2 (#715 7076126573), Defect 2. It is pre-existing, in both arms, and a HARD correctness item.
- The goblin DOES try to fight back, and the legality wrapper caught every refusal:
  - NEW s42: 8 of 9 calls refused FRIENDLY_FIRE_ILLEGAL (wolves 46 and 47, all at distance 1);
  - NEW s45: 26 refused;
  - BASE s45: 19 refused.
- The cause (inspected, 87792e3e8 src/engine/hostility.py:109-118, attack_allowed): with a wild creature on either side the faction verdict is dropped, so an attack is allowed only if (i) the ATTACKER hunts the target (PREDATION), or (ii) the target's task payload target_id == the attacker and the target's relation to the attacker is an attack relation.
- At every refused tick, the wolf's payload target_id is None: it is between blows, in mode REPOSITION/WANDER, while its relation to the goblin is PREDATION.
- CONFLICT-03, an accepted rule: "if A may attack B, then B may attack A … It never differs in whether it is ALLOWED to fight back." This is a defect of an accepted rule. It is also the prerequisite of Step B.

## Scope
1. Permission is a property of the PAIR. An attack is allowed when the faction verdict allows it, or when EITHER party's appraisal of the other is PREDATION, so B may attack A whenever A may attack B. The target's current task no longer matters for PERMISSION (designer's fix direction). Whether B CHOOSES to strike stays in the decision layer (Step B).
2. Tests, each with a failing control:
   - B0: a prey's strike on its predator between the predator's blows (payload None) is LEGAL. N = 2 kind pairs by properties × 3 seeds, all holding.
   - A non-hunting, non-hostile pair is still refused.
   - Symmetry: for each sampled pair, allowed(A→B) == allowed(B→A).
3. Bible ch02 §7 (the legality and readiness gate), divergence (Bug Fix) and parity (DEV-016 and the legality entries) updated together. Check the DEV-016 text against the new attack_allowed.

## Out of Scope
- Choosing to fight back (Step B).
- The faction hostility tables.

## Acceptance Criteria
1. B0 and symmetry hold, and each fails on its control.
2. No new asymmetric path remains: a grep and read of every legality entry point, stated in the ticket.
3. Docs, divergence and parity updated; hash change disclosed.

## Related Tickets
- TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN (Step B depends on this)
- TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO (DEV-016, an earlier symmetry fix)

## Related Docs
- docs/world_rules/capability-progression/conflict-combat.md CONFLICT-03
- docs/mechanics/02_combat_laws.md §7

## Related Stored Artifacts
- /mnt/data2/rpg-measure/o3prime_stage2_83a752cd_designer_read/read_notes.txt

## Related Code Areas
- src/engine/hostility.py (attack_allowed); src/engine/legality.py (LegalityServiceV2); src/engine/domain/combat_actions.py:56

## Assumptions / Open Questions
- Whether the same transient-task condition exists in any other legality path is checked under AC2.

## Durable state, lifecycle and clocks
None.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
