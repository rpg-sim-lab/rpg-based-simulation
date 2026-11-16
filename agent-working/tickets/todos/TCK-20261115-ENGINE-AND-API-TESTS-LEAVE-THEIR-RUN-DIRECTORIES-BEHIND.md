---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261115-ENGINE-AND-API-TESTS-LEAVE-THEIR-RUN-DIRECTORIES-BEHIND
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-ENGINE-AND-API-TESTS-LEAVE-THEIR-RUN-DIRECTORIES-BEHIND

## Title
Tests in tests/integration/scenarios, tests/unit/engine and tests/api build real kernels under default run ids and leave every run directory in data/runs

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found during the restore-id hotfix's local test pass on 2026-11-15 (TCK-20261115-A-RESTORED-SCENARIO-SHARES-ONE-RUN-DIRECTORY-PER-SPEC; rpg-implementer-ubuntu, worktree rpg-ubuntu-restore at 943a3323b). Filed by rpg-planner-ubuntu at lead-planner's ask.

data/runs was empty before one serial pass of -m "not slow" over those three directories, and held 199 run dirs after it, read at 20:3x. 190 have default ids (run_<n>_<n>_<n>_<hash>). None of them is restored_*: the restore fix's own cleanup works.

Grouped by run_manifest.json scenario_name, read-only, and mapped to the test files that set that name on origin/main:

| scenario_name | dirs | test file |
|---|---|---|
| lodging | 50 | tests/unit/engine/lodging_kernel.py |
| PROD_SMALL | 34 | generic profile name; the producers are not yet narrowed |
| test_scenario | 26 | ScenarioRuntimeService runs on the test spec (tests/integration/scenarios/test_scenario_runtime_service.py and siblings) |
| differentiation-test | 26 | tests/integration/scenarios/test_entity_differentiation.py |
| test | 20 | generic; not yet narrowed |
| cli_default | 12 | tests/api/test_api_key_auth.py |
| proof_digest_test | 5 | tests/unit/engine/test_proof_digest_contract.py |
| digest_test | 5 | tests/unit/engine/test_kernel_digest_via_scheduler.py |
| auth-test | 5 | tests/api/test_api_key_auth.py |
| admission-test | 5 | tests/api/test_admission_control.py |
| PROD_DEFAULT | 4 | generic; not yet narrowed |
| information_seeking_wiring | 2 | tests/integration/scenarios/test_information_seeking_wiring.py |
| hunger-test | 2 | tests/integration/scenarios/test_hunger_satiation.py |
| test-force-full-scan-boot-* | 3 | tests/unit/engine/test_runtime_status.py |

Effects:
- every local run of these suites leaves about 200 dirs in a worktree's data/runs;
- CI runners are ephemeral, so CI isn't affected;
- the leftovers are mixed into the run data that sessions must clean by run id, and a session can't tell them from its own;
- deleting them needs an owner go, which repeats per run.

## Scope
1. Narrow the three generic names (PROD_SMALL, test, PROD_DEFAULT) to their producing tests, by a recording plugin over one serial run or by a read of the kernel-building helpers. Don't guess.
2. Per producer, the smallest fix that keeps the test's meaning:
   - give the kernel its own artifact dir under tmp_path, if the kernel or repo takes a base_dir;
   - or record the run id the kernel actually used (kernel._run_id) and remove exactly that dir after the test, with the opt-in pattern in tests/named_run_dirs.py (#926 and the restore-id hotfix).
   Never clean by glob or time window: a parallel worker's or another session's run must never be touched.
3. A guard test, or a conftest check, that asserts a suite run leaves no new data/runs entry it didn't name.

## Out of Scope
- Deleting the existing leftover dirs. That's the owner's delete list.
- tools/ and the sim measurement tools, which clean their own runs by run id (owner #715 6893767224).

## Acceptance Criteria
1. One serial -m "not slow" pass over the three directories leaves data/runs exactly as it found it.
2. The same under -n 2 --dist loadgroup.
3. No test's assertions change. No sim hash changes, since run ids are names only.

## Related Tickets
TCK-20261115-A-RESTORED-SCENARIO-SHARES-ONE-RUN-DIRECTORY-PER-SPEC; TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING (tests/named_run_dirs.py); TCK-20261115-AN-EXPLICIT-RUN-ID-DELETES-AN-EXISTING-RUN-DIRECTORY.

## Related Docs
docs/testing/test_taxonomy.md

## Related Stored Artifacts
None.

## Related Code Areas
tests/unit/engine/lodging_kernel.py; tests/api/test_api_key_auth.py; tests/api/test_admission_control.py; tests/integration/scenarios/; tests/named_run_dirs.py; src/observability/reporting/artifact_repository.py (base_dir)

## Assumptions / Open Questions
Q1: does RunArtifactRepository's base_dir reach Kernel construction in these tests? If so, a tmp_path base_dir is the simplest fix.

## Implementation Notes
Unscheduled; dispatch needs a go. Rides rpg-planner-ubuntu's next PR as a ticket filing.

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
