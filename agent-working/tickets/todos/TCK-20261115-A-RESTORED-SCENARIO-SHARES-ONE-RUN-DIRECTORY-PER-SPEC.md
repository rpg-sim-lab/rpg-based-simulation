---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20261115-A-RESTORED-SCENARIO-SHARES-ONE-RUN-DIRECTORY-PER-SPEC
phase: open
date: 2026-11-15
tags: [determinism]
---

# TCK-20261115-A-RESTORED-SCENARIO-SHARES-ONE-RUN-DIRECTORY-PER-SPEC

## Title
Every restore of one scenario spec builds its kernel under the same run id, so concurrent restores delete each other's run directory

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found on #926's CI (job 132779887252, -n auto --dist loadgroup), and relayed by platform-planner on 2026-11-15. Two tests in tests/integration/scenarios/test_scenario_runtime_service.py::TestCheckpointRestore failed at the same moment on two xdist workers:
- gw0: create_run(overwrite=True) rmtree hit "Directory not empty: data/runs/restored_test_scenario".
- gw1: "Manifest not found for run_id: restored_test_scenario".
#926's fresh CI at 6fc21dd12 was green. That is one green run, not proof the race is gone.

Root, checked on origin/main by rpg-planner-ubuntu:
- src/engine/scenario_checkpoint.py:110-116 builds the restored Kernel with `run_id=f"restored_{spec.id}"`.
- The explicit id is deliberate (comment at l.107-109): it suppresses the Domain.INIT RNG draw that would break restore determinism.
- So every restore of one spec shares data/runs/restored_<spec id>, which run_identity.create_run_directory replaces through create_run(overwrite=True), an rmtree followed by a create.
- It's a product bug too: two concurrent API restores of the same scenario (src/api/routes/scenarios.py:99) collide.

## Scope
1. A unique restore id that is still explicit, so no RNG draw comes back: `f"restored_{spec.id}_{os.getpid()}_{uuid.uuid4().hex[:8]}"`. uuid4 is not the simulation RNG, and the run id is a name only. I grepped: no src/, frontend/src or test reader parses the `restored_` text, and the API tests mock the restored service.
2. Tests that restore a real kernel remove that restore's run dir by its id (`svc._kernel._run_id`), never by glob or time window. Use the opt-in named-cleanup pattern from #926 (tests/named_run_dirs.py), or a direct removal by that id.
3. A test where two restores of one spec get two different run dirs, and neither removes the other's.

## Out of Scope
- The general explicit-id overwrite in run_identity (TCK-20261115-AN-EXPLICIT-RUN-ID-DELETES-AN-EXISTING-RUN-DIRECTORY).
- An xdist_group on the restore tests. That would hide the collision rather than fix it.

## Acceptance Criteria
1. The restore-determinism tests pass UNCHANGED: the same state seed and per-tick digest after restore, which proves no RNG draw came back.
2. Two restores of one spec use different run dirs.
3. The scoped tests pass with CI's flags (-n 2 --dist loadgroup) over tests/integration/scenarios, tests/unit/engine and tests/api, twice, with no restored_* dir left.
4. No simulation hash changes.

## Related Tickets
TCK-20261115-AN-EXPLICIT-RUN-ID-DELETES-AN-EXISTING-RUN-DIRECTORY; TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING (#926, where it surfaced).
- TCK-20261110-A-RESTORED-SCENARIO-DROPS-ITS-GOVERNOR-AND-EVENT-RECORDER (u24, P3 hotfix) is on the same restore path (scenario_checkpoint.py). It is NOT folded in: whichever lands second re-syncs on top (u24 rpg-planner's overlap check, 2026-11-15).
- TCK-20261110-A-RUN-RESTORED-FROM-A-CHECKPOINT-EQUALS-THE-UNINTERRUPTED-RUN-TICK-BY-TICK (testing) has a strict xfail citing the GOVERNOR ticket. Unique run ids should not move its hashes; testing re-checks the xfail reason after this fix lands, so tell testing-planner at merge.

## Related Docs
docs/engine/ (the restore contract, if one exists)

## Related Stored Artifacts
None.

## Related Code Areas
src/engine/scenario_checkpoint.py; src/engine/run_identity.py; tests/integration/scenarios/test_scenario_runtime_service.py

## Assumptions / Open Questions
- The owner paused src/engine work under both epics until after M1 (#715 6889952914). This fix is outside both epics, but dispatching it needs a go from lead or the owner.

## Implementation Notes
Implementer: rpg-implementer-ubuntu, once free; after #926 merges. Small: one line plus tests.

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
