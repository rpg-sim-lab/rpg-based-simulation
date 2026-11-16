"""Static pins for the Test phase's environment verdict in implement-ticket.js and test-scoper.md
(TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS).

Raw-source-text tests, like tests/tools/test_perf_tag_test_scoper_wiring.py: implement-ticket.js is never executed and no
JS test runner exists for .claude/workflows/*.js.
"""
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
_JS = (_REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js").read_text(encoding="utf-8")
_SCOPER = (_REPO_ROOT / ".claude" / "agents" / "test-scoper.md").read_text(encoding="utf-8")


def _schema_block() -> str:
    start = _JS.index("const TEST_SCHEMA = {")
    return _JS[start:_JS.index("\n}\n", start)]


def test_the_test_schema_carries_an_optional_environment_flag_and_note():
    block = _schema_block()
    assert "environment_failure: { type: 'boolean'" in block and "environment_note: { type: 'string'" in block
    required = re.search(r"required: \[([^\]]*)\]", block).group(1)
    assert "environment_failure" not in required and "environment_note" not in required


def test_an_environment_failure_returns_its_own_verdict_before_any_test_passed_row():
    branch = _JS.index("if (testResult.environment_failure) {")
    passed_row = _JS.index("pushGate('Test:passed'")
    assert branch < passed_row < _JS.index("if (!testResult.passed) {")
    body = _JS[branch:passed_row]
    assert "pushGate('Test:environment'" in body
    assert "writeMonitoring('TESTS_ENVIRONMENT_FAILED')" in body
    assert "status: 'TESTS_ENVIRONMENT_FAILED'" in body
    assert "Test:passed" not in body and "TESTS_FAILED" not in body


def test_environment_failure_takes_precedence_over_passed_and_the_comment_says_so():
    comment = _JS[_JS.rindex("// A run that died of the environment", 0, _JS.index("if (testResult.environment_failure) {")):
                  _JS.index("if (testResult.environment_failure) {")]
    assert "takes precedence over `passed`" in comment and "a chunk that died never counts as a pass" in comment
    # The branch tests the flag alone, never `passed && ...`, so a true `passed` cannot hide it.
    assert re.search(r"if \(testResult\.environment_failure\) \{", _JS)
    assert "testResult.passed && testResult.environment_failure" not in _JS


def test_a_real_test_failure_still_returns_tests_failed():
    tail = _JS[_JS.index("if (!testResult.passed) {"):]
    assert "await writeMonitoring('TESTS_FAILED')" in tail.split("pushEvent('Test', 'test-scoper', 'ok'")[0]
    assert "status: 'TESTS_FAILED'" in tail


def test_the_prompt_sends_a_capped_host_through_the_helper_and_asks_for_the_flag():
    assert "python3 -m tools.delivery.host_test_caps" in _JS
    assert "python3 -m tools.delivery.capped_pytest" in _JS
    assert "Set environment_failure=true" in _JS


def test_the_floor_still_requires_bare_directories_in_the_prompt():
    assert "as a bare, whole directory path" in _JS and "never a specific file" in _JS


def test_the_hand_run_guidance_matches_the_pipeline():
    assert "## Hosts that set a Test-phase cap" in _SCOPER
    assert "python3 -m tools.delivery.capped_pytest" in _SCOPER
    assert "environment_failure: true" in _SCOPER and "Never\nretry" in _SCOPER


def test_the_gate_policy_vocabulary_and_contract_list_the_environment_gate():
    from tools.agent_orchestration_claude_adapter.gate_policy_extractor import (
        count_agent_result_field_call_sites,
        extract_agent_result_field_gates,
    )

    gates = {g["result_field"]: g for g in extract_agent_result_field_gates() if g["phase"] == "Test"}
    assert gates["environment_failure"]["on_fail_status"] == ["TESTS_ENVIRONMENT_FAILED"]
    assert gates["passed"]["on_fail_status"] == ["TESTS_FAILED"]
    counts = count_agent_result_field_call_sites(_REPO_ROOT / ".claude" / "workflows" / "implement-ticket.js")
    assert counts["environment_failure"] == 1 and counts["passed"] >= 1


def test_the_environment_message_says_when_real_failures_came_with_it():
    branch = _JS[_JS.index("if (testResult.environment_failure) {"):_JS.index("pushGate('Test:passed'")]
    assert "other test(s) also failed and are listed in failed_tests: read them before re-running." in branch
    assert "died of the environment (memory or a killed process), not because a test failed." in branch
