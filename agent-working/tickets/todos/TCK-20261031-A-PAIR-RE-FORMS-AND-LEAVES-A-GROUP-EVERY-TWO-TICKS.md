---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-10-31
tags: [cooperation, social]
---

# TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS

## Title
A pair of entities forms a group and is expelled from it about every 2 ticks. Cause: a same-tick leadership election moves the leader off the entity holding the group's contract, and the dissolution check reads the contract from the current leader. Once group ids stop repeating, each cycle leaves a retained dissolved record. Fix as ruled: a typed contract binding on the group, plus an election cadence that starts at formation.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while verifying TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP. rpg-planner agreed this separate ticket, counts first, with rpg-designer to rule (Ruling 2, in that ticket's staging `rpg_designer_ruling_2026-10-31.md`). A retention or bound rule for dissolved records is a lifecycle rule for the designer, not for the group-id PR.

Behaviour finding, on BOTH trees: on lifecycle_full_coverage_world, seed 42, 200t, entities (37,38) form a group and are expelled about every 2 ticks (read in the event lines at t130-140; the implementer reports it from t102). Trees: 6fdfdf555 and branch rpg-ubuntu-group-id-alloc-impl. Data: /data/vboxuser/Work/groups_base/out/tr_{base,branch}.jsonl (scratch; copy what the close needs into staging).

Measured group store on that scenario: at t199, base 20 records (20 dissolved), branch 54 (53 dissolved). Branch 32 records at t158, 54 at t199, about 0.5 per tick while the churn runs. About 950 by 2000t is an extrapolation from one 200t scenario, not a measurement.

Later measurement, s42, 2000t, 3 worlds: formations go from 225 to 571, 185 to 1035 and 96 to 839 (crowded_frontier, frontier_living_world, urban_political), whole tick +5.1%, +35.6%, +14.6%, which holds the group-id PR. So the old id defect may have been suppressing this churn; that reading is untraced. The profiled runs of the group-id ticket test it.

Counts and trace, done 2026-11-01 (raw, scratch: /data/vboxuser/Work/groups_base/out6/ and out_trace/; copy what the close needs into staging). s42, 2000t, audit_mode, FULL, base 6fdfdf555 vs branch edb638b6a; all 6 hashes equal run18.
- Contract-missing dissolutions: crowded_frontier 192 to 464, frontier_living_world 141 to 831, urban_political 50 to 626. FULFILLED: 15 to 84, 26 to 156, 35 to 201. Expired: 0 in all.
- On the branch 1,916 of the 1,921 contract-missing dissolutions end a group formed the tick before. None of the 2,304 across all 6 runs is before t100.
- Trace, entities 19 and 33 on crowded_frontier, and chain `cnt_recruit_1_8_542`: the contract sits only on the source's map and never leaves it. Formation makes `entity_a` leader (`groups.py:322`) and leaves `last_leadership_check_tick` at its default 0 (`groups.py:340-347`, `state.py:735`), so from t100 the 100-tick gate (`party_lifecycle.py:48,76`) is open on the formation tick. A sociability gap of 0.2 or more elects the other member, `groups.py:165` then finds no contract on the new leader, and the group dissolves at t+1. The holder re-forms it at t+2. Same pattern on base for this pair; two chains traced.
- Superseded: the first reading that the old id defect alone suppressed the churn. Base's ghosts do reduce the number of cycles (740 of 850 extra formations on frontier_living_world involve base ghosts), but the cycle itself is older than the id fix.

## Scope
1. Done: counts and one-cycle trace, sent to rpg-designer.
2. Fix as ruled below: the typed binding, the dissolution check that reads it, the three typed reasons, the formation-tick stamp, all in this one ticket.
3. The re-measure in the ruling. Each run set needs lead-planner's go. The final hold rule also stands on top of it: non-audit at FULL, audit figure beside it, alternating 3 per tree.
4. The ruling's OPEN item: re-count the FULFILLED dissolutions and trace one, for the designer to rule before the close.
5. Divergence entry covering the id fix plus the binding (rewrite of 2.146, class Bug Fix), and parity entries.

Batching (rpg-designer): the group-id fix does not land alone. It lands with this fix, in the same batch, with this fix first or together. Designer's lean: a group that forms should not dissolve without a typed end reason that has changed since it formed; re-forming identical membership on unchanged conditions is the defect.

## Out of Scope
- Group id allocation, which stays with TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP.
- Why base keeps an overwritten record one tick longer (rpg-planner: base's store is the corrupted one).
- The no-partner blocker growth: TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK.
- Duplicate recruit contracts per pair: TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE.

## Acceptance Criteria
1. Counts and the one-cycle trace are in investigation.md, each with the run, seed and commit.
2. rpg-designer's ruling is recorded word for word before implementation (below).
3. `GroupRecord` has the typed binding, set once at formation, one writer, omitted from the canonical dict when None. The dissolution check reads the contract from the binding's holder, never the current leader, with the three typed reasons.
4. The GroupRecord built at formation stamps `last_leadership_check_tick` with the formation tick.
5. Tests on the real code, not the replica: each of the ruling's TESTS items. Including, as positive control, that the same election on the unfixed lookup dissolves.
6. The re-measure's report is complete and its STOP rule is honoured.
7. The designer has ruled on the FULFILLED re-count before the close.
8. The hold rule (Ruling 2's test: total tick time up more than 5% in any of the three worlds, or the store passing 2000 records by 2000t) is judged on the final non-audit measurement. Divergence and parity entries are in.

## Related Tickets
- TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP (found here; may be held on this ticket)
- TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED (retains dissolved records)
- TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK and TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE (found here)

## Related Docs
- docs/parity_ledger/social_narrative.yaml

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/systems/world_systems/groups.py
- src/engine/pipeline_phases/groups.py
- src/systems/social_systems/party_lifecycle.py
- src/core/state.py (GroupRecord)
- src/domains/cooperation/phase.py

## Assumptions / Open Questions
- Priority raised to P1 by rpg-planner: this blocks the s42 re-anchor chain. Not dispatched: lead-planner is asking the owner's go; no code until it relays the yes.
- Size of the behaviour change is not known until the re-measure: groups now last, so hashes and timing move.
- Whether BINDING_CONTRACT_NOT_ACTIVE should stay as ruled for FULFILLED is open (see the ruling).

### rpg-designer's ruling, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"SHAPE A, as a typed binding on the group, with the formation-tick stamp folded in. B and C are REJECTED.
RULE: what keeps a contract-formed group together is the contract that formed it, held by the entity that holds it. A leadership change does not change that binding. A group is dissolved for its contract only when the binding contract is no longer ACTIVE (fulfilled, expired or removed), or when its holder has left the group or died. Each of these is a typed dissolution reason.
SHAPE:
1. A typed binding on GroupRecord, e.g. bound_by: Optional[ContractBinding(holder_id, contract_id)].
- It is set once at formation (the groups.py:322 path), from the contract the formation scan used.
- It has one writer (formation) and is cleared only with the group.
- It is omitted from the canonical dict when None, so groups not formed by a contract are unchanged.
2. The dissolution check (groups.py:159-166) reads bound_by.contract_id from bound_by.holder_id's contracts, never from the current leader's.
- Typed reasons: BINDING_CONTRACT_NOT_ACTIVE (with the status), BINDING_CONTRACT_MISSING (with the holder present) and BINDING_HOLDER_LEFT.
- The 'not-found = invalid' path stays for MISSING, which is now a real removal.
3. FOLD IN: the GroupRecord built at formation stamps last_leadership_check_tick = the formation tick (groups.py:340-347).
- A default of 0 that opens the election on the formation tick is a hidden default and arbitrary leader flipping. The cadence starts at formation.
- Both changes go in ONE ticket, as one defect chain.
WHY NOT B: an election would become a contract writer, and a recruit contract with source 19 would sit on 33. That misstates who recruited whom.
WHY NOT C: it changes the leadership law to fix a lookup.
A matches both laws in force: one state basis, and no dissolution without a changed typed reason.
TESTS, on the real code, not the replica:
- An election that moves the leader off the holder does not dissolve a bound group.
- Each of the 3 typed reasons dissolves.
- A group formed at tick t holds no election before t+100.
- bound_by round-trips and is omitted when None.
- Groups not formed by a contract are byte-identical.
- The 19/33 chain on crowded s42: the group formed at about t100 lasts until its contract ends.
RE-MEASURE: groups now last, so hashes and timing move. Run the paired 15 runs (3 worlds x s42-46, base 6fdfdf555) with the id fix AND the churn fix together.
- STOP on any per-world rise in deaths by cause, with victim ids and first diff.
- Report:
- group lifetime p50/p90;
- formations, and dissolutions by typed reason;
- re-formations by the same members within 10 and 50 ticks (expect about 0 for this chain kind);
- overwrites and ghosts (still 0);
- frontier tick time against the 35.6% rise.
OPEN, after the fix (the designer rules from the counts, before the close, not before the fix): re-count the FULFILLED dissolutions (84/156/201) and trace one. Does a fulfilled recruit contract ending its group match the fiction, or is 'recruitment fulfilled' the moment the group should become permanent? This may move the rule for BINDING_CONTRACT_NOT_ACTIVE.
FINDINGS to file (counts first, not in this ticket):
- block_no_partner_<id>_<tick> is one new blocker per tick per entity, grouped or not. That looks like a blocker that is re-created and never deduplicated, and it likely explains the per-living blocker growth. Lean P2: TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK.
- About 12 ACTIVE recruit contracts are held at once for the pair 19->33: duplicate contract creation per pair. Count the active recruit contracts per pair across the runs; P2 if material.
Then the owner go via you. The 2.146 rewrite covers the id fix plus the binding (class Bug Fix; the planner numbers it)."

lead-planner's note, same message: the final hold rule (non-audit at FULL, audit figure beside it, alternating 3 per tree) still stands on top of the re-measure. Each run set needs its go. No code until it relays the owner's yes.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
