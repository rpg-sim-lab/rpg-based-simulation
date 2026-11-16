---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test Plan — TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS

## Regression Surface
- `tools/gate_checks/test_scope_coverage_static.py` and `gate_cli test_scope`: the floor's directories and the bare-directory rule must be unchanged (`tests/tools/test_test_scope_coverage_static.py` passes unchanged).
- The terminal-status contract and its pinned counts: `tests/agent_orchestration/`, `tests/agent_orchestration_claude_adapter/`, `tests/agent_replay/`.
- The role cards' token budget (`tests/tools/test_session_cards.py`) when `registries/` gains a file.

## New Tests Required
`tests/tools/test_host_test_caps.py`, `test_capped_pytest.py`, `test_test_scope_capped_runner_gate.py`, `test_test_phase_environment_verdict.py`.

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1 | investigation | evidence | the vehicle's Test Summary and capped confirmation | the 57+7 were environmental | `investigation.md` |
| AC2 | unit | regression | ticket AC2; the rulings of agent-working-planner | a capped host chunks under the cap; a dead chunk is labelled | `pytest tests/tools/test_capped_pytest.py tests/tools/test_host_test_caps.py` |
| AC3 | unit | invariant | ticket AC3; `test_test_scope_coverage_static.py` | the floor gate still rejects a command that omits a required directory | `pytest tests/tools/test_test_scope_coverage_static.py tests/tools/test_test_scope_capped_runner_gate.py` |
| AC4 | static source pin | invariant | ticket AC4 | an environment failure returns `TESTS_ENVIRONMENT_FAILED` before any `Test:passed` row | `pytest tests/tools/test_test_phase_environment_verdict.py tests/agent_orchestration tests/agent_orchestration_claude_adapter tests/agent_replay` |

Negative cases: no cap entry runs unwrapped; a failing test is never an environment failure; no retry; MemAvailable below the floor stops without a wait loop.

## Scoped Pytest Commands
`pytest tests/tools/test_host_test_caps.py tests/tools/test_capped_pytest.py tests/tools/test_test_scope_capped_runner_gate.py tests/tools/test_test_phase_environment_verdict.py tests/tools/test_test_scope_coverage_static.py tests/tools/test_session_cards.py tests/agent_orchestration tests/agent_orchestration_claude_adapter tests/agent_replay -n 0`

## Anti-Drift Test Guards
The static pin on `implement-ticket.js` and the pinned terminal-status counts.
