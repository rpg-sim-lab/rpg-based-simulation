---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET

## Title
A group member keeps attacking the group's shared target while an adjacent hostile kills it: self-defence must outrank group_bias in target_score

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
This is a child of TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER: the smallest ENGAGE-BRACKETING step. rpg-designer filed it via rpg-planner on 2026-11-01, so it is ready for either option of the churn owner row (draft at main-checkout .claude/handover/drafts/rpg-designer-churn-e10-owner-row.md).
- (a) Hold the churn fix behind this rule.
- (b) Land churn with disclosure, with this rule ordered next.

Case: ubuntu groups batch C, Tier 2 crowded s43, churn-on-F3 arm. Victim e10 is the VANGUARD of group 10043 (leader 4, bound under the churn fix, shared target 30). Its killer e27 is ungrouped and killed it at t927.
- At t894, 30 and 27 were both adjacent to e10.
- Score key at src/engine/tactical.py:428: (not_adjacent, group_bias, is_current_target, -capability_confidence, hp, dist * pressure_dist_mod, id).
  - 30 scored (0, 0.1, 1, -0.584, 114, 1.0).
  - 27 scored (0, 1.0, 1, -0.584, 40, 1.0).
  - group_bias (trust-based focus fire, halved for VANGUARD, tactical.py:397-411) picked 30. Without it, hp would have picked the attacker 27.
- e10 kept BRACKETING 30 at t895-896 while 27 hit it. rpg-designer ruled this death FED under the churn test (i): the fix kept the group alive, and a pre-existing rule did the rest.

## Scope
1. Add a term to target_score ahead of group_bias: "is this hostile attacking me", meaning it hit this entity within N ticks. A hostile attacking the entity outranks the group's shared target, and the rest of the key keeps its order.
2. N is a content or tuning value (combat tuning or content data), NOT a number in code. The source of "hit me within N ticks" uses the existing typed attacker record (CombatComponent.last_attacker_id, plus a typed last-hit tick if one exists; else add one with a FieldRule and checkpoint coverage). It is not a free-form metadata read.
3. Scope is target selection only. Bracketing movement, REGROUP and hazard weighting stay in ENGAGE-BRACKETING / H1.

## Out of Scope
- The churn fix (TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS). rpg-designer: do NOT widen churn with this rule, because it changes combat targeting for everyone.
- Hazard weighting of BRACKETING/INTERCEPTING/REGROUP moves (H1, owner decision).
- Retuning group_bias or trust.

## Acceptance Criteria
- Unit tests:
  - e10's t894 position replayed as a unit case: adjacent shared target 30 vs adjacent attacker 27 that hit within N, so it picks 27;
  - plain focus fire unchanged when nobody is attacking the member: the shared target still wins via group_bias;
  - no change when the attacker is the shared target itself;
  - N read from content/tuning, with a test that changing it changes the window.
- Paired deaths under the death-STOP bar (Tier 1 / Tier 2) on the standard seeds, base vs fix. rpg-designer reads any Tier 2 set.
- Bible ch.02 (combat laws, tactical modifiers) and the parity ledger (combat_movement.yaml) are updated in the same change. An intentional_divergences entry is added if the Bible states the current order.
- Hot-loop: yes. target_score runs per hostile per evaluating entity. The added term is a field read and a compare. Under the perf pause (#715 6556861718), timing is NOT MEASURED and is covered by checkpoint (a).

## Related Tickets
- TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER (parent; H1/N3)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (churn; the owner row that orders this)
- TCK-20261021-A-SUBJECT-IN-A-FIGHT-IT-CHOSE-NEVER-DISENGAGES-AT-ITS-FLEE-LINE (FLEE-LINE, precedence chain)

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
- ubuntu groups batch C evidence: out_t2/crowded_frontier_s43.jsonl (rpg-planner-ubuntu raw read), via the churn ticket's evidence folder on origin rpg-ubuntu-group-id-alloc-impl.

## Related Code Areas
- src/engine/tactical.py:390-428 (target_score), :542/:552 (VANGUARD BRACKETING)
- src/core/death_cause.py, CombatComponent.last_attacker_id

## Assumptions / Open Questions
- Whether a typed last-hit tick exists on CombatComponent today. The investigation states it.
- Whether "attacking me" also covers a hostile whose current target is this entity but that has not hit yet. Assumed no (hit within N) unless rpg-designer widens it.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary

## 2026-11-01 owner order and post-answer correction (#715 6560083151)
- Owner chose (b): churn lands disclosed; this ticket is ordered NEXT (P1), measured on top of churn.
- Correction recorded on the owner comment: rpg-planner-ubuntu's later rows (out_t2/crowded_s43_e10.jsonl) show the bias held e10's target only about t894-897 of a 34-tick fight. After that e10 targeted its attacker and still died, and (ii) is at most partly met. So the rows do NOT show that this rule would have saved e10. The e10 unit case still pins the t894 ordering, and the paired re-measure judges the rule's effect. Do not claim saved deaths from e10. rpg-designer: "e10 does not prove a save; acceptance is paired deaths, not the e10 replay surviving." The e10 unit case asserts the PICK, not survival. The ticket stays P1 because the rule is still wrong (an attacker outranked by focus fire).
- e10's trust in leader 4 is 0.8, from bonds, matching the tuple.
