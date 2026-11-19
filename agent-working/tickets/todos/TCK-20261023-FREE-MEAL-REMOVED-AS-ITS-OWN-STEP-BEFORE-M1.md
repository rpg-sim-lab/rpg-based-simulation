---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1
phase: open
date: 2026-10-23
tags: []
---

# TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1

## Title
Remove the free meal for every kind (decision 73) as its own measured step against v1, before milestone 1

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner ruling 2026-10-23 (#715 6356123802): decision 73's free-meal removal is a separate step BEFORE milestone 1, measured against v1 (341f700d0) as the milestone 0 gate's own step (roadmap §12.3, the free-meal off arm). If it moves the world, its record is the milestone 1 base (v1.1). It retires the V1 known entry (TCK-20261007-EAT-BESIDE-THE-INN-FEEDS-A-SUBJECT-THAT-CANNOT-PAY-FREE-MEAL, expires 2026-12-31).

## Scope
1. Remove the free meal for every kind at once (decision 44/73): no hunger drop without an accepted transfer (the inn charge accepted at 0 gold and clamped, building_services.py:71-74 / conservation.py:256 / inventory.py:156, per the V1 entry's note).
2. Measure it as its own paired step against 341f700d0 (3 worlds x seeds 42-46 x 5000t, full decision-76 stop rules), plus the §12.3 gate H1-H7 and R1-R5 on the off arm.
3. If the world moves, record v1.1 (gate rebaseline plus disclosure delta); retire the V1 known entry.

## Out of Scope
Milestone 1 items. Births (decision 67).

## Acceptance Criteria
- V1 = 0 violations on all 15 gate runs; the V1 known entry removed.
- The paired step passes the stop line, or the owner rules.
- The gate H1-H7 hold on the off arm; R1-R5 reported.

## Related Tickets
TCK-20261019-RECORD-BASELINE-V1 (v1 recorded 341f700d0).

## Related Docs
docs/plans/systemic_world/roadmap.md §12.3, §12.5; docs/plans/systemic_world/v1_disclosure.md; owner_decision_memo.md.

## Related Stored Artifacts

## Related Code Areas
src/systems (building_services, conservation, inventory); src/ai need_pull

## Assumptions / Open Questions

## Implementation Notes
- 2026-11-19 (rpg-planner, lead-planner-u24): OVERLAP with the P0 coin fix, TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN.
  - The coin fix keeps SERVICE_PAYMENT_LAW = CLAMP. It adds one price helper and makes debit = credit = paid; no payee means debit 0, counted. It rewrites the same _service_result / pricing code as #781 (conservation.py, lodging.py, building_services.py).
  - When #781 un-holds (the ATOMIC flip, owner decision 44 / D73), it needs a REAL resync onto the coin fix, and a re-check of its can't-pay semantics against the fixed CLAMP path.
  - It keeps the coin fix's price helper and its resolver balance test (a refusal debits 0).
  - The coin fix lands first, as the P0.
- 2026-11-19, DISPATCH PRECONDITIONS (rpg-planner; owner directions via lead-planner-u24 on #715). All are set on this ticket BEFORE any data:
  - SEQUENCE: Wave 0.3 of the M1 Phase 1 plan. It starts after the coin fix merges, and is its own behaviour segment with a boundary recorded before and after.
  - GATE READ, compared against the TRUE MAIN BASELINE (run 44452967207): the read must show EXACTLY the 15 known V1 free-meal rows leaving, and no other row changing class (rule (a)).
  - HUNGER BARS (owner: individual starvation is OK, a population must not collapse from hunger; rpg-designer writes the exact bars). FIRST USE is here, because removing the free meal raises starvation risk.
    - HARD: no population collapses by hunger in any cell.
    - REPORTED: starvation deaths per in-world day, per cell, base vs fix.
    - Both are pre-registered against the base with numbers, and with their event periods in ticks and in days at 2400 ticks/day (the bar-period rule). The window must cover several periods, or the bar is declared untestable in that window.
  - HUNGER BARS, rpg-designer's text (#715 6999218200), plus the owner's scope (latest lead comment). They are PRE-REGISTERED here, before data:
    - PERIOD (from main's code): the starving line is 95, death comes 6000t after it, and base hunger is 0.1/tick (humans at half rate). So fed-to-dead is about 7900t (3.3 days) for a human and about 6950t (2.9 days) for base-rate kinds.
      - A 5000t window (2.08 days) cannot hold one full cycle, so collapse is UNTESTABLE at 5000t.
      - W = 24,000t (10 days, at least 3 cycles), fixed from arithmetic, not from data. 12 cells, about 3-4 h of u24 host time.
    - P0, FIRST: for each base free-meal user, name the alternative food path in reach. If any user has none, #781 does NOT run until that gap is closed.
    - P1, HARD at W, 0 collapses. Per world/seed, and per hunger-bearing species group with >= 5 members at t0, a collapse is ALL of:
      - (a) end living <= 50% of t0 (births counted);
      - (b) starvation >= 50% of that group's deaths;
      - (c) the base does not show the same.
      A group going extinct with starvation >= 50% of its deaths also counts. A collapse already present in base is a pre-existing finding for the owner.
    - P2, HARD leading indicator, readable at 5000t: every base free-meal user gets a non-free food before reaching hunger 95, or is named.
    - P3, REPORTED per in-world day:
      - starvation deaths / hunger-bearing living count;
      - starving-line (95) crossings;
      - weakened (>= 85) body-days;
      - a FLAG when one day's starvation deaths exceed 10% of a group's start-of-day count.
  - The CURRENT GATE V3 STARVATION ROWS, to cite as base context (main's report, inherited; values from the ubuntu lead's artifact read):
    - frontier_living_world/42: e55 small_plant_eater starved at t4745, FORAGE judged open but never tried.
    - crowded_frontier/42: e7 human starved at t2045, at the PERC-alone head.
    These are individual deaths, not collapses. Their tickets are separate (the starvation fix ticket: SURV-06/07, the H6 recorder spy). #781's P0/P2 read must say whether either is a free-meal user.
  - Other food-touching changes get only the 5000t early-warning check (P2-style) plus the P3 rows; the W read is for #781 and the M1 checkpoints only (owner scope). Births is not re-run.
  - Settings-in-data rule: any new tuning value goes to data/. The pre-push run covers tests/unit/** by directory plus statics.

## Test Summary

## Files Changed

## Completion Summary
