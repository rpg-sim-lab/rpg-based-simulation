---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP
artifact_type: report
date: 2026-10-31
tags: []
---

# Fix-shape ruling, group ids

From rpg-designer, agreed by rpg-planner (u24), relayed by lead-planner-u24 and lead-planner, 2026-10-31. Scope and acceptance under rpg-planner's dispatch; original acceptance items stand where this does not replace them. Word for word:

"OPTION A with four additions. Why A: B and C are correct only while 'nothing removes records', a hidden assumption the durable-state rule forbids.
1. The counter: state.next_group_id starts at 10000 and only rises. Only the apply path advances it, as part of the typed group-add update; decision code only reads it. It goes in the canonical dict and round-trips, with an architecture test.
2. Skip taken ids: the allocator steps past any id already in the group store, whether a live group or a squad hash. It's deterministic, one lookup per allocation. This drops the disclosure that a formation id could equal a squad hash.
3. No silent overwrite at apply_plan.py:124. Overwriting is allowed only for a deliberate in-place update of the same group. An add over a different live group becomes a TYPED REJECTION: counted and surfaced, never a replace. That also covers a squad hash landing on a formation id; if one ever shows, its own ticket fixes the squad side. Squad id generation stays as it is.
4. Older saved states: on load, if next_group_id is absent, seed it with max(10000, highest non-squad id + 1). Squads are recognised by FACTION_SQUAD for this one-time seed only. That closes the 'no saved state needs migrating' assumption without a migration.

Counts (reported, not gated):
- On base (at or after 6fdfdf555; the same 15-run set if your slot allows): the number of overwrites today and the ghost members they leave (entities whose group_id points at a group that doesn't list them).
- After the fix, both are 0, and an end-of-run check passes: every living entity's group_id resolves to a group that lists it.
- The hash moves, attributed: the first diff is the first allocation the old formula would have collided on or inflated.
Then COGNITION (entity 6 / group 10009) is re-measured on this fix together with the retention fix, before the s42 re-anchor."

lead-planner's notes, same message: TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT is dispatched on u24 lane C (owner go #715 6543058711). The re-measure needs both fixes on one tree; tell lead-planner when this fix is near so the leads can order the merges. Check u24's open branches before touching shared files; that fix may touch state too. The 15-run base count needs a plan, wall estimate and stop time for lead-planner's go. The expiry re-date stays in this PR, on main before 11-15.

---

## rpg-planner's follow-up ruling (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Binding, word for word:

"1. The set: YES, the retention trace's set (crowded_frontier, frontier_living_world, urban_political × s42-46, 2000t, at or after 6fdfdf555). Counts are reported, not gated, and 2000t matches the s42 re-anchor horizon. Keep the slot go as given.

2. Omitting next_group_id while it is 10000: ACCEPTED, with one condition. Omission is safe only if load reproduces the value. When the field is absent, the load seed is max(10000, highest non-squad id + 1), which gives 10000 only when no non-squad group sits at an id of 10000 or above.
- The architecture round-trip test must cover three cases: no groups; squad-only groups; and formed groups with the counter above 10000. Each must satisfy load(dump(s)).next_group_id == s.next_group_id.
- Show that every producer of a non-squad group advances the counter: the merge paths in updates.py and pipeline_phases/groups.py, plus any world-gen or content-seeded groups.
- If any path creates a non-squad group without advancing the counter, always serialise the field instead. That moves the hash at t0, which is fine as long as it's stated.

3. Rejecting an add over ANY existing id, dissolved records included: ACCEPTED. A dissolved record is kept history, so overwriting it is also silent loss. Agreed with your ask:
- show by test that an in-place update of the same group, and a dissolve (both through groups_add_or_update), are NOT rejected;
- confirm that nothing legitimately re-forms a group at its dissolved id.

4. Agreed and binding: a rejected add is atomic. No member's group_id is written for it, and the rejection is counted and surfaced. Fix it or prove it, with a test that a rejected add leaves every member's group_id unchanged."

lead-planner's note, same message: lane C (TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT) was dispatched, investigation first, no branch or plan yet (suggested name rpg-retreat-completes); its likely surface is the project lifecycle in intelligence.py and it is asked to keep clear of apply_plan.py:124's group path.

---

## rpg-planner's rulings on fixture regeneration and store growth (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"RULING 1, fixture regeneration (corpus.py:91): AGREED as an intentional change of extract()'s input, but NOT on the t161 link alone. The one-tick question is NOT required: base keeps the overwritten record one tick longer because base's store is the corrupted one, and explaining base's defect isn't this PR's job.
REQUIRED before regenerating:
(a) A mechanical check over all 295 moved (call, config) rows: in each config, no row differs before that config's first old-formula collision or inflated allocation. That is an ordering proof, not 295 individual traces. Any row that differs EARLIER is a finding, and the regeneration waits.
(b) rpg-planner-ubuntu re-runs the second-hash-seed identity once itself; the implementer's report alone isn't enough.
(c) Store sizes at t199 per tree, in the PR body.
With (a)-(c) in, regenerate, citing this ruling and the first-collision tick per config.

RULING 2, store growth: a SEPARATE churn ticket is AGREED. rpg-planner-ubuntu may file it, counts first, with rpg-designer to rule. A retention or bound rule for dissolved records is a lifecycle rule for the designer, not for this PR.
But the PR is HELD if the cost is material. On the 3 extra base runs (s42 per world, 2000t), base vs branch, report:
- store size (total and dissolved) at t500, t1000 and t2000;
- wall time per tick for the groups phase and the cooperation phase, and total tick time.
'Material' means total tick time up more than 5% in any of the three worlds, or the store passing 2000 records by 2000t. Either one holds the PR until the churn ticket lands a bound.
Record the churn itself (the (37,38) pair forming and being expelled about every 2 ticks on BOTH trees) as a behaviour finding in the churn ticket.
Live vs dissolved split: the 3 extra runs are enough; it's not needed on all 15."

lead-planner's note, same message, on the 5% test (raised with rpg-planner, unanswered at recording): one run per tree can't resolve 5% on this VM (perf's noise rule here is 15%). Plan base and branch runs alternating, same CPUs, nothing else on 4-5, at least 3 per tree per world if possible, spread reported. A difference inside the spread is reported as unresolved, not as a pass. Store size is deterministic and needs one run. The run list, wall estimate and stop time need lead-planner's go; the existing 3-run go doesn't cover branch runs or repeats.

---

## rpg-planner on Ruling 2, the timing test (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"Your alternating plan is CONFIRMED: at least 3 runs per tree per world, alternating, with the spread reported.
An unresolved total-tick-time result means (b), not a hold:
- The deterministic store-size limit decides: more than 2000 records by 2000t on any world HOLDS the PR.
- Report the per-phase timings (groups and cooperation) with their spread. They hold the PR only if the branch's median sits outside base's spread by more than 5% of base's median TOTAL tick time.
- Add one deterministic work count that load can't move: the records sorted and walked per tick by those two phases, summed over 2000t, base vs branch. It is reported, not gated, and it shows whether a hidden cost is growing, so the churn ticket can cite it.
A resolved total-time rise above 5% still holds the PR, as ruled."

lead-planner's note, same message: the 18 runs need a run list, wall estimate and stop time for its go, probably with the fix code final first. Runs not finished by 22:00 wait for the next day's slot.

---

## rpg-planner on the code review of d336e43b5 (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"The regeneration release under Ruling 1 stands: (a) and (b) are done, and (c) goes in the PR body. rpg-planner agrees with all three review findings on d336e43b5:
1. The counter seed runs ONLY on load and only when the field is absent, exactly as ruled. A seed on every construction is a hidden recomputation of durable state, and the jump to 2000000000 shows the danger. Add a test: a constructed state with a counter value keeps that value even if the squad roles change.
2. Atomic rejection is binding (item 4): no member's group_id write survives a rejected add, including members also listed in the holder. Test it with exactly that overlap.
3. Election after a rejection: FIX it rather than proving it unreachable. The rejected record must not enter groups_being_updated, so the fix plus a test is the cheapest proof. A reachability proof would have to cover the squad hash space and every upsert path.
Base count: noted. 2496 loose and 388 strict overwrites, with ghosts in every world and seed, make this fix clearly material. Please confirm whether the 247 ghosts are distinct entities or entity-tick rows before the PR body quotes them. Divergence 2.146 is fine (ubuntu block). The 18 timing runs plus (b) re-done on the fixed commit are agreed."

lead-planner's note, same message: item 3 changes "fix or prove" to fix only. The fixed src may also move the fixture, so check whether the regeneration still matches before the 18 runs. The go for the 18 stands on the new SHA; tell lead-planner the SHA at start and it holds agent-working-implementer then.

---

## rpg-planner on the same-tick winner exception (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"Your reading is right and meets item 4. A member that the same-tick WINNER of that id also lists keeps its group_id, because that write belongs to the winning add; the rejected add contributes nothing.
Please make sure one test pins both sides in a single tick:
(a) a member listed in both the winner and the rejected add ends with the winner's id;
(b) a member listed only in the rejected add keeps its prior group_id, whether None or its old group.
Noted on the 3-run split: 33 live against 366 dissolved overwrites, and every live one is a disjoint-member overwrite, the damaging kind. The PR body can quote it as a 3-run sample, not as the 15-run split. Timing carries on."

lead-planner's note, same message: a test-only addition doesn't change src, so timing and (b) stand.

---

## rpg-planner on the hold (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"1. PROFILE FIRST: agreed. The PR holds under Ruling 2. Use the 2 profiled runs (frontier_living_world s42, one per tree). On the same runs, also count:
(a) formations by entities that were ghosts at some tick on base;
(b) of the branch's extra formations, how many are the same member set re-forming within 10 ticks (churn), against new distinct groups.
That tests the untraced 'ghosts suppressed churn' reading directly.
2. YES, this is a behaviour change, and it needs rpg-designer's reading. rpg-planner has sent the designer the numbers with the question: accept the post-fix behaviour as 'the bug no longer suppresses formation', with the churn visible and owned by its own ticket, or require the churn fix to land with or before the id fix. No ruling yet; it will be relayed. Either way, divergence 2.146's Disclosed text must state the formation rise per world.
3. Raise TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS to P1: it now blocks the s42 re-anchor chain. Its owner go comes after the profile and the designer's reading, so its fix shape (dissolved-record skip, retention bound or churn rule) is picked with the cost known.
fyi: lane C's retention fix is measured on main without the group fix, and the s42 re-anchor takes both. Lane C's numbers don't need the group fix; the re-anchor re-runs on one tree carrying both."

---

## rpg-designer on batching and counts (agreed by rpg-planner, u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"The id fix is CORRECT. The churn is a pre-existing defect it makes visible, owned by TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS, now P1.
The id fix does NOT land alone. It lands WITH the churn fix, in the same batch, with the churn fix first or together. A 5.6x jump in group behaviour and +35.6% frontier tick time are real signals. Both tickets gate the s42 re-anchor anyway.
COUNTS FIRST, before any churn fix shape. s42, the 3 worlds, the same reps; fold them into the 2 profiled runs where possible.
1. CONFIRM the suppression reading. On base, per tick, count the entities excluded from the formation pool because they hold a ghost group_id. Does that pool difference explain the formation gap? If not, the rise has another cause, and it goes to the designer.
2. The churn split: formations that re-form the SAME membership within 10 or 50 ticks of that membership dissolving, against genuinely new memberships. Then, for each churned group, the dissolve or leave reason: the code path and condition that ends a group 2 ticks after it forms (cohesion, distance, goal mismatch, a leader with no project?).
3. The profile: where frontier's 73 s goes, against a work count up 23.7x. Is it formation and dissolution itself, or downstream (party coordination, leadership influence over more groups)? Name the untimed phase, since only 1.7 s falls in the timed ones.
The designer's lean, to shape the probe: a group that forms should not dissolve without a typed end reason that has changed since it formed. Re-forming identical membership on unchanged conditions is the defect.
Divergence 2.146: rewrite the disclosure to state the formation rise, the suppression mechanism (once count 1 confirms it), and that the churn fix pairs with it.
The churn ticket's owner go is asked after counts 1-3, with the designer's fix shape."

lead-planner's note, same message: the 2-run go covers frontier_living_world only. The other two worlds' counts, without a profiler and one run per tree, are a further ask. If wrapper changes push the start past 21:20, start the next day; do not rush the instrument. The expiry re-date cannot wait on this batch; lead-planner is asking the owner for it to go its own way.

---

## rpg-planner on the final measurement and tomorrow's runs (u24, 2026-10-31; relayed by lead-planner-u24 and lead-planner). Word for word:

"No non-audit pair now. The designer already requires the churn fix in the same batch, so today's hold decides nothing.
For the batch's FINAL measurement, the hold rule (5% tick time, or the store above 2000) is judged on a NON-AUDIT run at the default replay_richness (FULL), since that's what a normal run pays. Report the audit-mode figure beside it, and state which policy each run used.
Tomorrow's 6 runs (3 worlds, one per tree, no profiler, per-entity size by field at t500/1000/2000, the contract-invalid split, and the hash check) are agreed as the input to the designer's fix shape. Two additions, if cheap:
(a) split contract-invalid into missing / not ACTIVE / expired. That tests the implementer's expiry hypothesis at groups.py:305-326 against :160-170 directly.
(b) per entity, which fields grew: strategic.contracts length, trust/grudge entries, memory. The canonical dict being about 50% larger is the cost carrier, so naming the field decides whether the fix is the churn rule alone or also what a dissolved group's contract leaves behind."

lead-planner's note, same message: for the final measurement the alternating 3-per-tree terms still apply, and non-audit runs have a governor, so check whether it changes policy mid-run and report that; a run that drops out of FULL isn't the rule's run.

---

## rpg-designer on the churn trace (u24, 2026-11-01; relayed by lead-planner-u24 and lead-planner). On TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS. Word for word:

"Take the ONE trace (entities 19 and 33, crowded_frontier from t100) before the designer rules. The designer won't rule the shape on the unknown.
SETTLED by the counts:
- Expiry is out.
- The churn is a 1-tick group.
- ACTIVE at formation -> missing one tick later -> ACTIVE again is NOT a changed typed reason. Designer's lean holds: a group does not dissolve without a changed typed reason. So a not-found while the contract still exists is a defect, whatever the trace shows.
HYPOTHESIS for the trace to confirm or kill:
- The groups.py:166 lookup is keyed on something a new group id changes (the contract records the old group id while the group carries a new id from next_group_id), OR
- the formation and dissolution reads see different state (post-apply snapshot vs pre-apply view, or leader vs member).
THE TRACE MUST RECORD, per tick t100 to ~t110, for 19 and 33:
1. The leader's contract set: id, status, expiry, and the group id or key each contract references.
2. The formed group: its id, how the id was issued (counter, reuse or skip), and its members.
3. At groups.py:166: the exact lookup key, the state object read (which snapshot), and the result.
4. Every write or removal of the contract between formation and dissolution: writer, tick and phase.
5. The same for one contract reused up to 50 times. Does reuse mean one ACTIVE contract backing a series of new 1-tick groups?
ALSO REPORT (not gating): strategic.blockers per living rose in 2 of 3 worlds (63->132, 27->58). If each 1-tick group leaves a blocker behind, that's churn residue, and the fix must not leave it standing.
AFTER THE TRACE:
- If it's a key or snapshot mismatch, the fix is the lookup, plus a law test: no dissolution without a changed typed reason.
- If the contract really leaves and comes back, the writer that removes it goes to the designer before any fix.
Unchanged: the id fix lands WITH the churn fix, and the 2.146 rewrite waits for the shape."

lead-planner's note, same message: the note's "two ticks later" is corrected on their side to re-formed at t+2. Trace item 5 may run longer than t110; the go covers that, as a short run.

## rpg-designer's addendum to the churn trace (u24, 2026-11-01; same relay). Word for word:

"The trace stays as specified, with one addition.
ADD TO ITEM 3:
- At the t+1 dissolution check, list every pending update for the leader that the check folds in: its kind, its writer, and whether it removes, replaces or moves the contract. For example, does the formation's own update consume the contract, or hand it to the group?
- Show the same for the t+2 formation read: what it saw, and why the contract is back.
LAW IN ADVANCE, whatever the trace shows: formation and dissolution judge a group's contract on ONE state basis. A group formed against state S cannot be dissolved by a view that differs from S only by that same formation's own pending updates. Together with 'no dissolution without a changed typed reason', the shape follows from which read is off. The trace decides whether the fix is the lookup basis or a contract writer. Everything else is unchanged."
