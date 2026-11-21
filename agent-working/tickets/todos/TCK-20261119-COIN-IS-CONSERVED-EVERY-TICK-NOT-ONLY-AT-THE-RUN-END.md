---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261119-COIN-IS-CONSERVED-EVERY-TICK-NOT-ONLY-AT-THE-RUN-END
phase: open
date: 2026-11-19
tags: []
---

# TCK-20261119-COIN-IS-CONSERVED-EVERY-TICK-NOT-ONLY-AT-THE-RUN-END

## Title
A per-tick coin-conservation Hard Law check: total_coin(after) - total_coin(before) - declared == 0 every tick, so any phase's coin leak is caught when it happens (V6 moved from the run's end to every tick)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
rpg-designer's ruling (2026-11-19), while reviewing the P0 coin fix TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN:
- The "applied debit == resolved debit" invariant is NOT in the P0.
- Lane C's inspection settles the resolver's own sequence: resolve_all's running purse includes earlier same-tick resolver debits.
- But gold writers exist outside the resolver (e.g. action_intent.py:217), and no check catches a leak from another phase.

So: a HardLawMonitor invariant every tick, total_coin(after) - total_coin(before) - declared_coin == 0, using the same holder set as V6 (treasury.total_coin). It subsumes "applied == resolved".

## Scope
1. A new HardLawMonitor invariant over treasury.total_coin per tick, with declared world-creation coin as the only allowed delta, as in V6.
2. The question carried with it: can any gold writer outside the resolver cut a resolved debit (the apply clamp, inventory.py:230)? Inspect, then test.
3. Tests: a synthetic leak in a non-resolver phase trips the invariant on that tick; a balanced tick passes.

## Out of Scope
- The oracle-gap class (chests, home storage and currency items, which are outside total_coin). That's a separate oracle change, if ever.
- Fixing leaks the invariant finds: each becomes its own ticket.

## Acceptance Criteria
- The invariant trips on the exact tick of a synthetic leak and names the tick and the coin delta.
- On the 3 gate worlds at s42 and cf s46 at the P0's fix head, it reports 0 violations (a run under an S9). Any violation is a finding and goes to rpg-designer.
- The perf NFR: the per-tick cost is measured and stated (one total_coin per tick).

## Related Tickets
- TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN (the P0)
- TCK-20261119-RECRUIT-CHEST-AND-CRAFTING-COSTS-DEBIT-THE-PAYER-WITH-NO-PAYEE (the sibling P1)

## Related Docs
- docs/mechanics/03_economic_laws.md (conservation), docs/observability/ (hard laws)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/coinbreach/ (the V6 trace and the sink run)

## Related Code Areas
- src/observability/ (HardLawMonitor), src/core/treasury.py (total_coin), src/core/models/inventory.py:230 (the apply clamp), src/engine/action_intent.py:217

## Durable state, lifecycle and clocks
No durable state. The invariant reads state at tick end, and observability only reports.

## Assumptions / Open Questions
- Lands after the P0, so the invariant starts green on the gate worlds.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
