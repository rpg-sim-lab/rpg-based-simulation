---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-01
tags: [cooperation, social]
---

# PR notes (draft, for rpg-planner's review; the PR body is rendered by tools/delivery/pr_render.py from the tickets, these are the notes to carry into it)

Branch `rpg-ubuntu-group-id-alloc-impl`. One batch, two tickets: TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP (group ids) and TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (the contract binding). Divergence 2.146 and parity SOC-278 / SOC-279 cover both. Findings that travel in `todos/` and are not worked here: TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK, TCK-20261101-A-PAIR-HOLDS-MANY-ACTIVE-RECRUIT-CONTRACTS-AT-ONCE, TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION; filed by rpg-planner: TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK.

## Method line (every measurement)
Timing: non-audit, pinned FULL (PinnedNormalGovernor), ConcurrentExecutionAdapter. Production on this host is not measured; the only evidence on that is the default-governor smoke (frontier_living_world s42 base, 600 ticks: FULL 66, MINIMAL 281, OFF 253). No comparison with run18's +35.6% (audit, 6fdfdf555 vs edb638b6a: a different mode and base). Audit figures are context from different single runs. Death, group and lag figures are audit_mode, `PYTHONHASHSEED=0`, cores 4-5. Figures may change if the measurement is re-run on F3.

## What the batch changes
- Group ids come from a typed, only-rising counter; an add never replaces a record (apply rejects it, counted).
- A group formed by a contract is bound to it and to its holder (`contract_holder_id`); a leadership change cannot dissolve it; every end of a bound group carries a typed reason in a fixed precedence; the election cadence starts at formation; one shared liveness predicate; formation binds the latest-expiring live contract (-1 ranks latest; "qualified a partner" = passed the live / alive / ungrouped / not forming / within-10-tiles checks); a bound group is relevant on the tick its contract is due.
- Old checkpoints: one post-unpickle step in `src/engine/checkpoint_fields.py` (table `FIELD_RULES`, `CheckpointFieldMissingError`, a 400 on the restore route). Slotted dataclasses unpickle positionally, so `next_group_id` is the last field of `AuthoritativeState` and the new `GroupRecord` fields come after `_canonical_cache`; the guard is `tests/unit/core/test_pickled_record_field_order.py`. `GroupRecord` moved to `src/core/group_record.py` and is re-exported by `src.core.state` (an old-path pickle test).
- `checkpoint_fields.py`: F3 landed it first; this batch's rows are added to F3's table (FIELD_RULES list, F3's FieldRule shape). Restore order: spec check before fill_missing_fields (F3's order inverted; found by test_restore_raises_on_spec_id_mismatch with the group FIELD_RULES rows).
- Code-health: extraction commit eb5f79e94 is behaviour-preserving (state hashes of 400-tick s42 runs identical before and after on three worlds); `codebase.health check` gives 0 worse.
- Existing tests changed: 4 hand-built groups in `test_domain_7_social.py` and `test_social_phase7.py` gain `contract_holder_id`; two kernel pins regenerated (the lifecycle pin of the event-extractor characterization: id fix moved 295 rows from call 59, the binding 297 rows from call 101, none before 100).

## Notes owed
- N14 / F3 ordering (rpg-planner's note): groups that now last feed REGROUP targets, which ties to F3's lodger suppression and to N14. If the churn fix lands before N14-on-F3, the N14 base should sit at or after it, or the order must be disclosed.
- 247 = distinct living entities per run, summed over the 15 base runs (not 247 different entities).
- `post_lost` is dropped from the figures.
- Faction squads: 0 in all runs; the squad path is covered by tests only.
- The field-order guard: `tests/unit/core/test_pickled_record_field_order.py` (fields may only be appended).
- The pin / default-path sentence: with the push shapers ON (default), `extract()` emits 4 lines over the 200-tick lifecycle run and none of group_joined, group_expelled, cooperation_event or contract_milestone_completed; `as_built` and `default_flags` carry none of these events, so a pin that does not move there means the default path does not carry them, not that behaviour is unchanged.
- The milestone -963 (2768 to 1805 events in the lifecycle pin): it follows fewer ACTIVE contracts (sum of ACTIVE contracts over ticks 2419 to 1265, contracts created 44 to 27, most ACTIVE for one pair 24 to 6); the shaper re-scans every ACTIVE contract each tick.

## Results (post-F3: base 30307228c = origin/main with F3, arm effd2e8fc = this fix merged on it; head 07ec1cee9 is src-identical to the arm)
Method for every timing line: non-audit, pinned FULL (PinnedNormalGovernor), ConcurrentExecutionAdapter, s42, 2000 ticks, cores 4-5, one run at a time. Production on this host is not measured by this method (smoke: frontier s42 base, 600 ticks, default governor: FULL 66, MINIMAL 281, OFF 253). Audit figures come from different runs and are context only.
- 15 paired audit runs (3 worlds x s42-46, 2000 ticks): Tier 1 death bar did not fire in any world; hard law `{}` on all 30 runs; lag 0 on every FULFILLED end (217 / 356 / 186 on the arm); contracts phase skipped the last tick per run. Formations (5 seeds summed, crowded / frontier / urban) 988 to 332, 934 to 504, 805 to 218; ids handed out twice 884 / 810 / 595 to 0; ghosts 0. Death totals base to arm: crowded HAZARD 22 to 20, COMBAT 82 to 83, DEFEAT 55 to 52; frontier 42 to 37, 62 to 63, 35 to 31; urban 10 to 9, 19 to 21, 19 to 15.
- Timing (B: 3 paired reps per tree): crowded -7.6% (143.2 s to 132.2 s), urban -0.1% (156.8 s to 156.6 s), frontier +6.7% median (239.4 s to 255.5 s), slower in all 3 pairs (+9.8/+6.2/+7.8) but UNRESOLVED under the overlap rule (5.0 s overlap on one base run); likely real, unresolved. Groups rises (crowded 0.27 to 0.40, frontier 0.26 to 0.85, urban 0.32 to 0.51 ms/tick median, under the bars) and cooperation falls (1.345 to 0.987, 4.014 to 3.097, 5.449 to 2.134), net to about 0; frontier's ~8 ms/tick is not attributed (resolution_overhead +2.0, combat_engagement +1.4, advancement +0.9 shown, not explained). Host swap burst during frontier arm rep 1 (11,400 pages of swap-in on the slowest arm run, 284.4 s) reported, not repeated; the other two pairs still read +6.2/+7.8. Hold rule (total > 5% resolved, store > 2000, ruled phase beyond base spread by > 5% of base total): fired in no world. All 18 runs FULL on 2000 of 2000 ticks; hashes identical across reps and equal to the audit set's (crowded 4cdcf4659b17 to 6e697606225a, frontier 5ad7d147ffd2 to 9dd1e97d70a1, urban cf3992930175 to d327ea389dbf). Production timing not measured; perf checkpoint (a) covers it.
- Crowded: persistence 35.9 to 29.7 ms/tick, a resolved fall, cause not shown; not offered as a gain. The persisted-record counts (36,449 to 55,465) are pre-F3 figures and were not re-read on this tree.
- Visits: base's whole-store visits come from the timing counters (store records visited per run, groups passes plus cooperation: 72,822 / 106,890 / 69,944). The three base visit-count runs did not run (the step-(a) counter imports live-group code the base tree lacks; failed in one second, before any tick; no simulation lost, no timing run affected). Arm (count runs, hashes equal to the timing runs): per-pass visits = live at phase start + (A) 0 dirty dissolved ids skipped at the guard + (B) 45 / 109 / 59 same-tick adds; residual 0, no late visits; sums 11,966 / 29,422 / 17,994; the live filter scans about 93 / 154 / 106 store records per tick. The arm's unfiltered store-entry counters read x1.70 / x1.92 / x2.01 of base's.
- Store at t2000 on s42: 19 to 45 (crowded), 28 to 109 (frontier), 19 to 59 (urban); dissolved 45 / 103 / 56 on the arm. The store keeps every dissolved record; with step (a) the groups and cooperation phases do per-group work for live groups only; the live filter's whole-store scan grows with run length.
- H1 clusters (hazard walks, traced before F3): NOT SHOWN as caused by the fix for crowded s42 victims 1, 6, 7 and frontier s43 victims 1, 7 (followers whose group's shared target equalled the chase target; the target-score group bias at `tactical.py:428` is second in the sort key and was not excluded); FAIL (no causal step) for the other traced victims.

## Close disclosures (rpg-planner's list, rpg-designer's ruling under owner (b); tickets not on main are cited by id)
1. crowded s43 e10: FED by (i), pre-existing focus-fire group_bias. The rider is not shown to save it (bias held t894-897 only; e10 picked 27 from t898 (traced pick; target rows from t901) and died anyway).
2. frontier s45 e22: FED by the letter only (the walk into range was its own congestion redirect; it dies on base too, t1029).
3. v17 and v24: NOT SHOWN.
4. Per-seed rises with totals down: frontier s43 21 to 35, urban s42 8 to 10.
5. The e30 kill cluster (frontier s43, 4 group members, untraced; ENGAGE-BRACKETING evidence).
6. The lodged-leader seam (2.155): TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS (+ audit TCK-20261101-A-LODGER-DECISION-PATH-AUDIT). Probe rows: a lodged stayer chosen leader and bound holder at a formation in 9 rows (frontier s44 3, s45 3, urban s42 3, s43 0). Outside-follower tile conditions on urban s42: 193 of 370 outside-member ticks with a lodged leader (follow-specific conditions, task target = leader and a REGROUP/FOLLOW reason, were 0).
7. FULFILLED with a lodged party = term expiry (exception (c)).
8. The 2.146 rewrite as already agreed.
9. Rider ids, not on main: TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET (P1, next, measured on top of churn) and TCK-20261101-A-LOW-HP-VANGUARD-TAKES-ROLE-GATED-MOVES-INTO-CONTACT (P2, counts first).
e12 and e23 are final NOT FED, and v9 NOT FED. e12 and e23 died within 50 ticks of a bed leave; both leaves were plain rest ends (F3 re-lodge churn, N14), not a decision this change made.

## Builders and the counter
- Builder list: the list of src sites that build a state with groups and no counter is empty today (19 construction and `replace` sites scanned: only the apply copy and `to_readonly` pass groups; the apply copy passes the counter). `tests/unit/core/test_state_builders_pass_the_group_counter.py` enforces it for any future builder (`to_readonly` exempt by name; positive control on a planted bad source).
- Named gap: a hand-built runtime state with groups above 10000 and no counter keeps 10000. That is safe while records are kept, since the allocator skips taken ids. Only restore seeds the counter (FIELD_RULES) and checks it (`GroupCounterBehindStoreError`).
- Which of F3 or this batch landed `checkpoint_fields.py` first: F3 did (30307228c); this batch's four rows are in F3's table and shape, one class name `CheckpointFieldMissingError`.

## Evidence
`agent-working/staging_artifacts/TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS/evidence/` (set15, timing, trace15, trace59f, fixture, out6, trace); raw scratch under /data/vboxuser/Work/groups_base (kept until the PR lands).

- Local-only observation: tests/unit/perf/test_benchmark_record.py::...cpu_affinity fails when pytest runs under a taskset pin (cores 4-5) and passes without the pin; it is main's perf test reacting to the affinity, not this batch.
- Step (a) (live-group iteration) is in the batch: state hashes unchanged on three worlds (66101cd32511, a872018bf494, ae41db137ac7), per-pass visits = live at phase start + same-tick adds, residual 0.

- Step (a) ticket: TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK is on main (todos/). This PR delivers step (a) only; (b) and (c) stay open, so it must NOT appear under Closes: (check the rendered body; if it does, tell the planner, no hand edit).
