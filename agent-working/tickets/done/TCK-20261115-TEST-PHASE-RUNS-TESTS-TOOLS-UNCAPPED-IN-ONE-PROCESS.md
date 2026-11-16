---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS
phase: done
date: 2026-11-15
tags: [ai, testing]
---

# TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS

## Title
implement-ticket's Test phase runs the whole of tests/tools in one uncapped process, so on a loaded host the pipeline reports memory failures as test failures.

## Status
DONE

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
1. [x] Read the evidence first: the vehicle's Test Summary, the capped confirmation run's outcome for the 64 node ids, and the run's backup in `/data/vboxuser/aw-native-pass2/`. Record in investigation.md whether the 57 failures and 7 errors were environmental.
2. [x] Make the Test phase's pytest run bounded on a shared host, without weakening the test-scope floor. The floor's directories still all run, and every test in them still runs. Candidate designs to weigh, not a decision:
   - the test-scoper wraps its command in the host's cap when one is configured, for example by an environment variable or a repo helper;
   - the floor's directories run as chunks, one process each, with the results summed;
   - the Test phase separates a run that died of the environment (ENOMEM, MemoryError INTERNALERROR, a killed process) from a test failure, and returns a distinct verdict rather than TESTS_FAILED.
   Pick by the evidence from item 1. Prefer the smallest change that keeps the verdict truthful.
3. [x] Apply the same rule to the hand-orchestrated path's guidance, for example `.claude/agents/test-scoper.md`, so a hand-run Test phase isn't treated differently.
4. [x] Tests for each piece of behaviour that changes.

## Out of Scope
- Changing which directories the floor requires, or the bare-directory rule.
- The host's overcommit settings or its swap. If the capped confirmation shows commit pressure, lead-planner's separate finding covers it.
- Any further native implement-ticket run (the owner: no more Workflow runs on this epic, #715 6894904885).

## Acceptance Criteria
1. [x] investigation.md states whether the 57 failures and 7 errors were environmental, citing the capped confirmation run.
2. [x] The Test phase's pytest is bounded in memory, CPU, or both on a host that sets a cap, or its failure is labelled environmental. A test shows the chosen behaviour.
3. [x] The test-scope floor gate still rejects a command that leaves out a required directory, shown by its existing tests passing unchanged.
4. [x] An environment-caused failure is never reported as TESTS_FAILED without being labelled, or the ticket states why the chosen design makes that impossible.

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
Hand-orchestrated (the owner allows no Workflow runs, #715 6894904885), dispatched under #715 6908488337 on design C ruled by agent-working-planner.

- `registries/session_test_caps.yaml`: per-host numbers, ubuntu 3G / swap 0 / CPUs 4-5 / MemAvailable floor 3 GB, u24desktop 2.5G / swap 0 / CPUs 4-5 / floor 3 GB (#715 6908508876), `max_tests_per_chunk` 700 on both. A host with no entry runs unwrapped. The file was first named `host_test_caps.yaml` with an owns line in `session_roles.yaml`; that line took four agent-working role cards 1-5 tokens over `CARD_BUDGET_TOKENS` (456). The owner chose the rename so the existing `registries/session_*.yaml` glob owns it (#715 6908596463); no card changed.
- `tools/delivery/host_test_caps.py`: the loader. Host key is `host_names[hostname]` from `registries/session_project.yaml`, else the raw hostname; `RPG_TEST_CAP_*` env overrides.
- `tools/delivery/capped_pytest.py`: takes the same bare directories the floor requires; `--collect-only` under the cap, chunks of whole test files in sorted order packed up to `max_tests_per_chunk`, each chunk under `systemd-run --user --scope -p MemoryMax -p MemorySwapMax` with `taskset`, a MemAvailable floor check before each chunk (a miss is an environment failure, never a wait loop), summed counts, an environment classification anchored to how a death really appears (`OSError: [Errno 12] Cannot allocate memory`, `INTERNALERROR>` with `MemoryError`, `E   MemoryError`, a bare `Killed` line, exit 137/-9; case-sensitive, so a failing test that only mentions those words stays a test failure), no retry, `passed` requiring every chunk to have passed (a chunk that failed without a summary line adds an error entry naming it), one `CAPPED_PYTEST_RESULT:` JSON line. Exit 0 / 1 / 2 / 3.
- Gate: `check_capped_runner` in `test_scope_coverage_static.py`, reached through an optional `runner_policy` argument, so the floor's existing results are unchanged when no cap applies. `gate_cli test_scope` passes the loaded cap.
- `implement-ticket.js` (reviewed by agent-working-planner before commit): optional `environment_failure` and `environment_note` in `TEST_SCHEMA`, two prompt sentences, and a branch before the `Test:passed` row that returns `TESTS_ENVIRONMENT_FAILED` recording only `Test:environment`. `environment_failure` takes precedence over `passed`. The planner's rulings: enforcement included, config in `registries/`, chunks sized from a `--collect-only` count.
- `TESTS_ENVIRONMENT_FAILED` added wherever the old status is listed: the orchestration contract (`terminal-statuses.yaml`, `gate-policy.yaml`, the re-rendered adapter), `gate_policy_extractor`, the replay sampler, the schema and workflow docs, and the pinned counts in four tests. Prose and fixtures describing the real-failure path are unchanged.
- `.claude/agents/test-scoper.md` and `docs/guides/testing.md` carry the hand-path guidance.
- Review fixes by agent-working-planner on db5d44a7b: the false pass on a summary-less failure, the over-loose environment text, the wording when real failures came with an environment death, and flags that take a value (`VALUE_FLAGS`; other flags must be value-free or `--flag=value`).

## Test Summary
- Scoped, repo `.venv` python, `-n 0`: `tests/tools/test_host_test_caps.py test_capped_pytest.py test_test_scope_capped_runner_gate.py test_test_phase_environment_verdict.py test_test_scope_coverage_static.py test_session_cards.py test_gate_cli.py tests/agent_orchestration tests/agent_orchestration_claude_adapter tests/agent_replay`: 325 passed (before the gate-policy additions); the three agent_orchestration directories alone gave 154 passed after them, and the environment-verdict file 8 passed.
- `test_test_scope_coverage_static.py` passes unchanged (AC3): the floor's directories and the bare-directory rule are untouched.
- Real run of the helper on this host: `python3 -m tools.delivery.capped_pytest tests/tools/test_host_test_caps.py tests/tools/test_test_scope_coverage_static.py -m "not slow and not extra_slow"` ran one chunk under `systemd-run` (3G, CPUs 4-5), 44 passed, `environment_failure` false.
- Cards: `test_session_cards.py` passes with the final `registries/` (the first attempt failed the token budget; see Implementation Notes).
- Positive control for the environment patterns, on real output: the Test agent's pytest output kept in `wf_f48f4fae-569`'s transcript (only a 1,175-character excerpt of a 99-test rerun survives, not the full 57 failures and 7 errors, which is a stated gap). It shows `/usr/lib/python3.13/subprocess.py:1801: OSError: [Errno 12] Cannot allocate memory: '/usr/bin/python3'` three times, so the real text does have the errno form. `is_environment_failure` matches it (3 matches), and does not match the real failure's lines (`test_no_live_code_names_a_moved_root`, `tests/tools/test_knowledge_index_staleness.py:160: 'knowledge-index'`). Three tests in that excerpt (`test_ticket_field_values.py` CLI tests) hit the ENOMEM and one (the paths guard) was the real failure.
- No full `tests/tools` run was made (it needs the lead's per-run go); CI runs it.

## Files Changed
- registries/session_test_caps.yaml (new)
- tools/delivery/host_test_caps.py, tools/delivery/capped_pytest.py (new)
- tools/gate_checks/test_scope_coverage_static.py, tools/gate_checks/gate_cli.py
- .claude/workflows/implement-ticket.js, .claude/agents/test-scoper.md
- agent-working/agent-orchestration/terminal-statuses.yaml, gate-policy.yaml, rendered/claude-adapter.yaml
- tools/agent_orchestration_claude_adapter/gate_policy_extractor.py, tools/agent_replay/sampler.py
- docs/agent-monitoring/schema.md, docs/ai/workflows.md, docs/ai/ticket-lifecycle.md, docs/ai/system_overview.md, docs/guides/testing.md
- tests: test_host_test_caps.py, test_capped_pytest.py, test_test_scope_capped_runner_gate.py, test_test_phase_environment_verdict.py (new); count pins in test_contract_structure.py, test_terminal_status_extractor.py, test_terminal_status_schema.py, test_generator_containment.py
- agent-working/tickets/done/ (this ticket), agent-working/stored_artifacts/ (artifacts)

## Completion Summary
The implement-ticket Test phase is bounded and truthful on a host that sets a cap. `tools/delivery/capped_pytest.py` runs the required bare directories in deterministic chunks under the host's memory and CPU cap, reads the numbers from `registries/session_test_caps.yaml`, and reports a run killed by the environment as `environment_failure`; the workflow returns `TESTS_ENVIRONMENT_FAILED` for it, ahead of any `Test:passed` row, and `test_scope_coverage` rejects a command that skips the helper on a capped host. A host with no entry is unchanged.

Known gap: the helper is only enforced on the pipeline path through the gate and the prompt; a hand-run Test phase relies on `test-scoper.md` and `docs/guides/testing.md`. Nothing yet stops a person running raw `pytest tests/tools/` on a capped host.

Known gap: no native pipeline run has exercised the new branch, because the owner allows no more Workflow runs; it is pinned by static source tests only.

Known gap: `max_tests_per_chunk` is 700 on both hosts (owner-approved with the file, #715 6908555025). The planner's capped run fit about 1,000 tests a chunk under 3G, so it is a conservative starting value, not a measured limit.
