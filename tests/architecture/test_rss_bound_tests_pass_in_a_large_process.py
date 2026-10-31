"""The four tests that failed only in a wide run still pass when the process is already large.

TCK-20261023-FOUR-TESTS-FAIL-ONLY-IN-A-WIDE-SCOPED-RUN-ORDER-DEPENDENT. The cause was not a leaked
fixture: a wide scoped run grows the pytest process past 512 MB, and these tests built a profile with
``max_ram_mb=512`` that the engine compares with the live process RSS, so the kernel went CONSTRAINED
and the certification harness reported ``failed_envelope``. Each of the four is about something other
than RAM, so its ceiling must never bind. This guard re-runs them in a fresh process that first holds
1200 MB, which is what a wide run looks like to them.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

FOUR = (
    "tests/integration/kernel/test_authoritative_outcome_truth.py::test_replay_sources_from_refined_update",
    "tests/certification/test_envelope_violations.py::test_harness_detects_missing_degradation_mode",
    "tests/certification/test_harness_contract.py::test_certification_detects_semantic_drift",
    "tests/certification/test_resilience_recovery.py::test_harness_catches_failed_recovery",
)

_RUNNER = """
import sys, pytest
ballast = bytearray(1200 * 1024 * 1024)
for i in range(0, len(ballast), 4096):
    ballast[i] = 1
sys.exit(pytest.main(["-q", "-p", "no:cacheprovider", *sys.argv[1:]]))
"""


def test_the_four_pass_in_a_process_already_holding_1200_mb():
    done = subprocess.run(
        [sys.executable, "-c", _RUNNER, *FOUR],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
    )
    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-1000:]
