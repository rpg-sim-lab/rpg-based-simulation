---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261101-A-LOW-HP-VANGUARD-TAKES-ROLE-GATED-MOVES-INTO-CONTACT
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-LOW-HP-VANGUARD-TAKES-ROLE-GATED-MOVES-INTO-CONTACT

## Title
A VANGUARD below a hp line still takes role-gated moves (BRACKETING) into contact: counts first

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
This is the second child of TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER, filed by rpg-planner at rpg-designer's request on 2026-11-01. The VANGUARD BRACKETING branch (src/engine/tactical.py:542/:552) reads the role, not the entity's own hp. Two churn-on-F3 victims from ubuntu groups batch C took BRACKETING moves at low hp while being hit:
- urban s42 e23, VANGUARD at hp 32: hit 6 times by e17 (t1671-1686), died t1687. Ruled NOT FED for the churn fix (participation); provisional pending the retreat_destination probe.
- frontier s45 e22, at hp 35: ruled FED under the churn test (i), because group_bias 0.2 vs 1.0 changed its target. Its killers e13 and e1 were not the bias target. Positions are unknown, so the walk might have been the same without the group.

The sibling child TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET fixes target choice. This ticket covers role-gated MOVES at low hp.

## Scope
Counts first, with no fix shape before the counts and the designer's ruling:
1. On the standard seeds (base and current main), count per run the VANGUARD role-gated moves (BRACKETING and any other role branch at tactical.py:542-552) taken at hp below candidate lines (for example 25/35/50% of max), split by whether the entity was hit within the last 10 ticks.
2. Count deaths within 50t of such a move, with killer and cause, and whether the killer was the bracketed target.
3. Name the existing hp lines (flee line, LOW-HP-RETREAT branch) that a VANGUARD's role branch bypasses, with file:line.
Proposed rule, for the designer to confirm after the counts: below a hp line, a VANGUARD does not take role-gated moves into contact. The hp line is a content or tuning value, not a number in code.

## Out of Scope
- Target selection (the sibling self-defence ticket).
- Hazard weighting of moves (H1).
- The LOW-HP-RETREAT cornered / no-home-region gap (TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE).

## Acceptance Criteria
- The counts 1-3 are reported on base and main for the same seeds, and rpg-designer rules on the rule shape and the hp line.
- If a fix follows:
  - the hp line is read from content/tuning;
  - unit tests cover a low-hp VANGUARD not bracketing into contact, and a healthy VANGUARD unchanged;
  - deaths are paired under the death-STOP bar;
  - Bible ch.02 and the parity ledger are updated.
- Hot-loop: yes if fixed (the tactical branch runs per entity evaluation). Under the perf pause (#715 6556861718), timing is NOT MEASURED and is covered by checkpoint (a).

## Related Tickets
- TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER (parent)
- TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (sibling)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (churn; batch C evidence)
- TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE (FLEE-LINE)

## Related Docs
- docs/mechanics/02_combat_laws.md; docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
- ubuntu groups batch C traces (urban s42 e23; frontier s45 e22), via the churn ticket's evidence folder on origin rpg-ubuntu-group-id-alloc-impl.

## Related Code Areas
- src/engine/tactical.py:542/:552 (VANGUARD BRACKETING), :390-428 (target_score)

## Assumptions / Open Questions
- e22's role at its fed tick (VANGUARD or another role) is to be confirmed from the rows.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
