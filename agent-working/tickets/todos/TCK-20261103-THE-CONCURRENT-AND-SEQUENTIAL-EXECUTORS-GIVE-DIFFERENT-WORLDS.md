---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS

## Title
The concurrent and sequential executors give different worlds on the same seed, with no load, against the bit-identical law

## Status
OPEN

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
- Priority P1 because each executor repeated its own result. That has only been shown on ubuntu, on one tree and seed. Raise to P0 if counts show most seeds split early, or if `_freeze_cache` fires: results would then depend on memory addresses and may not repeat across hosts or Python builds.
- Holder: rpg-planner (src/engine/executor.py routes to rpg, lead-planner-u24 2026-11-03). rpg-planner-ubuntu is diagnosing; who builds the fix is settled between the two. perf-planner gets a finding through the ubuntu lead (Phase B's timings ran the concurrent adapter, and CORE-PERF-020 is the freeze cache's reason for existing) and gives its view on the fix's cost. testing-planner homes the long-horizon test.
- The owner knows (#715 6585858521, via the lead). rpg-designer's decision row follows the first split.
- Dispatch needs an owner yes.

## Implementation Notes
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
- Horizon: provisional floor 3000 ticks, finalised when the split is named. extra_slow budget is 600s/8GB per test: measure one arm first; if two arms don't fit, ask testing-planner, and don't quietly drop below t2100.
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
- rpg-designer ruling, conditional on ubuntu's per-call log: the stored 10-tick plan is the rule (route_search module text, divergence 2.128), so concurrent is off it if it discards the store. But the plan store is then durable behaviour state, written by object.__setattr__ during decision, outside the hash, and unclear on restore, which breaks the durable-state rule on the reference path too. Lean fix (A): plans become real state: in the digest and checkpoints, written through apply as typed per-(entity, goal) updates, read by workers from the packet; sequential behaviour stays the same. (B) a pure step function is rejected unless (A) proves too costly, because it would move the sequential world. movement_cache gets the same read. Tests to add: a restored run equals an unbroken one past a live plan's expiry; local vs concurrent on a gate world. A digest change for route_plans moves pins, so place it with the digest ticket, not twice. Don't assume one cause: the base's split at t2051-2100 may be another.
- The fix won't settle it alone: packets, `frozen_grid` and other frozen maps, ordering and RNG could diverge too. If it ships as the cause, it needs the convergence check.

## Test Summary

## Files Changed

## Completion Summary
