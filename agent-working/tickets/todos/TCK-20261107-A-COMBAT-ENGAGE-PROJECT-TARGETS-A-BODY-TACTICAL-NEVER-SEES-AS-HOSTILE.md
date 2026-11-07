---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261107-A-COMBAT-ENGAGE-PROJECT-TARGETS-A-BODY-TACTICAL-NEVER-SEES-AS-HOSTILE
phase: open
date: 2026-11-07
tags: []
---

# TCK-20261107-A-COMBAT-ENGAGE-PROJECT-TARGETS-A-BODY-TACTICAL-NEVER-SEES-AS-HOSTILE

## Title
A COMBAT_ENGAGE project can target a body tactical never sees as hostile, so it idles on a dead objective until it fails: counts first

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found in lane A's predator-45 trace (frontier s42, pinned, base 65d43dfa9 and ENG head e844e2845, hashes equal to paired). Requested by rpg-designer on 2026-11-07.

On e844, predator_hunter 45 holds COMBAT_ENGAGE projects with DEFEAT_ENEMY objectives on persons and creatures (25, 28, 30, 16, 5). Each is abandoned FAILED in turn and replaced. Its hood.hostiles is empty, so it runs the no-hostiles block, where pursue_objective returns None for DEFEAT_ENEMY (tactical_objective.py:124-126). The result: 107 empty no-op decisions in the window t3095-5000, parked one tile from an inn at (41,31), starving to hunger 100. A town group then avoids it and starves beside the inn (frontier s42, ENG's row). It was never hit and has no retreat project.

Hypothesis (rpg-designer): two definitions of "hostile". CombatEngageScorer (src/ai/goals/scorers.py ~:196-215) picks the nearest hostile by the strategic layer's test; tactical's classify_neighbours builds hood.hostiles by its own. When they disagree, the strategic layer adopts an objective tactical never pursues. It is the same dead-objective loop as ENG's hunt defect, by another door.

## Scope
Counts first, pinned runner, base and e844, per kind:
1. COMBAT_ENGAGE projects whose target is not in the subject's hood.hostiles at adoption and during the project's life.
2. Idle decision ticks under them, and how they end (FAILED, replaced, other).
3. Which needs went unmet meanwhile.
4. A code read of the two hostility tests side by side, file:line.
If the loop is common on both arms, it's a world-wide defect and ENG's part is incidental.

Fix lean (rpg-designer, after counts): one hostility predicate, read by the scorer and by tactical, so the strategic layer can't choose a fight tactical can't see.

## Out of Scope
- Why e844 keeps the engage project where base has FATIGUE (not needed, rpg-designer).
- ENG's hunt exemption (TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED).

## Acceptance Criteria
- Counts 1-4 reported, [D]/[I] marked; rpg-designer rules on the shape.
- If fixed: one predicate, tests for a target strategic and tactical disagree on, Bible 04 and parity updated, divergence id from u24's block (2.159, then 2.200-2.249).
- Hot-loop: yes if fixed (scorer and neighbour classification). Under the perf pause (#715 6556861718), timing is NOT MEASURED; say so at close.

## Related Tickets
- TCK-20261028-CURRENT-PROJECT-CLEARED-WITHOUT-ENDING-LEAVES-ORPHANED-ACTIVE-RECORDS (v9's objective-target mismatch is a cousin)
- TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED (ENG; the hunt case)
- TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- /mnt/data2/scratch-eng/p45_{65d43dfa9,e844e2845}.json (lane A, scratch)

## Related Code Areas
- src/ai/goals/scorers.py (CombatEngageScorer), src/engine/tactical_avoid.py (classify_neighbours), src/engine/tactical_objective.py:124-126, src/engine/tactical.py:278-290

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
