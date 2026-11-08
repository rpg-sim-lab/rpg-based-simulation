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
A grouped transfer's trial resolves each intent without the node charges, reservations, treasury or building purse and stock taken by the intents before it in the same group

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
1. Confirm reachability. List every producer that sets `group_id` on a `ResourceTransferIntent`. For each, note whether one entity's group can hold two intents that draw on the same NODE, GROUND_ITEM, CORPSE, treasury, or building purse or stock. Record the result in Implementation Notes. Whatever the answer, the fix goes ahead (ruling Q2).
2. Fix it in the ruling's shape (Implementation Notes, ruling Q1). Before the group trial loop in `resolve_all`, make group-local shallow copies of `new_node_updates`, `reservations`, `new_resource_updates` (treasury_pending) and `new_building_updates` (building_pending). After each accepted trial intent, run the same `_apply_world_effects` and `_note_effects` on those copies. Pass the copies into the next `resolve()`. Discard them when the group is rejected. Leave the commit loop unchanged.
3. Shallow-copy safety, which the ruling requires.
   - Confirm that every value in those four dicts is replaced, never mutated in place (replace, merge, apply_transfer, int). Record the check.
   - Planner note: at 8d9f3ebf3, `_apply_world_effects(result, entity_id, nodes, buildings, home_storage, ground_rem, corpses_rem, reservations, corpses_upd)` and `_note_effects(res, resource_updates, source_debits, owed)` also write to home_storage, ground_rem, corpses_rem, corpses_upd, source_debits and owed. The trial must not write to the live versions of these. Give them group-local copies or throwaways, and record which.
   - If a value is mutated in place, stop and report it rather than deep-copying around it.
4. Tests, through the apply path (`ResourceTransactionSystem.resolve_all`):
   - (a) two NODE intents in one group on a 1-charge node: the second is rejected and the group rolls back with no charges_delta applied;
   - (b) two NODE intents in one group on a 2-charge node: both are accepted;
   - (c) one treasury-funded pair whose total exceeds the balance: rolled back;
   - (d) a rejected group leaves all four live dicts unchanged.
5. Update docs/mechanics/resource_conservation_contract.md (the grouped-transaction text) and the matching parity-ledger entry wherever the contract states group trial behaviour.

## Out of Scope
- The independent (gid None) path, which #848 already fixed for NODE.
- Re-adding a NODE reservation. Per the #848 ruling, the in-tick charges_delta is the whole record.
- `_note_depletion`, metrics, `in_tick_processed_ids` and the trace, which stay commit-only (ruling Q1).
- The recruit group spanning two entities (`recruit_{payer}_{target}_{tick}`, core_actions.py:188-213). rpg-designer raised it as an unverified FYI. Looking into it needs its own owner clearance.
- New group producers.

## Acceptance Criteria
- AC1: Step 1's producer list and reachability verdict, and step 3's in-place-mutation check, are recorded in the ticket.
- AC2: Tests 4(a) and 4(c) are red on the unfixed code, and all of 4(a)-(d) are green after the fix.
- AC3: The commit loop is unchanged, so one code path still applies effects to the live dicts.
- AC4: These pass unchanged: tests/unit/resource/test_node_charge_accounting.py, tests/integration/kernel/test_node_charge_cross_actor.py, tests/integration/kernel/test_race_conditions_v2.py (including test_multi_intent_group_rollback_race), tests/unit/resource/test_conservation_rejection_paths.py, and tests/unit/economy.
- AC5: Measurement (ruling): equal end-state fingerprints between base and arm on crowded, 5x5000, pinned and paired, with no death-bar read. This uses lead's heavy slot and can ride a combined run. If any world differs, stop and bring the rows to rpg-designer via rpg-planner-ubuntu.
- AC6: The contract and parity-ledger text match the code, changed in the same change.

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
- Q1 and Q2 are answered by rpg-designer's ruling (Implementation Notes): fix it, in the group-local-copy shape, even if no producer reaches the case.
- Dispatch waits for the owner's go. The ruling's clearance (#715 6724663134) covers Q1 and Q2 only.

## Implementation Notes
Ruling, recorded word for word (relayed by lead-planner from lead-planner-u24, 2026-11-09):

Group-trial ruling (rpg-designer, under #715 6724663134), for TCK-20261109-A-GROUPED-TRANSFER-TRIAL-DOES-NOT-SEE-ITS-OWN-EARLIER-INTENTS. Read myself at 8d9f3ebf3 (src/engine/economy.py, the group branch after `else:  # Resolve group together`, and src/core/conservation.py). Text to record word for word:

Q1. Yes. A group is all or nothing, so its trial must see what its own earlier intents would take (Bible 03 §1). The finding is confirmed, and it's wider than nodes and reservations. The trial loop passes the live `new_node_updates`, `reservations`, `new_resource_updates` (treasury_pending) and `new_building_updates` (building_pending), and none of them advances between intents. Only `group_current_inventory` does. `_apply_world_effects` and `_note_effects` run only in the commit loop. So the same overcount reaches treasury (`_fund_reward`/`can_pay`, `_wage_result`) and building purse and stock (`_purse_now`, `_stock_now`) as well as NODE, GROUND_ITEM and CORPSE. The shape is right: make group-local shallow copies of those four dicts before the trial loop. After each accepted trial intent, run the same `_apply_world_effects` and `_note_effects` on the copies, and pass the copies into the next `resolve()`. Discard them when the group is rejected. Leave the commit loop as it is: it writes to the real dicts, so there's still one code path that applies effects. The implementer must confirm that the values in those dicts are replaced, never mutated in place (replace, merge, apply_transfer, int), or the shallow copy isn't safe. Not in scope: `_note_depletion`, metrics, `in_tick_processed_ids` and the trace, which stay commit-only.

Q2. Fix it, even if no producer reaches the case. The simpler option is a guard plus a test. It would leave the trap in place for the next producer that puts two intents in one group. A guard rejecting such groups would also make a new rule of its own, for example turning away two harvests on a 2-charge node. Conservation is one of the owner's exceptions to preferring the simpler fix, and the fix is about ten lines in one place. Tests: two NODE intents in one group on a 1-charge node, so the second is rejected and the group rolls back with no charges_delta applied. Two on a 2-charge node, both accepted. One treasury-funded pair whose total is more than the balance, rolled back. A rejected group leaves all four live dicts unchanged.
Measurement: if scope step 1 confirms every group has at most one intent per entity, the fix can't change any world. Prove that with equal end-state fingerprints on crowded, 5x5000, pinned and paired, not with a death-bar read. That can ride a combined run. If any world differs, stop and bring the rows to me.

FYI, not part of this ruling and not verified: the recruit group (`recruit_{payer}_{target}_{tick}`, core_actions.py:188-213) spans two entities. The group loop runs inside one entity at a time, so all-or-nothing doesn't hold across payer and target. Whether something else keeps the target from being paid when the payer is rejected, I haven't checked. If rpg-planner wants it looked at, it needs its own owner clearance.

(end of ruling)

## Test Summary
(empty)

## Files Changed
(empty)

## Completion Summary
(empty)
