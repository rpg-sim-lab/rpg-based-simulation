---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
phase: done
date: 2026-11-09
tags: []
---

# TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE

## Title
A COMBAT_RETREAT project walks its owner to the town centre through the strategic pass, against Bible 04's rule that a chosen retreat takes no step (held flight, memo row 91 (2))

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
In a kernel scene (hp 8/100, an acting hostile adjacent, no tactical retreat destination, a stored target elsewhere) the subject walks toward the town centre on base e512a40d9 from t16 and again from t22. The writer is src/systems/strategic_systems/intelligence.py:670 (fused_strategic_pass copies the active objective's target_position into the nav target), for the project built by CombatRetreatScorer (src/ai/goals/scorers.py:248-252, target state.town_center). Bible 04 section 1 says a chosen retreat is a stored target that takes no step (Chapter 2 section 7, CONFLICT-04) and the owner held the retreat flight (memo row 91 (2), measured as G).

## Scope
1. Confirm in a world scene (a real town centre, not the lodging fixture's default) that a COMBAT_RETREAT project walks its owner through the strategic pass. 2. rpg-designer scopes: keep the walk and fix the Bible sentence, or stop the strategic write for a retreat project. Measured as a behaviour step if code changes.

## Out of Scope
- The low-hp retreat hold of TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE.

## Acceptance Criteria
- The scoping is written and the designer's call recorded before any code.

## Related Tickets
- TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE

## Related Docs
- docs/mechanics/04_strategic_cognition.md (section 1, the wound escalates like a need)
- docs/guidelines/intentional_divergences.md (2.200)

## Related Stored Artifacts
- None.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (fused_strategic_pass, :670)
- src/ai/goals/scorers.py (CombatRetreatScorer, :248-252)

## Assumptions / Open Questions
- Dispatch needs an owner yes.

## Implementation Notes
Found by rpg-implementer on 2026-11-09 with a unit-run spy on NavigationUpdate; no code in this ticket yet.

2026-11-11 WIDENED (rpg-designer ruling on the non-flight P2 design; rpg-planner recorded it):
- The question is no longer just COMBAT_RETREAT. It is now: does ANY stored target (REGROUP, RETREAT, HOLD, WANDER) step while the subject is engaged? That is Bible 02 §7, "It leaves only by a decision … and that decision pays the opportunity attack" and "A strategic retreat … stays a stored target and takes no step". The answer is either option S2 ("an engaged subject with no decision on the tick takes no step") or a Bible text change. Either way it lands in intelligence.py or the movement phase.
- Not merged with TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING. That ticket stops only the felt-lethal step, at resolve_move's free-swing site, and lands first. This ticket's scoping is measured on a base that includes it.
- Evidence, the 8 stored-target rows from that ticket's Scope 1 trace (free_swing_trace.py sha256 7c22df89…, all hash-matched; outputs in /mnt/data2/scratch-b/fst_out/):
  - In each row the task at tick start was ENTITY_ACT with no decision on t or t-1, and the movement phase walked the stored navigation target into an opportunity attack.
  - The rows: crowded s42 #14 t323, #3 t2050, #12 t4971; crowded s43 #37 t1632, #12 t3053 (flight tree 83004a122); def2 crowded s43 #1 t2942, #8 t2795; def2 s45 #5 t1300 (tree 3300928e8).
  - The writers: fused_strategic_pass :678 (REGROUP) in 4 rows, and :670 (RETREAT/HOLD/REGROUP) in 3 rows. In the def2 #8 row the source is route_movement_intent:274 (WANDER).
- Note, rpg-planner: divergence 2.84 stops an entity holding an action task (ENTITY_ACT WITH a payload) from walking a left-behind target. The def2 rows are ENTITY_ACT with an EMPTY payload, so 2.84 does not cover them. Scope whether an empty held ENTITY_ACT is itself the defect. TCK-20261020-A-PURSUING-HOSTILE-WAKES-ITS-TARGET already asked that and recorded it as an open finding.
- intelligence.py stays on the hands-off list for this ticket. It is also the next-gen stage 3 slice (contract spec §8), and architecture-planner-u24 waits for this ticket to clear.

## Test Summary
No code lands. The tests written for shape (iii) lived on the parked branch `rpg-stored-target-engaged-step` (ea6417079, never pushed): scoped set 1 failed, 1248 passed, 3 skipped, 1 xfailed; the one failure was the corpus DEFEAT test, deliberately left red. Verification of this close: the spy cells' end hashes equal their plain twins (listed in `measurement.md`).

## Files Changed
Tickets, stored artifacts and two doc notes only. No src, tests, data or config. docs/parity_ledger/combat_movement.yaml COMB-342 `support_boundary` and docs/guidelines/intentional_divergences.md 2.89 "Disclosed shortfall" each gain the designer's re-measurement sentence (rpg-designer, 2026-11-13; owner). The Bible does not change.

## Completion Summary
Closed as MEASURED, NO CHANGE (hand-orchestrated, path-reason investigation_only). Owner decision: "(b) No change" (#715 6842890741, 2026-11-13); dispatch #715 6813573421; "(a) build and measure, then decide" #715 6818590421.

**Answer to the question.** Yes: a stored target (REGROUP, RETREAT, HOLD or WANDER) steps beside a hostile that is perceived and adjacent but not engaged, because the CONFLICT-04 movement gate (`MovementCandidateSelector.movement_target`, candidate_selector.py:176-178) counts only an *engaged* hostile (`hostility.is_engaged`: either side's task payload names the other), while the opportunity attack (`LegalityServiceV2.get_engaged_hostiles`) counts whoever is adjacent. Of the stepped rows, a perceived-but-unnamed hostile swung 63/64 (frontier_marches) and 75/75 (crowded_frontier); an unperceived one 1/68. An empty held `ENTITY_ACT` is not covered by 2.84, which needs a payload.

**What shape (iii) did.** Counting a perceived adjacent hostile in the gate (`adjacent_perceived_hostile`, shared with `move_ends_here`) cut undecided free-swing damage on fm s42 from 835 to 34, but brought the freeze back even with Decision 32's wake in place: 9440 gate-hold ticks (base 377), 23 holds of 50+ ticks in which the hostile landed no hit (longest 801, subject 7 vs 68, t3549-4349), and 3 holds still in force at tick 4999. That tripped the owner's freeze limit in the first fix cell; S2 stopped after 2 of 30 spied runs, the designer ruled the stop final, and the owner chose no change. **28 spied cells were never run**; the DEFEAT, COMBAT and STARVATION bars were not evaluated.

**Evidence.** `measurement.md` (hashes, sha256s, tables), `investigation.md` (code read with file:line), the two spies (stored_target_spy.py 8a122160, stored_target_fix_spy.py 9b3d3ca8) and the S2 driver. Raw results: /mnt/data2/rpg-measure/stored_target_s2/ (fix frontier_marches_42.json fcab40cb66f5…, base c48cb8e7beea…, four plain twins) and /mnt/data2/rpg-measure/storedtarget/.

**Never to land from the parked branch** (`rpg-stored-target-engaged-step` @ ea6417079): the Bible 02 §7 text, divergence 2.206, the COMB-342 text/evidence-name/boundary edits, the world_rules conflict-combat.md edit, the 2.89 "superseded by 2.206" note, the `adjacent_perceived_hostile` rename in candidate_selector.py and the test edits. Deleting the branch/worktrees is the user's call: delete list `rpg-stored-target-engaged-step`, worktrees `storedtarget`, `wt-st-base`, `wt-st-fix` (and `stclose` after merge).

**Known gap:** the loop behind the long holds is an UNTRACED hypothesis (a held subject and a hostile re-deciding into the held step: in the longest hold the stored_or_live and target_set_no_move_task branches alternate 401/400); the trace that would test it (fm s42 fix, subject 7 vs 68, t3549-3600) was not run.

**Findings, not tickets:** (a) fm's 149-row slice of a catalog-hostile adjacent neighbour the subject does not perceive at distance 1 goes to the producer investigation; (b) 4 crowded and 3 fm rows took swing damage while NOT stepping (LEGAL, occupancy or exhaustion failure), noted only.

Known gap: knowledge-index-update not run: worktrees use main's index (lead-planner-u24, 2026-11-12).
