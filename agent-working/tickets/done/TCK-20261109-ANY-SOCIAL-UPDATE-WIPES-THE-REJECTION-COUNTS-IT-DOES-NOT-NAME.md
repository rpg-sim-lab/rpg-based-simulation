---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME
phase: done
date: 2026-11-09
tags: []
---

# TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME

## Title
Any social update wipes the rejection counts it does not name, so recruitment's social-fatigue penalty almost never builds up

## Status
DONE

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
- TCK-20261109-RECRUITMENT-FATIGUE-HAS-NO-RECENT-WINDOW (the counts are lifetime; the window is that ticket)
- TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD (follow-up investigation: no corpus world exercises this fix; filed by the lane that closes it)
- TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS (paydown ticket for the updates.py module-length raise)

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

**What was built (2026-11-11).** `src/core/social_counts.py::add_rejection_counts(base, increment)` is the one sum rule: it keeps every count in `base`, adds each `increment` entry and does not mutate. `RelationshipService.process_update` (relationships.py) and `SocialUpdate.merge` (updates.py) both call it. The first cut inlined the loop in both places and tripped three code-health rows; rpg-planner ruled the shared helper (one definition, not a line move). Keying is unchanged (`candidate.rejection_count[offerer]`); familiarity, debt, fear and salience stay last-writer-wins. Parity: new SOC-280 in `social_narrative.yaml`. No divergence entry (the measurement moved nothing). Staging artifacts (plan, investigation, test_plan) were written before the code.

**Ratchet.** One row rose: `src/core/updates.py` module-length 1315 to 1316 (the one import line). Owner #715 6785100551 raised it and named the paydown ticket TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS on the row. By the owner's new rule every raised ceiling names its paydown ticket, so the earlier `fused_strategic_pass` complexity row (437 to 438, owner #715 6776776165) now names TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE. The completeness pin moved scope 361 to 362 and unbound 255 to 256 (helper left unbound).

## Test Summary
- `tests/unit/social/test_rejection_counts_kept.py` (9 rows): trust-only update keeps the counts; an increment for one offerer keeps the other's; a new offerer is added beside existing counts; merge sums two same-tick rejections to 2; two offerers stay separate; merged-then-applied adds 2; merge does not sum familiarity; canonical-dict round trip; the appraisal fatigue penalty reads the kept count. On unfixed source 7 of the 9 failed (the other two are guards that hold before and after).
- `tests/unit/core/test_social_counts.py` (6 rows): empty, empty increment, empty base, disjoint, overlapping, no mutation.
- `tests/unit/social` + `tests/unit/core` + the completeness test at -n 1: 721 passed (before the main sync). mypy_gate rc 0. `codebase.health check` OK, 0 worse.
- Measurement (pinned runner, PYTHONHASHSEED=0, 5000 ticks, counting spy rejcount_spy.py sha256 66f46abf008fa3ceb5ebc1c58fd4b8016e6dc8387d3450c60f2bfd8bccb9182e, approved by rpg-designer): base main 5c6990e51 vs fix 8bcf033c8, 4 worlds (crowded_frontier, urban_political, frontier_living_world, highland_traverse) x seeds 42-46 = 40 spied cells, plus 4 plain unspied base s42 twins. All 20 pairs have identical final hashes; all 4 twins equal their spied cells. Spy counts: 0 recruitment appraisals, 0 accepted, 0 not-accepted, 0 LOYALTY_ACCEPTANCE passes, 0 loyalty-gate skips by fatigue, final rejection-count sum 0, in every cell on both arms.

## Files Changed
- `src/core/social_counts.py` (new), `src/core/updates.py`, `src/systems/social_systems/relationships.py`
- `tests/unit/social/test_rejection_counts_kept.py` (new), `tests/unit/core/test_social_counts.py` (new), `tests/unit/tools/test_mechanism_registry_completeness_check.py` (pin lines)
- `docs/parity_ledger/social_narrative.yaml` (SOC-280)
- `codebase/baselines/code_health_exceptions.jsonl` (two rows: updates.py module-length ceiling and value 1316 with its retiring ticket; `fused_strategic_pass` row names its retiring ticket)
- `agent-working/tickets/todos/TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS.md` (filed paydown ticket). The follow-up investigation TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD is filed by the lane that closes it, not by this PR.
- This ticket, moved to `done/`; its staging artifacts under `agent-working/stored_artifacts/`.

## Completion Summary
The wipe is fixed: an applied SocialUpdate keeps the rejection counts it does not name and adds its increment, and `SocialUpdate.merge` sums the increment per key. Bug Fix per rpg-designer's 2026-11-09 ruling.

Disclosure (rpg-designer, verbatim): "The fix is not exercised in any corpus world (crowded, urban, fliving, highland × 5 seeds × 5000: zero recruitment appraisals at SocialAppraisalSystem._appraise_recruitment). The world-level effect is unmeasured. Hash identity shows no side effect on these worlds. Not counted: stops before :83 (TOTAL_DISTRUST, BETRAYAL_HISTORY) and recruits outside appraise_contract. The hook was proven live by a direct appraise_contract call (CANCELLED/insufficient_incentive)."

Also recorded: per-seed tallies not computed; trajectories bit-identical, so every world × cause delta is 0 and no role changes. Recruit accepted 0 / rejected 0, LOYALTY_ACCEPTANCE 0; all 4 worlds are 0-offer worlds.

Known gap: recruitment not exercised in any measured world; world-level effect NOT MEASURED. The behaviour is shown by the unit rows only.
Known gap: all 20 base/fix pairs have identical final hashes, so the fix moves no measured trajectory.
Known gap: counts are lifetime, bounded by the 0.5 cap (5 rejections); the recent window is TCK-20261109-RECRUITMENT-FATIGUE-HAS-NO-RECENT-WINDOW.
Known gap: the spy counted appraisals through `SocialAppraisalSystem._appraise_recruitment`; appraisals stopped before it (TOTAL_DISTRUST, BETRAYAL_HISTORY) and recruits made outside appraise_contract are not counted.
Hot-loop: the apply runs once per social update applied; timing NOT MEASURED (perf pause, #715 6556861718).
Reviewer note: updates.py module-length 1315 to 1316, owner #715 6785100551, retiring ticket TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS; fused_strategic_pass's earlier +1 (owner #715 6776776165) now names TCK-20261101-FUSED-STRATEGIC-PASS-RESTRUCTURE as its retiring ticket.
