"""The close-time advisory flags a ticket's evidence scripts that name ``_run_engine`` (TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE).

Report-only: OK / WARN / NA, never raises. It reads only Python files under the ticket's stored or staged artifacts."""
from __future__ import annotations

from pathlib import Path

import pytest

from tools.test_architecture import evidence_runner_advisory as adv

TICKET = "TCK-20260101-SOME-TICKET"


def _script(root: Path, rel: str, body: str, base: str = "agent-working/stored_artifacts") -> None:
    path = root / base / TICKET / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_a_script_that_calls_run_engine_is_flagged_with_its_line(tmp_path):
    _script(tmp_path, "evidence/probe12.py", "import x\nfrom tools.calibrate_simq import _run_engine\nrun = _run_engine('w', 1, 10)\n")
    status, text = adv.check_evidence_runner(TICKET, "standard", tmp_path)
    assert status == "WARN" and "evidence/probe12.py:2" in text and "evidence/probe12.py:3" in text and "not the pinned runner" in text


def test_a_script_on_the_pinned_runner_is_ok(tmp_path):
    _script(tmp_path, "evidence/probe.py", "from tools.test_architecture.rpg_gate_run import build_kernel\nkernel = build_kernel('w', 1, 'r')\n")
    status, text = adv.check_evidence_runner(TICKET, "standard", tmp_path)
    assert status == "OK" and "none names _run_engine" in text


def test_a_longer_name_is_not_a_match_and_markdown_is_not_a_script(tmp_path):
    _script(tmp_path, "a.py", "x = my_run_engine_helper()\n")
    _script(tmp_path, "notes.md", "we used _run_engine here\n")
    assert adv.check_evidence_runner(TICKET, "standard", tmp_path)[0] == "OK"


def test_staged_scripts_are_read_too_and_no_scripts_is_not_applicable(tmp_path):
    assert adv.check_evidence_runner(TICKET, "standard", tmp_path)[0] == "NA"
    _script(tmp_path, "s.py", "_run_engine()\n", base="agent-working/staging_artifacts")
    assert adv.check_evidence_runner(TICKET, "standard", tmp_path)[0] == "WARN"


def test_an_unreadable_root_never_raises(tmp_path):
    status, _ = adv.check_evidence_runner(TICKET, "standard", tmp_path / "does-not-exist")
    assert status == "NA"


def test_the_done_checker_reports_the_advisory_without_changing_its_verdict():
    from tools.gate_checks import done_checker_static as dc

    names = [r["condition"] for r in dc.run_advisory_checks("TCK-20260101-NOT-A-TICKET", "standard")]
    assert "evidence_runner_pinned" in names
    assert {r["status"] for r in dc.run_advisory_checks("TCK-20260101-NOT-A-TICKET", "standard")} <= {"OK", "WARN", "NA"}
