"""The unwired-subject advisory (TCK-20261109-AN-ADVISORY-GUARD-LISTS-TESTS-WHOSE-SUBJECT-SYSTEM-THE-PIPELINE-NEVER-RUNS).

``tools/test_architecture/unwired_subject_check.py`` lists ``src/systems`` classes the authoritative pipeline never reaches and the tests that import them without
``pytest.mark.unwired_subject("<reason>")``. It is report only. These tests run it on a synthetic package and once on the real tree; they assert the report, and that
nothing here can fail a build on its findings.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.test_architecture import unwired_subject_check as uw

PIPELINE = '''
from src.systems.wired_sys import WiredSystem
{extra_import}


class AuthoritativeApplyPipeline:
    def refine(self, state, update):
        def run_phase(name, upd, fn, flag=None):
            return fn(upd)

        update = run_phase("wired", update, lambda u: WiredSystem.run(state, u))
        {extra_call}
        return update
'''


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _tree(tmp_path: Path, *, extra_import: str = "", extra_call: str = "pass") -> Path:
    root = tmp_path / "repo"
    _write(root, "src/engine/pipeline.py", PIPELINE.format(extra_import=extra_import, extra_call=extra_call))
    _write(root, "src/systems/wired_sys.py", "class WiredSystem:\n    @staticmethod\n    def run(s, u):\n        return u\n")
    _write(root, "src/systems/strategic_systems/hidden.py", "class HiddenSystem:\n    @staticmethod\n    def enforce(s, u):\n        return u\n")
    _write(root, "src/systems/hidden_facade.py", "from src.systems.strategic_systems.hidden import HiddenSystem\n__all__ = ['HiddenSystem']\n")
    _write(root, "src/systems/late.py", "class LateSystem:\n    @staticmethod\n    def go():\n        return 1\n")
    _write(root, "tests/test_hidden_unmarked.py", "from src.systems.hidden_facade import HiddenSystem\n\n\ndef test_it():\n    assert HiddenSystem.enforce(None, None) is None\n")
    _write(root, "tests/test_hidden_marked.py", "import pytest\nfrom src.systems.strategic_systems.hidden import HiddenSystem\n\npytestmark = pytest.mark.unwired_subject('facade is the public import')\n\n\ndef test_it():\n    assert HiddenSystem\n")
    _write(root, "tests/test_wired.py", "from src.systems.wired_sys import WiredSystem\n\n\ndef test_it():\n    assert WiredSystem.run(None, 1) == 1\n")
    return root


def _symbols(report, key="unwired"):
    return sorted(r["symbol"] for r in report[key])


def test_the_synthetic_report_names_exactly_the_reexport_only_systems_and_the_unmarked_importing_test(tmp_path):
    report = uw.analyse(_tree(tmp_path))
    assert _symbols(report) == ["src.systems.late.LateSystem", "src.systems.strategic_systems.hidden.HiddenSystem"]
    hidden = next(r for r in report["unwired"] if r["symbol"].endswith("HiddenSystem"))
    assert hidden["referenced"] == "re-export only" and hidden["src_importers"] == ["src.systems.hidden_facade"]
    late = next(r for r in report["unwired"] if r["symbol"].endswith("LateSystem"))
    assert late["referenced"] == "unreferenced"
    assert [t["file"] for t in report["flagged_tests"]] == ["tests/test_hidden_unmarked.py"]
    assert [t["file"] for t in report["acknowledged_tests"]] == ["tests/test_hidden_marked.py"]
    assert report["acknowledged_tests"][0]["reasons"] == ["facade is the public import"]
    assert report["counts"] == {"subject_symbols": 3, "wired": 1, "dispatch_reached": 0, "unwired": 2, "flagged_tests": 1, "acknowledged_tests": 1}


def test_the_wired_set_comes_from_the_pipeline_source_at_run_time(tmp_path):
    before = uw.analyse(_tree(tmp_path / "a"))
    after = uw.analyse(_tree(tmp_path / "b", extra_import="from src.systems.late import LateSystem", extra_call="LateSystem.go()"))
    assert "src.systems.late.LateSystem" in _symbols(before) and "src.systems.late.LateSystem" not in _symbols(after)
    assert after["counts"]["wired"] == before["counts"]["wired"] + 1
    assert after["pipeline"]["found"] and after["pipeline"]["run_phase_calls"] >= 1


def test_an_import_that_is_never_used_reaches_nothing(tmp_path):
    root = _tree(tmp_path, extra_import="from src.systems.late import LateSystem", extra_call="pass")
    report = uw.analyse(root)
    late = next(r for r in report["unwired"] if r["symbol"].endswith("LateSystem"))
    assert late["referenced"].startswith("import-only") and late["src_importers"] == ["src.engine.pipeline"]


def test_a_module_reached_for_one_symbol_leaves_its_unnamed_class_dispatch_reached_not_unwired(tmp_path):
    root = _tree(tmp_path)
    _write(root, "src/systems/wired_sys.py", "class WiredSystem:\n    @staticmethod\n    def run(s, u):\n        return u\n\n\nclass ByName:\n    pass\n")
    report = uw.analyse(root)
    assert _symbols(report, "dispatch_reached") == ["src.systems.wired_sys.ByName"] and "src.systems.wired_sys.ByName" not in _symbols(report)


def test_an_extra_root_adds_what_that_module_uses(tmp_path):
    root = _tree(tmp_path)
    _write(root, "src/engine/kernel.py", "from src.systems.late import LateSystem\n\n\ndef boot():\n    return LateSystem.go()\n")
    assert "src.systems.late.LateSystem" not in _symbols(uw.analyse(root, ["src/engine/kernel.py"]))


def test_a_module_used_as_an_attribute_chain_is_followed(tmp_path):
    root = _tree(tmp_path, extra_import="import src.systems.late as late", extra_call="late.LateSystem.go()")
    assert "src.systems.late.LateSystem" not in _symbols(uw.analyse(root))


def test_the_exit_code_is_zero_with_findings_and_the_json_parses(tmp_path, capsys):
    root = _tree(tmp_path)
    assert uw.main(["--repo", str(root)]) == 0
    assert "## unwired src/systems symbols" in capsys.readouterr().out
    assert uw.main(["--repo", str(root), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["counts"]["unwired"] == 2


def test_the_real_tree_completes_and_the_found_case_is_unwired_with_its_tests():
    report = uw.analyse()
    redirection = next(r for r in report["unwired"] if r["symbol"] == "src.systems.strategic_systems.redirection.StrategicRedirectionSystem")
    assert redirection["referenced"] == "re-export only" and redirection["tests"]
    flagged = {t["file"]: t["unwired"] for t in report["flagged_tests"]}
    assert "tests/unit/strategic/test_redirection.py" in flagged
    assert "src.systems.strategic_systems.redirection.StrategicRedirectionSystem" in flagged["tests/unit/strategic/test_redirection.py"]
    assert report["pipeline"]["found"] and report["pipeline"]["run_phase_calls"] > 10
