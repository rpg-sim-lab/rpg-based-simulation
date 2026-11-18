---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261119-RECRUIT-CHEST-AND-CRAFTING-COSTS-DEBIT-THE-PAYER-WITH-NO-PAYEE
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-RECRUIT-CHEST-AND-CRAFTING-COSTS-DEBIT-THE-PAYER-WITH-NO-PAYEE

## Title
RECRUIT, CHEST and CRAFTING transactions with gold_cost > 0 debit the payer and credit no one: a latent undeclared coin sink (EXCH-02)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Lane C found these while reading conservation.py for the P0 coin fix (TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN). rpg-designer ruled them a SIBLING P1, so the P0 stays narrow.

RECRUIT/CHEST and CRAFTING intents with gold_cost > 0 debit the payer with no payee. By EXCH-02's contract (no undeclared sink; rpg-designer, 2.109) they are breaches. They are latent: V6 passes on every gate world on main except the one traced cell, which was a different path.

## Scope
1. Rule a payee per path, from content. Each choice goes to rpg-designer BEFORE code:
   - RECRUIT: the recruit's own purse;
   - CHEST: whoever owns the chest, or price 0 if no one does;
   - CRAFTING: the workshop building when one serves, otherwise price 0.
2. A DECLARED sink would need the owner, since the law allows none. rpg-designer does not recommend one.
3. Each fixed path leaves the P0's KNOWN_UNBALANCED set in its balance test. That test asserts each listed kind is STILL unbalanced, so a fix forces the set edit. Removing a fixed kind is the expected edit here, not an owner ask; it is stated in the PR.

## Out of Scope
- The REST/EAT service path (the P0).
- The ATOMIC payment law (#781, owner decision 44).

## Acceptance Criteria
- Every RECRUIT, CHEST and CRAFTING accepted result balances, and the P0's balance test has an empty KNOWN_UNBALANCED set.
- Each path's payee choice is recorded with rpg-designer's ruling.
- No existing expectation changes without an owner ask; statics after every src commit; V6 stays 0 on the gate worlds.

## Related Tickets
- TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN (the P0; it owns the balance test and the price helper)
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#781, held)

## Related Docs
- docs/mechanics/03_economic_laws.md, docs/parity_ledger/town_resource.yaml, docs/guidelines/intentional_divergences.md 2.109

## Related Stored Artifacts
- None.

## Related Code Areas
- src/core/conservation.py (the RECRUIT, CHEST and CRAFTING branches of ResourceTransactionResolver)

## Durable state, lifecycle and clocks
No new durable state is expected. A payee is an existing holder: a purse, a building or a treasury.

## Assumptions / Open Questions
- Lands after the P0, since it uses the P0's price helper and balance test.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
