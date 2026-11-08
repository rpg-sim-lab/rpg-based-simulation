---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261109-A-GROUPED-TRANSFER-TRIAL-DOES-NOT-SEE-ITS-OWN-EARLIER-INTENTS
phase: open
date: 2026-11-09
tags: [economy]
---

# TCK-20261109-A-GROUPED-TRANSFER-TRIAL-DOES-NOT-SEE-ITS-OWN-EARLIER-INTENTS

## Title
A grouped transfer's trial resolves each intent without the node charges or reservations taken by the intents before it in the same group

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found by rpg-planner (u24) while it reviewed TCK-20261107-A-HARVEST-IS-REJECTED-ONE-CHARGE-EARLY-WITHIN-A-TICK (#848). rpg-planner-ubuntu confirmed it on origin/main 8d9f3ebf3. The finding is disclosed in that ticket's Completion Summary and was left unfixed there.

`ResourceTransactionSystem.resolve_all` (src/engine/economy.py, the "Resolve group together" branch, about :166-185 at 8d9f3ebf3) trial-resolves a group's intents in a loop. Each intent gets `node_overrides=new_node_updates` and `reservations=reservations`. Between trial intents the loop advances only `group_current_inventory`. `new_node_updates` and `reservations` change only after the whole group is accepted, through `_apply_world_effects` in the commit loop. So a later intent in the same group does not see the node charge or the GROUND_ITEM/CORPSE reservation that an earlier intent in that group would take.

Concrete case: one entity's group holds two NODE intents on a node with 1 remaining charge. Both trials compute remaining = 1, both are accepted, and the commit then applies charges_delta -2. That is one more yield than the node has, which breaks Bible 03 §3 (atomic conservation; a node yields until it reaches 0) and the TOWN-122 intent. The same shape applies to two intents on one GROUND_ITEM or CORPSE inside one group.

This predates #848. Before #848 the NODE reservation was also not updated between trials, so #848 did not change it.

Reachability at 8d9f3ebf3: no src producer is known to put two same-source NODE, GROUND_ITEM or CORPSE intents into one group. The group_id producers found were recruitment (RECRUIT), quest rewards, party rewards, combat KILL_REWARD, inn EAT and lodging (TOWN_SERVICE). The defect is therefore latent: any caller that builds such a group reaches it, and so would a future producer. Scope step 1 must confirm reachability before the fix is sized. Do not assume it is unreachable just because the crowded runs never showed it.

## Scope
1. Confirm reachability. List every producer that sets `group_id` on a `ResourceTransferIntent`. For each, note whether it can put two intents on the same NODE, GROUND_ITEM or CORPSE source into one group. Record the result in Implementation Notes.
2. Add a red test that goes through the apply path (`ResourceTransactionSystem.resolve_all`): one entity, one group of two NODE intents, a 1-charge node. Expect the group to be rejected as a whole (one intent gets SOURCE_DEPLETED and no intent in the group commits), and the node to keep its 1 charge. Add a sibling case for a CORPSE or GROUND_ITEM source if step 1 shows the same shape is reachable or cheap to pin.
3. Fix it so that each trial intent sees the trial effects of the intents before it in its group. Do not mutate the shared `new_node_updates` or `reservations` during the trial: a rejected group must leave both exactly as they were. One option is a group-local copy of the node overrides and reservations that is advanced per trial intent and discarded on rejection. The rule owner picks the shape (see Assumptions).
4. Update docs/mechanics/resource_conservation_contract.md ("Concurrent Actor Protection" and the grouped-transaction text) and the matching parity-ledger entry, if the contract states the group trial behaviour.

## Out of Scope
- Any change to the independent (gid None) path, which #848 already fixed for NODE.
- Re-adding a NODE reservation. Per the #848 ruling, the in-tick charges_delta is the whole record.
- New group producers.

## Acceptance Criteria
- AC1: Step 1's producer list and its reachability verdict are recorded in the ticket.
- AC2: The new apply-path test is red on the unfixed code and green after the fix.
- AC3: A rejected group leaves `node_overrides` and `reservations` byte-for-byte as they were before the group. A test asserts this.
- AC4: The existing tests still pass unchanged: tests/unit/resource/test_node_charge_accounting.py, tests/integration/kernel/test_node_charge_cross_actor.py, tests/integration/kernel/test_race_conditions_v2.py (including test_multi_intent_group_rollback_race), and tests/unit/resource/test_conservation_rejection_paths.py.
- AC5: If step 1 finds no src producer, the close says so, and no world measurement is needed (no world path changes). If a producer exists, the change alters world paths, so the default measurement tier applies.
- AC6: Contract and parity-ledger text match the code, updated in the same change.

## Related Tickets
- TCK-20261107-A-HARVEST-IS-REJECTED-ONE-CHARGE-EARLY-WITHIN-A-TICK (done, #848): disclosed this finding.
- TCK-20260427-RESOURCE-CONSERVATION-HARDENING (done)

## Related Docs
- docs/mechanics/03_economic_laws.md §3
- docs/mechanics/resource_conservation_contract.md
- docs/parity_ledger/town_resource.yaml (TOWN-122, TOWN-123)

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/economy.py (`resolve_all` group branch, `_apply_world_effects`)
- src/core/conservation.py (`ResourceTransactionResolver.resolve`)

## Assumptions / Open Questions
- Q1 (rpg-designer, rule owner): should a group trial see its own earlier intents' charges and reservations? This ticket assumes yes, because one group taking more yield than the source holds breaks atomic conservation. Get the ruling before implementing.
- Q2: if step 1 finds the case is unreachable from src, does the rule owner still want the fix, or a guard plus a test? This ticket recommends the fix, since it is small and the defect is latent.

## Implementation Notes
(empty)

## Test Summary
(empty)

## Files Changed
(empty)

## Completion Summary
(empty)
