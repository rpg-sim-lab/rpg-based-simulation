"""TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED: tests/conftest.py's resource budget lowers only the SOFT RLIMIT_AS.

An unprivileged process can never raise a lowered hard limit, so a hard cap set by the first test would fix the address space for
every later test in the process (a `resource_budget_large` test after a medium one would silently keep 4 GB). The real
`pytest_runtest_setup` sequence runs in one child process, so this pytest process keeps its own limits. Pure rlimit reads."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_GB = 1024 ** 3
_CHILD = r"""
import json, resource, signal, sys
sys.path.insert(0, ".")
if len(sys.argv) > 2:
    hard = int(sys.argv[2])
    resource.setrlimit(resource.RLIMIT_AS, (hard, hard))
from tests import conftest as c

start_hard = resource.getrlimit(resource.RLIMIT_AS)[1]

class Cfg:
    def __init__(self, b): self.b = b
    def getoption(self, name): return self.b

class Item:
    def __init__(self, b, large=False): self.config = Cfg(b); self.large = large
    def get_closest_marker(self, name): return object() if self.large and name == "resource_budget_large" else None

seen = []
for step in sys.argv[1].split(","):
    budget, _, mark = step.partition("+")
    c.pytest_runtest_setup(Item(budget, large=bool(mark)))
    seen.append(list(resource.getrlimit(resource.RLIMIT_AS)))
    signal.alarm(0)
print(json.dumps({"start_hard": start_hard, "seen": seen}))
"""


def _sequence(steps, inherited_hard=None):
    argv = [sys.executable, "-c", _CHILD, ",".join(steps)] + ([str(inherited_hard)] if inherited_hard else [])
    out = subprocess.run(argv, cwd=_REPO, capture_output=True, text=True, check=True).stdout
    return json.loads(out.strip().splitlines()[-1])


def _seen(steps, inherited_hard=None):
    return _sequence(steps, inherited_hard)["seen"]


@pytest.mark.parametrize("first", ["small", "medium"])
def test_a_large_test_after_a_smaller_budget_sees_8_gb(first):
    seen = _seen([first, "medium+large"])
    assert seen[1][0] == 8 * _GB


def test_a_small_test_after_a_large_one_sees_1_gb():
    assert _seen(["medium+large", "small"])[1][0] == 1 * _GB


def test_the_hard_limit_is_unchanged_after_both():
    for steps in (["medium", "medium+large"], ["medium+large", "small"]):
        result = _sequence(steps)
        # Compared with the hard limit the child started with, so a runner that already has a finite hard limit still passes.
        assert [row[1] for row in result["seen"]] == [result["start_hard"]] * 2


def test_an_inherited_finite_hard_limit_clamps_the_soft_limit_and_is_kept():
    hard = 6 * _GB
    seen = _seen(["medium+large"], inherited_hard=hard)
    assert seen[0] == [hard, hard]  # min(8 GB, 6 GB) soft, the inherited hard unchanged
