---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261103-TWO-UNOWNED-V3-STARVATIONS-APPEARED-ON-MAIN-WITH-THE-RETREAT-FIX
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-TWO-UNOWNED-V3-STARVATIONS-APPEARED-ON-MAIN-WITH-THE-RETREAT-FIX

## Title
Two unowned V3 starvation deaths show on main in crowded_frontier after #826, and the advisory gate report that showed them was not routed

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Requested by rpg-designer on 2026-11-03 after rpg-planner-ubuntu's pinned base showed crowded s42 e30 starving. rpg-planner then read the gate's rolling issue #669.

Gate report, run 41454964932, head 9ced8fb24 (pinned sequential, 5000t):
- `V3 [crowded_frontier/42]`: e30 leader, t2211, untried FORAGE, INN_MEAL, SCAVENGE. Unowned.
- `V3 [crowded_frontier/45]`: e37 raider, t2338, untried BUY, FORAGE, INN_MEAL, SCAVENGE, WORK_SHIFT. Unowned.

Both are listed NEW on the 2026-11-02 #669 comment. The previous run (41303978015, b9879de8f, 2026-11-01), which has F3 and lacks #826, did not list them. `git log 30307228c^..9ced8fb24 -- src data` shows only F3 and #826 (65d43dfa9). So they first show with #826.

Limit on that reading: it shows where they appear, not that #826's rule starved them. This metric has come and gone on crowded seeds with other changes (#669: `V3 [crowded_frontier/42]` RESOLVED 2026-10-30, `V3 [crowded_frontier/46]` NEW 2026-10-30, RESOLVED 2026-11-01), and any behaviour change reroutes the world.

How it reached main unnoticed: the gate is a daily scheduled advisory report (.github/workflows/rpg-gate-report.yml, no push or pull_request trigger), so no gate ran at #826's close. #826's own close used a concurrent-path `_run_engine` table at 2000t, before t2211 and t2338. The report came about 3 hours after the merge and was not routed. rpg-planner saw it only on 2026-11-03.

Not a credit to ENG: e844e2845 lacking the record on s42 is a different world (rpg-designer). It doesn't touch #828's gate, which judges its arm alone, or ENG's order.

## Scope
1. Each subject's last stretch from rows on the pinned base 65d43dfa9, with the same questions as e34: hunger project and way; goal scores, winner and runner-up; cap refusals with SUSPENDED count; tactical reason; group and contract; each way open or closed with its reason, and whether it is really admitted; ticks crossing hunger 60 and 95 with hp; last meal. Hash equal to the paired base.
2. FED test against #826: did a step #826 changed (retreat completion, cap exemption) select what displaced the need? Compare on 30307228c at the same seed where it helps. Verdict: fed / pre-existing gap / not shown.
3. A verdict goes to rpg-designer, then the owner through lead-planner-u24. Known entries are the owner's only; nothing is added here.
4. Routing: who reads #669 when it goes NEW on an unowned V3. rpg-planner proposes reading it after each RPG merge, and a merge-time note for hand merges. Whether it should be a pre-merge check is for testing-planner and the owner (cost: 50-60 min).

## Out of Scope
- #826's pinned re-measure (ordered separately; its table may add evidence).
- ENG, N14, row 88.
- Other findings on #669 (V1 counts are outside this ticket).

## Acceptance Criteria
- Both last stretches read, with direct reads and inference marked, and a verdict for each from rpg-designer.
- The owner has the row if a merged fix fed either, or a known-entry decision is needed.
- The routing decision is recorded.
- Hot-loop: no (no code yet). A fix is its own ticket.

## Related Tickets
- TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT (#826)
- TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED (ENG)
- TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
- TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-06, SURV-07)
- docs/plans/systemic_world/owner_decision_memo.md rows 54, 56, 83, 88

## Related Stored Artifacts
- Issue #669, run 41454964932; /mnt/data2/rpg-measure/results/65d43dfa9f2b-72320cac-5000/

## Related Code Areas
- tools/test_architecture/rpg_gate_known.yaml, .github/workflows/rpg-gate-report.yml
- src/ai/goals/present_threat.py, src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- b9879de8f's source equals F3's for this purpose: only #826 changes src or data after F3, by git log.
- Row 88's panic line may come up once rows are read (rpg-designer); no guess here.
- Dispatch of the reads: rpg-planner orders them as part of the #826 re-measure, already owner-ordered by rpg-designer's ruling; any fix needs an owner yes.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
