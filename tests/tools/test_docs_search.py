"""Tests for tools/gate_checks/docs_search.py (TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH).

The replay cases use committed minimal docs subsets under tests/tools/fixtures/docs_search/ (the cited lines of
the audited docs plus one decoy per exclusion class), so they run without the git history. The same function
runs against the real history with tools/gate_checks/docs_search_replay.py.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

from tools.gate_checks import docs_search
from tools.gate_checks.done_checker_static import _DOCS_BULLET_RE

FIXTURES = Path(__file__).parent / "fixtures" / "docs_search"
CASES = json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))


def _run_case(name, with_old_terms=True):
    root = FIXTURES / name
    head = docs_search.DirSource(root / "head") if (root / "head").exists() else None
    base = docs_search.DirSource(root / "base") if (root / "base").exists() else None
    case = CASES[name]
    return docs_search.search_docs_for_change(
        case["changed"], docs_search.DirSource(root / "docs_tree"), head, base,
        case["old_terms"] if with_old_terms else [],
    )


def _paths(result, key):
    return {item["path"].rsplit("/", 1)[-1]: item for item in result[key]}


# --- AC 1: the replay -------------------------------------------------------------------------------------------


def test_the_837_replay_finds_items_1_2_and_6():
    result = _run_case("case_837")
    assert {"simulation_kernel_contract.md", "deterministic_execution.md"} <= set(_paths(result, "required"))
    assert "kernel_concurrency_design_philosophy.md" in _paths(result, "required") | _paths(result, "candidate")


def test_the_786_replay_finds_item_5_in_the_readme():
    result = _run_case("case_786")
    assert any(item["path"] == "README.md" for item in result["required"] + result["candidate"])


def test_item_9_is_excluded_with_its_reason_and_hits_on_the_819_replay():
    excluded = _paths(_run_case("case_819"), "excluded")
    item = excluded["import_linter_soak_review.md"]
    assert item["reason"] == "review-record"
    assert item["hits"], "an excluded doc keeps its hits, so it is visible and never silently dropped"
    assert item["path"] not in [i["path"] for i in _run_case("case_819")["candidate"]]


# --- AC 3: one test per exclusion class ------------------------------------------------------------------------


@pytest.mark.parametrize("filename, reason", [
    ("old_ledger.md", "archive"),
    ("D99.md", "audit"),
    ("REGISTRY.yaml", "registry"),
    ("superseded_plan.md", "historical-status"),
    ("soak_review.md", "review-record"),
])
def test_each_exclusion_class_is_excluded_with_its_reason(filename, reason):
    excluded = _paths(_run_case("case_837"), "excluded")
    assert excluded[filename]["reason"] == reason and excluded[filename]["hits"]


def test_an_active_plan_is_not_excluded():
    assert docs_search.exclusion_reason("docs/plans/live_plan.md", "---\nstatus: active\n---\n") is None


def test_a_live_guide_is_a_candidate_not_required():
    result = _run_case("case_837")
    assert "live_guide.md" in _paths(result, "candidate") and "live_guide.md" not in _paths(result, "required")
    assert "unrelated.md" not in {**_paths(result, "candidate"), **_paths(result, "required")}


def test_parity_ledger_hits_are_candidates_owned_by_parity_updater(tmp_path):
    (tmp_path / "docs" / "parity_ledger").mkdir(parents=True)
    (tmp_path / "docs" / "parity_ledger" / "infra.yaml").write_text("evidence: src/engine/executor.py\n")
    result = docs_search.search_docs_for_change(["src/engine/executor.py"], docs_search.DirSource(tmp_path))
    assert result["candidate"][0]["owner"] == "parity-updater" and not result["required"]


def test_engine_matrices_are_not_normative():
    assert docs_search.is_normative("docs/engine/contracts/simulation_kernel_contract.md")
    assert docs_search.is_normative("docs/architecture/worker_notes.md") is False
    assert docs_search.is_normative("docs/architecture/kernel_contract.md")
    assert not docs_search.is_normative("docs/engine/matrices/worker_bounds_matrix.md")


def test_candidates_are_ranked_direct_hit_before_importer_hit(tmp_path):
    (tmp_path / "src" / "engine").mkdir(parents=True)
    (tmp_path / "src" / "engine" / "executor.py").write_text("def run_batch():\n    return 1\n")
    (tmp_path / "src" / "engine" / "kernel.py").write_text("from src.engine.executor import run_batch\n")
    (tmp_path / "docs" / "guides").mkdir(parents=True)
    (tmp_path / "docs" / "guides" / "a_importer.md").write_text("see src/engine/kernel.py\n")
    (tmp_path / "docs" / "guides" / "z_direct.md").write_text("see src/engine/executor.py\n")
    result = docs_search.search_docs_for_change(["src/engine/executor.py"], docs_search.DirSource(tmp_path))
    assert [i["path"].rsplit("/", 1)[-1] for i in result["candidate"]] == ["z_direct.md", "a_importer.md"]
    assert result["candidate"][1]["kinds"] == ["importer"]


# --- symbols, old terms, importers, mechanisms -------------------------------------------------------------------


def test_public_symbols_are_non_underscore_def_and_class_names_only():
    text = "def public_one():\n    pass\n\ndef _private():\n    pass\n\nclass PublicClass:\n    async def go(self):\n        pass\n"
    assert docs_search.public_symbols(text) == ["PublicClass", "go", "public_one"]


def test_one_word_names_are_not_searched_as_symbols():
    assert not docs_search.identifier_shaped("execute")
    assert docs_search.identifier_shaped("chunk_worker") and docs_search.identifier_shaped("WorkerPacket")


def test_a_symbol_at_base_and_absent_at_head_becomes_an_old_term():
    result = _run_case("case_837")
    assert "old-behaviour terms: --old-term plus 1 public symbol(s) at base and absent at head" in result["notes"]


def test_without_a_base_only_explicit_old_terms_count():
    result = docs_search.search_docs_for_change(["src/x.py"], docs_search.DirSource(FIXTURES / "case_837" / "docs_tree"))
    assert any("--old-term only" in note for note in result["notes"])


def test_a_removed_symbol_found_in_prose_is_a_term_hit(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("Workers call old_view_builder() each tick.\n")
    (tmp_path / "head" / "src").mkdir(parents=True)
    (tmp_path / "head" / "src" / "m.py").write_text("def new_thing():\n    pass\n")
    (tmp_path / "base" / "src").mkdir(parents=True)
    (tmp_path / "base" / "src" / "m.py").write_text("def old_view_builder():\n    pass\n")
    result = docs_search.search_docs_for_change(
        ["src/m.py"], docs_search.DirSource(tmp_path), docs_search.DirSource(tmp_path / "head"),
        docs_search.DirSource(tmp_path / "base"),
    )
    assert result["candidate"][0]["kinds"] == ["term"]


def test_mechanism_entries_citing_a_changed_path_make_mechanism_hits(tmp_path):
    (tmp_path / "registries").mkdir()
    (tmp_path / "registries" / "mechanisms.yaml").write_text(
        "mechanisms:\n  - id: combat_resolution\n    implemented_by: [src/engine/combat.py::CombatResolutionSystem]\n")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "note.md").write_text("The combat_resolution mechanism rolls damage.\n")
    result = docs_search.search_docs_for_change(["src/engine/combat.py"], docs_search.DirSource(tmp_path))
    assert result["candidate"][0]["kinds"] == ["mechanism"]


def test_the_regex_importer_scan_names_its_source(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("x = 1\n")
    (tmp_path / "src" / "b.py").write_text("from src import a\n")
    result = docs_search.search_docs_for_change(["src/a.py"], docs_search.DirSource(tmp_path))
    assert any(n.startswith("importers: regex scan of src/") and "1 file" in n for n in result["notes"])


def test_the_graph_importers_are_used_when_a_graph_is_given(tmp_path):
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({
        "nodes": [{"id": "a", "source_file": "src/a.py"}, {"id": "b", "source_file": "src/b.py"}],
        "links": [{"source": "b", "target": "a", "relation": "imports_from"}],
    }))
    result = docs_search.search_docs_for_change(["src/a.py"], docs_search.DirSource(tmp_path), graph_path=graph)
    assert any(n.startswith("importers: graph graph.json") for n in result["notes"])


def test_an_unreadable_graph_falls_back_to_the_regex_scan_and_says_so(tmp_path):
    graph = tmp_path / "graph.json"
    graph.write_text("not json")
    result = docs_search.search_docs_for_change(["src/a.py"], docs_search.DirSource(tmp_path), graph_path=graph)
    assert any("graph unavailable" in n for n in result["notes"])


# --- F5: comments and docstrings -------------------------------------------------------------------------------


def test_comment_hits_cover_invariant_comments_and_docstrings_only():
    text = '"""Module.\n\nInvariant: packets never read the live world.\n"""\n\n# must stay deterministic\nx = 1\n# unrelated remark\ny = 2\n'
    hits = docs_search.comment_hits("src/m.py", text)
    assert [h["line"] for h in hits] == [3, 6]
    assert all(h["path"] == "src/m.py" for h in hits)


def test_comment_keywords_match_on_word_boundaries():
    assert docs_search.comment_hits("m.py", "# back to the stack, then track it\n") == []
    assert docs_search.comment_hits("m.py", "# the worker must ack the packet\n")


def test_an_f5_comment_hit_is_returned_for_a_changed_file():
    hits = _run_case("case_837")["comment_hits"]
    assert {h["line"] for h in hits} >= {3, 9}


def test_unparseable_python_gives_no_comment_hits_and_no_error():
    assert docs_search.comment_hits("m.py", "def broken(:\n") == []


# --- AC 4: the Verify parser is untouched ---------------------------------------------------------------------


def test_the_candidate_and_excluded_tables_never_match_the_verify_bullet_regex():
    table = "\n".join(
        f"| `{item['path']}` | {', '.join(item['kinds'])} |"
        for item in _run_case("case_837")["candidate"] + _run_case("case_837")["excluded"]
    )
    assert table and not _DOCS_BULLET_RE.search(table)


# --- sources ------------------------------------------------------------------------------------------------


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def test_a_pinned_ref_reads_the_docs_tree_at_that_ref_not_the_working_tree(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "guide.md").write_text("see src/engine/executor.py\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "first")
    (tmp_path / "docs" / "guide.md").write_text("nothing here any more\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "second")
    pinned = docs_search.search_docs_for_change(["src/engine/executor.py"], docs_search.GitRefSource(tmp_path, "HEAD~1"))
    live = docs_search.search_docs_for_change(["src/engine/executor.py"], docs_search.DirSource(tmp_path))
    assert [i["path"] for i in pinned["candidate"]] == ["docs/guide.md"] and live["candidate"] == []


def test_the_cli_prints_marker_json_for_a_pinned_run(tmp_path, capsys):
    root = FIXTURES / "case_819" / "docs_tree"
    assert docs_search.main(["--repo-root", str(root), "--changed-file", "codebase/structure/importlinter.toml"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("MARKER:")
    assert re.search(r"import_linter_soak_review", out) and "review-record" in out
