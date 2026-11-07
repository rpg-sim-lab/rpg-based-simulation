---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS
phase: done
date: 2026-11-03
tags: []
---

# TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS

## Title
The concurrent and sequential executors give different worlds on the same seed, with no load, against the bit-identical law

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-planner-ubuntu on 2026-11-03 while chasing a #828 V3 red. Relayed by lead-planner-u24: implementer's results, raw being located, not checked by the lead or rpg-planner.

On crowded s45:
- build_kernel with only `ConcurrentExecutionAdapter` reproduces `_run_engine` (t2000 014bd9e2230c, e34 dead).
- build_kernel with only a 100 ms budget equals plain pinned (d60d4287b8f4, e34 alive), so the budget is out.
- The governor never leaves NORMAL, the host was idle, and each executor repeats its own result. So results change with no load, and it is not random.
- The #828 arm splits before t900. The base splits in t2051-2100.

Production takes the concurrent path (src/engine/kernel.py:193-198: `profile.max_worker_count > 0` picks `ConcurrentExecutionAdapter`; PROD_SMALL has 2 workers). The RPG gate and tools/rpg_measure take `LocalSequentialExecutor`.

The law exists: docs/engine/matrices/full_certification_test_matrix.md requires bit-identical equivalence between local and concurrent runs, and the certification contract requires a sequential baseline hash. Its kernel test reportedly runs one tick (lead-planner-u24's read), and short runs would miss a split this late.

rpg-designer's framing (2026-11-03): an executor difference is a defect to fix so that the two agree. Pinned stays the measuring ruler until then, and is not a claim about what players get.

Why it matters: what production runs and everything measured since the paired tool landed are different worlds on these seeds. How much they differ in general is unknown.

## Scope
1. Name the cause: rpg-planner-ubuntu's per-tick diff t1-t900 on the #828 arm and t2051-2100 on base, then the first differing field and the code that writes it. Likely shapes, none shown: worker result order, a stale read in a worker, an RNG draw that depends on packet grouping.
2. Counts: how many seeds and worlds split, and the first split tick, base main, 2 workers vs sequential.
3. A long-horizon equivalence test (long enough to catch these seeds, within test budgets), failing today. Home and tier are testing-planner's call.
4. Fix so that the concurrent path equals the sequential path, in the direction that leaves sequential hashes unchanged where possible, so pinned evidence and baselines stay valid. If the fix must move sequential results, stop and report: that's a new baseline and an owner decision.

## Out of Scope
- Governor or budget behaviour under load (not implicated by the controls; rpg-designer treats that as a separate degraded-world question).
- The digest coverage (TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ), though a hash equal under a narrow digest doesn't prove the executors agree, so the equivalence test should read that ticket's result.
- Re-measuring #826 and #828.

## Acceptance Criteria
- Cause named with file:line and a replay.
- The long-horizon equivalence test passes on the standard worlds and seeds.
- Sequential hashes unchanged, shown by neutral runs, or a stop as in Scope 4.
- docs/engine and the parity ledger (infrastructure.yaml) state the law as tested, with its horizon.
- Hot-loop: probably yes (executor and commit path). Under the perf pause (#715 6556861718) timing is NOT MEASURED unless the fix needs it; say so at close.

## Related Tickets
- TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
- TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (#828)
- TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT (#826)

## Related Docs
- docs/engine/matrices/full_certification_test_matrix.md
- docs/engine/deterministic_execution.md
- docs/plans/architecture/port_leak_audit.md (section 6)

## Related Stored Artifacts
- None yet; ubuntu's raw is being located.

## Related Code Areas
- src/engine/kernel.py:193-198, src/engine/executor.py (`ConcurrentExecutionAdapter`, `LocalSequentialExecutor`), src/core/worker_protocol.py
- tests/integration/kernel/test_executor_determinism.py, test_determinism_suite.py, test_tied_worker_result_order.py, tests/perf/test_concurrency_parity.py
- tools/calibrate_simq.py (`_run_engine`), tools/test_architecture/rpg_gate_run.py (`build_kernel`)

## Assumptions / Open Questions
- Priority P1 because each executor repeated its own result. That has only been shown on ubuntu, on one tree and seed. Raise to P0 if counts show most seeds split early. The second trigger (`_freeze_cache` firing, so results depend on memory addresses) is down for now: zero stale hits in one run. It returns if any address-dependent path shows up.
- Holder: rpg-planner (src/engine/executor.py routes to rpg, lead-planner-u24 2026-11-03). rpg-planner-ubuntu is diagnosing; who builds the fix is settled between the two. perf-planner gets a finding through the ubuntu lead (Phase B's timings ran the concurrent adapter, and CORE-PERF-020 is the freeze cache's reason for existing) and gives its view on the fix's cost. testing-planner homes the long-horizon test.
- The owner knows (#715 6585858521, via the lead). rpg-designer's decision row follows the first split.
- Dispatch needs an owner yes.

## Implementation Notes
2026-11-03 THIRD CAUSE (rpg-planner-ubuntu, via lead; scratch boundary check pending): WorkerPacket declares `blocked_tiles` with default [] (worker_protocol.py:101 on its branch), but packet construction never sets it; only the sequential readonly view does (executor.py:58-59). Buildings are in blocked_tiles (compiler.py:666), so on the packet they weren't solid once the fix's empty building_tiles skipped the buildings scan. The guard missed it because a defaulted field fails no lookup: the banned placeholder pattern, in a field that predates this build. Added acceptance (rpg-planner as reviewer): a PR-lane field-parity test over every WorkerPacket field found by dataclasses.fields. Each field equals the state's on a gate-world state at several ticks (t0, mid-run, after lodging and after a building change), or sits in an exclusion list with reason and owner. A defaulted field that construction never sets fails. The PR text names the causes it would have caught.
Field-parity test, rpg-designer's three notes adopted: compare by content, not identity; per-field exceptions need a reason and owner, and a packet field that shares a state field's name but differs in meaning is refused outright (the `seed` case); run at several gate-world ticks so drift during a run is caught. If that's too slow for a PR lane, split into a fixture version in the PR lane and a gate-world version in the slow lane.
2026-11-03 FINAL TEST RULING (testing-planner, via lead-planner-u24; supersedes every earlier horizon and test-shape line in this ticket): no golden value and no cross-test comparison. One standalone `extra_slow` test per (world, seed) in tests/integration/kernel/, running sequential and concurrent live, comparing hashes and entity fields every 100 ticks: 2200t on the base that split late (crowded s45 base, t2051-2100), 2000t on the others. One concurrent-twice test on that world at 2000t, worker count and governor pinned. The evidence run uses the same horizons. Red on pre-fix src shown in the PR text. One PR, test plus fix, no known-reds entry (rpg-planner). A short PR-lane test on the named cause. No re-anchor inside the fix PR: old and new values listed, rpg-planner rules on expectations, testing-planner sees the list first.

2026-11-03 rpg-designer (owner row drafted at main-checkout .claude/handover/drafts/rpg-designer-executor-failure-row.md, not yet answered): ubuntu found the concurrent path turns worker exceptions into no-ops under a written contract (bounded_concurrency_contract.md:39-40). Proposed: the guard stops a production run on an undeclared read; other errors keep the no-op for now, counted; any count above zero fails evidence runs and the long test, with the raise option back to the owner if non-zero. Add to scope: the no-op count, and the `clans` read and its test (detail from rpg-planner-ubuntu). Evidence runs report the no-op count (also for TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE). Testing-planner's final test ruling (lead's relay) supersedes the 3000t one below: extra_slow per world and seed, 2000t, 2200t for the base that split late, red on pre-fix src, one 600t concurrent-twice case, governor pinned, short PR-lane test; no re-anchor inside the fix PR by default, old and new values listed, rpg-planner rules, testing-planner sees the list first.

2026-11-03 ACCEPTED FIX SHAPE (rpg-designer; owner row at main-checkout .claude/handover/drafts/rpg-designer-executor-owner-row.md; go, builder and size are the owner's):
- World seed on the packet; flags on the packet.
- A guard failing on executor-side reads of state fields the packet lacks (the 11,011 getattr/hasattr reads; `building_tiles` is the next named one).
- A long-horizon test on gate worlds and seeds comparing cognition too, with `timeline` excluded (event-id ticket), on top of testing-planner's ruling below.
- Separate from #828. Sequential hashes unchanged, or stop.

2026-11-03 STATE AT FILING TO MAIN (rpg-planner-ubuntu; raw spot-checked by it, otherwise its implementer's; one world and seed; relayed, not checked by rpg-planner):
- With the seed change alone, concurrent equals sequential on hashes for the #828 arm and base through t2100.
- SECOND DIVERGENCE, outside the hash: the worker packet has no `feature_flags`, so src/engine/domain/combat_actions.py:126-127 reads ENABLE_COMBAT_ENGAGEMENT as OFF on concurrent (learning calls 153 vs 241 by t2000; line read by lead-planner-u24). On production paths, learning-weighted engagement has been partly off.
- With both fixed, cognition is identical by content at 9 sampled ticks.
- Not supported to t601: perception.py:97 as a second consumer of the packet seed (290 calls outside the executor, seed 45 on both). rpg-planner's earlier suggestion is withdrawn.
- Size: not one line. Proposed shape adds a guard against reads of names missing on the packet, so this is standard tier, not a hotfix. Both defects (seed, feature_flags) are in this ticket's scope, plus the guard; the 27 `state.seed` lines are still read.
- Landing: separate from #828, whose re-measure is sequential. Build: rpg-planner-ubuntu's side, on the offer, sized here; dispatch needs an owner yes.

2026-11-03 CAUSE NAMED (rpg-planner-ubuntu; proof runs pending at this entry): under `ConcurrentExecutionAdapter`, `state.seed` reads a per-packet seed (src/engine/executor.py:286-293), not the world's, so `wander_destination` (src/engine/tactical_destinations.py:117) draws a different point: e30 at t600 on the #828 arm, reproduced with the repo's RNG to the digit (one seed).

rpg-designer rulings on it: concurrent is wrong; `state.seed` means the world seed everywhere. Fix: `packet.seed` carries the world seed, with a separately named field only if a real reader needs one (rpg-planner's grep on main found no reader of `packet.seed` by that name in src or tests). The ticket reads each of the 27 `state.seed` lines, among them src/domains/combat_engagement/perception.py:97 (observation noise), src/ai/coming_of_age.py:146, src/town/guild.py:85, src/domains/world_emergence/phase.py:59/:66. Sequential and pinned proofs aren't touched. Acceptance stays the long-horizon test on gate worlds and several seeds, because the proof runs are one seed; a split remaining after the fix is a second cause. P1 stands unless the proof or a host check says otherwise. The closes' "production path differs" line drops once this lands and the long test is green. Owner row after the proof. Older lines below are the diagnosis history; the plan-store and `_freeze_cache` leads are not the cause.

2026-11-03 rpg-designer rulings:
- By test_local_vs_concurrent_identical in the certification matrix this is a defect, not a degraded world. The law stands.
- Lean: concurrent comes to sequential. It flips only if the first split shows sequential is the one breaking a rule.
- All rule measurement stays on pinned sequential. F3 and ENG stay valid as measurements of the reference but do not yet describe production.
- #828's re-measure starts after the first split is named, if the fix touches only the concurrent path.
- Real acceptance: local vs concurrent hash equal on a gate world across several hundred ticks (the current tests reportedly run 1 tick or 2 entities). This is a floor; the seeds here split as late as t2051-2100, so the horizon must also reach those. testing-planner decides the test's home.
- Every pending close carries: "measured on the sequential reference; the production path differs until TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS lands". #826's correction says its table was the concurrent world.

2026-11-03 testing-planner ruling on the long-horizon test:
- Home: tests/integration/kernel/, beside test_long_run_determinism.py, marked `extra_slow` (Slow regression lane). Not PR lanes, not the rpg gate, not tests/certification/test_cert_long_run_stability.py (those skip in CI).
- Once the split is named, also a short regression test on the named cause in a PR lane.
- Horizon: SUPERSEDED, see FINAL TEST RULING. (Was: a provisional 3000-tick floor.)
- Compare hashes every 100 ticks, fail on the first mismatch, naming the tick. A gate world and the seeds and bases that split, named in the test.
- Conditions: (1) concurrent twice and sequential once, worker count pinned; concurrent vs concurrent decides `kind`. (2) Shown red on current src on a named world and seed, and the first CI run is red too; if CI doesn't reproduce it, tell testing-planner. (3) audit_mode and governor pinned as #827/#829 settled (out-of-reach RAM ceiling). (4) The test states its strength is limited by the digest (TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ).
- Parking: a plain failing test plus a slow_known_reds entry in the same PR, not xfail: exact test id, owner rpg-planner, this ticket, expiry about 4 weeks, kind `flaky` if concurrent races, else `broken`. The fix PR deletes the entry. lead-planner-u24 reviews the entry. Tell testing-planner on dispatch.

Lead candidate (rpg-designer's read of src/engine/executor.py:239-257 on main; firing NOT shown): `_freeze_cache` holds (id, frozen) per key and drops the original, so address reuse can return a stale frozen copy for groups, buildings, corpses and so on.
- Log by comparing content on cache hits, without keeping originals alive: holding them changes addresses and could hide it.
- If it fires, the fix is a held reference and an identity compare. Then compare local vs concurrent again, because the adapters differ in other ways too.
- Also read the other caches at :259-275.

2026-11-03 perf-planner's view (read only on 0e7b1030c, nothing run or measured, relayed): held reference plus `is` should cost close to nothing on the normal path (7 keys per execute call, at most one old container per key until the next call); the one real cost is that a hit stale today becomes a `deep_freeze`, in proportion to how often the bug fires. rpg may take it on correctness with no perf review or timing set. A stale hit may need two or more replacements between two execute calls; not traced. CORE-PERF-020 records no measured benefit; removing the cache may be simpler, but that is for after the pause, with a measurement.
- The earlier "0 id matches, 0 stale hits" (TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID) is empty evidence: `frozen_probe.py` hooked `LocalSequentialExecutor.execute`, while `_freeze_cache` is on `ConcurrentExecutionAdapter`. Correct docs/engine/deterministic_execution.md ("probed without a stale hit") in this ticket.
- rpg-designer: a `_freeze_cache` stale-hit count of 0 wouldn't clear this ticket; the per-field diff decides. Take the `is` fix only once the cause reading is in, so it doesn't change the world mid-diagnosis.
- ubuntu's diff at t600 (hashes equal): `timeline` on all 38 entities, `cognition` on e16 and e30, `route_plans`, `_spatial_grid_cache` already differ, so the origin is before t601. A t1-t601 field digest is next. It may change this ticket's scope.
- Second lead, code read only, test running on ubuntu: src/engine/route_search.py:146-149 sets `route_plans` on whichever object it is given. The concurrent path passes a WorkerPacket, so it may build a throwaway store per call and search fresh, where sequential reuses a plan valid for 10 ticks. If so, it is a logic difference unrelated to `_freeze_cache`, and which behaviour is the rule goes to rpg-designer. Also check checkpoint restore: a store outside the hash that may not be saved could change a restored world.
- WITHDRAWN by rpg-designer the same day (ubuntu's rows don't support it; no fix shape stands until a cause is named; kept as history only). Earlier conditional ruling: the stored 10-tick plan is the rule (route_search module text, divergence 2.128), so concurrent is off it if it discards the store. But the plan store is then durable behaviour state, written by object.__setattr__ during decision, outside the hash, and unclear on restore, which breaks the durable-state rule on the reference path too. Lean fix (A): plans become real state: in the digest and checkpoints, written through apply as typed per-(entity, goal) updates, read by workers from the packet; sequential behaviour stays the same. (B) a pure step function is rejected unless (A) proves too costly, because it would move the sequential world. movement_cache gets the same read. Tests to add: a restored run equals an unbroken one past a live plan's expiry; local vs concurrent on a gate world. A digest change for route_plans moves pins, so place it with the digest ticket, not twice. Don't assume one cause: the base's split at t2051-2100 may be another.
- `_freeze_cache` result (implementer's, unchecked): zero stale hits in one full 2000t concurrent run on crowded s45, end hash unchanged; it barely hits except ground_items (1997 of 2000, 0 different). Out as the lead on this one run. The `is` fix isn't the fix for this split; it stays optional on correctness. Route test is next.
- Route-plan result (rows read raw by rpg-planner-ubuntu, unchecked by rpg-planner): hypothesis NOT supported. On both runners all 8240 route calls come from the apply path on AuthoritativeState, with equal hits and searches. So rpg-designer's plan-store ruling above, conditional on discarding, doesn't currently describe the cause, and no fix shape stands. First difference: call 8234, tick 600, e30, same start [38,33], goal [33,32] sequential vs [40,34] concurrent. So the executors produced different movement intents from an input whose hash is equal: decision context or unhashed input such as cognition, not shown. Cause open. The route_plans-outside-the-hash question stays on the digest ticket.
- The fix won't settle it alone: packets, `frozen_grid` and other frozen maps, ordering and RNG could diverge too. If it ships as the cause, it needs the convergence check.

2026-11-03 BUILD NOTES (rpg-ubuntu-implementer; branch rpg-ubuntu-executor-parity off 9eeb0fd97; owner go #715 6593491826, failure answers #715 6593673717):
- Built: packet carries the world seed and the state's feature_flags, building_tiles, town_center, clans by value; `PacketFieldMissingError` guard (`WorkerPacket.__getattr__`) with the allow-list `PACKET_DERIVED_CACHE_NAMES` (a reason per name); the error passes through the worker_manager handlers (`_process_chunk_wrapper`, `_wrap_work` and with it the :175 local rerun, `_collect`); all other worker exceptions keep Failure-to-No-Op and are counted by wrapping `failure_no_op` (zero required). Contract section 4 states the one exception.
- Horizon: testing-planner's final ruling supersedes the 3000t line in the testing-planner paragraph above: 2200t on crowded s45 (the base that split at t2051-2100), 2000t on the other cases (rpg-planner seat-5 record, relayed via lead). The case list comes from the pre-fix evidence run and goes to testing-planner first.
- Divergence 2.147 (Bug Fix; ubuntu's block is 2.145-2.149, then 2.160-2.199); parity ledger INFRA-439 (checked free by rpg-planner).
- Record correction, not a fault: TCK-20260824-TOWN-CENTER-POINTER-FIX called `WorkerPacket.town_center` a dead field; its premise missed the executor-path reader `MovementSystem._route_step` (movement.py:112), reached in the executor through `resolve_move` from the MOVE action (domain/movement_actions.py:27). The field is back, and its test now pins the consumer.
- building_tiles: the packet is built from `state.building_tiles` at the single construction site (a test pins that src/engine/executor.py is the only constructor). Crowded s45 has NO building tiles (len 0 at all 1,118 reads), so the long test cannot catch a wrong-empty map on that world; the evidence run covers worlds with tiles (urban, frontier).
- Expectation changes held for and accepted by rpg-planner: tests/unit/kernel/test_worker_protocol.py (town_center now live) and tests/unit/engine/test_service_reach_on_a_worker_packet.py (packet now carries building_tiles). SimQ pins run before (trees/0e7b1030c) and after (this worktree): no moved pin so far (test_anchors_audit_mode 11/11, test_calibrate_simq 9/9, population stability 1/1 on both).
- Not in scope and not done: the `is` fix for `_freeze_cache` (zero stale hits in one 2000t concurrent run, caveat terrain sampled); the process-pool path (no caller passes use_processes=True); timing (NOT MEASURED, perf pause).

### Third cause: blocked_tiles (crowded s42, 2026-11-03)
- Measured: with causes 1 and 2 fixed, crowded s42 split at t1974 (sequential `ec7b2abfdc96`, concurrent `74ea4809ee83`; at t1973 every entity and state field equal; at t1974 only state.groups and e37 navigation/strategic/task differ). The executor-output trace names e37's tactical call at t1973: the state returns the held pursuit, the packet INTERCEPTING with aim point (40,31). Line trace: neighbours identical (15 raw, 5 filtered, same order), first differing local `intercept_pos` at tactical.py:606 (`PositioningService.find_intercept_position`); it asks `verify_occupancy` about (40,31), the inn tile (building 20003). Pieces: state `blocked_tiles` holds the tile (the compiler adds each building tile, compiler.py:666) -> PATH_NOT_FOUND; the packet's `blocked_tiles` had a default `[]` never set by the executor -> LEGAL. `building_tiles` is empty in all three gate worlds (t0: 0 vs 5/8/7 buildings and blocked tiles), so it moves no decision. No snapshot, claim, occupant or lodger involved at that tile (state has no occupancy_snapshot at t1973).
- Fix: `blocked_tiles=state.blocked_tiles` on the packet (executor.py), field default `frozenset()`; sequential unchanged; crowded s42 sequential = concurrent = `aa2fa3053507` at t2000.
- Guard: `tests/unit/kernel/test_executor_context_parity.py` field-parity test over `dataclasses.fields(WorkerPacket)` (PR lane fixtures: t0, mid-run, after lodging, after a building change; extra_slow gate world at t0/150/600, 50 s); derived structures compared with fresh rebuilds; positive controls: `blocked_tiles` unset fails 6, a stale occupancy_map fails, a stale state snapshot fails. Audit: the only defaulted packet fields the executor did not set were `blocked_tiles` and `transient_claims` (None on the state outside resolution; listed with its reason).
- Docs: contract section 4, divergence 2.147, INFRA-439, the occupancy_snapshot allow-list comment (the old 'same occupants' claim was unverified).

## Test Summary
- PR lane (unit-core-world, `tests/unit/kernel`, `-m "not slow and not extra_slow"`): `tests/unit/kernel/test_executor_context_parity.py` (23 tests: seed, flags, building_tiles/town_center, service reach, join-clan, the guard, the field-parity test over `dataclasses.fields(WorkerPacket)` at four stages, the derived structures against fresh rebuilds, the defaulted-field audit, two stale-occupancy controls), `test_worker_failure_paths.py` (8), `test_executor_equivalence_digest.py` (5: the digest and compare helpers incl. the terrain control). Fixed head: all pass. Pre-fix src (9eeb0fd97): context_parity 16 failed / 7 passed, worker_failure_paths collection error (imports PacketFieldMissingError), digest 4 passed (it tests the helpers).
- Positive controls: executor `blocked_tiles=` line removed -> 6 fail; a stale occupancy_map and a stale state snapshot each fail; a changed terrain value is named at a sampled tick; a non-thread pool fails loudly; a cyclic field is named by the digest.
- Slow lane (extra_slow, slow-regression.yml): `tests/integration/kernel/test_executor_equivalence_long.py`: CASES crowded s45 2000t, crowded s43 2000t, urban s42 2000t, frontier s44 2000t, plus `test_the_concurrent_executor_repeats_itself` (2000t), and the gate-world field-parity cases (t0/150/600, 50 s). Crowded s43 replaced crowded s42 on the ratio of each case's wall to crowded s45's, measured as pytest items in one session (`--resource-budget large`, cores 4-5): s43 430.1 s (ratio 0.917), s44 451.2 s (0.962), s45 at 2000t 468.8 s. Crowded s42 left the list for time (identical code took 429.7 s at 05:09 and 584.6 s at 06:14 on this VM; cause of the change not found). Its late split, the packet's missing `blocked_tiles`, stays guarded in the PR lane.
- Horizon of crowded s45: 2000t, not 2200t. The content comparison reaches the pre-fix concurrent split by t300; the canonical-hash split at t2051-2100 on main is evidence, not a required horizon. Reason for the cut: s45 at 2200t passed at 599.5 s, 0.5 s under the 600 s alarm (head 637c6856e); s45 at 2000t passed at 468.8 s on identical src (cbbc77814).
- Long tests on 637c6856e (one VM, cores 4-5): s45 2200t passed 599.5 s; urban s42 passed 548.7 s; frontier s44 FAILED on the 600 s resource alarm (`TimeoutError` in tests/conftest.py, not a parity result; no known-reds entry, no re-run); the repeat test passed 484.25 s.
- VM caveat: the bare 2000-tick sequential loop took 200.8 s (urban s42) and 286.4 s (frontier s44) on 2026-11-07, 30-43% more than the same arms in the evidence run earlier that day; the digest adds about 3% (1.7 s vs 1.1 s per arm urban, 2.8 s vs 1.8 s frontier over 20 samples: groups_base/digcurve_*.log). Cause of the slower machine not found.
- Fallback agreed with testing-planner: (1) testing-planner reads the first Slow regression run itself. (2) Any long test over 540 s or hitting the alarm drops to 1500t in a test-only follow-up PR owned by this ticket's follow-up. (3) A CI alarm shows as a failing UNOWNED test: no known-reds entry, no re-run.
- blocked_tiles revert proof on the final head (the executor's `blocked_tiles=state.blocked_tiles` line removed): `tests/unit/kernel/test_executor_context_parity.py` has 6 failed, 17 passed: `test_every_packet_field_equals_the_states_value_at_each_stage[t0]`, `[mid_run]`, `[after_lodging]`, `[after_building_change]`, `test_a_defaulted_packet_field_is_shown_set_by_the_executor_or_listed`, `test_a_walled_or_built_tile_is_blocked_on_the_packet_as_on_the_state`.
- Disclosure: the 15-case evidence harness (`groups_base/out_evidence2`) compared the state's `terrain` only by its error text, because the tuple-keyed dict was not JSON-serialisable (the same text on both arms, so terrain was never compared by content in that run). Fixed in this PR: the digest canonicalises tuple-keyed dicts and the tests fail naming any field they cannot serialise, with PR-lane controls (`tests/unit/kernel/test_executor_equivalence_digest.py`). rpg-planner rates it low risk because terrain is static during a run (apply.py:512; local_world_interaction_contract section 4).
- Evidence run (15 cases, 3 worlds x seeds 42-46; groups_base/out_evidence2): fixed concurrent equals sequential in all 15 at every sampled tick (hash and every entity/state field), 0 worker no-ops; pre-fix concurrent differs in all 15 (t100-300, an entity's cognition), reaches the hash in 6 of 15; 4 sequential pins equal pre-fix vs fixed. CI on 157327d64: 25 pass, 1 fail (Code health, execute() 140 > 136, fixed by the _batch_views move), 4 skipping.
- Known gap: the no-op count exists only inside the tests (monkeypatched `failure_no_op`), with no manifest counter; carried to TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE (rpg-planner).
- Known gap: frontier s44's 2000t test does not fit the 600 s alarm on this VM today (two arms of a 286 s tick loop); CI judges it (fallback above).
- Known gap: lockstep early stop for the long test is not built (the failure list and the patched failure_no_op are module-global, plus other process-global state), a follow-up.
- Known gap: the three causes are not separated per case in the 15-case table (the earlier split masks the later); blocked_tiles was isolated on crowded s42 only.

## Files Changed
- src: `src/core/worker_protocol.py` (WorkerPacket: seed, feature_flags, building_tiles, town_center, clans, blocked_tiles; PacketFieldMissingError; derived-cache allow-list), `src/engine/executor.py` (packet construction; `_batch_views` helper), `src/engine/worker_manager.py` (guard pass-through; failure counting).
- tests: `tests/unit/kernel/test_executor_context_parity.py`, `test_worker_failure_paths.py`, `test_executor_equivalence_digest.py`, `test_worker_protocol.py` (town_center now has a consumer), `tests/unit/engine/test_service_reach_on_a_worker_packet.py`, `tests/integration/kernel/test_executor_equivalence_long.py`.
- docs: `docs/engine/contracts/bounded_concurrency_contract.md` (section 4), `docs/engine/deterministic_execution.md`, `docs/engine/matrices/full_certification_test_matrix.md`, `docs/guidelines/intentional_divergences.md` (2.147), `docs/parity_ledger/infrastructure.yaml` (INFRA-439), `docs/REGISTRY.yaml`.

## Completion Summary
The concurrent executor (production) now hands domain logic the sequential world: the packet carries the world seed, the state's flags, building_tiles, town_center, clans and blocked_tiles; an undeclared state read raises and stops the run; every other worker exception stays a counted no-op. Three causes (seed, flags and the other defaulted reads, blocked_tiles), each measured to a first difference. Sequential results unchanged (4 pins). Evidence and tests as above. Review: rpg-planner 837#issuecomment-6697372043, testing-planner 837#issuecomment-6697389011.
Known gap: no manifest counter for worker no-ops (carried to TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE); lockstep early stop not built (follow-up); the three causes are not separated per case in the evidence table.
