"""Tests for tools/world_glossary_registry.py (TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY)."""
import json
import sys
from pathlib import Path

import pytest

_TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import world_glossary_registry as wg  # noqa: E402

_REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def root(tmp_path):
    (tmp_path / "docs" / "mechanics").mkdir(parents=True)
    (tmp_path / "docs" / "mechanics" / "05_world_evolution.md").write_text("# w\n", encoding="utf-8")
    (tmp_path / "docs" / "guides").mkdir(parents=True)
    (tmp_path / "docs" / "guides" / "x.md").write_text("# x\n", encoding="utf-8")
    return tmp_path


def _add(root, term="tick", **kw):
    args = {"description": "One step of the simulation clock.", "source": "docs/mechanics/05_world_evolution.md#time"}
    args.update(kw)
    return wg.add_term(term, args["description"], args["source"], root=root)


def test_add_appends_one_valid_row(root):
    row = _add(root)
    lines = wg.registry_path(root).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == row
    assert set(row) == {"term", "description", "source", "added"}


def test_load_returns_term_keyed_rows(root):
    _add(root, "tick")
    _add(root, "Tick")  # case-sensitive: a different term
    assert set(wg.load_registry(root)) == {"tick", "Tick"}


def test_load_missing_and_empty_file_is_empty(root):
    assert wg.load_registry(root) == {}
    wg.registry_path(root).parent.mkdir(parents=True, exist_ok=True)
    wg.registry_path(root).write_text("", encoding="utf-8")
    assert wg.load_registry(root) == {}


def test_load_raises_on_duplicate_term(root):
    path = wg.registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = json.dumps({"term": "tick", "description": "d", "source": "docs/core/s.md", "added": "2026-11-11"})
    path.write_text(row + "\n" + row + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        wg.load_registry(root)


def test_re_adding_a_term_is_refused_and_writes_nothing(root):
    _add(root)
    before = wg.registry_path(root).read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="already registered"):
        _add(root, description="Another description.")
    assert wg.registry_path(root).read_text(encoding="utf-8") == before


@pytest.mark.parametrize(
    "source, fragment",
    [
        ("docs/mechanics/missing.md", "does not exist"),
        ("docs/guides/x.md", "must be under"),
        ("docs/mechanics/../guides/x.md", "must not contain"),
        ("/etc/passwd", "must be under"),
    ],
)
def test_bad_source_is_refused_and_writes_nothing(root, source, fragment):
    with pytest.raises(ValueError, match=fragment):
        _add(root, source=source)
    assert not wg.registry_path(root).exists()


def test_blank_description_or_term_is_refused(root):
    with pytest.raises(ValueError, match="description"):
        _add(root, description="  ")
    with pytest.raises(ValueError, match="term"):
        _add(root, term=" ")
    assert not wg.registry_path(root).exists()


def test_cli_add_and_duplicate_exit_codes(root, capsys):
    argv = ["add", "region", "--description", "A named area.", "--source", "docs/mechanics/05_world_evolution.md", "--root", str(root)]
    assert wg.main(argv) == 0
    assert wg.main(argv) == 1
    assert "already registered" in capsys.readouterr().err
    assert len(wg.registry_path(root).read_text(encoding="utf-8").splitlines()) == 1
    assert wg.main(["list", "--root", str(root)]) == 0


def test_cli_bad_source_exits_non_zero_and_writes_nothing(root):
    argv = ["add", "region", "--description", "d", "--source", "docs/mechanics/nope.md", "--root", str(root)]
    assert wg.main(argv) == 1
    assert not wg.registry_path(root).exists()


def test_committed_registry_rows_resolve():
    """Corpus check: every committed row is well-formed and its source still resolves. Empty or absent passes."""
    for term, row in wg.load_registry(_REPO).items():
        assert row["description"].strip(), term
        assert wg.source_problem(row["source"], _REPO) is None, (term, row["source"])
        assert row.get("added"), term
