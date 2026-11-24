---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT

## Title
Step A of the goblin-30 fix: a RESOLVED objective keeps pulling a subject, so a decided flight is pulled back toward the finished goal again and again; flight must hold while its threat holds

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
rpg-designer's ruling on motive stage 2 (#715 7076126573; read notes at /mnt/data2/rpg-measure/o3prime_stage2_83a752cd_designer_read/read_notes.txt; seal 4e97ee4d; VALID), Defect 1, attributed to #953/#954.
- NEW s42, goblin 30, t1801-2710 (dies t2610):
  - its current project is fatigue, with objective fatigue_20003 (reach_location, inn 20003) in status RESOLVED in 819 of 910 rows;
  - its mode is REGROUP for 691 ticks and RETREAT for 202, with 44 REGROUP→RETREAT and 44 RETREAT→REGROUP switches;
  - meanwhile wolf 46 holds THREATENING at distance 1 (goblin→wolf THREATENING, wolf→goblin PREDATION).
- So flight IS decided, and then pulled back to REGROUP toward the resolved goal.
- BASE s45, same goblin: the fatigue project is ACTIVE and flight holds (RETREAT 1012 of 1383 ticks, only 9 RETREAT→WANDER).
- This breaches owner point 1 ("a resolved goal never blocks"; Bible ch04 sentence) and point 3 (the AGENCY-07 amendment "flight holds once decided", owner #715 7076096298). Owner order: Step A = points 1-3, before Step B (#715, "fix 1-3 first, point 4 as separate step").

## Scope
1. (a) A project whose active objective is RESOLVED advances to its next objective or completes in the same pass, so it stops pulling (ch04 goal lifecycle).
2. (b) A decided flight holds while the same threat is present, per the AGENCY-07 amendment. Flight ends only when the threat term no longer holds, or at safety. The reach distance, safety and hysteresis are engineering; any constant goes in data.
3. Mechanic-scenario tests (the tests/mechanic_scenarios pattern), with the designer's invariants verbatim (drafts/rpg-planner-goblin-fix-invariants.md):
   - N = 2 kind pairs chosen by properties (for example wolf→goblin, wolf→small_plant_eater) × 3 fixed seeds = 6 cases, and ALL must hold;
   - A1 wary, no panic; A2 approach, then flee; A3 flight holds; A4 a resolved goal never blocks; A5 danger over need; A6 wakes when hit;
   - A7 NEED PATH YIELDS TO A PRESENT THREAT (rpg-designer, 2026-11-22, from #995's integration probe): a subject whose need step's route would put it adjacent to a hostile that is a present threat to it does not take that step; it flees or holds per A2/A3. One case is #995's broke variant of tests/integration/observability/test_starving_subject_eats_past_a_hitter_left_behind_through_the_real_kernel.py: a wounded gold-0 worker whose FORAGE route (opening_steps._forage_step, node 10005) runs onto a held raider's tile and dies at t25. That test lands as a STRICT xfail citing A7 and flips to pass when this ticket lands. The cause is pre-existing, EXPOSED by #781's free-meal removal (forage was never chosen while a free meal sat 2 tiles away). Probe: /mnt/data2/rpg-wt/freemeal-logs/read_probe_all.py 99245351…, scene1.txt.
     A SECOND case (rpg-designer, 2026-11-22): #995's broke variant of tests/integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py. A gold-0 merchant's own FORAGE steps at t5-t7, (42,31) → (42,30) → (42,29), pass a STILL predator at (41,30) at Chebyshev 1 (the metric counts only the merchant's own steps against the predator's prior tile). It's a STRICT xfail at #995 fb71ed342. Both xfails are this invariant's acceptance tests and flip to pass when A7 lands.
   - each with a failing control (the pre-fix tree, or the guard removed).
4. Bible ch04/AGENCY-07 evidence lines updated to SUPPORTED with the test paths; a divergence entry (Bug Fix) and parity.
5. A re-trace on the motive kit to judge points 5 and 6: R7 no-decision PASS in NEW s42/s45, and R6 NEW ≤ 2× BASE. That needs its own S9.

## Out of Scope
- Fighting back (Step B: TCK-20261122-AN-ATTACKED-SUBJECT-CHOOSES-TO-FIGHT-BACK-WHEN-FLIGHT-FAILS-OR-IT-CAN-WIN).
- The strike permission defect (TCK-20261122-A-PREY-MAY-NOT-STRIKE-ITS-PREDATOR-BETWEEN-THE-PREDATORS-BLOWS).
- Kind-specific logic of any sort.

## Acceptance Criteria
1. A1-A7 hold in all 6 cases, and each fails on its control.
2. The re-trace: R7 no-decision PASS where it failed, and R6 within 2× BASE.
3. Docs, divergence and parity updated in the same change; hash change disclosed.
4. Any changed existing test expectation is an owner ask.

## Related Tickets
- TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES (the bug candidate)
- TCK-20261122-A-FLEEING-SUBJECT-KEEPS-FLEEING-AND-AN-ATTACKED-ONE-WEIGHS-FIGHTING-BACK (the rules text)
- TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT

## Related Docs
- docs/mechanics/04_strategic_cognition.md §1 (the resolved-objective sentence) and §4
- docs/world_rules/knowledge-agency/agency-decision.md AGENCY-07 and its amendments

## Related Stored Artifacts
- /mnt/data2/rpg-measure/o3prime_stage2_83a752cd/ and its designer_read

## Related Code Areas
- the strategic project/objective lifecycle (src/systems/strategic_systems/intelligence.py, src/core/strategic.py)
- tactical flight (src/engine/tactical.py, src/engine/tactical_threat.py)

## Assumptions / Open Questions
- Whether (a) alone removes the flip, or (b) is needed too. Both are in scope; the scenarios decide.

## Durable state, lifecycle and clocks
Objective status, an existing typed field, gains a same-pass advance or complete. Any flight-hold state must be typed, with a lifecycle that ends when the threat ends.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
