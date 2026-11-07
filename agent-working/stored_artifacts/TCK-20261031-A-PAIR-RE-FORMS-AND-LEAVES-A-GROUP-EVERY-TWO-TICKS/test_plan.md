---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-01
tags: [cooperation, social]
---

# Test plan

All tests on the real `GroupSystem.update_groups` / `GroupPhase.resolve` / kernel path, not the replica. New file `tests/unit/social/test_group_contract_binding.py` (+ one scenario test below).

## Ruling's tests
1. Election that moves the leader off the holder does not dissolve a bound group (pair, sociability gap >= 0.2, tick >= 100 so the gate is open, binding holder = old leader; run through the election pass and the dissolution check on consecutive ticks).
2. Each of the 3 typed reasons dissolves, and the record carries the typed reason: contract ACTIVE -> FULFILLED/other status (NOT_ACTIVE with status), expired by tick (NOT_ACTIVE, EXPIRED), removed from the holder's map (MISSING, holder present), holder dead / inactive / not a member (HOLDER_LEFT).
3. A group formed at tick t holds no election before t+100 (check_leadership returns (None, None) up to t+99, acts at t+100); formation stamps `last_leadership_check_tick == formation tick`.
4. `bound_by` round-trips (`to_canonical_dict` -> reconstruct) and is omitted when None; reason fields likewise.
5. Groups not formed by a contract are byte-identical (squad record; hand-built record; canonical dict equality against the pre-change dict, and the corpus fixture `kernel_runs.jsonl` for worlds with no contract groups).
6. The 19/33 chain on crowded s42: the group formed at about t100 lasts until its contract ends. Short run to t~140 on crowded_frontier (needs the 12-second trace shape), asserting one live group id for the pair from the first t>=100 formation until the contract's expiry tick.

## Added by the designer (advance ruling)
7. A group whose binding contract ends dissolves and does not rebind to the pair's next ACTIVE contract (two ACTIVE contracts for the pair; first ends; assert dissolved, `bound_by` unchanged, no new group the same tick from the dissolved id).

## Controls
- Positive control: the same election on the UNFIXED lookup (leader-map read) dissolves the group. Run the old lookup as a named helper in the test (copy of the removed three lines) against the identical state, assert dissolved; then the fixed code on the same state, assert not dissolved.
- Dirty-set reach: a bound group is visited after its contract changes status (through the kernel path), otherwise it outlives the contract.
- Fallback: hand-built `contract_id` with `bound_by=None` behaves as before (whichever option the planner picks for question 2).

## Existing tests to run (scoped, cores 4-5)
`tests/unit/social/` (groups, group_lifecycle_fields, party_lifecycle, party_agency, phantom_leader, domain_7_social, group_id_allocation), `tests/unit/domains/cooperation/`, `tests/integration/domains/cooperation/`, siege/faction tests that read groups_add, `tests/unit/engine` replay/fingerprint tests, `tests/codebase/test_*parity*` and the mechanisms/paths guards before any push.

## Re-measure (needs lead-planner's go; after the sync)
15 paired runs: 3 worlds x s42-46, base 6fdfdf555 vs the branch, id fix and churn fix together, audit_mode; then the final non-audit pass at FULL, 3 per tree alternating, policy stated per run.
STOP and report on any per-world rise in deaths by cause (victim ids and first diff). Report: group lifetime p50/p90; formations, and dissolutions by typed reason; re-formations by the same members within 10 and 50 ticks, split by binding contract: SAME contract_id as the dissolved group is true churn and gated at about 0; DIFFERENT contract (the pair's next ACTIVE duplicate) is reported, not gated, attributed to TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE, and the duplicates stay out of the batch unless a death STOP's first diff traces to a duplicate-driven re-form; overwrites and ghosts (still 0); frontier tick time against the 35.6% rise; re-count of FULFILLED dissolutions (84/156/201 before) with the trace of one, for the designer before the close.
Hold rule on the final non-audit: total tick time up more than 5% in any world, or the store past 2000 records by 2000t.
Instrument gaps to add (read-only wrapper): re-form split by binding contract, group lifetime p50/p90, dissolution by typed reason from the record field.

## Revision after plan review (rpg-planner, 2026-11-01; open items with rpg-designer: Q1 O1 vs O2, Q6 scope)
Settled: no legacy fallback (a group with no holder is not dissolved for its contract; hand-built tests that need contract dissolution get a holder; any change to `test_domain_7_social.py` expectations is listed in the PR). Dead holder who is also the leader is recorded BINDING_HOLDER_LEFT; a dead leader who is not the holder dissolves as today (SOC-176) with no contract reason; reasons are set on bound groups only, squads stay byte-identical. The shape below assumes the planner's recommendation (`contract_holder_id` plain field; stored reason on every end of a bound group: the 3 contract reasons plus LEADER_LOST, MEMBERS_BELOW_TWO, DEFECTION). Test names are updated if the designer rules otherwise.

Additional tests:
8. Holder drifts out of a group of 3 or more: it drops out in the member loop (distance); the next tick's group-level check records BINDING_HOLDER_LEFT. (Bound group of 3, holder leaves cohesion.)
9. Holder dead and also leader: recorded BINDING_HOLDER_LEFT; dead leader who is not the holder: dissolves, reason LEADER_LOST (if the designer accepts every-end scope), no contract reason.
10. `party_lifecycle.py:205` (defection leaves <= 1 member): dissolution_tick set together with reason DEFECTION on a bound group; unbound group: reason stays None.
11. Fingerprint: `to_canonical_dict` carries the holder and both reason fields; changed holder changes the canonical hash; `fingerprint.py:_group_identity` (identity string has contract_id, omits dissolution_tick and most fields): add `holder=` only when set and test that a changed holder changes the identity string; unbound groups' string unchanged.
12. Dirty-set reach, through the kernel path with members otherwise idle: (a) status change on the holder's map (ACTIVE -> FULFILLED) dissolves the group on the tick it is visible; (b) pure time expiry (no write, `state.tick > expiry_tick`) dissolves the group. If either fails the test documents that live bound groups can outlive a contract; per planner: stop and report before changing the dirty set.
13. Typed status: NOT_ACTIVE carries `ContractStatus` (the enum has EXPIRED, FULFILLED, FAILED, BETRAYED, CANCELLED, OFFERED, ACCEPTED, COUNTERED); the stored contract status is stored as the typed value, not a string; time expiry on a stored-ACTIVE contract records `ContractStatus.EXPIRED`.
Positive control (test 14, listed here explicitly): the same election on the UNFIXED lookup (leader-map read, copied as a named helper) dissolves; the fixed code on the identical state does not.

Re-measure additions: per run, live bound groups whose contract has ended, and for how many ticks (planner: if any outlive the contract, stop and tell before changing the dirty set). "Groups now last" is the designer's expectation measured by the 15-run report; nothing is tuned to reach it.
