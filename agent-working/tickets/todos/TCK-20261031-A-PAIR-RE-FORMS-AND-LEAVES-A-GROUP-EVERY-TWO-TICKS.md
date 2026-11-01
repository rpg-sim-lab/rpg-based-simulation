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
