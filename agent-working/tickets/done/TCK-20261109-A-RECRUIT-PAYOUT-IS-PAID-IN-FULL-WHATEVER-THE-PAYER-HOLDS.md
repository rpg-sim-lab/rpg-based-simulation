---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261109-A-RECRUIT-PAYOUT-IS-PAID-IN-FULL-WHATEVER-THE-PAYER-HOLDS
phase: done
date: 2026-11-09
tags: [economy]
---

# TCK-20261109-A-RECRUIT-PAYOUT-IS-PAID-IN-FULL-WHATEVER-THE-PAYER-HOLDS

## Title
A recruit payout is paid to the recruit in full whatever the payer holds, so a short payer mints the difference, and nothing rolls one side back when the other is rejected

## Status
DONE

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
Ruled direction: B, narrowed to the gold path (rpg-designer, #715 6724908875; ruling word for word in Implementation Notes).
1. Confirm no test asserts execute_recruit's two `resource_transfers` intents. The ruling found none (test_recruitment.py covers appraisal only; test_team_up.py names it only in a docstring). If one does, stop: that is an RPG test-expectation change and needs rpg-planner's sign-off.
2. In `CoreActions.execute_recruit` (src/engine/domain/core_actions.py:188-213), remove the two `resource_transfers` intents and their `group_id`. Keep the function, its appraisal, its contract creation (`strategic_upd` with the contract on both sides, now carried outside the transfer intents) and the router branch. Do not edit the RECRUIT/CHEST branch in `resolve()`.
3. Add a unit test: execute_recruit's accepted path emits no `resource_transfers` and still creates the contract on both sides. test_phase5_negative_cases.py:283-286 (TARGET_NOT_FOUND) must still pass unchanged.
4. Docs: add the ruling's sentence word for word to docs/mechanics/resource_conservation_contract.md, and the same sentence under the SOC-05 entry in docs/guidelines/intentional_divergences.md. In strategic_cognition.yaml (:3608-3670), correct the "live-reachable via execute_recruit()" wording if you touch those entries; otherwise name it in the close as left. Update any parity-ledger entry that cites the recruit gold transfer.

## Out of Scope
- Option A (a conserving recruit transfer). It is deferred until RECRUIT is wired, under the rule sentence this ticket records.
- The RECRUIT/CHEST branch of `resolve()`.
- Removing `execute_recruit` or its router branch.
- The grouped-trial fix (TCK-20261109-A-GROUPED-TRANSFER-TRIAL-DOES-NOT-SEE-ITS-OWN-EARLIER-INTENTS).
- Adding a RECRUIT producer.

## Acceptance Criteria
- AC1: Step 1's result is recorded.
- AC2: execute_recruit emits no `resource_transfers`, and the contract is still created on both sides, both pinned by the new unit test. That test is red on the unfixed code.
- AC3: test_phase5_negative_cases.py and test_recruitment.py pass unchanged, as do the conservation and economy suites (tests/unit/resource, tests/unit/economy).
- AC4: The rule sentence appears word for word in resource_conservation_contract.md and under SOC-05 in intentional_divergences.md. The strategic_cognition.yaml wording is fixed, or named as left.
- AC5: No world measurement (ruling): nothing reaches the path, and the gate's RECRUIT accepted count is 0. Equal end-state fingerprints may ride a combined run if one happens.

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
- Q1 is answered: B, narrowed to the gold path (ruling in Implementation Notes).
- Dispatch waits for the owner's go. The ruling clearance (#715 6724908875) covers the A/B choice only.

## Implementation Notes
Ruling, recorded word for word (relayed by lead-planner from lead-planner-u24, 2026-11-09):

Recruit payout ruling (rpg-designer, under #715 6724908875), for TCK-20261109-A-RECRUIT-PAYOUT-IS-PAID-IN-FULL-WHATEVER-THE-PAYER-HOLDS. I read it myself at 8d9f3ebf3. Text to record word for word:

Choice: B, narrowed to the gold path only. Remove the two `resource_transfers` intents (and their group_id) from `CoreActions.execute_recruit` (core_actions.py:188-213). Keep the function, its appraisal, its contract creation and the router branch. Don't edit the RECRUIT/CHEST branch in `resolve()`.

Findings, confirmed: (1) the RECRUIT branch (conservation.py:446-467) checks only `gold < gold_cost`. execute_recruit leaves gold_cost at 0, so the payer is never rejected, and a payer holding less than the payout mints the shortfall. That breaks Bible 03 §1. (2) The two sides are separate per-entity groups, so they aren't tied together. (3) The case can't be reached: nothing in src issues RECRUIT, and the gate baseline's RECRUIT accepted count is 0.0 on every seed (rpg_gate_v1.json, O4.accepted).

Why not A now: recruitment is planned. The owner's 2026-10-06 answer, recorded in intentional_divergences.md (SOC-05 entry), says the contract "binds when RECRUIT is wired". But A isn't the CORPSE shape done once. A corpse can't spend in its own tick, and a live payer can: the payer's own transfers resolve in id order in the same tick, so `_corpse_food_result`'s check of the source's stored gold could overdraw it. A correct A needs the payer's in-tick running balance, and it needs a world in which to measure it. Neither exists while nothing issues RECRUIT. Designing an unreachable transfer now costs more and proves nothing (owner rule 6698958617). What B leaves out: no gold moves on a recruitment contract until it's wired. Nothing in src reaches it today.

Why the gold path only, and not the whole action: the function's appraisal direction and contract shape are cited as the pattern in the Bible (04:1083), in social_narrative.yaml (:2334, :3773, :3866) and in strategic_cognition.yaml (:3608, :3641, :3670). test_phase5_negative_cases.py:283-286 pins its TARGET_NOT_FOUND path. Removing the function would turn all of those into stale citations for no gain. Removing the two intents takes away both the minting and the atomicity gap.

Rule to record, so the payout returns correctly: add one sentence to docs/mechanics/resource_conservation_contract.md, and the same under the SOC-05 entry in intentional_divergences.md. "A recruitment payout, when RECRUIT is wired, is one conserving transfer: the payer must hold the payout net of its own transfers earlier in the tick, and the recruit is credited only as the payer's source debit (TCK-20261109-A-RECRUIT-PAYOUT-IS-PAID-IN-FULL-WHATEVER-THE-PAYER-HOLDS retired the unconserving path); it is measured when it is wired." In strategic_cognition.yaml (:3608-3670), the entries saying the scorer is "live-reachable via execute_recruit()" are already contradicted by social_contract_scorer.py:88. The ticket should correct that wording if it's touching them. If not, name it as left.

Tests: a unit test that execute_recruit's accepted path emits no resource_transfers and still creates the contract on both sides. Scope step 1 must confirm that no test asserts those intents. I found none: test_recruitment.py covers appraisal only, and test_team_up.py only names it in a docstring. If one does assert them, that's an RPG test-expectation change and rpg-planner signs it off.
Measurement: none needed in worlds. Nothing reaches the path, and the gate's RECRUIT count of 0 is the evidence. If a combined run happens anyway, equal end-state fingerprints can ride it.

This also settles my earlier FYI: removing the intents removes the cross-entity group. Back to idle.

(end of ruling)

Scope step 1 result: one test asserted the two RECRUIT intents, which the ruling had not expected: tests/unit/resource/test_resource_v2_boundary.py::test_recruitment_gold_handoff (it pinned `resource_transfers[0].gold_delta` of -500 and +500). I stopped and sent it to rpg-planner-ubuntu. rpg-planner (u24) signed off under #715 6725103948: rewrite it in place, keep the fixture and the execute_action router path. It is now `test_recruitment_moves_no_gold_until_recruit_is_wired`: a test-expectation change signed off by rpg-planner under #715 6725103948. test_recruitment.py covers appraisal only and is unchanged; test_team_up.py names `execute_recruit` only in a docstring; test_phase5_negative_cases.py:283-286 (TARGET_NOT_FOUND) passes unchanged.

Change: `execute_recruit` emits no `resource_transfers` and no group_id; the contract goes into `EntityUpdate.strategic` on both sides (one `StrategicUpdate` shared by both). The RECRUIT/CHEST branch of `resolve()` is not edited.

Disclosed, not widened:
- With no RECRUIT intents, the RECRUIT reservation guard and the RECRUIT branch in conservation.py (~:450) are unreachable from the apply path.
- The contract used to commit only when the transfer group was accepted. It now commits on any accepted appraisal, which is what the ruling intends.
- strategic_cognition.yaml:3608 ("live-reachable via execute_recruit()") is left as it is; it was already contradicted by social_contract_scorer.py:88.
- The rule sentence is word for word in docs/mechanics/resource_conservation_contract.md and as a bullet in docs/guidelines/intentional_divergences.md §2.72, where the owner's "binds when RECRUIT is wired" answer sits (there is no heading named SOC-05 in that file).

## Test Summary
- New tests/unit/social/test_recruit_moves_no_gold.py (2 tests): on the unfixed code both fail (transfers present; contract not on EntityUpdate.strategic); after, pass.
- Rewritten test_recruitment_moves_no_gold_until_recruit_is_wired: asserts no transfers on both sides, the contract (id, kind RECRUITMENT, status ACTIVE, source, target, terms payout 500) on both sides, recruiter readiness_delta -100.0, recruit last_offer_tick_set 0, and an apply-path check (refine then ApplyPath.apply_partial): both entities' gold unchanged, the recruiter keeps 1000, the contract is in state. It fails on the unfixed code, passes after.
- Scoped run: tests/unit/social, test_phase5_negative_cases, tests/unit/resource, tests/unit/economy, tests/integration/domains/cooperation, tests/integration/kernel: 829 passed, 1 skipped. `codebase.health`: OK, 0 worse.
- Measurement: none, per the ruling (nothing issues RECRUIT).

## Files Changed
src/engine/domain/core_actions.py; tests/unit/social/test_recruit_moves_no_gold.py; tests/unit/resource/test_resource_v2_boundary.py; docs/mechanics/resource_conservation_contract.md; docs/guidelines/intentional_divergences.md; this ticket.

## Completion Summary
AC1-AC5 met: step 1 recorded, execute_recruit emits no transfers and the contract is created on both sides (both pinned, red before), the named suites pass, the rule sentence is word for word in both docs, and no world measurement was run. strategic_cognition.yaml:3608 wording left as is. No known gap beyond the disclosures above.
