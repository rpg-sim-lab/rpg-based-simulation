"""The test-scope gate on a host that sets a Test-phase cap (TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS)."""
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from gate_checks.test_scope_coverage_static import check_capped_runner, check_test_scope_coverage  # noqa: E402
from tools.delivery.host_test_caps import HostCap  # noqa: E402

CAP = HostCap("fakehost", "3G", "0", "4-5", 3.0, 700)
FILES = ["tools/knowledge_search.py"]
BARE = "python3 -m pytest tests/tools/ -m 'not slow' -q"
HELPER = "python3 -m tools.delivery.capped_pytest tests/tools/ -m 'not slow' -q"


def _status(results, condition):
    return next(r["status"] for r in results if r["condition"] == condition)


def test_with_no_cap_the_results_are_exactly_what_they_were():
    assert check_test_scope_coverage(FILES, BARE) == check_test_scope_coverage(FILES, BARE, None)
    assert check_capped_runner(BARE, None) == []
    assert [r["condition"] for r in check_test_scope_coverage(FILES, BARE)] == ["test_scope_covers:tests/tools/"]


def test_a_capped_host_rejects_a_command_that_skips_the_helper_with_a_named_reason():
    results = check_test_scope_coverage(FILES, BARE, CAP)
    assert _status(results, "test_runs_through_capped_helper") == "FAIL"
    evidence = next(r["evidence"] for r in results if r["condition"] == "test_runs_through_capped_helper")
    assert "fakehost" in evidence and "tools/delivery/capped_pytest.py" in evidence


@pytest.mark.parametrize("command", [HELPER, "python3 tools/delivery/capped_pytest.py tests/tools/ -q"])
def test_a_capped_host_accepts_either_spelling_of_the_helper(command):
    results = check_test_scope_coverage(FILES, command, CAP)
    assert _status(results, "test_runs_through_capped_helper") == "PASS"
    assert _status(results, "test_scope_covers:tests/tools/") == "PASS"


def test_the_floor_is_still_enforced_when_the_helper_is_used():
    results = check_test_scope_coverage(FILES, "python3 -m tools.delivery.capped_pytest tests/tools/test_one.py", CAP)
    assert _status(results, "test_scope_covers:tests/tools/") == "FAIL"
    assert _status(results, "test_runs_through_capped_helper") == "PASS"
