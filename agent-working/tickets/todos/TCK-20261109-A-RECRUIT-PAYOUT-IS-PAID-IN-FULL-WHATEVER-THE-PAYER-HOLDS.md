---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261109-A-RECRUIT-PAYOUT-IS-PAID-IN-FULL-WHATEVER-THE-PAYER-HOLDS
phase: open
date: 2026-11-09
tags: [economy]
---

# TCK-20261109-A-RECRUIT-PAYOUT-IS-PAID-IN-FULL-WHATEVER-THE-PAYER-HOLDS

## Title
A recruit payout is paid to the recruit in full whatever the payer holds, so a short payer mints the difference, and nothing rolls one side back when the other is rejected

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
This came from a read-only check the owner cleared at #715 6724864316 ("Clear the check (Recommended)"). It followed an unverified note from rpg-designer in its group-trial ruling (#715 6724663134). rpg-planner-ubuntu checked it on origin/main 8d9f3ebf3.

`CoreActions.execute_recruit` (src/engine/domain/core_actions.py:137-213) returns two EntityUpdates. Each carries one `ResourceTransferIntent` with source_kind RECRUIT and the same `group_id = recruit_{payer}_{target}_{tick}`:
- payer: `gold_delta=-payout`
- target: `gold_delta=+payout`

Neither intent sets `gold_cost`, which defaults to 0 (src/core/update_models/resources.py:24).

1. No balance check on the payer. The RECRUIT branch of `resolve()` (src/core/conservation.py:446-467) checks only `target_inventory.gold < intent.gold_cost`, which is `gold < 0` and never true. So the payer's intent is accepted whatever it holds. `InventoryService.apply_update` then clamps gold at 0 (src/core/inventory.py:156, :230). The target's intent is accepted and credited the full payout. A payer holding g < payout loses g, the target gains payout, and payout - g gold is created. That breaks Bible 03 §1 (atomic conservation).
2. No atomicity across the two sides. `resolve_all` groups intents per entity, so this "group" is two one-intent groups on two entities. A rejection of one side (for example IDEMPOTENCY_VIOLATION, or TARGET_LOCKED from a reservations dict) does not roll back the other. rpg-designer's note asked whether anything else prevents that. Nothing in the resolver or apply path ties the two sides together.

Reachability: latent. Nothing in src issues a RECRUIT action. `action_router.py:63` routes it, but no producer emits it; src/ai/goals/social_contract_scorer.py:88 records the same ("nothing in `src` issues RECRUIT"). The crowded runs in #848 showed coin delta 0, which fits that. The cooperation path's `cnt_recruit_` contracts (src/domains/cooperation/services.py:280) carry no gold transfer and are not affected (to re-confirm in step 1).

## Scope
1. Confirm reachability. Is any RECRUIT action producer present at the working base? Does the cooperation `cnt_recruit_` path move gold anywhere? Record both.
2. Ask the rule owner (rpg-designer, via lead) which direction to take:
   - (A) Fix the recruit payment as one conserving transfer. For example, the payer side checks it holds the payout. The target is credited only through the payer's accepted result, as a source debit (the way CORPSE loot debits the dead entity at conservation.py:152-157) rather than as an independent intent.
   - (B) Retire the unreachable `execute_recruit` gold path.
   Recommendation: (A) if recruitment is planned to come back; (B) if it is not. Do not implement before the ruling.
3. Implement the ruled direction with a red-then-green apply-path test: a payer holding less than the payout creates no gold, and the totals before and after are equal.
4. Update docs/mechanics/03_economic_laws.md, resource_conservation_contract.md and the parity-ledger entry if they describe recruitment payment.

## Out of Scope
- The grouped-trial fix (TCK-20261109-A-GROUPED-TRANSFER-TRIAL-DOES-NOT-SEE-ITS-OWN-EARLIER-INTENTS). That one is about intents inside one entity's group.
- Adding a RECRUIT producer.

## Acceptance Criteria
- AC1: The reachability result is recorded.
- AC2: The rule owner's ruling is recorded word for word before any code change.
- AC3: Under (A), a short payer creates no gold and a rejected payer side leaves the target unpaid; both are tested through the apply path. Under (B), no src path pays RECRUIT gold, and tests that pinned it are updated with the rule owner's sign-off.
- AC4: If step 1 confirms nothing reaches it, the close says so and no world measurement is needed.

## Related Tickets
- TCK-20261109-A-GROUPED-TRANSFER-TRIAL-DOES-NOT-SEE-ITS-OWN-EARLIER-INTENTS
- TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING (done)

## Related Docs
- docs/mechanics/03_economic_laws.md §1
- docs/mechanics/resource_conservation_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/domain/core_actions.py (`execute_recruit`)
- src/core/conservation.py (RECRUIT branch)
- src/engine/economy.py (`resolve_all` per-entity grouping)
- src/core/inventory.py (gold clamp)

## Assumptions / Open Questions
- Q1 (rule owner): direction (A) or (B)?
- Dispatch needs the owner's go after the ruling.

## Implementation Notes
(empty)

## Test Summary
(empty)

## Files Changed
(empty)

## Completion Summary
(empty)
