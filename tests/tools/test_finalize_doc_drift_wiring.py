"""The Finalize-tail doc drift advisory in implement-ticket.js (TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT)."""

from pathlib import Path

WORKFLOW = (Path(__file__).resolve().parents[2] / ".claude" / "workflows" / "implement-ticket.js").read_text(encoding="utf-8")


def _block():
    start = WORKFLOW.index("Advisory-only doc drift report")
    end = WORKFLOW.index("return {\n  status: 'DONE'", start)
    return WORKFLOW[start:end]


def test_the_advisory_runs_after_the_mechanism_check_and_before_the_return():
    assert WORKFLOW.index("mechanism_registry_changed_code_check") < WORKFLOW.index("Advisory-only doc drift report")


def test_it_passes_the_start_sha_and_cannot_fail_the_shell_call():
    block = _block()
    assert "doc_drift.py --format advisory --start-sha ${startSha} || true" in block


def test_it_only_logs_and_never_blocks_or_records_a_failed_event():
    block = _block()
    assert "log(`ADVISORY:" in block
    for forbidden in ("throw", "pushEvent", "pushStaticGate", "status: 'FAILED'", "return {"):
        assert forbidden not in block


def test_the_template_literals_contain_no_stray_backticks():
    """A backtick inside the command template once broke node --check (and 13 tests); keep the block's backticks paired."""
    assert _block().count("`") % 2 == 0
