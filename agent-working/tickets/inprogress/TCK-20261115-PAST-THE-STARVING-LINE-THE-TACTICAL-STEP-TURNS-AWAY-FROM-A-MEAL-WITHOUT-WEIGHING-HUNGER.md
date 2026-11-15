---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER

## Title
Past the starving line, with a meal 1-2 ticks away, the tactical fight-or-flee step (a panic retreat or a chase) takes the subject away from the meal without weighing starvation (SURV-07)

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
D1 from the V3 trace. Owner choice: #715 6893303548, "(a) Two defect tickets (Recommended)", on rpg-designer's row .claude/handover/drafts/rpg-designer-v3-trace-owner-row.md. This is the cause of the V3 gate red after #884 (#669: crowded_frontier s45 e5 and s46 e4). Trace: spy b1500149 on tree 824483949, both cells hash-matched with 0 errors (/mnt/data2/rpg-measure/v3trace/cellA.json a0468694…, cellB.json cec87d05…).
- **s45 e5:** at t2155 the decision is PANIC_RETREAT, away from the inn. The subject has hp 1, hunger 100, the inn 2 ticks away, and e35 engaged. It dies of STARVATION at t2161.
- **s46 e4:** at t3226 the decision is a tactical ENTITY_MOVE with target_id 35, the pursuit branch (tactical.py ~:773 on 824483949). The subject has hp 32, hunger 100, the inn 1 tick away. It takes 2 hits at t3237 and dies of STARVATION at t3245, 2 ticks from the inn.
- SURV-07 (row 83) says that past the starving line, starvation is a present threat, weighed against the hostile threat, with neither winning by default. The goal level weighs it; these tactical branches do not.

## Scope
1. The design is rpg-designer's, written before dispatch. It folds in the designer's parked finding on branch order at hp < 15% (tactical ~:508). The planner and implementer plan from it, and the designer reviews.
2. Implement it, through typed state only, with the Bible 02 and 04 text, the parity ledger and a divergence entry in the same change.
3. Measurement: the death bar, 3 worlds × 5 seeds, paired (decision 76), with the §12.5 stop rules.

## Out of Scope
- The V3 way-open rule. The designer parked it as a P3 record-honesty item, with no ticket.
- The felt-lethal hold and its memory (the trace showed it was correct).
- D2, the walk-target reset (its own ticket).

## Acceptance Criteria
- Past the starving line with an open meal in reach, the tactical step weighs starvation against the threat, as SURV-07 says. Unit tests cover the two traced shapes, retreat and pursuit, and a control where the threat must still win.
- The paired run is inside its stop rules. The V3 rows cf/45 e5 and cf/46 e4 are resolved, or re-owned with a stated reason.
- Docs, ledger and divergence entry in the same change.

## Related Tickets
- TCK-20261115-THE-GO-TO-TOWN-STEP-RESETS-THE-WALK-TARGET-ON-A-TOWN-TILE (D2)
- TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING (#884, 2.204, where the V3 rows came from)
- TCK-20261111-FELT-LETHAL-MEMORY-HAS-NO-RECENCY-WINDOW (not reopened)

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-07, row 83)
- docs/mechanics/02_combat_laws.md, docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/tactical.py (PANIC_RETREAT sites ~:279/:535; pursuit ~:773; the branch order ~:508)

## Assumptions / Open Questions
- Landing hold: this moves crowded bases, so it doesn't land while HOLD stage 2 is measuring. The night-wrap ticket and D2 have the same hold.
- Dispatch is the owner's yes, through lead, after the designer's design.

## Implementation Notes
- 2026-11-15 (rpg-planner): rpg-designer's design v1 is FINAL, at main-checkout .claude/handover/drafts/rpg-designer-d1-starving-tactical-design.md. Step 0 (owner #715 6893555631; spy f349e5fd; a.json 15fb056c and b.json 4889b9d4, both REPRO_OK) confirmed the hypothesis:
  - A, t2155: e34 at distance 5 still counts as acting only through the hit term, so the subject panics away from an inn 2 ticks off.
  - B, t3226: e36 at distance 2 acts only through the hit term, so need_yields.
- The fix: past STARVING_LINE only, `_hit_acts_on` requires the hitter to still reach the subject (Manhattan <= max(1, hostile.combat.range)). Term (a) is unchanged, and the memo row 88 window below the line is unchanged. It is one predicate shared by need_yields, _panic_holds and acting_threat_to, and adds no new number.
- Dropped from v0: (i), engage only acting hostiles. B's target order comes from the group shared-target bias in TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (ubuntu), to be re-checked after that lands. The hp<15% branch order stays parked (0 of 8 attack returns were below 15%).
- Docs: Bible 04 LAW P, a Bug Fix divergence cross-referencing 2.135 and row 88, and a ledger row by COMB-346.
- Tests: 5 unit, 1 tactical and 1 real-kernel integration test (listed in the draft).
- Measurement: the paired 3x5 death bar, plus r1 (people starvation within 3 ticks of an open way) and r2 (COMBAT/DEFEAT of past-line subjects). An r2 Tier 1 rise is a STOP to rpg-designer. Then re-read the V3 cells.
- The plan goes to rpg-designer for review before Implement.

## Test Summary

## Files Changed

## Completion Summary
