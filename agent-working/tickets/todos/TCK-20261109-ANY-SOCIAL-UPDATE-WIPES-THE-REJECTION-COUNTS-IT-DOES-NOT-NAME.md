---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME

## Title
Any social update wipes the rejection counts it does not name, so recruitment's social-fatigue penalty almost never builds up

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Finding F3 of the next-generation engine contract spec (architecture-planner-u24, child 4, §9, a static read of 1fb40ac76), relayed by lead-planner-u24 on 2026-11-09. rpg-planner checked it on main 1fb40ac76.

src/systems/social_systems/relationships.py:133 rebuilds the component with `rejection_count={k: social.rejection_count.get(k, 0) + v for k, v in update.rejection_increment.items()}`. The result keeps only the keys in this update's increment. Every applied SocialUpdate therefore drops every other source's count, including a trust-only or familiarity-only update with an empty increment.

The live reader is src/systems/social_systems/appraisal.py:125 (`_appraise_recruitment`, the "Domain 7 Hardening: Social Fatigue" penalty of -0.1 per recent rejection, capped at 0.5, which also gates the loyalty acceptance at < 0.2). The live writers are the five rejection paths in src/engine/domain/core_actions.py (:223, :296, :371, :477, :545). So a count above 1 survives only until the subject's next social update of any kind.

Related, from the same §9: F2. SocialUpdate.merge takes the last writer per key for rejection_increment (updates.py:384) and does not sum it. Two rejections of the same source in one tick count once.

## Scope
1. Make the apply keep the counts the update doesn't name, and add the increment to them. Do not drop them.
2. Make SocialUpdate.merge sum rejection_increment per key (F2, this field only).
3. Tests:
   - a trust-only update leaves rejection_count unchanged;
   - an increment for source A leaves source B's count;
   - two same-tick increments for A merge to 2;
   - the appraisal fatigue penalty reads the kept count.
4. The Bible and parity text: find the SOC entry for social fatigue (or add one), and record the change in intentional_divergences.md (u24 block, 2.200-2.249).
5. Paired measurement on the pinned runner, at the default tier plus the worlds where recruitment runs. rpg-designer sets the bar.

## Out of Scope
- The other F2 fields (familiarity, debt, fear, salience, which are last-writer-wins per key). Whether they should sum is a design question for rpg-designer and the next-generation engine contract, not this fix.
- Decay of rejection counts over time. "Recent" in appraisal implies a window, and none exists. Note it, and ask rpg-designer whether a decay belongs here.
- F1, F4, F5, F6 and F7 of the same §9.

## Acceptance Criteria
- The tests in Scope 3 pass.
- The paired measurement passes rpg-designer's bar, or its result is taken to the owner.
- The parity ledger and divergence entries are updated in the same PR.
- Hot-loop: maybe. The apply runs per social update applied. Under the perf pause (#715 6556861718), timing is NOT MEASURED; say so at close.

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (child 4, contract spec §9)
- TCK-20260619-E41-PARTY-LOOP (done), TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY (done)

## Related Docs
- docs/plans/architecture/next_generation_engine_contract_spec.md §9 (on architecture-next-generation-engine-epic)
- docs/plans/architecture/next_generation_engine_merge_inventory.md
- docs/world_rules/social-lineage/social-relations.md (SOC-05 recruitment)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/systems/social_systems/relationships.py:133
- src/core/updates.py:322-384 (SocialUpdate rejection_increment, merge)
- src/systems/social_systems/appraisal.py:125
- src/engine/domain/core_actions.py (rejection writers)

## Assumptions / Open Questions
- Is the wipe ever intended, as a reset of fatigue on any interaction? Nothing in the code says so, and the comment calls it fatigue from repeated offers. rpg-designer rules.
- Dispatch needs rpg-designer's priority ruling, under the depth rule (#715 6731764470), and a slot after the current RPG heads.

## Implementation Notes
2026-11-09 rpg-designer ruling (re-read on 1fb40ac76):
1. The wipe is a bug, not intended. Class: Bug Fix.
   - Bible 07 :65 and social_systems_contract.md :59 say only "social fatigue check".
   - Neighbouring fields (betrayal_count, combat_loss_counts, trust) are cumulative.
   - The keying is correct (candidate.rejection_count[offerer]); don't change it.
   - Add a divergence entry only if the paired measurement moves anything.
   - Parity: add a social_narrative.yaml entry, or amend the :3932 entry, citing the new unit test.
2. Decay is OUT of this ticket. The fix keeps the counts and sums the merge, nothing more. Disclose in the ticket and the parity note that counts are lifetime, bounded by the 0.5 cap (5 rejections). The window is TCK-20261109-RECRUITMENT-FATIGUE-HAS-NO-RECENT-WINDOW (P3). last_offer_tick is per subject, not per offerer, so it can't serve as the window.
3. Priority: after the current heads (flight, hardening and hit-wake re-measures, next-gen child 2, A+B).
   - Its own paired measurement, never sharing a base with those.
   - Bar: the standing death-stop bar, plus recruitment accepted and rejected counts per world. A move there is expected and is not a trip.
   - Report LOYALTY_ACCEPTANCE separately, since the < 0.2 gate now bites after 2 rejections.

Test rows (replace Scope 3):
- a trust-only SocialUpdate leaves rejection_count intact;
- a merge of two same-tick rejections from one offerer gives 2;
- two offerers stay separate;
- a round-trip through to_canonical_dict.

## Test Summary

## Files Changed

## Completion Summary
