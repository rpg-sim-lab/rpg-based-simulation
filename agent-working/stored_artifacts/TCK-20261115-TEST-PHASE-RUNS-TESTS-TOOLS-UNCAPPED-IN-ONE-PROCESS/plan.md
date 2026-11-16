---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Implementation Plan — TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS

Design C, ruled by agent-working-planner; the owner dispatched it (#715 6908488337). Hand-orchestrated: the owner allows no Workflow runs (6894904885).

1. `registries/session_test_caps.yaml`: per-host cap numbers (ubuntu 3G / swap 0 / CPUs 4-5 / MemAvailable floor 3 GB; u24desktop 2.5G, #715 6908508876). Named and owned through the `registries/session_*.yaml` glob (#715 6908596463). A host with no entry runs unwrapped.
2. `tools/delivery/host_test_caps.py`: the loader. Host key is `host_names[hostname]` from `registries/session_project.yaml`, else the raw hostname. Env overrides per run.
3. `tools/delivery/capped_pytest.py`: collect-only, chunk by sorted test file up to `max_tests_per_chunk`, run each chunk under `systemd-run … taskset`, MemAvailable floor per chunk, summed counts, environment classification, never a retry, one `CAPPED_PYTEST_RESULT:` JSON line. Exit 0 / 1 / 2 / 3.
4. Gate: `test_scope_coverage_static.check_capped_runner`, reached through an optional `runner_policy` argument of `check_test_scope_coverage`; `gate_cli test_scope` passes the loaded cap. No cap means no extra result, so the floor's existing tests are unchanged.
5. `implement-ticket.js`: an optional `environment_failure` / `environment_note` in `TEST_SCHEMA`, two prompt sentences, and a branch BEFORE the `Test:passed` row that returns `TESTS_ENVIRONMENT_FAILED` and records only `Test:environment_failure`. `environment_failure` wins even when `passed` is true. Reviewed by agent-working-planner before commit.
6. `.claude/agents/test-scoper.md`: a section for hosts that set a cap (the hand-run path).
7. The new terminal status wherever the old one is listed: the orchestration contract and its rendered adapter, the replay sampler, the schema and workflow docs, and the pinned counts.
8. Tests: loader (hostname pin), helper with a fake runner, the gate, and a static pin of the workflow branch.

Out of scope: which directories the floor requires, the bare-directory rule, the host's overcommit or swap, any native run.
