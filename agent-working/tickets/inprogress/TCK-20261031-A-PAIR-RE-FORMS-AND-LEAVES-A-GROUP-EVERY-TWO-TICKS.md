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
- Priority raised to P1 by rpg-planner: this blocks the s42 re-anchor chain. Owner's go: #715 6552476734, dispatch per the ruling, one batch with the id fix. Heavy runs need lead-planner's go; push and merge are separate.
- PR note, from rpg-planner (u24, relayed by lead-planner): groups that now last feed REGROUP targets, which ties to F3's lodger suppression and to N14. If the churn fix lands before N14-on-F3, the N14 base should sit at or after it, or the order must be disclosed.
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

### rpg-designer's ruling in advance for the re-measure, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"RE-FORMATIONS: split the re-forms by the same members at 10 and 50 ticks by binding contract.
- SAME contract_id as the dissolved group: true churn, GATED at about 0.
- DIFFERENT contract (the pair's next ACTIVE duplicate, e.g. _39 then _54): reported, NOT gated, and attributed to TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE.
- The duplicates stay OUT of this batch unless a death STOP's first diff traces to a duplicate-driven re-form.
NO REBINDING: a group whose binding contract ends does not quietly rebind to the pair's next ACTIVE contract. That would hide the duplicate defect. The duplicates ticket fixes the source.
Note 1 (12 contracts at t100, before the first churn) goes into the duplicates ticket's counts as it stands."

### rpg-designer on the churn plan at 8f0a5dd74, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"Q1 = A, Q2 = A. The three defaults are accepted, each with one tightening, and the dirty-set risk gets a law in advance.
Q1, A: keep GroupRecord.contract_id as the one stored id and add contract_holder_id. ContractBinding was only an 'e.g.'; the rule is one copy of one fact.
- contract_holder_id is omitted from the canonical dict when None, so squads and unbound groups stay byte-identical.
- The fingerprint includes it for bound groups; their hashes move anyway.
Q2, A: every end of a bound group carries a typed reason: the 3 contract reasons plus LEADER_LOST, MEMBERS_BELOW_TWO and DEFECTION.
- It is an ENUM on the typed dissolution record or event, never a string. Unbound groups stay None.
- FIXED PRECEDENCE when several apply on one tick, one reason per dissolution: BINDING_HOLDER_LEFT > BINDING_CONTRACT_MISSING > BINDING_CONTRACT_NOT_ACTIVE > LEADER_LOST > DEFECTION > MEMBERS_BELOW_TWO.
- The cause outranks the consequence: a pair whose holder dies is HOLDER_LEFT, not MEMBERS_BELOW_TWO.
- Test one tick with several reasons.
DEFAULTS:
- The holder is the leader and dies -> BINDING_HOLDER_LEFT. Accepted; it follows from the precedence.
- A non-holder leader dies -> dissolves as today (SOC-176), reason LEADER_LOST. Accepted.
- No legacy fallback: accepted, but make it EXPLICIT. A GroupRecord with contract_id set and contract_holder_id None is INVALID at construction or validation (a typed error), not silently unbound. Tests build with a holder.
DIRTY-SET RISK, law in advance: a bound group dissolves ON THE TICK its binding contract stops being ACTIVE. Its validity must not depend on whether the group happens to be dirty or on a full-scan tick.
- The implementer's count comes first: live bound groups whose contract has ended, with the lag in ticks.
- If the count is above 0, the fix is IN THIS TICKET, since the binding is what makes the gap reachable. Lean: an expiry is known ahead of time, so a bound group is relevant on the tick its contract's expiry falls due, and a contract status write marks its bound group dirty. Deterministic, with no full scan.
- Re-measure gate: lag = 0.
- If the count is 0 only because the full-scan cadence happens to cover it, that is still a FINDING: send it to the designer with the cadence. A lag hidden by cadence is not a lag of 0 by law."

lead-planner's note, same message: "invalid at construction" means loading an old save or checkpoint with a contract_id and no holder would raise. The load path needs handling, or that's a question back to the designer; don't choose silently.

### rpg-designer on checkpoint restore, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"OPTION A, under one rule that answers both questions. Seed the counter, and refuse a missing holder on a bound group.
RULE: restore may fill a field missing from an older checkpoint ONLY when its value is a pure function of the loaded state that a ruling already defines. Otherwise it refuses with a typed error. It never guesses. It is ONE post-unpickle step in ScenarioCheckpointer's restore (the single authoritative restore path), with no scattered fixups.
APPLIED:
1. next_group_id: SEED it. Addition 4 already defines it as max(10000, the highest non-squad id + 1) from the loaded groups. That is derivation, not a second writer.
2. contract_holder_id on an UNBOUND group (contract_id None): set it to None, the only valid value. NOTE: a slotted record unpickled from an old checkpoint lacks the slot entirely, so without this step EVERY group raises AttributeError, not only bound ones. Test it.
3. contract_holder_id on a BOUND group (contract_id set): REFUSE with a typed error that names the group and says the checkpoint predates the group-contract binding. B's guess from the contract's source fails when the contract is gone, and it adds a second writer. That checkpoint stops being restorable, which is accepted since there are no checkpoint files in git or data/.
TESTS: an old-shape pickle with
- an unbound group: restores, holder None, counter seeded;
- a bound group: raises the typed error;
- a current-shape round-trip: byte-equal.
GENERAL FIX: agreed. A checkpoint-format version in the header, refusing an unknown or older version BEFORE unpickling, is its own ticket, P2, filed by rpg-planner-ubuntu. Any field added to a slotted state record has this hazard today. F3's lodged_in and beds on the u24 rpg side are one case; the designer is telling rpg-planner."

rpg-designer's addendum, same ruling (same relay). Word for word:

"Restore SEEDS next_group_id by calling the existing seeded_next_group_id from the one post-unpickle step. That's the same derivation __post_init__ uses, so there is one definition and no second writer. Restore REJECTS a bound group with no holder (typed error) and sets None on unbound groups. Add a test: an old-shape pickle with the counter slot missing restores with the seeded value, and groups.py:38 and apply.py:350 read it without error."

### rpg-designer on the two corrections, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"1. CHECKPOINT FORMAT: raise TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION to P1. A silently shifted slot is worse than a crash: it corrupts state with no signal and breaks replay. 'Append new fields last' is a convention nobody enforces.
Shape lean (the planner refines):
- The header carries a schema fingerprint: the ordered field names of every slotted state record.
- Restore accepts an exact match.
- It also accepts a mismatch whose ONLY difference is fields appended at the end that FIELD_RULES names. Those are filled by the derive-or-refuse rule.
- Any other difference (an insert, reorder, rename or removal) refuses with a typed error BEFORE any value is used.
- A checkpoint with no header (today's) is treated as the pre-fingerprint schema only if its shape matches; otherwise it is refused.
- The rule stands with one precondition made explicit: 'a pure function of the loaded state' applies only once positional integrity is proven.
- It does NOT block F3 or the churn fix: both append last and test it. It should land soon after the second of them, and its FIELD_RULES rows reuse checkpoint_fields.py.
- If the fingerprint guard belongs in tests/architecture, testing-planner owns that file and gets the ask from the ticket's planner.
2. EXPIRY / FULFILLED: noted. A time expiry writes FULFILLED, so a status write marking the bound group dirty covers it. The lag = 0 gate stays across the 15 runs.
The designer's OPEN item is provisionally CLOSED, as intended:
- A recruit contract is a TERM. ACTIVE reaching expiry_tick -> FULFILLED means the term was served, and the group it bound ends with BINDING_CONTRACT_NOT_ACTIVE(FULFILLED).
- Renewal is a new contract, never a quiet rebind.
- Confirm from the record in the re-measure, not a new trace: for every FULFILLED dissolution of a bound group, the dissolution tick equals the contract's expiry tick (lag 0).
- Any FULFILLED end BEFORE expiry is a non-time fulfilment: count those and trace one to the designer.
- Renewal vs leak for the per-pair duplicates (_54 to _74) stays with TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE.
Ubuntu status (pin regenerated last, a STOP if anything moves before t100, helper extraction in its own hash-identical commit, no ratchet raise): no objection."

### rpg-designer on the re-measure STOP, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"BASE: c9b9a50f4 is ACCEPTED (a STOP must not charge #803 to this fix). rpg-planner confirms #803 is behaviour-neutral. F3 and retention measure on 6fdfdf555; whichever of them lands second re-measures on top of the other.
Q1: PER WORLD. That is the designer's rule as written, not option B changing it: a rise in deaths by cause per world, across its 5 seeds. A per-pair check is the driver's choice, not the designer's STOP. One pair in diverged trajectories (total -1, HAZARD +2) can't separate cause from chaos.
- Run the remaining 14 pairs.
- Report per-pair rises with victim ids and the first death diff, WITHOUT stopping on them.
- The STOP is judged per world, on HAZARD, COMBAT and DEFEAT separately.
Q2: HOLD THE TRACE until the 15 runs show whether a world STOP fires.
- If one fires, the trace goes as you approved: the first state diff, and for each extra victim of that cause, grouped at entry or not, and whether the group is a duplicate-driven re-form.
- If none fires, no trace. Report the s42 HAZARD victims 3/11/5 (earlier on the branch) per-pair for the record.
Q3: B. At formation the scan binds the ACTIVE contract with the LATEST expiry_tick, with ties broken by the lowest contract id.
- Binding a contract about to expire when a longer one exists produces 1-tick groups, which is churn in effect.
- The fiction: a pair joins on the term with the most time left.
- Formation only, no rebinding, deterministic. The duplicates stay visible: count ACTIVE recruit contracts per pair (67 is the headline for that ticket).
- C stays out: the source fix belongs to TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE, counted after this fix.
- Test: with two ACTIVE contracts for a pair, the group binds the later-expiring one and lasts until its expiry.
FACT 2: 'ON THE TICK' must not depend on phase scheduling.
- Use ONE shared predicate from the contracts module, e.g. contract_is_live(contract, tick) = ACTIVE and tick < expiry_tick. The groups check uses it, so a bound group whose contract is due ends ON its expiry tick even if the contracts phase skipped.
- The reason is BINDING_CONTRACT_NOT_ACTIVE(FULFILLED), the status an ACTIVE contract takes at expiry via resolve_expirations. Never EXPIRED: EXPIRED is for OFFERED and COUNTERED only.
- The _binding_end backstop reduces to that predicate. The backstop and lag gate stay at 0, and the contracts phase still writes the status when it next runs.
- Test: a contracts-phase skip on the expiry tick still dissolves on that tick with FULFILLED.
FACT 3: HOLDER_LEFT. A non-holder leader's group whose holder drifts away ends because its holder left; the size rule firing the same tick is the consequence. The 15 runs report the count.
THEN: the FINAL tree (latest-expiry pick plus contract_is_live) gets all 15 pairs vs c9b9a50f4. Gates:
- per-world deaths by cause;
- same-contract re-forms about 0;
- lag 0;
- overwrites and ghosts 0;
- group lifetime p50/p90 reported (the designer expects p50 well above 1);
- frontier tick time against the 35.6% rise."

lead-planner's decision, same message: skip the 14 interim pairs on the current tree; make Q3, Fact 2 and Fact 3 first, then run all 15 on the final tree, stopping per world as ruled. "Rise" is to be defined before the runs and sent to it. Each run set needs its go when src is final.

### rpg-designer's world STOP bar, set before the data, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"For each (world, cause) among HAZARD, COMBAT and DEFEAT, against the same seeds on base:
TIER 1, BLOCKING STOP: the fix's total for that cause across the 5 seeds rises by >= max(2, ceil(10% of base's total)) AND rises in >= 3 of the 5 seeds. This stops, and the trace goes as approved.
TIER 2, VICTIM REVIEW (any rise above 0 that misses tier 1): no stop by itself. Each extra victim of that cause gets its first state diff and death path, reported against one test: does the path pass through this fix's mechanism?
- Here that means the victim was in a group formed or dissolved under the new binding, or in a re-form within 50 ticks of its death (same contract or a duplicate).
- ANY victim that passes through the mechanism -> STOP, sent to the designer with the chain.
- If none do, it's divergence, reported.
REPORTED ONLY:
- a rise in a world's all-cause total with no cause in either tier;
- every per-pair rise, with victim ids.
WHY: across 9 comparisons, chance alone moves +1s. A mechanism-traced death counts whatever the size; a chaos-sized rise with no mechanism doesn't. This matches F3's subject 17 (+1, traced, divergence) and the retention exemption (first diffs at cap-exempt adoptions, which is a mechanism, so it was dropped).
It applies to this batch, and the designer uses the same bar for the rpg lanes from now on."

rpg-designer's correction, same relay: "do NOT run the 14 parked pairs on 9e3b07c22. The Q3 pick and Fact 2 change the tree, so run ALL 15 pairs ONCE on the final tree vs c9b9a50f4, with the gates as listed."

lead-planner's note, same message: "extra victim" is fixed per world before the runs: the victims present on the branch and absent on base for that cause, per seed. Tier 2's traces need instrumented runs; list them in the go ask. My draft definition of a rise is dropped.

### rpg-designer on the first-pair trace, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"1. NOT A NEW TICKET: the INTERCEPTING chase along y=40 into terrain draining 20 hp/tick, with no retreat, looks like TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER. The designer ruled that in the N14 s44 analysis: there is no engagement exemption from hazard avoidance (in s44, followers adopted scout 16's target and walked into bandit_road, hazard 2.0).
- Check whether the INTERCEPTING writer (tactical.py:612) is inside that ticket's scope. If its path ignores hazard, it's the same law: a chase is a move, and it avoids hazard like any move.
- Attach entities 3, 11 and 5 there as evidence, and widen the scope if it named only bracketing moves.
- File separately ONLY if the path does respect hazard and the drain comes from something else.
2. MECHANISM TEST, sharpened (the same for every lane): 'passes through the fix's mechanism' = a CAUSAL step in the death chain is behaviour the fix changed. Being in a group, or a diverged world, is NOT enough.
- Churn fix, entity 3 (leader and holder on a fresh contract): did the INTERCEPTING chase come from group engagement (a group target, a follower adopting the leader's target, or similar)? If yes, the fix's longer-lived groups feed a known defect.
- 11 and 5 (ungrouped) FAIL the test as described.
3. AN EXPOSED OLD DEFECT: if the final 15 show a tier-1 HAZARD STOP whose victims share this path, the fix isn't wrong. The older defect then ranks first: the hazard ticket moves AHEAD of the landing (like the id fix landing with the churn fix). It is NOT waived as divergence. Below tier 1, it's tier-2 divergence, reported, with the victims attached to the hazard ticket.
4. FIRST DIFFS: the t176 movement diff is base's overwrite of live group 10021 being removed. That's the id fix doing its job; no action."

### rpg-designer's final Tier 2 wording, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"TIER 2 TEST (final wording): a victim passes the mechanism test ONLY if, within the lane's window before death, a CAUSAL step of its death path is behaviour the fix changed. For the churn fix:
- it was following a group objective of a group formed or dissolved under the new binding; OR
- that group's dissolution or re-form changed its goal or its location.
Merely being grouped, or a diverged world, does NOT pass.
WINDOWS, named in each lane's brief: churn 50t; F3 and retention 200t.
OUTCOMES, three, never two:
- PASS -> STOP, sent to the designer with the chain.
- FAIL -> divergence, reported.
- NOT SHOWN (the trace can't establish the chain either way) -> to the designer with the rows. Neither a pass nor divergence; the designer rules each case.
On the s42 examples: 11 (ungrouped, 29t after its term ended, on a chase) FAILS unless the dissolution changed its goal into that chase. 3 FAILS unless the chase came from its group's objective. The trace states which.
LAG: accepted. The final set records the true expiry tick on each dissolution, with a positive control, and any lag above 0 is a gate failure. The 11 late-by-1-7 cases aren't re-run; contract_is_live should take them to 0."

lead-planner's note, same message: rpg-planner (u24) takes the widening of TCK-20261020-ENGAGE-BRACKETING-MOVES-WALK-A-GROUP-INTO-A-HAZARD-CLUSTER. Its go is given for the final tree once src is final and reviewed, with the SHA told to it at start.

### rpg-designer on the relevance fix, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"RULES the relevance fix NOW, in this ticket. The positive control proves the gap by construction, so the fix is needed whatever the 15 runs show.
FIX: a bound group is RELEVANT to the groups phase on the tick its binding contract becomes due, using the same due test as contract_is_live and resolve_expirations, regardless of the dirty set and of whether the contracts phase ran.
- Derived from state: the bound groups whose holder's contract is due this tick, by an index or by a scan over bound groups only.
- No new durable field, unless an index is needed for cost. In that case the index is typed, rebuilt on restore, and listed in FIELD_RULES.
- Tests:
- the implementer's positive control (due, outside the dirty set, contracts phase skipped) now dissolves ON that tick with FULFILLED;
- an unbound or not-due group is NOT added to the relevant set.
THE RUNNING BATCH: let it FINISH. Deaths, lifetimes and re-forms on fc22ae71f stay valid evidence. Also report the count of (bound group due, contracts phase skipped, group not dirty) tick-instances; your 'lag 0 with skipped phases' report nearly gives this already.
- Count 0 in all 15: the fix can't change those runs. Prove it with 3 runs byte-equal to fc22ae71f (one per world), and close on the batch.
- Count above 0: re-run ONLY the affected pairs on the fixed tree, and judge the lag gate there.
- Your added stop (lag above 0 -> stop at the end of that pair, to the designer) stays for the current batch.
READINGS ACCEPTED:
- expiry -1 (no expiry) ranks latest;
- 'qualified partner' as defined;
- formation refuses a DUE contract (no born-dead groups);
- resolve_expirations on the shared due test, with no behaviour change.
(Victim reads, also relayed: the designer has entity 3 as NOT SHOWN via the shared-target bonus; if that path recurs on the final tree, the trace must answer it.)"

lead-planner's note, same message: the fix may be coded while the batch runs, on a separate tree from the runs; short test runs may overlap. The 3 byte-equal or re-run sets have its go when the list is sent.

### rpg-designer's correction on hazard deaths, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Replaces the hazard part (items 1 and 3) of its ruling on the first-pair trace. Word for word:

"The designer said a chase 'avoids hazard like any move', and that ENGAGE-BRACKETING meant 'no engagement exemption from hazard avoidance'. That was WRONG: NO move avoids hazard.
- v1 disclosure H1 (docs/plans/systemic_world/v1_disclosure.md): 'Subjects do not leave or avoid a draining regional hazard'. Routes weigh terrain cost only (2.128).
- H1 is owed to the owner after v1, and the ENGAGE-BRACKETING ticket is tied to it (row N3).
- So these deaths are not a lane defect that a lane can rank ahead. They're a disclosed world gap that needs an OWNER decision.
REVISED DECISION RULE for hazard deaths, any lane:
1. A victim whose death path is a walk into a draining hazard with no avoidance is H1 EXPOSURE. Tier 2 then asks only whether the fix's change is a causal step that put it on that walk within the window (a group objective, a dissolution, a leave, a retreat, ...). The hazard itself is never the fix's mechanism.
2. A tier-1 HAZARD rise whose extra victims are H1 exposure FED by the fix's causal step becomes an OWNER ROW via the leads: (a) bring H1 (hazard avoidance, or at least leaving a draining hazard) forward before the landing, or (b) land the fix with the rise disclosed against H1. The designer's lean comes with the numbers; the lane doesn't decide.
3. H1 exposure NOT fed by the fix FAILS Tier 2: divergence.
VICTIMS FILE (old tree, nothing runs for it):
- Entity 3: NOT SHOWN (shared_target 34 until t402, with the target_score bonus). If it recurs as an extra victim on the final tree, the trace must answer whether the group's shared-target bonus picked 34.
- Entity 5: NOT SHOWN (left its group the tick before; writer not shown).
- Entity 11: FAILS (ungrouped INTERCEPTING; H1 exposure).
- Entity 32 on base: a panic retreat into the hazard, also H1, on base."

### rpg-designer on Tier 2's scope and crowded_frontier, 2026-11-01 (u24; relayed by lead-planner-u24 and lead-planner). Word for word:

"A, with the exception, as both of you prefer.
- Tier 2 applies to a (world, cause) whose 5-seed TOTAL rose above 0 and missed tier 1.
- A per-seed rise inside a world total that did NOT rise is reported only (the 'per-pair rises reported' line), with victim ids. The implementer's per-seed reading is corrected.
CROWDED: no STOP and no Tier 2 (HAZARD 22->21, COMBAT 89->86, DEFEAT 48->40, all causes 159->147). The gates hold.
EXCEPTION, NOT GATING: trace the crowded s42 HAZARD cluster (2 at t417; 6, 5, 1, 7 and 13 at t444-453) if a trace pair is left after the other worlds. It is H1 evidence, not a STOP test.
- The question: did the group objective (a shared target or bracketing), or a group ending, put them on the walk (the N3 shape)?
- If yes, it goes to ENGAGE-BRACKETING and to the H1 owner row, as the mechanism H1's first step must cover.
- Report the outcome as PASS, FAIL or NOT SHOWN, for the record.
Noted:
- s45 audit tick +27% (single run): report it in the frontier tick-time line; not gating on single runs.
- The byte-equal runs remain the proof for the relevance fix."

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary

### rpg-designer's ack on the 15 paired runs (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

1. URBAN Tier 2 (6, 16, 17 on s42; 14 on s44), standing reading:
- FED needs a CAUSAL step, within 50t of death, where the churn fix's changed behaviour selects the victim's walk or target: a group objective or shared target of a group formed under the new binding, or a goal or location change from its dissolution or re-form.
- Fight participation shifted by longer-lived groups is trajectory (NOT FED).
- Outcomes: PASS -> STOP to the designer; FAIL -> divergence; NOT SHOWN -> rows to the designer.
2. H1 CLUSTERS: entities 5, 1, 7 and 13 appear in both crowded s42 and frontier s43. Ids are spawn order, so these are DIFFERENT entities with the same spawn slot.
- Record each one's spawn role (starting party or faction slot), and whether the two clusters are the same contract kind and group shape.
- A spawn-slot pattern would mean a starting-group configuration walks into hazard on its first long-lived group, which is useful for H1's first step.
3. LAG: the independent check (all 741 FULFILLED ends 101-109 ticks after the contract's id tick, none early) stands alongside the _binding_end instrument. The 3 byte-equal runs plus the positive-control test carry the dirty-set law. No further proof is needed.

### rpg-designer on Tier 2 close and the hazard window (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

The churn Tier 2 is CLOSED as divergence. Urban s42 16, 6 and 17 FAIL, and s44 14 is not an extra. The relevance fix is proven byte-equal. Nothing gates the churn landing on the designer's side beyond the final non-audit measurement.
After that, the close/push ask carries: the 2.146 rewrite (the id fix plus the binding); the disclosures: the duplicates ticket for different-contract re-forms, the lag instrument caveat, single-run audit timing, and the H1 clusters.
HAZARD / WINDOW: no fresh probe now, and the window stays at 50t. The NOT SHOWN cases (crowded 1, 6, 7; frontier 1, 7) are recorded as H1 evidence as they stand and don't gate. What they show, enough for H1's design: novice workers in recruit pairs follow a group's shared target into a chase that ends beside a draining hazard. The last leg is their own pick, and nothing on the way weighs hazard.
A read (not measured) finding goes to ENGAGE-BRACKETING (rpg-planner u24 owns it): target_score ranks group_bias directly after adjacency (tactical.py:428). That ticket's counts-first step takes the target_score probe at the pick tick when it's scheduled. The designer is adding both to the H1 owner-row draft.

### rpg-planner on the final measurement's method (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

(d) is the deterministic way to meet the rule's intent, the cost of normal computation at FULL with no audit-only work. Conditions:
1. Installed by the wrapper ONLY, on PROD_SMALL, with no src change on either tree. Both arms (base c9b9a50f4 and the fix) use the same wrapper and pin.
2. Before any arm runs: one smoke run per world AND per tree must show mode FULL on EVERY tick. Any non-FULL tick is a STOP to rpg-planner.
3. The report calls it 'non-audit, pinned FULL (PinnedNormalGovernor)', never plain 'non-audit'. It discloses that production on this host isn't measured, and cites the smoke rows (frontier s42 600t: FULL 66 / MINIMAL 281 / OFF 253) as the only evidence on that.
4. The hash comparison with the audit runs is informational only, not a gate. Any mismatch goes to rpg-planner before anyone reads anything into it.
5. Run18's +35.6% (audit, 6fdfdf555 vs edb638b6a) is NOT compared with this result: a different mode and base, stated in the report.
6. Heavy slot: on ubuntu, no u24 slot is needed.

lead-planner's terms, same message: go stands on those terms, including the smokes: 3 worlds x 2 trees first, short. Then the 18. Message lead when the 18 actually start, after the smokes have passed. Other terms unchanged, stop at 90 min.

### rpg-planner adds a smoke check (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

No objection to rpg-planner-ubuntu's (d) picks, including the default ConcurrentExecutionAdapter. The hold rule doesn't assume the sequential executor; it assumes both arms run the same setup, so keeping the audit runs' executor is the better match.
One cheap check is added, since the helper's docstring says 'Pair it with LocalSequentialExecutor' without giving a reason:
- In the smoke step, run ONE world TWICE on the same tree with the concurrent adapter and the pin. The final hashes must be IDENTICAL. If they aren't, it's a STOP to rpg-planner before any arm runs, because the concurrent path would be bringing host timing back in.
- The report names the executor next to 'pinned FULL'.
The other picks are fine: inject governor= from the wrapper, NORMAL maps to FULL with policy recorded per tick, and the zeroed signals are disclosed under condition 3.

### rpg-planner on the final measurement's outcome (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

1. Crowded persistence -10.9 ms is NOT a hold. The rule guards cost the fix ADDS: a resolved rise in a total or in a phase beyond its bar. A resolved fall never fires, named phase or not, so rpg-planner-ubuntu's reading is right and the implementer's 'fired' is wrong. Two conditions:
- The hashes are identical, so state is identical, but the report should still say WHY persistence fell. Most likely fewer group/contract records to persist after the churn fix; the store figures move the other way, so name it. The work count below should show it. If no one can explain it: 'resolved fall, cause not shown', not a gain.
- It is NOT offered as a speed claim in the PR.
2. Overall: NO HOLD FIRES, with frontier UNRESOLVED. That is not a pass, and the push ask WAITS for the pending count.
- Totals: crowded is a resolved fall; urban +2.3% is within spread; frontier +9.7% median is UNRESOLVED (overlap 1.7 s, resting on one base rep; the fix was slower in 3/3 pairs). Phases: largest +3.31 ms vs a 6.72 ms bar, under. Store: at most 110 of 2000, within.
- REQUIRED before the push ask: the deterministic work count, base vs fix per world, summed over 2000t (records sorted and walked per tick by groups and by cooperation), plus the groups phase's own row. The 6 runs on ubuntu are fine.
- How the count decides the frontier line:
(i) Frontier's count RISES, attributable to the fix's shape (the ContractBinding holder lookup or contract_is_live walks). Disclose 'frontier: expected real cost rise, estimated <median>% (UNRESOLVED by timing), from <N> extra records walked per tick', and cite the groups phase row. Not a hold, UNLESS that phase row is itself a resolved rise beyond its bar, which is a STOP to rpg-planner.
(ii) The count is FLAT or LOWER on frontier. Disclose 'frontier +9.7% median UNRESOLVED; no extra work counted; timing spread (one base rep)'. Not a hold.
(iii) The count rises by more than about 2x what the timing rise suggests, OR rises in a world where timing didn't move: STOP to rpg-planner before the push ask.
- The disclosure keeps: non-audit pinned FULL with ConcurrentExecutionAdapter; production on this host not measured (smoke row only); no comparison with +35.6%; the audit figures from different single runs as context only.
The push ask goes once the count is in and sorted into (i) or (ii). (iii) comes back through me to rpg-planner first.

lead-planner's note, same message: fix (iii)'s "about 2x" before reading the count, in plain numbers, so the sort isn't chosen after seeing it; send lead the reading. A count rising in urban or crowded also reaches (iii) as written.

### rpg-planner fixes the (iii) thresholds and the frontier wording (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

The (iii) thresholds are FIXED NOW, before any count is seen.
A (frontier): CONFIRMED as written. The time-equivalent is right; rpg-planner did not mean a plain 19.4% on the count. It fires if R x T > 52.2 s (R > 4.66), with T = 11.2 s from base rep 1.
B (crowded/urban): CHANGED, because 1% would fire on the fix's intended effect.
- It fires per world and per phase alone (C_g and C_c separately) if C_fix / C_base > 2 x that world's STORE RATIO.
- Store ratios: crowded 45/19 = 2.37, urban 79/19 = 4.16, so it fires above 4.74x and 8.32x base.
- Frontier ALSO gets the same per-phase check (110/28 = 3.93, fires above 7.86x), alongside A.
- Rationale: the work should scale roughly with the live records the fix keeps, and more than twice that is the 'work far beyond what the design explains' case that (iii) exists for.
- A rise at or below the bar is NOT a STOP. It's disclosed with its rows, as 'groups/cooperation work rises with the live-group store (C ratio x vs store ratio y), as designed'.
- rpg-planner's prediction, stated first: C_g rises in every world, below the bar; C_c is roughly flat.
ATTRIBUTION: CONFIRMED. The frontier line uses (i) or (ii) for the count, but the cause claim is limited to what the count shows. Wording:
'frontier +9.7% median, UNRESOLVED by timing (fix slower in 3/3 pairs; overlap 1.7 s on one base rep). Groups and cooperation account for about 2 s of the 26 s (C ratio <x>); the rest is not attributed. By median difference, resolution_overhead +3.3, persistence +2.1 and combat_engagement +1.7 ms/tick moved; their cause is not shown.'
- Do NOT name 'trajectory' or 'longer-lived groups' as a cause. It's a reasonable guess, but nothing measured it. A ticket is optional if the designer wants that attribution later.
- Unchanged: crowded's persistence fall needs a stated cause or 'cause not shown', and is not offered as a gain.

lead-planner's note, same message: "store" here is at t2000; if the count uses another store basis, say so before reading.

### rpg-planner confirms the corrections, the lifecycle disclosure and the order (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

ALL THREE corrections are CONFIRMED, and the outcome stands: (i), no hold, (iii) doesn't fire.
1. Frontier line, CONFIRMED: 'Groups rose about 1.4 s and cooperation fell about 1.5 s, net about 0 of the 26 s (store-visit ratio x1.92); the rest is not attributed. By median difference, resolution_overhead +3.3, persistence +2.1 and combat_engagement +1.7 ms/tick moved; their cause is not shown.' ADD: 'groups phase median 0.270 -> 0.990 ms/tick on frontier, a resolved rise, under its 6.72 ms bar.'
2. ONE quantity, CONFIRMED: 'store records visited per tick, summed'. State that cooperation's own walk wasn't separately counted, and that cooperation's time fell. No further count is needed.
3. CONFIRMED: 'groups/cooperation work rises with the group store, mostly retained dissolved records (visit ratio x vs store ratio y)'. (i)'s 'attributable to the fix's shape (holder lookup / contract_is_live)' is DROPPED. The bars stand.
Crowded persistence: 'resolved fall, cause not shown; persisted-record counts rose 36,449 -> 55,465'. Not offered as a gain. CONFIRMED.
RETAINED DISSOLVED RECORDS: more than an awareness line. Durable state needs a defined lifecycle, and this store now grows without bound and is visited every tick; the fix introduced that by ending the overwrite. It does NOT block the churn push. The disclosure states the rate: 'the group store keeps every dissolved record; at 2000t it holds 43-104 records and the groups and cooperation phases visit each one every tick (about 1 ms/tick on frontier at 2000t); this grows with run length.' rpg-planner is filing TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK (counts-first, linked to TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND) and asking rpg-designer for priority, including whether it must land before 5000t sets read the groups cost. The PR body cites that id.
ORDER: F3 lands FIRST (its owner ask is pending a re-sync after #822, which is awaiting the owner's merge), so the churn lane re-measures on F3 per the cross-lane rule. Push ask: when your PR notes carry these lines, after F3 is on main.

lead-planner's note, same message: wait for F3 on main before syncing. Send the re-measure list and estimate for what "re-measures on F3" needs; the 15 pairs and the 18 are both candidates, so ask rpg-planner through lead which applies. Keep the raw until the PR lands.

### rpg-planner on the re-measure on F3 (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

Skip A (F3 moves the hashes). Scope:
1. GATING: the full 15 pairs with the Tier death gates.
- Base = main with F3 landed; arm = the churn fix merged onto that main.
- Same worlds, seeds 42-46 and run length as the original Tier set, the standing death bar (tier 1/tier 2; FED/PASS only when the fix's changed behaviour selects the walk), and hard law {}.
- ADD one cross-lane row per world: lodger counts (lodged_in set ticks, leaves) base vs arm, plus group members who are lodged at a group decision. That's where the two fixes meet, since a lodged member is invisible and untargetable.
- Any tier-1 row, or a victim who was lodged or had just left a bed within 50t, is a STOP to rpg-planner.
2. WORK COUNT, cheap and deterministic: rerun the 6 s42 work-count runs on the new base and arm, and apply the same bars fixed earlier: A on frontier (R x 11.2 s > 52.2 s), and per phase > 2 x the store ratio. No noise; about 20 min.
3. TIMING, the 18 pinned runs: ONLY IF the work count's visit ratio moves by more than 25% in any world vs the pre-F3 ratios (x1.52 / x1.92 / x2.13), or (iii) fires. Otherwise the pre-F3 timing disclosure stands, plus one line: 'timing measured before F3; work count re-checked on F3, ratio within 25%'.
4. If the designer's step (a) (live-groups-only iteration, TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK, P2) lands WITH the churn fix, hash-equal on 3 worlds at 2000t, the timing question goes away: the 6 count runs would then show the visit count tracking live groups.
Host: all on ubuntu, no u24 slot needed. The u24 slot is lane C's (retention 15x2, running now).
D (identity on the merged src) is implied before the runs.

lead-planner's terms, same message: go for 1, 2 and D, starting after F3 is on main and the branch has synced; message lead first. The base for the (iii) store ratio changes on F3, so state the new ratios before reading the count.

### rpg-planner's final ruling on the re-measure on F3; SUPERSEDES the scope above (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

Final ruling: SKIP A; RUN B + C + D.
- A (hash probe): SKIP. F3 moves all three worlds, so the hashes will change. C is never skippable: the death bar was judged on a world that no longer exists once F3 lands, which is exactly what the cross-lane rule is for.
- C (15 pairs, death bar, audit): REQUIRED, the gating part.
- Same seeds and length as the original churn set, the standing tier-1/tier-2 bar, and hard law {}.
- PLUS the cross-lane row per world: lodged-member ticks at a group decision, and leaves, base vs arm.
- STOP to rpg-planner on any tier-1 row, or any victim who was lodged or had left a bed within 50t.
- The up-to-6 trace pairs are fine.
- B (18 timing runs + store-visit count + smokes and repeat): RUN IT. This REPLACES the 25%-trigger idea: the hold rule reads the cost on what actually lands, and it may also resolve frontier's UNRESOLVED line.
- Same setup: non-audit, pinned FULL, ConcurrentExecutionAdapter, the same smoke and repeat-hash check.
- The bars fixed earlier apply unchanged: totals >5% resolved; per phase vs its bar; A on frontier R x 11.2 s > 52.2 s; per-phase count > 2 x the store ratio.
- The PR disclosure takes B's numbers and DROPS the pre-F3 ones.
- D (identity on the merged src): yes.
If the designer's step (a) (live-groups-only iteration) is ready and hash-equal before B starts, B runs with it, and the store-visit count then shows it.
Base = main with F3 landed; arm = the churn fix merged onto that main. All on ubuntu.

lead-planner's terms, same message: go covers B, C and D, starting after F3 is on main and the branch has synced; message lead first, C before B. About 3.5 hours total. On B, measure with the host quiet.

### rpg-planner's rider: step (a) joins the batch, owner's go #715 6555733640 (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK (P2, rpg-designer ruling 2026-11-01), STEP (a) ONLY:
- The groups and cooperation phases iterate LIVE groups only, through a derived view (a status filter, or an index rebuilt from state).
- No new durable field unless cost forces one; if so, it's typed and has a FIELD_RULES row.
ACCEPTANCE:
- hash-equal to the churn tree on 3 worlds at 2000t;
- the frontier groups phase back near base per tick.
- Any hash move is a FINDING to the designer, named with its reader, and not patched past.
LANDING:
- With the churn fix if it's hash-equal before B starts (then B measures it); otherwise right after.
- It MUST land before any 5000t set that reports tick time (N14-on-F3, A'). If it isn't in when one runs, that set reports groups and cooperation ms separately, with the end store size.
NOT in this rider: step (b) (retention), which waits on the one retention policy with TERMINAL-PROJECTS, and step (c) (the id-reuse round-trip test).

lead-planner's terms, same message: implement before the F3 sync, so C and B run on the final tree. The 3-world hash check at 2000t has its go. The run-without-(a) default is withdrawn unless the hash check fails.

### rpg-planner's binding sections of TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK and the count bar with (a) (via lead-planner-u24 and lead-planner, 2026-11-01, word for word; the file is on rpg-planner's seat, uncommitted)

## Acceptance Criteria
- (a) live-only iteration (rider on the ubuntu churn lane, ubuntu owner #715 6555733640):
- The groups and cooperation phases do per-group work for LIVE groups only, through a derived view. No new durable field without a typed FIELD_RULES row.
- Final state hash equal to the churn tree (without (a)) on 3 worlds, s42, 2000t. Any difference is a finding to rpg-designer naming the reader, not patched past.
- Count bar, deterministic and from the same run: per-group work visits (groups and cooperation, each) EQUAL the summed live-group count per tick. Any excess is a finding naming what it visits. The derived view's own scan (filtering the store) is reported separately as 'store records scanned per tick, summed', disclosed, with no bar.
- Timing: frontier groups-phase median ms/tick at most 1.5 x base's median (base 0.270, so at most 0.405), or within base's spread. If not met, it is disclosed with the rows. It is not a STOP.
- Frontier bar A unchanged: R x 11.2 s > 52.2 s fires (iii).
- (b) retention: counts (every reader of a dissolved record, and store growth per 1000t at 5000t). One policy shared with TCK-20261020-TERMINAL-PROJECTS-ARE-RECORDS-WITH-NO-RETENTION-BOUND. Not on the critical path, and not in the rider.
- (c) id-reuse test: drop dissolved records, round-trip a checkpoint, and the next id issued is above every id ever issued. Not in the rider.
## Designer ruling (rpg-designer, 2026-11-01), P2
- (a) ITERATION, now: iterate LIVE groups only, since a dissolved record has no behaviour. Use a derived live view (a status filter or an index rebuilt from state), with no new durable field unless cost needs one (typed, through FIELD_RULES on restore). Acceptance: hash-equal to the churn tree on 3 worlds at 2000t, and the frontier groups phase back near base per tick. Any hash move means a phase reads dissolved records for behaviour, and that is a finding named with its reader. Land before any 5000t set that reports tick time (N14-on-F3, A'), with the churn fix if hash-equal or right after. If it isn't ready when such a set runs, that set reports groups and cooperation ms separately with the end store size, and discloses it.
- (b) RETENTION: one policy with TERMINAL-PROJECTS, counts first (contracts holding a group id, memory or beliefs, reputation, SimQ, read models, replay; growth per 1000t at 5000t).
- (c) ID REUSE: no reuse while next_group_id is persisted typed state. The load seed max(10000, the highest non-squad id + 1) applies only to an old checkpoint without the counter, through FIELD_RULES.
Related code: src/systems/world_systems/groups.py, src/engine/pipeline_phases/groups.py, src/systems/social_systems/group_service.py, and cooperation/GroupEvaluator.

COUNT BAR WITH (a): rpg-planner-ubuntu's 'at or below 2 x the live-group visits' is TIGHTENED to EQUAL. With live-only iteration, the per-group work visits are deterministic and should equal the summed live count exactly; 2x would hide up to one full extra pass. The filter scan is counted apart and disclosed, with no bar. The store-ratio bars are RETIRED for (a). Frontier A stays R x 11.2 s > 52.2 s. The timing bar is in the AC above, and it is disclosure, not a STOP.

### rpg-planner on the counter definition and the two expected excess sources (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

rpg-planner-ubuntu's counter definition is ACCEPTED as stated, before any reading (a loop-body entry before any dissolved-skip guard; per pass: election, defection, update_groups, cohesion; live count from state at phase start; compared per pass; counter not redefined).
The two expected sources are ruled NOW. Per pass, excess = visits - live_at_start must decompose EXACTLY into:
(A) Dirty-set dissolved ids read and skipped at the guard. Expected; disclosed as a named count per pass.
- BOUND: each dissolved id appears at most ONCE per pass, and only on its dissolve tick or the next.
- A dissolved id visited on any LATER tick is a FINDING to the designer: the dirty set keeps dissolved ids, so the work stays O(store).
(B) Rows created or dissolved THIS tick, entering election and defection. Expected; disclosed.
- BOUND: per pass and per tick, at most that tick's creations + dissolutions (from typed records in the same run).
RESIDUAL = excess - (A) - (B) must be 0 in EVERY pass of EVERY run. Any residual is a FINDING to the designer, naming what the visit was.
Within their bounds, neither (A) nor (B) goes to the designer. The disclosure line: 'per-pass visits = live at phase start + (A) <n> dirty dissolved ids skipped at the guard + (B) <m> same-tick adds/dissolves; residual 0'.
The implementation note is fine: 5 store walks move to a dict-order-preserving filter; the id allocator, hash and checkpoint readers stay whole-store. Hash-equal acceptance is unchanged and covers the dict-order point.

### rpg-planner on step (a) at a6902557b (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

Hash and count MET, and the timing miss is disclosed. That matches the ruling.
(1) Changed test expectation: OK, with conditions.
- The test's name and docstring say what it now asserts: 'a full-scan tick yields LIVE group ids; dissolved records stay in the store'.
- ADD one test pinning what didn't change: after a dissolve, the record is still in the store, the id allocator's next id is above it, and the state hash and checkpoint include it.
- If that test is cited by a parity-ledger or Bible entry, the entry's evidence line changes with it. Say which.
(2) Wording, AMENDED. Carry this everywhere, including the PR disclosure:
'The group store keeps every dissolved record (43-104 at t2000 on s42). With step (a), the groups and cooperation phases do per-group work for live groups only (per pass: live at phase start + same-tick adds; residual 0). The live filter scans the whole store 3 times per tick (83-154 records/tick at 2000t on s42), and that scan grows with run length. Frontier's groups phase is about 1.0 ms/tick with or without (a), against base's 0.27; where that time goes is not yet shown (attribution runs pending).'
The earlier '(about 1 ms/tick on frontier at 2000t)' is WITHDRAWN as a cost attribution. rpg-planner is amending the DISSOLVED-GROUP-RECORDS ticket's rationale the same way: the visit count is cut, and the cost cause is open.
On the 2 frontier runs: fine. A whole-store step that still costs per tick and grows with the store is the case that matters for 5000t sets. If attribution finds one, it's a FINDING to the designer, and it joins step (a)'s scope only by the designer's ruling.

### rpg-planner on attribution, the runtime seed and the second lander (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

1. Attribution ACCEPTED as no finding: the whole-store sites are about 10-20 us/tick (1-2%), and update_groups per call FALLS as the store grows. The rest is activity plus the formation scan, which grows with contracts per ungrouped entity.
Disclosure line: 'frontier groups phase about 0.98 ms/tick vs base 0.27, with or without (a). Whole-store work is about 1-2% of it. The difference is not yet named; the base profile is pending. The rising item over the run is the formation scan, growing with contracts per ungrouped entity (pre-existing loop shape; see TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE).'
- After the base profile names the difference, the line names it.
- Adding the formation-scan rows to that ticket is fine.
2. YOUR OBJECTION is UPHELD: no seeded fallback for next_group_id in update_groups. A runtime fallback hides a missing counter and can REISSUE ids, which is the very defect the groups-id fix exists to stop.
- Seeding happens ONLY on load, through FIELD_RULES.
- At runtime, next_group_id is a NON-OPTIONAL typed field on AuthoritativeState, so mypy is satisfied by the type, not by a default.
- If it can genuinely be absent at a call site, raise a typed error (an Error-suffixed name, per N818) and add a test that exercises it.
- Re-run the 3 pinned hashes after that change; they must be equal.
3. CheckpointFieldMissingError: F3 makes the same rename in src/engine/checkpoint_fields.py, and both lanes add FIELD_RULES rows. Whichever lands SECOND merges the module. Expect a textual conflict there: keep both sets of rows and the single class name. F3 is likely first (#823, being fixed for code-health and mypy).
4. Changed test: no parity or Bible citation, so no ledger change. Noted.

lead-planner's note, same message: 'non-optional' with a load seed has one catch: the old-shape slot is absent until restore's fill runs, so the fill step must run before any kernel read, and an old-shape test already covers that. Confirm it does.

### rpg-planner rules next_group_id's shape (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

next_group_id is RULED (3) plus your check. Not (1).
The ruling's intent was 'no runtime value that hides a MISSING counter for a state that HAS groups', not 'no initial value ever'. 10000 is the correct counter for an EMPTY store, so it's a fresh-state value, not a cover, provided every state with groups is guarded. (1)'s ~1,560 edits buy nothing beyond that and collide with every open lane.
CONDITIONS:
1. next_group_id: int = 10000 (non-optional), and __post_init__ seeds NOTHING. Restore seeds an absent slot only through FIELD_RULES, as now. The interim update_groups GroupCounterMissingError GOES AWAY, since the field can't be absent; keep a test that the type is int and never None after restore.
2. (i) Every src builder that constructs a state WITH groups passes the counter explicitly. The implementer's list goes in the PR body.
3. (ii) GroupCounterBehindStoreError (typed, Error suffix) is raised at load and in those builders if the counter is not above every non-squad stored id. NOT in __post_init__ or replace. Tests: one that raises, one that passes.
4. Your guard: a check that FAILS when a src construction of AuthoritativeState (or a builder) supplies groups without next_group_id, so the list can't silently go stale. ROUTING: if it lives in tests/architecture/**, that's testing-planner's area and needs its OK through me (u24). Otherwise put it under tests/unit/ as a static scan of src. Either is fine with rpg-planner.
5. Hashes: canonical omits the counter at 10000. Report any pinned hash that moves on a hand-built state, with the test name. The 3 pinned world hashes must stay EQUAL.
6. Retention reissue risk: rpg-planner is writing it into step (b)'s AC on TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK.
- A drop must never lower next_group_id.
- A state that has had records dropped must never be re-seeded from stored ids: FIELD_RULES' max(10000, the highest non-squad id + 1) applies only to pre-counter checkpoints, which predate any drop.
- Test: drop, round-trip, and the next id is above every id ever issued (already in (c)).
Then the 3 pinned hash runs proceed on that head.
If the guard goes in tests/architecture, send me the file and I'll get testing-planner's OK.

lead-planner's note, same message: suggests tests/unit/, to avoid the extra review round. Go for the hash runs stands on that head.

### rpg-planner confirms the restore-only reading (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

A restore-only GroupCounterBehindStoreError (after fill_missing_fields) plus condition 4's guard satisfies conditions 2 and 3, given the AST scan.
- Condition 2 becomes: 'the list is empty today; the guard enforces it for any future builder'. The PR body states the 19-site scan result.
- Condition 3: RESTORE ONLY. NOT in the apply copy: the allocator already steps past every stored id, and an O(store) check per apply isn't wanted.
- The guard (condition 4) must flag any src construction of AuthoritativeState (or replace on it) that supplies groups without next_group_id, with the apply copy and to_readonly excepted BY NAME. Its own test shows it failing on a planted example.
- Tests: run the 72 + 30 hand-built sites and report any that need a counter (ids at or above 10000 reaching restore), with names. No expectation edits without listing them.
- The gap is named: a hand-built runtime state with groups above 10000 and no counter keeps 10000. That's safe while records are kept, since the allocator skips taken ids. rpg-planner is adding to step (b)'s AC on the DISSOLVED ticket: 'a drop must never lower next_group_id, and a state with stored ids at or above the counter is refused at restore (GroupCounterBehindStoreError)'.
Your 3 pinned hash runs can PROCEED on that head.

### rpg-planner on the one test edit (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

The one test edit is OK. It encodes the ruled behaviour (construction doesn't seed) and doesn't loosen a check. Two small conditions:
1. SPLIT it, so each test name says what it asserts.
- Keep test_seed_skips_squads_and_covers_the_highest_non_squad_id for the load-time seed (the three seeded_next_group_id assertions).
- Move the changed line into its own test, e.g. test_construction_does_not_seed_next_group_id, asserting == GROUP_ID_BASE with groups present.
2. Next to it, add ONE assertion that the same state restored from a checkpoint without the counter IS seeded to 10042, or is refused with GroupCounterBehindStoreError if the fill leaves it behind. Whichever the restore path does, PIN it, so the gap is visible in one place.
Otherwise the implementer's results stand: 412 tests, no pinned hash moved, the static scan clean with its planted example failing, and to_readonly the only exemption. The hash runs proceed after the base profile.

### rpg-planner accepts the groups-phase disclosure (via lead-planner-u24 and lead-planner, 2026-11-01, word for word)

It doesn't break the ruling: it states measured counts (live group-ticks, call counts) and says plainly that the rise wasn't apportioned. That's a disclosed correlation, not a named cause. Use it as written, plus this clause after '(about 7,340 vs 1,600)': '; base's figure is approximate, as its id overwrites can merge group lifetimes'. The TOTAL line stays 'the rest is not attributed'. Don't carry 'longer-lived groups' into the total.

The accepted line, with that clause: "frontier groups phase about 0.98 ms/tick vs base 0.27, with or without (a). Whole-store work is about 1-2% of it. The fix has about 4.6x the live group-ticks over the run (about 7,340 vs 1,600; base's figure is approximate, as its id overwrites can merge group lifetimes), and more replace and merge calls in the phase (late window 18,281 vs 1,537 replace calls); the rise fits per-live-group work, but it was not apportioned by function. The rising item over the run is the formation scan, growing with contracts per ungrouped entity (pre-existing loop shape; see TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE)."

### rpg-planner on the STOP at frontier s43 entity 12 (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed)

YES to the trace pair (frontier s43, entities 12 and 6, t1360-1433). It's one of the 6 pre-approved pairs on your existing go, with no new owner ask, and the slot is yours until `urban_political` ends.
Conditions:
(1) The verdict is FED / NOT FED / NOT SHOWN, never PASS/FAIL. FED means a causal step in the 50t window is behaviour the fix changed: the BINDING_HOLDER_LEFT end, 10088 forming one tick after 10085 FULFILLED, or a lodged-member group decision. Name the killer and say whether it was visible and targetable.
(2) If FED: STOP, don't run `urban_political`, and report to rpg-planner. If NOT FED or NOT SHOWN: finish `urban_political` on the same go.
(3) In the same trace, say whether e12's leave at t1392 or the 10088 holder binding put e12 on the tile or route where it died, compared with base at the same ticks.
(4) The lodged-at-group-decision rise (s43 0->70, s44 0->738, s45 0->1192) is a new behaviour signal and must be explained before close, whatever the trace says. From existing rows only, no extra run, split those decisions by whether the member's goal or location changed within 10t. It goes in the close report beside s43 DEFEAT 3->10.
rpg-designer reads the verdict before any close ruling. Send your verdict to me; I'll relay it.

### rpg-planner on NOT SHOWN for entity 12 and the extra runs (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed, cc rpg-designer)

`urban_political` proceeds, and yes to both the entity 30 trace and the 3 extra runs. You have my slot go for both, one at a time, after urban and before B.
(1) e12: NOT SHOWN is accepted as the working verdict, but NOT SHOWN cannot close a STOP victim. So YES to the e30 trace from the pair allowance: target_score and candidate list for e12 and e30, t1395-1401. A role-gated branch firing (`tactical.py:351`/`:372`) means FED. A range entry, with the role-free path picking the same target, means NOT FED. rpg-designer rules the final verdict.
(2) Point 4: YES to the scope change. 3 arm runs, frontier s43/s44/s45, 2000t, audit, hash-neutral; confirm the hash equals the unprobed arm run. One row per lodged member at each group decision: entity, group, decision kind, and goal plus location at t and t+10.
(3) In the same 3 runs, for s43 DEFEAT 3->10, add one row per DEFEAT death: in a group within 50t (id, role), lodged or left bed within 50t, and killer id. No extra slot time.
rpg-designer's ruling is needed before any close of the groups ticket. Send the results and the memory figures to me before B. Your report on (1) decides whether B runs at all, so I'd expect FED to stop there rather than go on to B; confirm with rpg-planner's wording if it's unclear.

### rpg-planner on the second STOP and Tier 2 traces (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed, cc rpg-designer)

B stays held, and the traces and extra run below have my slot go, one at a time.
1. YES, e23 goes in the same test as e12. One trace pair: urban s42, e23 and e24, t1630-1687, with role-branch (`tactical.py:351`/`:372`) and target_score rows. ADD to both e12 and e23: for each lodging LEAVE, the writer and reason. The ~10-tick enter/leave flap in both cases is what needs explaining. A leave caused by a group/recruit decision the fix changed counts as FED, the same as a role-gated pick.
2. The second STOP doesn't change the running jobs: the e30 trace and the 3 frontier probe runs finish as they are. ADD ONE probe run, urban s42, with the same hash-neutral rows (one per lodged member at each group decision, plus per-death group/lodge rows). Run it after the frontier three, one at a time.
3. YES to the Tier 2 proposal: crowded s43, frontier s45 and urban s44, reusing the urban s42 and frontier s43 pairs. With e23 that is 6 of 6, and the allowance closes at 6. A 7th needs a fresh ask through rpg-planner. Order: e30 (running) -> e23 -> urban s42 probe -> crowded s43 -> frontier s45 -> urban s44.
B stays held until rpg-designer rules on both STOP victims and the Tier 2 set. If memory drops under 3 GB available, pause between jobs, not mid-run.
Send results to me for relay.

### rpg-designer's ruling criteria for groups C (via rpg-planner, lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed; criteria, not a ruling yet)

1. FED = the fix's own changed behaviour selected the walk or the target within the 50t window, acting on the victim OR the killer. Changed behaviour means one of: a Shape-A formation/end with a typed reason, holder binding, a leadership stamp, a role-gated target branch (`tactical.py:351`/`:372`), or group_bias in target_score (`tactical.py:428`).
- So trace rows must cover the KILLER too (e30 for e12; e23's killer) and include target_score's group_bias term.
- A lodging leave is FED only if its writer or reason traces to one of those decisions.
- A plain REST end or wake is F3 lodging churn and NOT fed. Log it as a re-lodge churn row for N14.
2. Surviving past the base death is trajectory, not FED by itself.
3. The lodged-at-decision probe runs (frontier s43/44/45, urban s42) need these fields per row: phase; decider (the lodged member itself, or another member); decision kind (formation / election / target / end); two flags, CHOSEN as leader and BOUND as holder. Report counts split by kind and by those flags.
- A lodged stayer that is chosen as leader or bound as holder is a lodger making a social choice indoors: a candidate F3×churn defect, independent of the victims. That split decides STOP or row.
- If the frontier runs already started without the decider/kind/flag fields, say whether those can be derived from what is logged. If not, the urban s42 run carries the full field set, and rpg-planner decides whether one frontier run repeats.
4. Tier 2 outcomes: FED -> STOP to rpg-planner; NOT FED -> divergence row; NOT SHOWN -> rows to rpg-designer. The allowance closes at 6.

### rpg-designer clears STOP victim 1 (via rpg-planner, lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed)

rpg-designer rules frontier s43 e12 NOT FED. The s43 seam check is clean: group 10088 formed 5t after the leave, so e12 was not lodged when chosen. STOP victim 1 is CLEARED.
- The e30 cluster (s43 DEFEAT 3->10) is report-only, since frontier's 5-seed DEFEAT fell 35->31. No slot. It goes in batch C's close disclosure as "per-seed cluster, untraced", with evidence on ENGAGE-BRACKETING.
- e12's leave/re-claim cadence goes as an F3 churn row on N14. Both are filed on rpg-planner's local seat branch.
Still open: victim 2 (e23) and the s44/s45 lodged splits. B stays held.

### rpg-designer on the lodged-leader formations (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed, cc rpg-planner)

The frontier s44 lodged-leader formations are a ROW, not a STOP. The queue keeps running; s45 and urban s42 carry on as planned.
WHY A ROW: no victim; no walk or target selected; hash-neutral; the gap is on both trees (designer confirmed: `domains/cooperation/services.py:280` builds cnt_recruit_{src}_{partner}_{tick} with no lodging check). The churn fix only makes groups last long enough to show it. Batch C's disclosure counts it as a row: 3 formations, 328 rows with a lodged leader.
SEMANTIC RULING: may a lodger take a social decision? NO, for NEW decisions. F3 ruled that a lodged stayer emits no intent, but the suppression sits at only two entries (fused_strategic_pass, cognition.evaluate_entity_intent). Cooperation is a third decision path F3 missed, so this is an F3 seam defect (2.155), not a group defect. Rule:
(1) A lodged stayer makes no new social decision: no offer, accept or counter of a contract, no help request. Same suppression as F3 class (a); time, needs and wake still run.
(2) Standing membership persists: a member that goes to bed stays a member, and its group keeps its contract and holder.
(3) Formation needs an accepted contract, so lodger-led formations fall to about 0. Election doesn't pick a lodged member while a non-lodged one is eligible; if every member is lodged, the current leader stays.
NEXT:
- The code read goes now (no slot). It lists EVERY path that can emit a decision or record for a lodged stayer outside F3's two suppressed entries (cooperation offer/accept, contract accept/counter, formation, election, trade, quest, social, other), each with a lodging answer. That list is the scope of a new P2 ticket on the F3 seam, which rpg-planner files. Suggested id: TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS.
- Ticket acceptance: lodged contract creations and acceptances = 0; lodged-leader formations about 0; membership persists through lodging (test); hash-identical where there are no lodgers; deaths paired under the bar.
- For the probe rows: record the lodging state of BOTH offerer and target at contract creation and at acceptance, to show whether offers, accepts or both leak.
It does not gate batch C. Send the list to me for relay.

### rpg-designer adds rule (4) on lodged leaders (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed, cc rpg-planner)

The code read is ACCEPTED and the ROW confirmed. CooperationPhase is a third path; it doesn't leak through F3's two entries.
- Base probe: NOT needed. Cite base reachability as "by code, unmeasured".
- Mechanism: the distance-10 check. Lodgers share the building tile, so formation sees them as side by side. The fix reads lodging; it doesn't adjust distance.
New rule (4): while a leader is lodged, it is ABSENT for following and regrouping. Followers outside don't take its building tile as a follow or REGROUP target; they act on their own until it leaves. An election in that time picks a non-lodged member. Otherwise followers walk to the inn door to regroup with a sleeper and rebuild the door jam F3 removed.
ASK for the s45 and urban s42 rows: count outside-follower ticks whose follow or REGROUP target is a lodged leader's building tile or reach tile. Above 0 means (4) is needed now; 0 means it goes into the ticket as a guard with a test only.
The ticket is filed by rpg-planner under lane F3 (2.155). Scope: rules (1)-(4); cooperation offer/accept, formation, election, follow/regroup. Evidence: the code read plus the s44/s45/urban s42 rows. Acceptance adds: outside follow targets on a lodged leader = 0.
If s45 has already started or finished without that count, say whether it can be derived; a repeat would be a new ask. Send the counts to me for relay.

### rpg-designer clears STOP victim 2 and sharpens FED (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed)

e23 (urban s42) = NOT FED. Both STOP victims are now CLEARED; B is held only for the 3 Tier 2 pairs.
New precise FED criterion, replacing ":351/:372" alone. A role-gated or group branch is FED only if it (i) changes the victim's or the killer's target, (ii) moves the victim into first contact with, or into range of, an attacker it wasn't already engaged with, or (iii) moves it into a hazard or onto a walk that leads to a new exposure. A reposition inside an engagement already chosen on a NOT FED pick, against the same target and the same attacker, is fight participation: NOT FED. The fix keeping a group alive makes a branch reachable; reachability is trajectory. Tier 2 marks the BRACKETING branch under the same (i)-(iii) test.
ENGAGE-BRACKETING evidence (a finding, not a fix cause): "urban s42 churn-on-F3 e23: VANGUARD BRACKETING (tactical.py:542/:552) repositions a hp-32 vanguard around its target while hit 4 times; killed t1687; NOT FED (participation)". The branch reads role, not own hp.
Rule (4): by the designer's definition (a follow/REGROUP TARGET on a lodged leader) the urban s42 count is 0, so it's a GUARD with a test, not "needed now". The 193 co-presence ticks can't separate following from walking to the same inn to rest.
Contracts: offers and accepts leak; FULFILLED with a lodged party is the term running out, allowed under (c). Ticket 1's acceptance: CREATED and OFFERED->ACTIVE with a lodged party = 0.
When the Tier 2 pairs finish, send me the results and memory and swap figures before anything on B.

### rpg-designer and rpg-planner on e23 item 1 (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed)

e23 item 1 is CLOSED, NOT FED. All 6 hits are e17's. e17 was at distance 1 at the first BRACKETING decision (state tick 1669), and that's what the test reads, so the exact t1668 distance isn't needed. The hostile list is [17] alone, so (i) and (ii) aren't met.
Only (iii) is open, via the running probe: [41,31] against [41,30] at t1679/1681, (A) free exit or (B) a group-member blocker on a group-branch tile.
PRE-CHECK FIRST (rpg-planner): is AVOID_NO_ROUTE a route_search failure to a far avoid target (give the avoid target and refusal reason), or were all neighbours blocked? If it's a far-target failure with a free neighbour, the box isn't the mechanism: the verdict rests on (B), and the no-route goes to the nav family.
B stays held on this and the 3 Tier 2 pairs. rpg-planner has no further asks on e23.

### rpg-designer recasts test (A) for e23 (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed)

Your correction is accepted and its one-tile-block inference withdrawn. (A) is recast as you proposed.
- STRICT (A), FED (iii): with e17's ACTUAL position at the same tick (t1679 and t1681), `retreat_destination` returns non-None from [41,31] and None from [41,30]. That means the group-role bracket step decided at t1677 moved e23 from a tile where flight was possible to a cornered one: a new exposure, STOP to rpg-planner.
- None from both tiles, or non-None from both: NOT FED. The bracket step didn't change whether e23 could flee.
- Not computable: NOT SHOWN, disclosed; on its own it doesn't hold B.
- (B) CONFIRMED NOT MET.
- Also in the probe: what moved e23 at t1680 and t1681 (writer and reason). If [41,31] at t1680 gave a destination but something else moved e23 back, name that writer. A group writer is (B)-like, FED; a combat push or other non-group writer is NOT FED.
LOW-HP-RETREAT findings, whatever the verdict (rpg-planner records them): (1) a cornered low-hp subject with no home_region holds still under an adjacent attacker and dies (e23: 6 hits, hp 32 at t1681), the same fallback gap as e9's "why no town_center"; (2) AVOID_NO_ROUTE means "no destination", so a rename row (NO_RETREAT_DESTINATION) goes on that ticket as a cheap separate fix.

### rpg-designer rules crowded s43 e10 FED (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed)

crowded s43 e10 = FED under (i). The tuples in code order show group_bias deciding (30 at 0.1 vs 27 at 1.0); the designer is not rewriting the test after the result.
- An OWNER ROW goes to the owner IN ANY CASE, because landing would ship a known fix-fed death. A second same-shape victim, or all-cause deaths up at the bar, only flip the designer's lean from (b) to (a):
 (a) hold churn behind a self-defence rider, "a hostile attacking you outranks the group's shared target";
 (b) DESIGNER'S LEAN: land churn with disclosure, with the rider ordered next as a P1 ENGAGE-BRACKETING child.
- lead-planner-u24 carries the row. The designer fills it once these land, so please send them to me: e27's positions t888-893 (ii); v34 plus the same-shape count across the 3 pairs; all-cause deaths in the 3 Tier 2 pairs vs base; e23's `retreat_destination` probe. Your base and v9 answers are already relayed.
- If base has the same group, target and pick at t894, the designer re-rules before the row goes; your rows say it doesn't.
B stays held until the owner answers. Please also still send the raw 7-field tuples and the trust value, since the designer's reading rests on relayed tuples.

### rpg-designer on the flip and e22 (via lead-planner-u24 and lead-planner, 2026-11-01, word for word as relayed)

The flip counts the NARROW shape only, so the count is 1 (e10). Option (a) holds behind a rider that wouldn't save a different-shape death.
e22 (frontier s45) = FED by the letter of (i), with its limit disclosed (11 and 5 both at distance 12, positions unknown). Its killers weren't the bias target, so the rider wouldn't have saved it.
The row presents 2 fix-fed deaths (1 of the rider's shape, 1 other). All-cause is down at 5 seeds, so lean (b) holds.
e22 is the second low-hp VANGUARD BRACKETING into a fight (hp 35; e23 was hp 32), so rpg-planner files a second ENGAGE-BRACKETING child: "a VANGUARD below a hp line does not take role-gated moves (BRACKETING) into contact", counts first.
ONE ASK for the row: e22's fate on base (when and how it dies there, from existing rows). Still pending as well: e27 t888-893 and e23's retreat probe.

### Owner's answer on the row: #715 6560083151 (via lead-planner-u24 and lead-planner, 2026-11-01)

"(b) Land now, disclose". Churn lands with both fix-fed deaths disclosed (e10 crowded s43; e22 frontier s45, by the letter). The rider (TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET, P1) is ordered next, measured on top of churn; then TCK-20261101-A-LOW-HP-VANGUARD-TAKES-ROLE-GATED-MOVES-INTO-CONTACT (P2, counts first). The comment also records e23 NOT FED and e10's trust of 0.8. This does NOT approve the push or merge, which stay as a separate ask.
lead-planner's terms for B: slot go; message lead the moment the timing set actually starts, don't start until it confirms the hold; record memory and swap activity across the set; implementer runs nothing else during the set on any core; B's numbers replace the pre-F3 ones; frontier stays UNRESOLVED unless B shows otherwise; after B the push ask goes to lead with the disclosure text.

### Churn close disclosure list (rpg-planner via lead-planner-u24 and lead-planner, from rpg-designer's ruling under owner (b) #715 6560083151, 2026-11-01, word for word)

The churn ticket's close disclosures must carry:
1. crowded s43 e10: FED by (i), pre-existing focus-fire group_bias. The rider is not shown to save it (bias held t894-897 only; e10 picked 27 from t901 and died anyway).
2. frontier s45 e22: FED by the letter only (the walk into range was its own congestion redirect; it dies on base too, t1029).
3. v17 and v24: NOT SHOWN.
4. Per-seed rises with totals down: frontier s43 21->35, urban s42 8->10.
5. The e30 kill cluster (frontier s43, 4 group members, untraced; ENGAGE-BRACKETING evidence).
6. The lodged-leader seam (2.155) -> TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS (+ audit TCK-20261101-A-LODGER-DECISION-PATH-AUDIT).
7. FULFILLED with a lodged party = term expiry (exception (c)).
8. The 2.146 rewrite as already agreed.
9. Rider ids: TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (P1, next, measured on top of churn) and TCK-20261101-A-LOW-HP-VANGUARD-TAKES-ROLE-GATED-MOVES-INTO-CONTACT (P2, counts first).
e12 and e23 are final NOT FED, and v9 NOT FED.
The rider and lodger ticket files are on rpg-planner's local seat branch rpg-planner-seat-3, not on main yet: cite them by id.

rpg-planner's amendment to item 1 of the list above (via lead-planner-u24 and lead-planner, 2026-11-01): use "t898 (traced pick; target rows from t901)", since the traced call is the primary row.
