---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER
phase: done
date: 2026-10-29
tags: []
---

# TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER

## Title
A dispatch that fails the same way more than 1100 times (EAT at a non-serving building, SOURCE_MISSING) never becomes a blocker, so the subject loops in place until it dies

## Status
DONE (merge accepted by the owner on the evidence, #715 7165253893; K2 only, K3 is its own ticket)

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Finding from rpg-designer (2026-10-29), based on rpg-implementer-2's D73 trace3: urban_political s46, tree 58c0821dc (src = 7cfd2cc0c), pure. Data: /mnt/data/scratch-rpg-implementer-2/d73/trace3/d73_s46.jsonl.
- Hero 22 stands next to building 20000 at (32,19) with path_len 0.
- Every tick, the router dispatches EAT at 20000. It fails with SOURCE_MISSING (nav.last_failure_reason SOURCE_MISSING).
- _hold_in_place (src/engine/domain/action_router.py:74) clears the target, and the hunger goal points back at the same building.
- This loops from about t800 until death, 1100+ ticks.
- Bible 04 / intelligence contract STRAT-191-194: infer_blockers() (src/systems/strategic_systems/intelligence.py about l.176) produces BlockerState from recent failures. Nothing learned from this one.
- First reading of the code (rpg-planner, not verified): infer_blockers maps navigation failures (PATH_NOT_FOUND, STUCK, OSCILLATING), congestion (wait or oscillation counts), and INTERACT capacity failures on harvesting projects. A failed EAT/service action with SOURCE_MISSING has no branch.
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO removes this instance. Any other wrong dispatch would loop the same way.

## Scope
Counts first. Numbers go to rpg-designer through rpg-planner before any fix shape:
- Why the repeated SOURCE_MISSING does not reach infer_blockers. Is the failure not recorded where infer_blockers reads it, or is it not a kind it maps?
- How often a same-target, same-reason action failure repeats 10 or more times in a row, on the gate worlds s42-46 (5000t), by action, reason and kind group. Use a pure probe: hash equal with and without it.
- Nav side, same class (rpg-designer, 2026-10-29). Crowded s46 worker 1 had 328 ticks of nav failure with reason position_swap, and no blocker was learned (c1610/w1c/). Urban s44 merchant 28 had occupancy_violation on every tick (CROWDED-SERVICE-DOOR case 1). Count which nav failure reasons reach infer_blockers and which do not: position_swap, occupancy_violation, PATH_NOT_FOUND, STUCK, OSCILLATING, and any others found. The fix shapes may split. Door congestion stays the DOOR ticket's own fix, but the count lives here.
- Design question for rpg-designer: should a failed service dispatch become a blocker that closes that way for the subject (and with what decay or expiry)?

## Out of Scope
- Fixing the earn arrival dispatch (the EARN ticket).
- Any fix before rpg-designer's ruling.

## Acceptance Criteria
- A counts table plus a cause statement (not recorded vs not mapped), sent to rpg-designer.
- If a fix is ruled:
  - a real-kernel test where a subject whose service dispatch fails N times gets a blocker, and the goal stops re-targeting that way;
  - a test where a single transient failure does not block;
  - Bible 04 STRAT-191-194 text, a parity ledger entry, a divergence entry;
  - a paired run.

## Related Tickets
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1

## Related Docs
- docs/mechanics/04_strategic_cognition.md (blockers, STRAT-191-194)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER/ (plan.md, investigation.md, test_plan.md; the plan was written before any code)

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (infer_blockers)
- src/engine/domain/action_router.py (_hold_in_place)
- src/core/strategic.py (BlockerState)

## Assumptions / Open Questions
Plan, investigation and test plan: agent-working/staging_artifacts/TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER/ (written before code). Open questions 1-6 are in plan.md section 7.
- Not a D73 blocker. Sequence after EARN. Not dispatched.

## Implementation Notes
Owner order: #715 7159601467 ("Skip stage 1, fix K2 then K3"), merge ruling #715 7165253893 ("Merge K2 on this evidence"). Rulings (rpg-planner and rpg-designer, rpg-designer-k2-fix-plan-rulings.md a73bc655d487395b): BOTH pieces, the root first, as separate commits; count only (no ends-held reason added); the existing soft blocker effect; N = 4, window 20, severity 0.5, all from data; the #996 experience memory not used; the two dead infer_blockers branches untouched (their own ticket).
(A) one shared bed-refusal predicate `service_admission.no_bed_for` (no free bed OR, in `finds_no_bed`'s own scope by the keeps_coin trait, the bed cannot be paid); asked by the fatigue arrival and the first REST execution; a broke subject's fatigue project ends with the existing typed WAY_CLOSED.
(B) a typed `ServiceRefusal` record on the navigation (cleared when the way is delivered), `infer_blockers` phase 5 files `blocker_service_<action>_<building>` (BlockerKind.ACCESS) after N consecutive counted refusals, expiry by the existing 200-tick quiet spell; limit, window, counted reasons and severity are data in `blocker_settings.yaml`.
Also in this change: the K2/K3 re-count kit (tools/rpg_measure/k2k3_count_*, merged from rpg-k2k3-count-kit) and the own-job kit v1-v3 sources (tools/rpg_measure/k2fix_ownjob_*), the evidence tools.

## Test Summary
New: tests/unit/engine/test_no_bed_for_purse.py (5, (A)), tests/unit/strategic/test_service_refusal_blocker.py (18 incl. 3 real-kernel, (B)), tests/tools/test_k2k3_count_kit.py (kit v6), tests/tools/test_k2fix_ownjob_kit.py (kit v3). Mutants m1-m4 of (B) each fail their control (scratch self-check).
NO-WRONG-CLOSE evidence for (A) (scope by the keeps_coin trait, never a "person" class): `test_a_body_without_the_coin_trait_and_a_building_without_beds_are_unchanged` (a body without keeps_coin_and_trades is unchanged; a building that declares no beds is unchanged), `test_a_subject_with_the_price_still_gets_the_rest_and_the_bed_at_arrival` (a payer is still served and lodged), `test_a_broke_keeps_coin_subject_arriving_at_a_lodging_inn_ends_way_closed_with_no_rest_dispatched`, and the unchanged tests/unit/engine/test_lodging_no_bed_and_arrival.py.
FOUR FORCED PINS (additive; each still asserts an exact set or number; edited with rpg-planner's ruling): tests/unit/engine/test_checkpoint_fields.py::test_a_navigation_without_lodged_in_restores_to_none_keeps_every_other_field_and_the_state_ticks and ::test_a_navigation_without_last_moved_tick_restores_to_never_stepped_and_keeps_every_other_field (the trailing field lists gain service_refusals), tests/unit/engine/test_checkpoint_group_fields.py::test_every_rule_names_its_ruling_and_the_step_is_the_only_caller (the FIELD_RULES set gains service_refusals), tests/unit/tools/test_mechanism_registry_completeness_check.py::test_wider_scope_numbers_pinned (scope_files 387 -> 388 and unbound_files 273 -> 274, from the check's own output).
The gates and full-directory results of the PR stage are in the PR body draft.

## Files Changed
src: core/service_refusals.py (new), core/navigation_component.py, core/updates.py, core/strategic.py, engine/service_admission.py, engine/building_arrival.py, engine/building_services.py, engine/domain/action_router.py, engine/patches.py, engine/apply.py, engine/checkpoint_fields.py, replay/fingerprint.py, systems/strategic_systems/blocker_lifecycle.py, systems/strategic_systems/intelligence.py, content/blocker_settings.py, content/schema.py, content/matrix.py; data/content/strategy/blocker_settings.yaml. docs: mechanics/04_strategic_cognition.md, mechanics/content_usage_matrix.md, guidelines/intentional_divergences.md (2.227), parity_ledger/strategic_cognition.yaml (STRAT-358), REGISTRY.yaml. tests: the four above plus the 4 pins. tools/rpg_measure: k2k3_count_* and k2fix_ownjob_* (spies, summaries, launchers). agent-working: this ticket and its stored artifacts, the monitoring shards.

## Completion Summary
K2 (a service dispatch that keeps failing never became a blocker) is fixed in two pieces and merged on the owner's ruling. EVIDENCE CHAIN: before the fix, kit v6 on main found K2 = 3 runs over 100 ticks (urban_political s42 2,400 ticks, REST at inn 20003, gold 0, not lodged; designer's read ff612c4c); the decisive run on the fix tree (the same cell, the same approved kit v6) found K2 = 0 (designer's read 4c31f8d1); the own-job run 1 (kit v2) found B(ii) false fires = 0 and B(iii) still looping = 0 in all four cells (designer's read 48bfbac0); (B) never fired in the gate worlds once (A) closed the loop (B(i) = 0, no refusal recorded).
DISCLOSED: A(i) (which half refused) is PARTLY RESOLVED, for attribution only: in run 1 every one of the 21 fix-arm WAY_CLOSED ends resolved to no building (other_unresolved, NOT MEASURED), the gold at each end was 0 or 5 (below the REST price 10); the re-run on kit v3 stopped on a serialization defect of the kit (a None key in a sorted dict) and was held by the owner's rule, so the split by half is not claimed and no neutrality bar applies (the fix acted in every cell). BALANCE: frontier_living_world s42 sleep_debt >= 98 reaches 30 subjects on the fix against 25 on main (urban 19 -> 18 and 17 -> 15, crowded 6 -> 5); on main 21 of the 25 reach it at tick 1961, never slept and never lodged, with gold 0 (designer files 00209194 / 890fba14): a cohort behaviour that exists on main, tracked as TCK-20261125-A-COHORT-IN-FRONTIER-NEVER-SLEEPS-FOR-ABOUT-2000-TICKS. The Q6 dead branches are TCK-20261125-TWO-INFER-BLOCKERS-BRANCHES-COMPARE-LOWERCASE-REASON-CODES-WITH-UPPERCASE-STRINGS. Limits: NO_BED_FREE names the bed, not the payment, for the purse half; a filed service blocker's fingerprint text reads "BlockerKind.ACCESS" where string-kind blockers read "access" (deterministic, self-consistent); the blocker closes the way softly (the existing x0.1 and the 0.2 need floor). K3 (TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH) is a separate change, not started.
