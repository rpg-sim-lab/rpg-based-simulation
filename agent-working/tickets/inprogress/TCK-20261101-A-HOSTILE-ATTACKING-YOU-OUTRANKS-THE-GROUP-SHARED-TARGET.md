---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET
phase: implement
date: 2026-11-01
tags: []
---

# TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET

## Title
A group member keeps attacking the group's shared target while an adjacent hostile kills it: self-defence must outrank group_bias in target_score

## Status
INPROGRESS

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
2. N is a named constant registered in the deferred-tuning register (D-13), following D-11/D-12; not an unnamed literal (amended by rpg-designer, #634 6883797779; the original line is quoted under Assumptions / Open Questions). The source of "hit me within N ticks" is the typed hit record: `CombatComponent.last_hit_attackers` (every attacker of the last hit, from TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER) and `last_hit_tick`. It is not a free-form metadata read.
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
  - N is the named constant `ATTACKED_RECENTLY_WINDOW_TICKS` (D-13, value 10), with a test that patching it changes the window. No test pins it equal to the row 88 act-test window.
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
- Original scope line 2, replaced by the 2026-11-15 amendment (#634 6883797779): "N is a content or tuning value (combat tuning or content data), NOT a number in code."
- Resolved: a typed last-hit tick exists (`CombatComponent.last_hit_tick`); the attacker set comes from ticket 1 (`last_hit_attackers`).
- Whether "attacking me" also covers a hostile whose current target is this entity but that has not hit yet. Assumed no (hit within N) unless rpg-designer widens it.

## Implementation Notes

### Known gaps (measured, disclosed)
- Long felt-lethal holds on frontier s42, new arm: e36 held 107 ticks from t3754; e12 was held at the last tick. Both are untraced. The one traced, e7 (a2 re-run, spy fb478ec8, #634 6905649093): e7's 56-tick hold: its only felt attacker, e30, stayed engaged (orthogonally adjacent) throughout without targeting it. The free swing runs with is_lethal=False, so stepping away would have ended in a terminal DEFEAT rather than a COMBAT death; the felt estimate was right that stepping away was terminal. e7 died COMBAT at t4222 from e30's hit of 23 against hp 6. These are the existing 2.204 hold reached more often on ticket 2's trajectory; ticket 1 alone is byte-identical to base (a1).
- Urban fight deaths 34 -> 43, mostly seed 45 (people deaths 10 -> 20). Up in 2 of 5 seeds; no Tier 1 trip.
- Worker fight deaths up in every world: frontier 17 -> 25, urban 3 -> 11, crowded 36 -> 39. Untraced. Observed only; they are NOT ticket 2's intent.
- Urban flee episodes 64 -> 233, and perceived-hostile samples 1859 -> 3815.
- Measurement: base 5ba65854c vs new 437160ac3, ghpair Phase 1 PASS (D76 no drift in all 3 worlds), Phase 2 HOLD_STOP at frontier s42 (new 3 qualifying holds vs base 0); rpg-designer #634 6893463789; owner chose land-and-disclose, #715 6906659466. Hot-loop timing is NOT MEASURED (perf pause #715 6556861718).

## Test Summary
Run on merge head (origin/main c9279925b merged), pinned to CPUs 4-5, `-m "not slow"`: tests/architecture, tests/mechanic_scenarios, tests/unit/{ai,engine,movement,perf,progression,strategic,tactical}: 2790 passed, 3 skipped, 1 xfailed, 2 failed (run twice, same result).
- tests/architecture/test_no_name_switches_in_decision_paths.py: 58 passed (now gates src/world and src/core).
- Fail 1: tests/unit/perf/test_benchmark_record.py cpu_affinity case: the test's changed value "4-5" equals the pin used for the run; passes unpinned (67 passed). Environment artefact of the pin.
- Fail 2: tests/unit/tactical/test_low_hp_retreat_gate.py::test_a_held_retreat_does_not_walk_a_stored_target_through_the_kernel: fails when run after tests/architecture; passes alone and with every other directory. It fails the same way on a clean origin/main c9279925b archive (255 passed, 1 failed), so it is not from this batch. Cause not investigated; not fixed here.
- No code changed after the measurement: `git diff origin/main HEAD -- src tests` and `git diff 5ba65854c 437160ac3 -- src tests` hash alike (5b91a901...).
- Hot-loop timing: NOT MEASURED (perf pause #715 6556861718).

## Files Changed

## Completion Summary
Landed with disclosures (owner #715 6906659466, 'Land, disclose'; rpg-designer #634 6893463789): see Known gaps. Measurement base 5ba65854c vs new 437160ac3: ghpair Phase 1 PASS, Phase 2 HOLD_STOP at frontier s42. Not pushed; push needs an owner ask.

## 2026-11-01 owner order and post-answer correction (#715 6560083151)
- Owner chose (b): churn lands disclosed; this ticket is ordered NEXT (P1), measured on top of churn.
- Correction recorded on the owner comment: rpg-planner-ubuntu's later rows (out_t2/crowded_s43_e10.jsonl) show the bias held e10's target only about t894-897 of a 34-tick fight. After that e10 targeted its attacker and still died, and (ii) is at most partly met. So the rows do NOT show that this rule would have saved e10. The e10 unit case still pins the t894 ordering, and the paired re-measure judges the rule's effect. Do not claim saved deaths from e10. rpg-designer: "e10 does not prove a save; acceptance is paired deaths, not the e10 replay surviving." The e10 unit case asserts the PICK, not survival. The ticket stays P1 because the rule is still wrong (an attacker outranked by focus fire).
- e10's trust in leader 4 is 0.8, from bonds, matching the tuple.
