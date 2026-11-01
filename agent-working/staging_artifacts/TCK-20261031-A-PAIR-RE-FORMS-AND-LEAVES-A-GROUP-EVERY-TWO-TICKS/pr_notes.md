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
- Old checkpoints: one post-unpickle step in `src/engine/checkpoint_fields.py` (table `FIELD_RULES`, `CheckpointFieldMissing`, a 400 on the restore route). Slotted dataclasses unpickle positionally, so `next_group_id` is the last field of `AuthoritativeState` and the new `GroupRecord` fields come after `_canonical_cache`; the guard is `tests/unit/core/test_pickled_record_field_order.py`. `GroupRecord` moved to `src/core/group_record.py` and is re-exported by `src.core.state` (an old-path pickle test).
- Which of F3 or this batch landed `checkpoint_fields.py` first: not known to me. When I wrote it no remote branch had that file, and origin/main at 56f63512a does not have it either; whichever lands second adds its rows to the first's module and re-runs both sets of old-shape tests.
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

## Results (pending nothing; figures may change on an F3 re-run)
- 15 paired runs (crowded_frontier, frontier_living_world, urban_political x s42-46), base c9b9a50f4 vs fc22ae71f: Tier 1 death bar did not fire; lag 0 on 741 of 741 FULFILLED ends; the contracts phase skipped one tick (tick 2000) per run, so lag 0 does not exercise the dirty-set rule (covered by a test and an independent range check, group-end ticks 101-109 for the 19/33 pair before the fix); overwrites and ghosts 0 on the fix; group lifetime p50 68-99, p90 99; same-contract re-forms 0 to 2 per run; different-contract re-forms 2-25 within 10 ticks (the duplicates ticket).
- Timing (pinned, 3 reps): crowded 164.0 s to 140.4 s (-14.4%); frontier 268.8 s to 294.9 s (+9.7%, UNRESOLVED by timing, the fix slower in 3 of 3 pairs +7.2/+22.1/+1.8%, the 1.7 s overlap rests on one base run; a real rise of unknown size expected); urban 175.0 s to 179.1 s (+2.3%). Hashes identical across repeats; all 18 runs FULL.
- Groups rose about 1.4 s and cooperation fell about 1.5 s, net about 0 of the 26 s (store-visit ratio x1.92); the rest is not attributed. By median difference, resolution_overhead +3.3, persistence +2.1 and combat_engagement +1.7 ms/tick moved; their cause is not shown. Groups phase median 0.270 -> 0.990 ms/tick on frontier, a resolved rise, under its 6.72 ms bar.
- One quantity: store records visited per tick, summed over 2000 ticks (base to fix): crowded 36,411 to 55,375 (x1.52), frontier 53,445 to 102,574 (x1.92), urban 34,972 to 74,591 (x2.13). Cooperation's own walk was not separately counted, and cooperation's time fell. Groups/cooperation work rises with the group store, mostly retained dissolved records (visit ratio x1.52 against store ratio x2.37, x1.92 against x3.93, x2.13 against x4.16; live groups at t2000 on the fix 2, 6, 6).
- Crowded: resolved fall of 10.9 ms/tick in persistence, cause not shown; persisted-record counts rose 36,449 -> 55,465. Not a gain.
- Disclosure: the group store keeps every dissolved record; at 2000t it holds 43-104 records and the groups and cooperation phases visit each one every tick (about 1 ms/tick on frontier at 2000t); this grows with run length (TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK).
- H1 clusters (hazard walks): NOT SHOWN as caused by the fix for crowded s42 victims 1, 6, 7 and frontier s43 victims 1, 7 (followers whose group's shared target equalled the chase target; the target-score group bias at `tactical.py:428` is second in the sort key and was not excluded); FAIL (no causal step) for the other traced victims, including the urban victims 6, 16, 17, 14. No move in this codebase avoids a hazard (routes weigh terrain cost only, 2.128).

## Evidence
`agent-working/staging_artifacts/TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS/evidence/` (set15, timing, trace15, trace59f, fixture, out6, trace); raw scratch under /data/vboxuser/Work/groups_base (kept until the PR lands).
