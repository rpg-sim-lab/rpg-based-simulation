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

## Test Summary

## Files Changed

## Completion Summary
