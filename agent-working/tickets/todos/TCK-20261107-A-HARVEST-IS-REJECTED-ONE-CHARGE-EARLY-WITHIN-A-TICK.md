---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261107-A-HARVEST-IS-REJECTED-ONE-CHARGE-EARLY-WITHIN-A-TICK
phase: open
date: 2026-11-07
tags: [economy, bug]
---

# TCK-20261107-A-HARVEST-IS-REJECTED-ONE-CHARGE-EARLY-WITHIN-A-TICK

## Title
A second harvest of a regular node in the same tick is rejected as depleted while one charge remains, because the earlier accepted harvest is counted twice

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
The owner asked, via personal-career on 2026-11-07, that this defect be ticketed. It is review row R-tx-01 (lead-planner draft `agent-working/lead/review_followups_2026-11-07.md`, Batch 3). Verified at origin/main a7f1bb3df:
- The availability check in `src/core/conservation.py:317-324` starts from `node.remaining_charges`.
- It adds the pending `node_overrides[source_id].charges_delta`.
- It also subtracts `reservations[("NODE", source_id)]`.
- Both are written for the same accepted harvest by `ResourceTransactionSystem._apply_world_effects` (`src/engine/economy.py:350-356`): `charges_delta` accumulates -1 and the reservation +1. The `nodes` dict it writes is the same `new_node_updates` passed back as `node_overrides` (`economy.py:33,103,121-124`).
- Example: a node has 2 charges and one harvest was accepted this tick. The second harvest sees 2 - 1 - 1 = 0 and gets `SOURCE_DEPLETED`, when 1 charge is left.
- Ch. 03 §3 says a regular node loses 1 charge per harvest.

## Scope
- First, the economy rule owner (rpg-designer) confirms that the double count is not intended.
- Then count the accepted harvest once, either by the pending delta or by the reservation.
- Fold in R-tx-09: exact debit and credit assertions on a successful transfer.
- Regression test: two harvests of a 2-charge regular node in one tick are both accepted; a third is rejected.

## Out of Scope
LOOT nodes (whole-node delta) beyond checking they keep their current behaviour.

## Acceptance Criteria
- The test above passes and fails on a7f1bb3df.
- Conservation tests and the parity entries for node charges (TOWN-122 and its neighbours) still pass.
- If it moves worlds, the change is measured on the gate worlds and disclosed.

## Related Tickets
- TCK-20260930-CORE-RPG-PILOT-NODE-CHARGE-ACCOUNTING (done; tests-only, did not cover two harvests in one tick)

## Related Docs
- docs/mechanics/03_economic_laws.md
- docs/mechanics/resource_conservation_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
src/core/conservation.py, src/engine/economy.py

## Assumptions / Open Questions
- Is the double count deliberate (a conservative in-tick guard)? This is a question for the rule owner, asked before building (the rule-owner rule).
- The world impact is unmeasured. Simultaneous same-node harvests may be rare.

## Implementation Notes
Planner scope (rpg-planner-ubuntu, 2026-11-08; owner dispatch "yes", logged at #715 comment 6720661924):
- Re-verified at origin/main 297494469: `conservation.py:317-324` adds `node_overrides[...].charges_delta` and subtracts `reservations[("NODE", id)]`; `economy.py:350-356` writes both for one accepted harvest into the same `new_node_updates` dict.
- BLOCKED on the economy rule owner. Nothing is built until rpg-designer confirms the double count is unintended. The question goes to rpg-designer via lead-planner and lead-planner-u24, and the ruling is recorded word for word in this ticket.
- If the ruling is "unintended": count the accepted harvest once, by `charges_delta`. Remove the NODE reservation subtract (`conservation.py:322-323`) and its write (`economy.py:356`); those are the only reader and writer of `("NODE", id)` at 297494469. Keep `charges_delta` because `new_node_updates` starts as `dict(update.node_updates)` (`economy.py:33`), so it also carries node changes made earlier in the tick, which a reservation never sees. LOOT already reaches 0 through its whole-node delta, so it is unchanged; assert that in the test.
- If the ruling is "intended": close by disposition, with no code. The ruling then needs a Bible ch. 03 §3 line or an intentional-divergences entry, and that is a planner follow-up.
- R-tx-09 (exact debit/credit assertions on a successful transfer) is folded in, as the ticket says.
- World impact: run the not-slow economy and conservation tests. Gate-world measurement only if those tests move, and only on a fresh go.

### Rule-owner ruling (relayed by lead-planner from lead-planner-u24, 2026-11-08)

Harvest ruling (rpg-designer, under #715 6721260970): it's a defect. Keep charges_delta and drop the NODE reservation, both where it's written and where it's read.

1. Defect, not an intended guard. One accepted harvest is counted twice. `_apply_world_effects` (src/engine/economy.py:350-356) adds the harvest's -1 to `new_node_updates[node_id].charges_delta` and also adds +1 to `reservations[("NODE", node_id)]`. Both resolve paths in that file (:103 independent, :175 grouped) pass the same `new_node_updates` as `node_overrides` and the same `reservations` dict. So `resolve()` (src/core/conservation.py:317-323) computes remaining = charges + delta - reserved = 2 - 1 - 1 = 0, and the second same-tick harvest on a 2-charge node gets SOURCE_DEPLETED with 1 charge left. That breaks Bible 03 §3: a regular node loses 1 charge per harvest and yields until it reaches 0. The guard isn't conservative in any useful way, because the delta already stops duplication on its own. It just loses real yield.

2. The proposed fix is right. charges_delta is the complete in-tick record: it starts from `update.node_updates`, so it carries node changes from earlier in the tick, and every accepted harvest in this phase adds to it. That alone keeps TOWN-122 (no duplicate yield). For a LOOT node, the delta takes every charge, so the reservation was never needed there either. Stop writing the NODE reservation at economy.py:356 as well as reading it at conservation.py:321-323. Nothing else reads that key (only the resolver), so leaving a dead writer would be a hidden durable-looking record with no reader. The GROUND_ITEM and CORPSE reservations stay as they are. This is the simpler option. The other way, keeping the reservation and dropping the delta, would lose the changes made earlier in the tick.

What the ticket must also change:
(a) tests/unit/resource/test_node_charge_accounting.py::test_reserved_last_charge_cannot_be_harvested_again_in_the_same_tick passes a reservation with no delta. It must be rewritten to the real apply-path shape: last charge taken earlier in the tick means delta -1, giving SOURCE_DEPLETED. Add the new case: 2-charge node, one harvest already accepted (delta -1), so the second is accepted and the node reaches 0. Add one through the apply path too: two actors on a 2-charge node in one tick both yield, and a third is rejected. This changes an RPG test expectation, so rpg-planner signs off. My ruling is that the new expectation is the Bible's.
(b) docs/mechanics/resource_conservation_contract.md, "Concurrent Actor Protection": the sentence "For NODE the reservation is subtracted from the remaining charges (`conservation.py:82-91`) ..." gets replaced with: "For NODE there is no reservation: the in-tick charges_delta (node_overrides) already counts every accepted harvest and earlier node change, so a node rejects with SOURCE_DEPLETED only when that count reaches 0." Also change "populates reservations only for NODE, GROUND_ITEM, and CORPSE" to "only for GROUND_ITEM and CORPSE". Update the TOWN-122 ledger evidence to the new test.
(c) Measurement: this changes world paths (more harvests succeed), so the default tier applies: crowded only, 5x5000, pinned and paired. Report how many same-tick repeat harvests the arm accepted on a node, because zero means crowded doesn't exercise the fix and that has to be named. Conservation counts must balance, and any arm STARVATION not covered by a known entry follows the usual rule. It can ride a combined run.

Everything else stays idle.

## Test Summary

## Files Changed

## Completion Summary
