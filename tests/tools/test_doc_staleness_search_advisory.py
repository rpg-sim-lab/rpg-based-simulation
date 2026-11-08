"""Tests for the satellite step and the staleness advisory (TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY).

The advisory (F3) is appended by `check_doc_staleness` from the shared docs search; the satellite step (F2) lives in
doc-updater's instructions and the Document-Update prompt, so those are pinned as text.
"""

import json
from pathlib import Path

from tools.gate_checks import changed_files, doc_staleness_check, docs_search, gate_cli

REPO = Path(__file__).parent.parent.parent
FIXTURES = Path(__file__).parent / "fixtures" / "docs_search"
CHANGED = ["src/engine/executor.py"]


def _search(case="case_837", changed=None):
    root = FIXTURES / case
    cases = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))
    head = docs_search.DirSource(root / "head") if (root / "head").exists() else None
    base = docs_search.DirSource(root / "base") if (root / "base").exists() else None
    return docs_search.search_docs_for_change(
        changed or cases[case]["changed"], docs_search.DirSource(root / "docs_tree"), head, base, cases[case]["old_terms"],
    )


def _advisories(results):
    return [r for r in results if r["status"] == "ADVISORY"]


def test_the_advisory_lists_untouched_live_docs_and_keeps_the_pass_verdict():
    results = doc_staleness_check.check_doc_staleness(CHANGED + ["docs/other.md"], True, None, _search())
    assert results[0]["status"] == "PASS"
    advisory = _advisories(results)[0]
    assert "docs/engine/deterministic_execution.md" in advisory["docs"]
    assert "docs/guides/live_guide.md" in advisory["docs"]


def test_a_touched_doc_is_not_listed():
    touched = ["docs/engine/deterministic_execution.md"]
    results = doc_staleness_check.check_doc_staleness(CHANGED + touched, True, None, _search())
    assert "docs/engine/deterministic_execution.md" not in _advisories(results)[0]["docs"]


def test_excluded_docs_never_appear_in_the_advisory():
    advisory = _advisories(doc_staleness_check.check_doc_staleness(CHANGED + ["docs/x.md"], True, None, _search()))[0]
    assert not {"docs/archive/old_ledger.md", "docs/audits/D99.md", "docs/REGISTRY.yaml", "docs/plans/soak_review.md",
                "docs/plans/superseded_plan.md"} & set(advisory["docs"])


def test_item_9_is_marked_excluded_in_the_input_and_never_listed():
    search = _search("case_819")
    assert [i["path"] for i in search["excluded"]] == ["docs/plans/codebase_health/import_linter_soak_review.md"]
    results = doc_staleness_check.check_doc_staleness(["codebase/structure/importlinter.toml", "docs/x.md"], True, None, search)
    assert all("import_linter_soak_review" not in doc for adv in _advisories(results) for doc in adv["docs"])


def test_critical_invariant_docs_come_first_and_are_named():
    search = {"required": [], "candidate": [
        {"path": "docs/guides/a_style_guide.md", "hits": [{"text": "see src/x.py"}]},
        {"path": "docs/engine/deterministic_execution.md", "hits": [{"text": "see src/x.py"}]},
        {"path": "docs/guides/b_runbook.md", "hits": [{"text": "workers acknowledge each packet (src/x.py)"}]},
    ]}
    advisory = _advisories(doc_staleness_check.check_doc_staleness(["src/x.py", "docs/y.md"], True, None, search))[0]
    assert advisory["docs"][:2] == ["docs/engine/deterministic_execution.md", "docs/guides/b_runbook.md"]
    assert advisory["critical"] == advisory["docs"][:2]
    assert "critical-invariant docs first: docs/engine/deterministic_execution.md" in advisory["evidence"]


def test_critical_words_match_on_boundaries():
    assert not doc_staleness_check.CRITICAL_INVARIANT.search("back to the stack, then track it")
    assert doc_staleness_check.CRITICAL_INVARIANT.search("the worker sends an ack")


def test_a_missing_or_malformed_search_result_leaves_the_output_byte_identical():
    base = doc_staleness_check.check_doc_staleness(CHANGED + ["docs/x.md"], True, ["docs/engine/kernel.md"])
    for bad in (None, {}, {"candidate": [{"hits": []}]}, "text", {"required": 3}):
        again = doc_staleness_check.check_doc_staleness(CHANGED + ["docs/x.md"], True, ["docs/engine/kernel.md"], bad)
        assert json.dumps(again) == json.dumps(base)


def test_the_advisory_never_changes_a_fail_verdict():
    failing = doc_staleness_check.check_doc_staleness(CHANGED, True, None, _search())
    assert [r["status"] for r in failing] == ["FAIL"]


def test_a_search_failure_in_the_gate_cli_leaves_the_gate_output_unchanged(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("search broke")
    monkeypatch.setattr(gate_cli.docs_search, "search_docs_for_change", boom)
    assert gate_cli._search_result(["src/engine/executor.py"], "HEAD") is None


def test_docs_only_changes_skip_the_search():
    assert gate_cli._search_result(["docs/a.md", "agent-working/x.md"], "HEAD") is None


# --- F2: the instructions and the prompt ------------------------------------------------------------------------


def _agent_text():
    return (REPO / ".claude" / "agents" / "doc-updater.md").read_text(encoding="utf-8")


def test_doc_updater_has_the_satellite_step_with_every_rule():
    text = _agent_text()
    assert "## Satellite step (candidates)" in text
    for needle in (
        "the rule \"never something you derive\n  yourself\" above does not apply to it",
        "Edit **explanatory** docs only",
        "cites the rule owner's approval",
        "do not edit the doc: report it in `blocker` as a defect or a proposed divergence",
        "Never write a defect into a normative doc as if it were intended",
        "Never edit an `excluded` doc",
        "`owner: parity-updater`",
        "`docs_skipped`",
        "A failed search never blocks the phase",
        "do not compute your own diff",
    ):
        assert needle in text, needle


def test_the_document_update_prompt_carries_the_satellite_search_command():
    js = (REPO / ".claude" / "workflows" / "implement-ticket.js").read_text(encoding="utf-8")
    phase = js[js.index("phase('Document-Update')"):js.index("pushEvent(\n  'Document-Update'")]
    assert "tools/gate_checks/docs_search.py --start-sha ${startSha}" in phase
    assert "satelliteSearchCmd" in phase and "DOC_UPDATE_SCHEMA" in phase


def test_the_doc_staleness_site_shows_every_advisory_row():
    js = (REPO / ".claude" / "workflows" / "implement-ticket.js").read_text(encoding="utf-8")
    assert "docStalenessResults.filter(r => r.status === 'ADVISORY')" in js


def test_the_investigator_is_told_to_build_the_list_by_search():
    agent = (REPO / ".claude" / "agents" / "investigator.md").read_text(encoding="utf-8")
    js = (REPO / ".claude" / "workflows" / "implement-ticket.js").read_text(encoding="utf-8")
    assert "tools/gate_checks/docs_search.py --changed-file" in agent and "Build the list by search" in agent
    assert "tools/gate_checks/docs_search.py --changed-file" in js


def test_the_search_cli_derives_the_same_changed_files_as_the_gate(monkeypatch, tmp_path, capsys):
    seen = {}

    def fake_search(changed, *args, **kwargs):
        seen["changed"] = changed
        return {"required": [], "candidate": [], "excluded": [], "comment_hits": [], "notes": []}

    monkeypatch.setattr(docs_search, "derive_changed_files", lambda sha: ["src/a.py", "docs/b.md", "agent-working/x.md"])
    monkeypatch.setattr(docs_search, "search_docs_for_change", fake_search)
    assert docs_search.main(["--repo-root", str(tmp_path), "--start-sha", "abc"]) == 0
    assert seen["changed"] == changed_files.code_paths(["src/a.py", "docs/b.md", "agent-working/x.md"]) == ["src/a.py"]


def test_a_failing_search_prints_an_error_marker_and_exits_zero(monkeypatch, tmp_path, capsys):
    def boom(*args, **kwargs):
        raise RuntimeError("no git")
    monkeypatch.setattr(docs_search, "search_docs_for_change", boom)
    assert docs_search.main(["--repo-root", str(tmp_path), "--changed-file", "src/a.py"]) == 0
    out = json.loads(capsys.readouterr().out[len("MARKER:"):])
    assert out["error"].startswith("RuntimeError") and out["candidate"] == []
