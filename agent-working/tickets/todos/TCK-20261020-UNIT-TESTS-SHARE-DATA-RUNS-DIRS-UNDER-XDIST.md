---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST
phase: open
date: 2026-10-20
tags: []
---

# TCK-20261020-UNIT-TESTS-SHARE-DATA-RUNS-DIRS-UNDER-XDIST

## Title
Unit tests that write fixed data/runs dirs fail under pytest-xdist because another worker removes the dir underneath them

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
rpg-implementer-2 found this on 2026-10-20 while checking rpg-pre-v1-fixes. It already exists on origin/main e52719485: 3 repeats of `-n 2 --dist loadgroup` on 4 files, on main and on the branch.
- `tests/unit/engine/test_run_manifest_signal_contract.py::test_a_live_run_and_an_audit_run_say_so` fails every time. The log shows `QualityPersistence.write_report: failed to write ... data/runs/sc_manifest_live/quality_report.json.tmp: No such file`. The test uses the fixed run ids `sc_manifest_canonical`, `sc_manifest_live` and `sc_manifest_audit` under the shared `data/runs`.
- Setup ERRORs that move between runs: `tests/unit/worldmodules/test_schema_unified.py::test_worldmodulespec_accepts_any_schema_version_string` on the branch, and the rpg_gate_harness hash test on main.
- The testing-owned `tests/unit/tools/test_rpg_gate_harness.py` globs `data/runs/rpg-gate-sandbox_world-s1-*`. It is routed to testing-planner and is out of scope here.
All of these pass when run serially, and CI's unit-infra lane passes.

## Scope
- Find which test removes the shared `data/runs` dirs while another worker is using them.
- Give the rpg-owned tests a per-test run root (a tmp_path or a worker-unique run id) or an xdist_group, so the full unit suite passes under `-n 2`.
- Explain the `test_schema_unified` setup error, or fix it.

## Out of Scope
- tests/unit/tools/test_rpg_gate_harness.py (testing-planner).
- Changing CI lane parallelism.

## Acceptance Criteria
- `pytest tests/unit -n 2` gives 0 failures and 0 errors on 3 repeats.
- No test writes a fixed id under the shared data/runs without isolation.

## Related Tickets
- TCK-20261020-CI-LANES-RUN-TRAILING-BACKSLASH-AND-XDIST (agent-working)

## Related Docs
- docs/testing/test_taxonomy.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/unit/engine/test_run_manifest_signal_contract.py
- tests/unit/worldmodules/test_schema_unified.py
- src/observability quality persistence (`QualityPersistence.write_report`)

## Assumptions / Open Questions
- Which test does the removing is still a guess (another worker's data/runs cleanup).

## Implementation Notes
After v1. Not a blocker.

## Test Summary

## Files Changed

## Completion Summary
