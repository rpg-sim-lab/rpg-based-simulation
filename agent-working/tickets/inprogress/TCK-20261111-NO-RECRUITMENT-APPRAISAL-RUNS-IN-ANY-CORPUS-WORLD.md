---
status: active
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD
phase: open
date: 2026-11-11
tags: []
---

# TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD

## Title
No recruitment appraisal runs in any measured corpus world. Find out whether recruitment is dead by defect or goes around the appraisal by design.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
This was found by the P1 measurement of TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME. rpg-designer ruled on 2026-11-11 to file it as an investigation. rpg-planner filed it the same day.

The run was 40 spied cells: crowded_frontier, urban_political, frontier_living_world and highland_traverse, seeds 42-46, 5000 ticks, two arms (main 5c6990e51 and fix 8bcf033c8). The spy is at /mnt/data2/scratch-c3/rejcount_spy.py, sha256 66f46abf…182e, approved by the designer. Results are in /mnt/data2/rpg-measure/results/{5c6990e51c2c,8bcf033c8898}-72320cac-5000/spy_*.json.
- ZERO recruitment appraisals were recorded at `SocialAppraisalSystem._appraise_recruitment` in any cell: accepted 0, rejected 0, LOYALTY_ACCEPTANCE 0, and the final rejection-count sum was 0 everywhere.
- A direct `appraise_contract` call on a RECRUITMENT contract did record a row (CANCELLED/insufficient_incentive), so the hook works.

The prior evidence points to a bypass, not to a dead mechanism. It is a lead, not proven:
- TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION (done) wired the accept half of recruitment through the cooperation path. `CooperationDecisionService.find_pending_incoming_offer()` (src/domains/cooperation/services.py) accepts any qualifying OFFERED RECRUITMENT contract via JOIN_PARTY, with "no trust check … no rejection path at all". The acceptance criteria are deferred as D-09 (docs/plans/deferred_tuning_decisions_register.md).
- Open todos show recruit contracts being created and accepted in play. TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE has crowded s42 entity 19 holding 12 ACTIVE recruit contracts at t100. TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS has groups formed on recruit contracts, with REQUEST_HELP / HIRE_SUPPORT going to `ContractService.create_recruitment_contract` at about :280.
- If that holds, the appraisal's recruitment branch, and with it the rejection counts that P1 fixes and the loyalty gate, never runs in play. The fix would be correct on a branch that no world reaches.

This is not a duplicate. The 2026-09-12 investigation asked whether groups form at all, and D-09 defers how acceptance should be tuned. This ticket asks which path recruitment actually takes in play, and whether the appraisal's recruitment branch is reachable.

## Scope
1. Measure first, read-only. One spy, which rpg-designer approves at a sha before it runs. Same 4 worlds × s42-46 × 5000 ticks on current main, and each spied cell's final hash must equal its plain twin. A mismatch is a STOP. It counts, per world and seed:
   - (a) RECRUITMENT contracts created, by creation site: src/systems/social_systems/contracts.py:124, src/engine/domain/core_actions.py:168, and cooperation's create_recruitment_contract path (about :280). Name any other site found.
   - (b) recruitment contracts stopped before :83 (TOTAL_DISTRUST, BETRAYAL_HISTORY);
   - (c) JOIN_PARTY selections, and how many groups form by each path (cooperation accept vs appraisal accept vs other);
   - (d) recruitment appraisals at `_appraise_recruitment`, to cross-check the P1 zero.
2. A code read naming every way a RECRUITMENT contract goes from OFFERED to ACTIVE or CANCELLED on main, with file:line.
3. rpg-designer rules. The test was fixed on 2026-11-11, before any rows: "dead" means zero RECRUITMENT contracts created in all 20 cells while groups still form, or a creation site that can never be reached. A bypass (contracts created and accepted without the appraisal) is a separate outcome the designer rules on: it may be by design, or a defect.
   Bypass test, fixed by rpg-designer on 2026-11-11 before any rows, ruled in this order:
   - DEAD: as above.
   - BYPASS BY DESIGN needs all four of these:
     - (i) every OFFERED→ACTIVE recruitment in every cell goes through find_pending_incoming_offer / JOIN_PARTY, or another path the 09-12 ticket or D-09 names; groups formed by the appraisal path = 0, and (d) = 0;
     - (ii) the code read shows `_appraise_recruitment` has no live caller for an OFFERED recruitment contract on main;
     - (iii) the 09-12 investigation's own trace shows the appraisal branch was already unreached before that wiring (cite its investigation.md line);
     - (iv) neither Bible ch07 nor the parity ledger states, as verified law, that trust, LOYALTY_ACCEPTANCE or rejection counts decide recruitment acceptance in play.
   - BYPASS AS DEFECT if (ii) fails (a live appraisal caller is shadowed by cooperation accepting first), or (iii) fails (the wiring replaced a working path), or (iv) fails (the docs claim what play skips). If only (iv) fails, the ruling is BY DESIGN WITH A PARITY GAP: a docs and ledger fix only (D-09's minimal accept stated as current law, plus a divergence entry).
   - MIXED: (d) > 0 in some cells. P1 is re-measured in those cells as a follow-up.
   - Optional spy addition: at each cooperation accept, a SHADOW verdict, i.e. what `appraise_contract` would have returned (status plus reason). Allowed only if appraise_contract is pure on main (no RNG draw, no state write, no cache), shown by the script's own code read and backed by the hash match. Inputs and verdicts only; the designer does the classing. If it isn't pure, drop it and say so.
4. No fix in this ticket. The investigation ends with the rows, the path map and the ruling. A fix, if any, is a new ticket.

## Out of Scope
- Tuning the acceptance criteria (D-09).
- The lodger and many-contracts todos named above. This ticket only cites them.
- Re-measuring P1. If this ticket finds a world where the appraisal runs, re-measuring P1 there is a follow-up (rpg-designer, 2026-11-11), not part of this ticket.

## Acceptance Criteria
- Per world and seed, counts for (a)-(d), from a designer-approved, hash-matched spy.
- A path map from OFFERED to the end state, with file:line on main.
- rpg-designer's ruling recorded: dead by defect, bypass by design, or bypass as a defect.

## Related Tickets
- TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME (where this was found)
- TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION (done; the JOIN_PARTY wiring)
- TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE
- TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS
- TCK-20261109-RECRUITMENT-FATIGUE-HAS-NO-RECENT-WINDOW (parked; depends on whether the appraisal runs)

## Related Docs
- docs/mechanics/07_social_political_dynamics.md (trust appraisal, contracts)
- docs/plans/deferred_tuning_decisions_register.md (D-09)
- docs/world_rules/social-lineage/social-relations.md (SOC-05)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260912-PARTY-FORMATION-REACHABILITY-INVESTIGATION/

## Related Code Areas
- src/systems/social_systems/appraisal.py (`_appraise_recruitment`, :83)
- src/systems/social_systems/contracts.py (:124)
- src/engine/domain/core_actions.py (:168)
- src/domains/cooperation/services.py (:53, :163, about :280; find_pending_incoming_offer)

## Assumptions / Open Questions
- The bypass reading comes from earlier tickets, measured on older trees. Re-measure on current main; don't carry the old counts forward.
- Host: one heavy process. Queued after lane B's P2 runs.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
