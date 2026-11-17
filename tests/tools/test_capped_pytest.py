"""tools/delivery/capped_pytest.py with a fake runner: no real systemd-run, no real pytest
(TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS)."""

import json

import pytest

from tools.delivery import capped_pytest as cp
from tools.delivery.host_test_caps import HostCap

CAP = HostCap("fakehost", "3G", "0", "4-5", 3.0, 3)
COLLECT = "\n".join(
    ["tests/tools/test_a.py::t%d" % i for i in range(2)]
    + ["tests/tools/test_b.py::t%d" % i for i in range(2)]
    + ["tests/tools/test_c.py::t0"]
    + ["", "5 tests collected in 0.1s"]
)


class FakeRun:
    """Answers collect-only with COLLECT; answers a chunk from `chunk_outputs` keyed by its first test file."""

    def __init__(self, chunk_outputs=None, collect=(0, COLLECT)):
        self.calls: list[list[str]] = []
        self.chunk_outputs = chunk_outputs or {}
        self.collect = collect

    def __call__(self, cmd):
        self.calls.append(cmd)
        if "--collect-only" in cmd:
            return self.collect
        first = next(a for a in cmd if a.endswith(".py") and a.startswith("tests/"))
        return self.chunk_outputs.get(first, (0, "2 passed in 0.1s"))


def _run(fake, mem=lambda: 6.0, cap=CAP):
    return cp.run_capped(["tests/tools/"], ["-m", "not slow"], cap, fake, mem)


def test_targets_are_the_existing_paths_and_everything_else_goes_to_pytest(tmp_path, monkeypatch):
    (tmp_path / "tests" / "tools").mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    targets, passthrough = cp.split_args(["tests/tools/", "-m", "not slow", "-q"])
    assert targets == ["tests/tools/"] and passthrough == ["-m", "not slow", "-q"]


def test_chunks_are_whole_files_in_sorted_order_packed_up_to_the_cap():
    counts = {"c.py": 1, "a.py": 2, "b.py": 2, "huge.py": 9}
    assert cp.plan_chunks(counts, 3) == [["a.py"], ["b.py", "c.py"], ["huge.py"]]
    assert cp.plan_chunks(counts, 3) == cp.plan_chunks(dict(reversed(list(counts.items()))), 3)
    assert cp.plan_chunks({}, 3) == []


def test_counts_are_summed_across_chunks_and_every_chunk_runs_under_the_cap():
    fake = FakeRun()
    result = _run(fake)
    assert result["mode"] == "capped" and result["host"] == "fakehost"
    assert len(result["chunks"]) == 2  # a+b (4 tests) would exceed 3, so a / b+c ... see assertion below
    assert result["pass_count"] == 2 * len(result["chunks"])
    assert result["passed"] is True and result["environment_failure"] is False
    for cmd in fake.calls:
        assert cmd[:4] == ["systemd-run", "--user", "--scope", "-q"]
        assert "MemoryMax=3G" in cmd and "MemorySwapMax=0" in cmd and cmd[cmd.index("taskset") + 2] == "4-5"


def test_a_test_failure_is_a_failure_not_an_environment_failure():
    fake = FakeRun({"tests/tools/test_a.py": (1, "FAILED tests/tools/test_a.py::t1 - assert 0\n1 failed, 1 passed in 0.2s")})
    result = _run(fake)
    assert result["passed"] is False and result["environment_failure"] is False
    assert result["fail_count"] == 1 and result["failed_tests"] == ["tests/tools/test_a.py::t1"]


@pytest.mark.parametrize(
    "returncode,text",
    [(1, "tests/x.py:9: OSError: [Errno 12] Cannot allocate memory"), (1, "INTERNALERROR> MemoryError"), (137, ""), (-9, ""), (1, "Killed\n"), (1, "E   MemoryError")],
)
def test_a_chunk_that_dies_of_the_environment_is_named_and_never_retried(returncode, text):
    fake = FakeRun({"tests/tools/test_a.py": (returncode, text)})
    result = _run(fake)
    assert result["environment_failure"] is True and result["passed"] is False
    assert "chunk 1/" in result["environment_note"] and "later chunks not run" in result["environment_note"]
    assert [c["status"] for c in result["chunks"]] == ["environment"]
    chunk_runs = [c for c in fake.calls if "--collect-only" not in c]
    assert len(chunk_runs) == 1  # no retry, and the next chunk is not started


def test_memavailable_below_the_floor_is_an_environment_failure_not_a_wait():
    fake = FakeRun()
    result = _run(fake, mem=lambda: 2.0)
    assert result["environment_failure"] is True and "2.00 GB is below the 3 GB floor" in result["environment_note"]
    assert [c for c in fake.calls if "--collect-only" not in c] == []


def test_a_collection_step_that_dies_of_the_environment_is_labelled():
    result = _run(FakeRun(collect=(1, "INTERNALERROR> MemoryError")))
    assert result["environment_failure"] is True and result["chunks"][0]["name"] == "collect"


def test_a_collection_error_is_a_failure_not_an_environment_failure():
    result = _run(FakeRun(collect=(2, "ERROR collecting tests/tools/test_a.py\nImportError")))
    assert result["environment_failure"] is False and result["passed"] is False and result["error_count"] == 1


def test_a_host_with_no_cap_runs_pytest_once_unwrapped(monkeypatch, capsys):
    monkeypatch.setattr(cp, "load_cap", lambda root: None)
    fake = FakeRun(chunk_outputs={})
    calls = []

    def run(cmd):
        calls.append(cmd)
        return 0, "7 passed in 1.0s"

    assert cp.main(["tests/tools/", "-m", "not slow"], run) == cp.EXIT_PASS
    assert len(calls) == 1 and "systemd-run" not in calls[0] and "tests/tools/" in calls[0]
    payload = json.loads(capsys.readouterr().out.split(cp.RESULT_MARKER)[1])
    assert payload["mode"] == "unwrapped" and payload["pass_count"] == 7
    assert fake.calls == []


def test_main_exit_codes_separate_failure_from_environment(monkeypatch, capsys):
    monkeypatch.setattr(cp, "load_cap", lambda root: None)
    assert cp.main(["tests/tools/"], lambda c: (1, "1 failed in 0.1s")) == cp.EXIT_FAIL
    assert cp.main(["tests/tools/"], lambda c: (1, "x.py:1: OSError: [Errno 12] Cannot allocate memory")) == cp.EXIT_ENVIRONMENT
    assert cp.main(["-q"], lambda c: (0, "")) == cp.EXIT_USAGE
    capsys.readouterr()


def test_summary_line_parsing():
    assert cp.parse_counts("x\n1 failed, 832 passed, 19 skipped, 28 deselected in 91.94s (0:01:31)") == {
        "passed": 832, "failed": 1, "errors": 0, "skipped": 19,
    }
    assert cp.parse_counts("2 errors in 0.5s")["errors"] == 2
    assert cp.parse_counts("no summary here") == {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}


def test_a_chunk_that_fails_without_a_summary_line_is_never_a_pass():
    fake = FakeRun({"tests/tools/test_a.py": (3, "INTERNALERROR> Traceback (most recent call last):\nINTERNALERROR> ValueError: boom")})
    result = _run(fake)
    assert result["passed"] is False and result["environment_failure"] is False
    assert result["error_count"] == 1 and "chunk 1/2 (rc 3, no failures parsed)" in result["failed_tests"]


def test_the_unwrapped_path_does_not_pass_on_a_failure_without_a_summary_either(monkeypatch, capsys):
    monkeypatch.setattr(cp, "load_cap", lambda root: None)
    assert cp.main(["tests/tools/"], lambda c: (2, "usage: pytest [options]\nerror: unrecognized arguments")) == cp.EXIT_FAIL
    assert cp.main(["tests/tools/"], lambda c: (3, "INTERNALERROR> ValueError: boom")) == cp.EXIT_FAIL
    capsys.readouterr()


def test_a_real_failure_that_only_mentions_a_memory_message_is_a_test_failure():
    out = (
        "FAILED tests/x.py::test_enomem_message - AssertionError: 'Cannot allocate memory' != 'x'\n"
        "tests/x.py:7: AssertionError: assert 'MemoryError' in 'ok'\n1 failed, 3 passed in 0.4s"
    )
    result = _run(FakeRun({"tests/tools/test_a.py": (1, out)}))
    assert result["environment_failure"] is False and result["passed"] is False and result["fail_count"] == 1
    assert cp.is_environment_failure(1, out) is False
    assert cp.is_environment_failure(0, "test_memoryerror_in_the_parameter_id PASSED killed") is False


def test_an_environment_death_with_real_failures_says_so_in_the_note():
    out = "FAILED tests/tools/test_a.py::t1 - assert 0\n1 failed in 0.2s\nOSError: [Errno 12] Cannot allocate memory"
    result = _run(FakeRun({"tests/tools/test_a.py": (1, out)}))
    assert result["environment_failure"] is True
    assert "1 other test(s) also failed and are listed in failed_tests: read them before re-running" in result["environment_note"]
    assert result["failed_tests"] == ["tests/tools/test_a.py::t1"]


def test_a_value_after_a_value_taking_flag_is_never_a_target(tmp_path, monkeypatch):
    for name in ("tests", "pytest.ini"):
        (tmp_path / name).mkdir() if name == "tests" else (tmp_path / name).write_text("")
    monkeypatch.chdir(tmp_path)
    targets, passthrough = cp.split_args(["-c", "pytest.ini", "tests", "--rootdir", ".", "--ignore", "tests", "-m", "x"])
    assert targets == ["tests"]
    assert passthrough == ["-c", "pytest.ini", "--rootdir", ".", "--ignore", "tests", "-m", "x"]


def test_a_clean_collect_listing_that_quotes_the_signatures_in_a_parameter_id_is_not_an_environment_failure():
    """The helper run over its own test file: collect-only lists ids like `test_x[1-tests/x.py:9: OSError: [Errno 12] ...]`."""
    listing = COLLECT + "\ntests/tools/test_a.py::test_dies[1-tests/x.py:9: OSError: [Errno 12] Cannot allocate memory]\n"
    assert cp.is_environment_failure(0, listing) is False
    result = _run(FakeRun(collect=(0, listing)))
    assert result["environment_failure"] is False and result["passed"] is True


def test_a_failed_summary_line_that_names_a_signature_in_its_id_is_a_test_failure():
    out = ("FAILED tests/x.py::test_a[OSError: [Errno 12] Cannot allocate memory] - assert 0\n"
           "ERROR tests/x.py::test_b[INTERNALERROR> MemoryError]\n1 failed, 1 error in 0.3s")
    assert cp.is_environment_failure(1, out) is False
