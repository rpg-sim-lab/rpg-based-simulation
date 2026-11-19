---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN

## Title
A service, fee or tax paid to a non-building source with no named treasury debits the payer and credits no one, so coin is destroyed (V6 breach, crowded_frontier s46)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
The V6 coin-conservation breach on crowded_frontier s46 was REPRODUCED by an S9-recorded trace (lane C; summary /mnt/data2/rpg-measure/coinbreach/summary_coin.txt, sha e59a2481; #715 6985210267):
- On 414fb74f7 at tick 3182, -10 coin: e12 140 -> 0, e9 +130, and a corpse appears with 0 gold.
- No chest, storage or currency-item movement, so rpg-designer classes it (a): a world-law breach, coin destroyed.
- writers_n = 0: no merge operand carried the gold.
- On main 51a6516cf this cell shows no breach. The trajectories diverge, so main is NOT cleared.

rpg-designer's ruling (#715, the lead's comment after 6985210267, is the spec): a sink by omission (EXCH-02). In src/core/conservation.py, `_service_result` (:254) and `_service_credit` (:133): a service, fee or tax with a non-building source and no named treasury debits the payer and credits no one. REST_PRICE_GOLD = 10 (src/engine/service_prices.py:8) equals the missing amount. That is a HYPOTHESIS until confirmed.

## Scope
1. FIRST, one confirming spy (lane C; a new S9 with designer-approved shas plus a kit preflight):
   - it wraps ResourceTransactionResolver on 414fb74f7, cf s46, for t3180-3182;
   - it logs the gold flows for e12 and e9: inventory gold_delta, source debit, building credit, treasury transfer, with source_kind, source_id, treasury_faction and transfer_kind;
   - it classes the result H1/H2/H3 per the designer's spec.
2. The fix, once confirmed: EVERY resolver path where debit > credits either NAMES a payee (a building, a treasury, an entity) or REFUSES the transaction. There is no silent sink.
3. A resolver-level balance test over ALL source_kinds: for every transaction, the payer's debit equals the sum of credits plus any DECLARED sink (none exist in law: rpg-designer, 2.109).
4. A regression test for the named path, the t3182 shape.
5. Docs: Bible ch. 03 (economic laws, conservation), the parity ledger TOWN entry, and a divergence entry if the behaviour changes.

## Out of Scope
- The oracle-gap class (b): chests, home storage and currency items in total_coin. None was seen in this breach.
- Prices and service availability.

## Acceptance Criteria
- The confirming spy names the path (H1/H2/H3) before any code change.
- The balance test fails on main for the named path, and passes after the fix for every source_kind.
- V6 delta is 0 on crowded_frontier s46 at the fix head, re-measured under an S9.
- No existing test expectation changes without an owner ask.
- Statics after every src commit; the perf NFR is stated.

## Related Tickets
- The P0 V6 spec, #715 6983277940; the trace result, #715 6985210267
- TCK-20261118-SLOW-REGRESSION-LANE-RED-SIX-UNOWNED-FAILURES-SINCE-M1 (a separate finding)
- TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY (priced services)

## Related Docs
- docs/mechanics/03_economic_laws.md (atomic conservation), docs/parity_ledger/town_resource.yaml, docs/guidelines/intentional_divergences.md 2.109

## Related Stored Artifacts
- /mnt/data2/rpg-measure/coinbreach/ (the kit, cells and summary; on the owner delete list after close-out)

## Related Code Areas
- src/core/conservation.py (_service_credit :133, _service_result :254, ResourceTransactionResolver :271)
- src/engine/service_prices.py, src/engine/service_admission.py, src/engine/lodging.py

## Durable state, lifecycle and clocks
No new durable state is expected. The fix names a payee or refuses. If a payee needs a new record, it gets a typed model first (rpg-designer).

## Assumptions / Open Questions
- H1/H2/H3 come from the designer's spec. The fix shape depends on the confirmed class.

## Implementation Notes
- 2026-11-19, PERIOD STATEMENT AND WINDOW RULING. This follows the owner's bar-period rule (#715 6997605774). It is recorded BEFORE any own-job output is read, and the run (S9 6997281236) started before the rule existed.
  - The window is 5000 ticks per cell, about 2.08 days at 2400 ticks/day. rpg-planner checked this from the live process args (`coinfix_spy.py crowded_frontier 46 5000 ...`). The 300 ticks in manifest ea3dd682 is the preflight fixture only.
  - Recorded base rate (lane C, from summary_sink.txt 13430e6e and summary_coin.txt e59a2481 only): cf s46 has 1 unbalanced TOWN_SERVICE row per 2.08 days (t3181, REST at building 20003, -10). The window covers it once. flw42, up42 and cf42 have no recorded base count.
  - P2 (rpg-designer) is a SINGLE-EVENT test. It tests the mechanism at that event, not a rate. Checks:
    - (i) the base and fix final hashes differ;
    - (ii) the fix cell's t3181 REST service row has debit == credit, or is the CLAMP no-pay case (debit 0 and payee_missing per Fix B), and no coin is lost at t3181;
    - (iii) the base row at t3181 shows the -10 loss.
    - (iv) is NOT added: the kit records only final_hash (coinfix_spy.py:211), not per-tick hashes, and no instrumentation is added.
    - Disclosed: P2 covers the REST path once. EAT and the other service paths are not exercised in cf s46.
  - P1/P3 in flw42, up42 and cf42 are COUNT FIRST, THEN JUDGE, with no hold. Each base cell reports its TOTAL priced services (balanced plus unbalanced). Fewer than 3 priced services in a cell makes P1 there "untestable (too few services in window)", not a PASS. P3 (V1 unchanged) and the bound apply as pre-registered.
- 2026-11-19 CONFIRMED (the S9-recorded confirming run, summary /mnt/data2/rpg-measure/coinbreach/summary_sink.txt 13430e6e; rpg-designer recounted it from the raw cells): CLASS H3, a world-law breach (EXCH-02), live on main.
  - At state tick 3181, e9 holds 0 gold; a TOWN_SERVICE/REST from building 20003 has gold_delta -10, gold_cost 0, and is ACCEPTED.
  - _service_credit gets price 0 and returns None (no credit), but the entity is written -10.
  - A same-tick INHERIT +140 hid it.
  - H1 (a non-building source) is refuted. The real path is a building service whose debit isn't matched.
- ROOT CAUSE (rpg-designer, inspected on main 51a6516cf): bed_delta (lodging.py:157) and inn EAT (building_services.py:78) price a service as gold_delta=-PRICE, gold_cost 0. _service_result (conservation.py:256) refuses only when gold < gold_cost (0 < 0 is false), so an unaffordable service is ACCEPTED, credited min(gold, price) = 0, and debited the full price.
- FIX, RULED (the existing law, SURV-06 / TCK-20261029):
  (1) a priced service is REFUSED unless the payer holds the full price at resolve time. Price = max(0, gold_cost - gold_delta), one helper used by both the check and the flows. The pre-tick balance pays; same-tick arrivals don't count.
  (2) when accepted, debit = price = credit (the building, else a named treasury). Never partial.
  (3) the unnamed-payee branch REFUSES.
- TESTS:
  - a resolver balance test: every accepted result over every source_kind sums to 0;
  - REST and EAT with gold < price are refused; with gold == price and gold > price, the building is credited exactly the price;
  - this exact case: a 0-gold payer plus a same-tick INHERIT; REST is refused, and e9 ends at +140;
  - an unnamed-payee fee is refused.
- DOCS: ch03, the parity entry, and a divergence entry if needed.
- OWN-JOB, fixed BEFORE data:
  - HARD: V6 delta 0, plus 0 unbalanced accepted results, on cf s46 at the fix tree and on the 3 gate worlds at s42;
  - REPORTED: REST and EAT "can't pay" refusals, fix vs base. A behaviour change (unpaid beds and meals stop); read it alongside the starvation-with-open-ways class.

- 2026-11-19 RE-RULED (rpg-designer; it SUPERSEDES the "FIX, RULED" and "TESTS"/"OWN-JOB" bullets above). Lane C found that refusing only the charge would deliver beds and meals FREE, and that today's SERVICE_PAYMENT_LAW = CLAMP ("payment never closes a service"; flipping to ATOMIC is owner decision 44 / D73). Option B, within CLAMP; no owner ask, no expectation changes:
  1. One price helper: price = max(0, gold_cost - gold_delta); paid = min(the payer's running gold at resolve, price).
  2. Debit = -paid = credit (the building, else a named treasury). Partial payment stays the law; at gold 0 the charge is 0.
  3. No payee: debit 0 (no coin destroyed), and the service goes ahead per the law. Each such call is COUNTED by observability (not durable). A P2 follow-up ticket makes every priced intent name its payee, with the count as evidence.
  4. Residual MINT risk is in scope:
     - inspect and state (labelled inspected) whether the running inventory includes every earlier same-tick debit of that payer;
     - a test: two same-tick charges summing to more than the purse; total applied debit == total credit, and the apply clamp never cuts a resolved debit;
     - if it can cut one, make that impossible, and add a Hard Law check that applied debit == resolved debit.
  - TESTS: a balance test over every source_kind; the exact t3181 case; the unnamed-payee case (debit 0, counted); the D test. The existing CLAMP tests (gold 3 and 0, partial credit) stay UNCHANGED and passing.
  - OWN-JOB, fixed before data:
    - HARD: V6 0, 0 unbalanced accepted results (cf s46 plus 3 worlds at s42), and 0 apply-clamp cuts of a resolved debit;
    - REPORTED: total REST/EAT coin charged, fix vs base. No service-refusal change is expected, so the starvation note is withdrawn.
  - DOCS: ch03, plus one sentence in service_admission.py and service_prices.py ("the debit equals what the payee receives"), plus the parity evidence.

- 2026-11-19 RULE (a) PREDICTION (rpg-designer, set BEFORE the own-job data). It rests on lane C's INSPECTED claim that apply clamps an entity debit at 0; if the own-job finds otherwise, the prediction is void and the designer re-predicts.
  - The old code destroys coin ONLY when an underpaying payer also gets a same-tick credit (like e9's INHERIT).
  - Predicted: all 15 V1 rows UNCHANGED; V6 cf s46 -10 -> 0; economy-graded rows unchanged, or up by at most one price per same-tick-credit case; every other gate row identical.
  - A move outside that is a finding and goes to the designer.
- #781 split (c) agreed (rpg-designer, lead): this fix is conservation under CLAMP; #781 (ATOMIC, decision 44) stays held and rebases onto this fix later.

- 2026-11-19 SHARPENED PREDICTION (rpg-designer, BEFORE the own-job data; it REPLACES "up by at most one price"):
  - P1: in every cell whose BASE arm has NO unbalanced accepted TOWN_SERVICE result, the FIX final hash == the BASE final hash EXACTLY. Expected for flw s42, up s42 and cf s42, unless their base rows show one.
  - P2: in cf s46 the hashes DIFFER (the t3181 case diverges the trajectory). Its differing gate rows are trajectory divergence, reported and classed by the designer row by row. The only prediction there is V6 -10 -> 0.
  - P3: the 15 known V1 rows are unchanged in every P1 cell.
  - Bound: per cell, the sum of |net| over the base arm's unbalanced TOWN_SERVICE rows is an upper bound on the coin the fix keeps.
  - P1 holds only if `git diff --stat 51a6516cf <fix head> -- src data config` lists only conservation.py, economy.py and run_ledger.py. If it lists anything else, P1 is void and the designer re-predicts. State that diff in the S9.

## Test Summary

## Files Changed

## Completion Summary
