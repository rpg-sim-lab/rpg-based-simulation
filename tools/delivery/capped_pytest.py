"""Run the Test phase's pytest in bounded chunks on a host that sets a cap, and say honestly when the environment killed it.

`python3 -m tools.delivery.capped_pytest tests/tools/ -m "not slow and not extra_slow"` takes the same bare test
directories the test-scope floor requires, plus ordinary pytest flags. It then:

1. reads this host's cap from `registries/session_test_caps.yaml` (`tools/delivery/host_test_caps.py`). A host with no
   entry runs pytest once, unwrapped, exactly as before;
2. collects with `--collect-only` (under the cap), groups whole test files in sorted order into chunks of at most
   `max_tests_per_chunk` collected tests, so the boundaries are deterministic and every collected test runs;
3. runs each chunk as its own process under `systemd-run --user --scope -p MemoryMax=... -p MemorySwapMax=... taskset -c ...`,
   checking `MemAvailable` against the floor first (below the floor is an environment failure, never a wait loop);
4. sums pass, fail and error counts across chunks, and names any chunk that died of the environment (`OSError: [Errno 12]
   Cannot allocate memory`, a `MemoryError` INTERNALERROR, a bare `Killed` line, a SIGKILL or exit 137). A run passes only if
   every chunk passed. It never retries: a retry would mask the signal;
5. prints one `CAPPED_PYTEST_RESULT:{json}` line. Exit code: 0 all passed, 1 test failures, 2 usage error, 3 an
   environment failure. A test failure and an environment failure are never reported as the same thing.

TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS. The runner and the MemAvailable reader are injected
so the tests need no real systemd-run.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Callable

from tools.delivery.host_test_caps import HostCap, load_cap

Runner = Callable[[list[str]], tuple[int, str]]

EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_ENVIRONMENT = 0, 1, 2, 3
RESULT_MARKER = "CAPPED_PYTEST_RESULT:"
ENVIRONMENT_RETURN_CODES = frozenset({-9, 137})
# Case-sensitive and anchored to how an environment death actually appears, so a failing test whose output merely mentions
# one of these words (an assertion on the message, a parameter id) stays a test failure. An OOM kill is recognised by its
# return code (ENVIRONMENT_RETURN_CODES), never by free text.
ENVIRONMENT_TEXT = re.compile(
    r"OSError: \[Errno 12\] Cannot allocate memory|INTERNALERROR>.*MemoryError|(?m:^E\s+MemoryError\b)|(?m:^Killed$)"
)
_BASE_FLAGS = ["-q", "--tb=line", "-rfE", "-p", "no:cacheprovider"]
# Flags that take a separate value. The value after one of these is passed to pytest as given, even when it names an
# existing path (`-c pytest.ini`, `--rootdir .`, `--ignore tests/x`). Any other flag must be value-free or use `--flag=value`.
VALUE_FLAGS = frozenset({
    "-m", "-k", "-c", "-p", "-o", "--rootdir", "--confcutdir", "--ignore", "--ignore-glob", "--deselect", "--junitxml",
})
_COUNT_NAMES = {"passed": "passed", "failed": "failed", "error": "errors", "errors": "errors", "skipped": "skipped"}


def default_runner(cmd: list[str]) -> tuple[int, str]:
    done = subprocess.run(cmd, capture_output=True, text=True, errors="replace", check=False)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def mem_available_gb() -> float:
    with open("/proc/meminfo", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) / (1024 * 1024)
    return 0.0


def wrap(cap: HostCap | None, cmd: list[str]) -> list[str]:
    """The command under the host's cap, or unchanged when there is no cap."""
    if cap is None:
        return cmd
    return [
        "systemd-run", "--user", "--scope", "-q",
        "-p", f"MemoryMax={cap.memory_max}", "-p", f"MemorySwapMax={cap.memory_swap_max}",
        "taskset", "-c", cap.cpus,
    ] + cmd


def split_args(argv: list[str]) -> tuple[list[str], list[str]]:
    """Targets are the arguments that name an existing path and are not the value of a flag in `VALUE_FLAGS`;
    everything else is passed to pytest as given."""
    targets: list[str] = []
    passthrough: list[str] = []
    after_value_flag = False
    for arg in argv:
        if after_value_flag:
            passthrough.append(arg)
            after_value_flag = False
        elif arg in VALUE_FLAGS:
            passthrough.append(arg)
            after_value_flag = True
        elif not arg.startswith("-") and os.path.exists(arg):
            targets.append(arg)
        else:
            passthrough.append(arg)
    return targets, passthrough


def pytest_cmd(extra: list[str]) -> list[str]:
    cmd = [sys.executable, "-m", "pytest"]
    if importlib.util.find_spec("xdist") is not None:
        cmd += ["-n", "0"]
    return cmd + extra


def collected_per_file(output: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for line in output.splitlines():
        match = re.match(r"^(\S+\.py)::", line)
        if match:
            counts[match.group(1)] += 1
    return dict(counts)


def plan_chunks(counts: dict[str, int], max_tests: int) -> list[list[str]]:
    """Whole files, sorted by path, packed in order up to `max_tests` collected tests; an oversized file is its own chunk."""
    chunks: list[list[str]] = []
    current: list[str] = []
    size = 0
    for path in sorted(counts):
        n = counts[path]
        if current and size + n > max_tests:
            chunks.append(current)
            current, size = [], 0
        current.append(path)
        size += n
    if current:
        chunks.append(current)
    return chunks


_TEST_ID_LINE = re.compile(r"^(?:FAILED |ERROR |PASSED |SKIPPED )|^\S+\.py::")


def is_environment_failure(returncode: int, output: str) -> bool:
    """A SIGKILL return code, or an environment signature in the output. A zero return code is never an environment
    death, and lines that only name a test (a collect-only listing, `FAILED path::test[param]` summary lines) are not
    searched: a parameter id may contain the very words the signatures look for. Found by running this helper over its
    own test file, whose parameter ids quote them."""
    if returncode in ENVIRONMENT_RETURN_CODES:
        return True
    if returncode == 0:
        return False
    text = "\n".join(ln for ln in output.splitlines() if not _TEST_ID_LINE.match(ln))
    return ENVIRONMENT_TEXT.search(text) is not None


def parse_counts(output: str) -> dict[str, int]:
    """Counts from pytest's last summary line, e.g. `1 failed, 832 passed, 19 skipped, 28 deselected in 91.9s`."""
    totals = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for line in reversed(output.splitlines()):
        if re.search(r"\bin [\d.]+s\b", line) and re.search(r"\d+ (passed|failed|error|errors|skipped)", line):
            for number, name in re.findall(r"(\d+) (passed|failed|errors?|skipped)", line):
                totals[_COUNT_NAMES[name]] += int(number)
            break
    return totals


def failed_ids(output: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r"(?m)^(?:FAILED|ERROR) (\S+)", output)]


def _result(mode: str, host: str | None) -> dict:
    return {
        "mode": mode, "host": host, "passed": False, "pass_count": 0, "fail_count": 0, "error_count": 0,
        "skipped_count": 0, "failed_tests": [], "environment_failure": False, "environment_note": "", "chunks": [],
    }


def _finish(result: dict) -> dict:
    """passed needs every chunk to have passed, not just zero parsed failures: a chunk that failed without a summary line
    (a usage error, a non-memory INTERNALERROR, a crash) must never read as a pass."""
    result["passed"] = (
        not result["environment_failure"] and result["fail_count"] == 0 and result["error_count"] == 0
        and bool(result["chunks"]) and all(c["status"] == "pass" for c in result["chunks"])
    )
    other = result["fail_count"] + result["error_count"]
    if result["environment_failure"] and other:
        result["environment_note"] += (
            f"; {other} other test(s) also failed and are listed in failed_tests: read them before re-running"
        )
    return result


def _add(result: dict, counts: dict[str, int], output: str, name: str = "run", code: int | None = None, status: str = "pass") -> None:
    result["pass_count"] += counts["passed"]
    result["fail_count"] += counts["failed"]
    result["error_count"] += counts["errors"]
    result["skipped_count"] += counts["skipped"]
    result["failed_tests"] += failed_ids(output)
    if status == "fail" and counts["failed"] == 0 and counts["errors"] == 0:
        result["error_count"] += 1
        result["failed_tests"].append(f"{name} (rc {code}, no failures parsed)")


def run_unwrapped(targets: list[str], passthrough: list[str], run: Runner) -> dict:
    result = _result("unwrapped", None)
    code, output = run(pytest_cmd(_BASE_FLAGS + passthrough + targets))
    status = "environment" if is_environment_failure(code, output) else ("pass" if code == 0 else "fail")
    result["chunks"].append({"name": "all", "files": len(targets), "rc": code, "status": status})
    _add(result, parse_counts(output), output, "all", code, status)
    if status == "environment":
        result["environment_failure"] = True
        result["environment_note"] = "the single unwrapped run died of the environment (memory text or SIGKILL)"
    return _finish(result)


def run_capped(
    targets: list[str], passthrough: list[str], cap: HostCap, run: Runner = default_runner,
    mem_gb: Callable[[], float] = mem_available_gb,
) -> dict:
    result = _result("capped", cap.host)
    code, output = run(wrap(cap, pytest_cmd(["--collect-only", "-q", "-p", "no:cacheprovider"] + passthrough + targets)))
    if is_environment_failure(code, output):
        result["environment_failure"] = True
        result["environment_note"] = "the collection step died of the environment"
        result["chunks"].append({"name": "collect", "files": 0, "rc": code, "status": "environment"})
        return _finish(result)
    counts = collected_per_file(output)
    if code not in (0, 5) or not counts:
        result["error_count"] += 1
        result["chunks"].append({"name": "collect", "files": 0, "rc": code, "status": "fail"})
        result["failed_tests"].append("collection")
        return _finish(result)
    chunks = plan_chunks(counts, cap.max_tests_per_chunk)
    for index, files in enumerate(chunks, start=1):
        name = f"chunk {index}/{len(chunks)}"
        free = mem_gb()
        if free < cap.mem_available_floor_gb:
            result["environment_failure"] = True
            result["environment_note"] = (
                f"{name} not started: MemAvailable {free:.2f} GB is below the {cap.mem_available_floor_gb:g} GB floor"
                f" ({len(chunks) - index + 1} chunk(s) not run)"
            )
            result["chunks"].append({"name": name, "files": len(files), "rc": None, "status": "environment"})
            break
        code, output = run(wrap(cap, pytest_cmd(_BASE_FLAGS + passthrough + files)))
        env = is_environment_failure(code, output)
        status = "environment" if env else ("pass" if code in (0, 5) else "fail")
        result["chunks"].append({"name": name, "files": len(files), "rc": code, "status": status})
        _add(result, parse_counts(output), output, name, code, status)
        if env:
            result["environment_failure"] = True
            result["environment_note"] = f"{name} died of the environment (memory text or SIGKILL); later chunks not run"
            break
    return _finish(result)


def main(argv: list[str] | None = None, run: Runner = default_runner) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    targets, passthrough = split_args(args)
    if not targets:
        print("capped_pytest: name at least one existing test directory, e.g. tests/tools/", file=sys.stderr)
        return EXIT_USAGE
    root = Path(__file__).resolve().parents[2]
    cap = load_cap(root)
    result = run_unwrapped(targets, passthrough, run) if cap is None else run_capped(targets, passthrough, cap, run)
    print(RESULT_MARKER + json.dumps(result))
    if result["environment_failure"]:
        return EXIT_ENVIRONMENT
    return EXIT_PASS if result["passed"] else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
