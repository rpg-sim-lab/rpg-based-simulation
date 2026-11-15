---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK
phase: open
date: 2026-11-10
tags: [testing, determinism]
---

# TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK

## Title
A conformance test shows a run restored from a checkpoint at tick K and continued to N has the same per-tick proof digest as the uninterrupted run, on a realistic world, at several split points

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner ruling on issue #715, comment 6757579399 (2026-11-10): "File, run later (Recommended)". testing-planner files one P2 conformance ticket: restore against uninterrupted, the per-tick proof digest, a realistic world, several split points. It queues behind the RPG batch (lane C hardening and hit-wake first) and runs in a free host slot named by rpg-planner. The filing rides testing-planner's next PR.

Findings behind it. These come from a static read by the QnA session, relayed by lead-planner-u24; nothing was run, and the line numbers are from main on 2026-11-10:
- The seed-0 restore bug is fixed by #848 (src/engine/scenario_checkpoint.py:92, `DeterministicRNG(base_seed=state.seed)`).
- `ScenarioCheckpointer.restore` builds its Kernel without the service's governor. `ScenarioRuntimeService._build_kernel` passes `governor=self._governor` (src/engine/scenario_runtime.py:424); the restore path doesn't. The effect is unchecked.
- Both paths hard-code `max_worker_count=0` (scenario_checkpoint.py:101, scenario_runtime.py:412), so restore is only exercised on the sequential executor.
- The existing continuation tests are tests/integration/scenarios/test_scenario_runtime_service.py:338 (`test_checkpoint_restore_determinism`) and :379 (`test_restore_keeps_the_state_seed_and_the_per_tick_digest`, seeds 0 and 13). They use 2 entities, 12 ticks and one split. That second test's own docstring says the per-tick digest alone did not diverge on that fixture under the old bug, so the fixture is too small to catch it.
- docs/engine/deterministic_execution.md (Regression tests list, about line 189) cites tests/integration/kernel/test_replay_fidelity.py for "checkpoint load -> resume -> same hash sequence". That file has no such test.
- There may be a process-salted `hash()` at src/systems/.../military_conflict.py:339 (listed in port_leak_audit.md). Not re-verified. It matters only if the restored run is in a different process from the uninterrupted one.

## Scope
- One new test module, in tests/integration/scenarios/ beside the existing restore tests (or tests/integration/kernel/ if that fits the doc's index better). It holds one parameterized conformance test:
  1. Build one realistic world with factions, groups, lodging and combat active within the run. Use an existing compiled world that the RPG gate already runs (e.g. crowded_frontier or frontier_living_world), not a hand-built two-entity state. Name the world and the seed in the test.
  2. Run it uninterrupted to tick N and record the per-tick proof digest for every tick (the proof digest, not the fingerprint; see deterministic_execution.md, "Stability checks, not proofs", PERF-D5).
  3. For each split point K in a set of at least 3, spread over the run (one early, one after groups and lodging have formed, one after combat has happened), checkpoint at K with `ScenarioCheckpointer`, restore it, continue to N, and assert the digest equals the uninterrupted one at every tick from K+1 to N.
  4. On a mismatch, report the first diverging tick and K. It is not enough to report only that the sequences differ.
- It compares the state's proof digest only, never governor mode events or status.current_mode. Restore drops a pinned governor, so mode telemetry can differ legitimately (rpg-planner's ruling, below). Mode events are compared only in the row where both paths pin the same governor.
- Three small rows, set by rpg-planner's ruling (2026-11-10, read on origin/main cf27795cb), next to the conformance test:
  - **Profile row:** the RuntimeProfile the restore path builds equals the one `_build_kernel` builds, field by field, for the same spec. The two blocks are hand-copied (scenario_checkpoint.py:95-105, scenario_runtime.py:405-415), so the row catches drift between them. It passes today.
  - **RNG row:** after restore, the RNG stream continues unbroken. The restored kernel's next draws, both per-domain stream and stateless, equal the uninterrupted run's at the same tick. Restore passes `run_id` to suppress the Domain.INIT draw on purpose (the comment at :106); this row pins that.
  - **Governor/recorder row:** a service built with a pinned governor (e.g. `zeroes_signals`) and a `scenario_event_recorder` keeps both across checkpoint and restore. It fails today, because restore rebuilds `ScenarioRuntimeService(spec)` (:118) and its Kernel without a governor (:111). It goes in as `xfail(strict=True, reason="TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER")`. The fix (restore takes and passes both through) is a src change, rpg-planner's to dispatch, with no RPG re-measure since no state changes. This ticket doesn't fix it.
- Before asserting, the test checks that the world actually reaches the behaviours it claims to cover (at least one faction, one group, one lodged entity, one combat event by the latest K). Otherwise a quiet world would pass vacuously.
- Pick N and K from a measured cost. State the cost (wall time, peak RSS) at scoping, before the test is written. The test must fit a marker tier: `slow` if it runs under the slow lane's per-test budget, `extra_slow` otherwise. It never goes in the PR lane.
- The doc line: when this test lands, point docs/engine/deterministic_execution.md's checkpoint-resume entry at the new test. Until then, the interim correction of that line rides a docs PR, per the owner ruling. This ticket only makes sure the line ends up pointing at a real test.
- Run it in the free host slot rpg-planner names, after the RPG batch. Message the start and finish to rpg-planner.

## Out of Scope
- Any src/ change. That includes passing the governor and recorder through on restore (rpg-planner's follow-on), a shared profile builder (an optional refactor, rpg-planner's call), and a fix for the salted hash.
- A concurrent-executor row. rpg-planner ruled no: the scenario service is deliberately sequential (INFRA-101/102), restore mirrors the build path, and making scenarios concurrent is a perf/platform decision for both paths together.
- The checkpoint format version (TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION).
- Replacing or deleting the two existing small restore tests. They stay as fast PR-lane checks.
- Cross-process restore. In scope only if rpg-planner's governor/executor ruling asks for it. If added, it is a second row, and it can't pass while the salted hash at military_conflict.py:339 is live.

## Acceptance Criteria
- [ ] AC1: The test runs a named compiled world and seed, and before comparing anything it checks that a faction, a group, a lodged entity and a combat event exist by the latest split point.
- [ ] AC2: It compares the per-tick proof digest at every tick K+1..N for at least 3 split points, and on failure names the first diverging tick and K.
- [ ] AC3: A perturb check is recorded in the Test Summary with no src/ change committed. For example, in a scratch copy, drop one stream from the RNG restore or skip `fill_missing_fields`; the test goes red at a named tick. This shows the test can catch a restore defect that the 2-entity fixture missed.
- [ ] AC4: The cost (wall time, peak RSS) was stated at scoping and measured on the run. The test carries `slow` or `extra_slow` to match, plus domain and level markers per docs/testing/test_taxonomy.md section 10.
- [ ] AC5: The profile row and the RNG row pass. The governor/recorder row is `xfail(strict=True)` citing rpg-planner's follow-on ticket, so that ticket's fix makes it XPASS and its PR turns it into a plain assert. The conformance test compares no mode telemetry unless both paths pin the same governor.
- [ ] AC6: docs/engine/deterministic_execution.md's checkpoint-resume entry names a test that exists, either this one or whatever the docs PR set.
- [ ] AC7: The run happened in a host slot rpg-planner named, with start and finish messaged.

## Related Tickets
- TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION (rpg, checkpoint format)
- TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER (rpg follow-on; flips the governor/recorder row)
- #848 (seed-0 restore fix)

## Related Docs
- docs/engine/deterministic_execution.md (Regression tests, PERF-D5)
- docs/engine/scenario_runtime_contract.md (Checkpoint Format)
- docs/testing/test_taxonomy.md (sections 5 and 10)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260619-E31C-CHECKPOINT/

## Related Code Areas
- src/engine/scenario_checkpoint.py (restore), src/engine/scenario_runtime.py (_build_kernel)
- tests/integration/scenarios/test_scenario_runtime_service.py

## Assumptions / Open Questions
- rpg-planner ruled 2026-11-10 (read on origin/main cf27795cb). (a) The governor is a gap, but it doesn't change authoritative state today: nothing sheds work in the scheduler, the executor is sequential, and replay is off on both paths. The only difference is mode telemetry, plus the dropped scenario_event_recorder. (b) No concurrent executor on restore. The follow-on is TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER (rpg, P3 hotfix); its ACs remove this ticket's strict xfail when it lands. If it lands first, the governor/recorder row is a plain assert from the start.
- Slot: the first gap after rpg-planner's current batch (hardening, hit-wake, child 2's cells, A+B). It's light: no measurement, scoped tests only. rpg-planner names the exact slot.
- The per-tick proof digest is reachable from a running service without a src/ change, the way the existing :379 test reads it. If it isn't, stop and tell testing-planner.
- The world compile and the run fit the slow lane's memory budget (large: 600 s, 8 GB per test). If not, `extra_slow` it is, and its CI home is decided at review.

## Implementation Notes
(implementer)

## Test Summary
(implementer)

## Files Changed
(implementer)

## Completion Summary
(implementer)
