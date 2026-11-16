---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS
phase: open
date: 2026-11-15
tags: [ai, testing]
---

# TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS

## Title
implement-ticket's Test phase runs the whole of tests/tools in one uncapped process, so on a loaded host the pipeline reports memory failures as test failures.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed by agent-working-planner on 2026-11-15, by the owner's decision (#715 6894904885). It was found in the native implement-ticket pass re-run `wf_f48f4fae-569`, on vehicle TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT, on host ubuntu.

The vehicle changed two flat `tools/*.py` files. The test-scope floor (`tools/gate_checks/test_scope_coverage_static.py::expected_test_dirs_for`, plus the bare-directory rule from TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE) therefore required the bare `tests/tools/` directory. The test-scoper agent ran `python3 -m pytest tests/tools/ -m "not slow and not extra_slow" -q --tb=line -rf -p no:cacheprovider`. That is one process, with no `-n`, no memory cap and no CPU pinning. The Test phase took most of the run's 48.5 min.

The result had 1 real failure, the vehicle's own defect. It also had 57 failures and 7 errors reported as `OSError: Cannot allocate memory` in subprocesses, plus one pytest `MemoryError` INTERNALERROR on a first attempt. The run ended TESTS_FAILED.

A 5 s MemAvailable watcher never saw less than 3.71 GB. Read on the host just before the run ended (agent-working-planner, read-only): `vm.overcommit_memory=0`, `Committed_AS` 13.59 GB over a `CommitLimit` of 13.48 GB, MemTotal 9.7 GB. The memory-failure cause is a hypothesis (fork refusals under commit pressure, or spikes between samples), not a finding. The capped confirmation run, recorded in the vehicle's Test Summary, decides it.

Both outcomes harm the pipeline. If the failures are environmental, the pipeline turns host memory pressure into TESTS_FAILED, the gate verdict that tells the implementer its code is wrong. If they are not, an uncapped full-directory run is still the heavy, unslotted run the host rules forbid (lead-planner, 2026-11-08: heavy runs need a per-run go, under `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`, with tests/tools chunked).

## Scope
1. Read the evidence first: the vehicle's Test Summary, the capped confirmation run's outcome for the 64 node ids, and the run's backup in `/data/vboxuser/aw-native-pass2/`. Record in investigation.md whether the 57 failures and 7 errors were environmental.
2. Make the Test phase's pytest run bounded on a shared host, without weakening the test-scope floor. The floor's directories still all run, and every test in them still runs. Candidate designs to weigh, not a decision:
   - the test-scoper wraps its command in the host's cap when one is configured, for example by an environment variable or a repo helper;
   - the floor's directories run as chunks, one process each, with the results summed;
   - the Test phase separates a run that died of the environment (ENOMEM, MemoryError INTERNALERROR, a killed process) from a test failure, and returns a distinct verdict rather than TESTS_FAILED.
   Pick by the evidence from item 1. Prefer the smallest change that keeps the verdict truthful.
3. Apply the same rule to the hand-orchestrated path's guidance, for example `.claude/agents/test-scoper.md`, so a hand-run Test phase isn't treated differently.
4. Tests for each piece of behaviour that changes.

## Out of Scope
- Changing which directories the floor requires, or the bare-directory rule.
- The host's overcommit settings or its swap. If the capped confirmation shows commit pressure, lead-planner's separate finding covers it.
- Any further native implement-ticket run (the owner: no more Workflow runs on this epic, #715 6894904885).

## Acceptance Criteria
1. investigation.md states whether the 57 failures and 7 errors were environmental, citing the capped confirmation run.
2. The Test phase's pytest is bounded in memory, CPU, or both on a host that sets a cap, or its failure is labelled environmental. A test shows the chosen behaviour.
3. The test-scope floor gate still rejects a command that leaves out a required directory, shown by its existing tests passing unchanged.
4. An environment-caused failure is never reported as TESTS_FAILED without being labelled, or the ticket states why the chosen design makes that impossible.

## Related Tickets
- TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT (the run that found it)
- TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN (run evidence)
- TCK-20260831-HOTFIX-TEST-SCOPER-BARE-DIRECTORY-RULE (the bare-directory rule)

## Related Docs
- docs/guides/delivery_process.md ("CI Failure Triage")

## Related Stored Artifacts
- none (run backup outside the repo: /data/vboxuser/aw-native-pass2/)

## Related Code Areas
- .claude/workflows/implement-ticket.js (Test phase, test-scope gate)
- .claude/agents/test-scoper.md
- tools/gate_checks/test_scope_coverage_static.py

## Assumptions / Open Questions
- The cap's values belong to the host and lead-planner, so the design reads them from configuration rather than hardcoding 3G.
- CI runs tests/tools in its own chunked jobs; this ticket changes only the pipeline's local Test phase.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
