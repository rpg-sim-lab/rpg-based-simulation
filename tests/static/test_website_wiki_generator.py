"""website/scripts/generate_wiki.py renders the wiki's World Knowledge pages from stored repository data.

The wiki is a view, not a second copy (owner, #715 6789779149): every rule, mechanism and catalog
entry on a page must come from its source file, and nothing may be added that the source lacks.
"""

import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent.parent
_SPEC = importlib.util.spec_from_file_location("generate_wiki", _ROOT / "website" / "scripts" / "generate_wiki.py")
gw = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gw)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("world-knowledge")
    counts = gw.generate(out)
    return out, counts


# ── against the real repository data ───────────────────────────────────────────────────────


def test_every_world_rule_appears_with_its_stored_statement(built):
    out, _ = built
    root = _ROOT / "docs" / "world_rules"
    families = [p for p in root.glob("*/*.md") if p.parent.name not in gw.WORLD_RULES_SKIP]
    assert families
    for family in families:
        _, rules = gw.parse_rule_family(family.read_text(encoding="utf-8"))
        page = out / "laws" / family.parent.name / family.name
        if not rules:
            assert not page.exists()
            continue
        text = page.read_text(encoding="utf-8")
        assert len(re.findall(r"^## [A-Z]+-\d+", text, re.M)) == len(rules), family
        for rule in rules:
            assert f"## {rule['id']} — " in text
            if rule["statement"]:
                assert f"> {gw._text(rule['statement'])}" in text


def test_every_mechanism_appears_once_on_its_layer_page(built):
    out, _ = built
    registry = yaml.safe_load((_ROOT / "registries" / "mechanisms.yaml").read_text(encoding="utf-8"))
    seen = []
    for layer in registry["layers"]:
        text = (out / "mechanisms" / f"{layer}.md").read_text(encoding="utf-8")
        seen += re.findall(r"^## .+ \{#([a-z0-9-]+)\}$", text, re.M)
    assert sorted(seen) == sorted(m["id"].replace("_", "-") for m in registry["mechanisms"])


def test_mechanism_state_labels_cover_the_registry_vocabulary():
    registry = yaml.safe_load((_ROOT / "registries" / "mechanisms.yaml").read_text(encoding="utf-8"))
    assert {m["state"] for m in registry["mechanisms"]} <= set(gw.STATE_LABELS)
    assert {layer["cadence"] for layer in registry["layers"].values()} <= set(gw.CADENCE_LABELS)


def test_each_catalog_page_has_one_row_per_stored_entry(built):
    out, _ = built
    for page in gw._catalog_pages(gw.Catalog()):
        entries = yaml.safe_load((_ROOT / "data" / "content" / f"{page['family']}.yaml").read_text(encoding="utf-8"))
        text = (out / "catalog" / f"{page['slug']}.md").read_text(encoding="utf-8")
        first_table = text.split("\n\n## ")[0]
        rows = [line for line in first_table.splitlines() if line.startswith("| ")][1:]
        assert len(rows) == len(entries), page["slug"]


def test_every_page_names_its_sources_and_they_exist(built):
    out, _ = built
    for page in out.rglob("*.md"):
        front = page.read_text(encoding="utf-8").split("---")[1]
        sources = yaml.safe_load(front)["source_docs"]
        assert sources, page
        for source in sources:
            assert (_ROOT / source).exists(), (page, source)


# ── behaviour on small fixtures ────────────────────────────────────────────────────────────


def _fixture_repo(root: Path, mechanism_extra: dict | None = None, glossary: list[dict] | None = None) -> None:
    (root / "registries").mkdir(parents=True)
    mechanism = {"id": "hunger_drive", "layer": "entity", "systems": ["progression"], "depends_on": [], "state": "gap"}
    mechanism.update(mechanism_extra or {})
    registry = {"layers": {"entity": {"cadence": "per_tick", "rank": 1, "weight": 5}}, "mechanisms": [mechanism]}
    (root / "registries" / "mechanisms.yaml").write_text(yaml.safe_dump(registry), encoding="utf-8")
    (root / "registries" / "system_registry.jsonl").write_text(json.dumps({"system": "progression", "note": "Growth"}) + "\n", encoding="utf-8")
    (root / "registries" / "mechanism_causal_edges.yaml").write_text("edges: []\n", encoding="utf-8")
    if glossary is not None:
        (root / "registries" / "world_glossary.jsonl").write_text("".join(json.dumps(r) + "\n" for r in glossary), encoding="utf-8")


def test_mechanism_summary_is_shown_only_when_the_registry_has_one(tmp_path, monkeypatch):
    _fixture_repo(tmp_path / "with", {"summary": "Beings get hungry."})
    _fixture_repo(tmp_path / "without")
    monkeypatch.setattr(gw, "REPO_ROOT", tmp_path / "with")
    gw.build_mechanisms(tmp_path / "out-with")
    monkeypatch.setattr(gw, "REPO_ROOT", tmp_path / "without")
    gw.build_mechanisms(tmp_path / "out-without")
    with_text = (tmp_path / "out-with" / "mechanisms" / "entity.md").read_text(encoding="utf-8")
    without_text = (tmp_path / "out-without" / "mechanisms" / "entity.md").read_text(encoding="utf-8")
    assert "Beings get hungry." in with_text
    assert "**State:** Not built yet" in without_text
    assert with_text.replace("Beings get hungry.\n\n", "") == without_text


def test_glossary_is_skipped_while_absent_or_empty_and_rendered_when_filled(tmp_path, monkeypatch):
    _fixture_repo(tmp_path / "absent")
    _fixture_repo(tmp_path / "empty", glossary=[])
    _fixture_repo(tmp_path / "filled", glossary=[{"term": "Tick", "description": "One step of world time.", "source": "docs/engine/kernel.md", "added": "2026-11-11"}])
    for name, expected in (("absent", 0), ("empty", 0), ("filled", 1)):
        monkeypatch.setattr(gw, "REPO_ROOT", tmp_path / name)
        assert gw.build_glossary(tmp_path / f"out-{name}") == expected
    text = (tmp_path / "out-filled" / "glossary" / "index.md").read_text(encoding="utf-8")
    assert "| Tick | One step of world time. |" in text
    assert "docs/engine/kernel.md" in text


def test_generate_clears_only_the_generated_folders(tmp_path):
    (tmp_path / "laws").mkdir()
    (tmp_path / "laws" / "stale.md").write_text("old", encoding="utf-8")
    (tmp_path / "index.md").write_text("hand-written", encoding="utf-8")
    gw.generate(tmp_path)
    assert not (tmp_path / "laws" / "stale.md").exists()
    assert (tmp_path / "index.md").read_text(encoding="utf-8") == "hand-written"


def test_parse_rule_family_joins_a_multi_line_statement_and_allows_none():
    text = "# World Rule Family: Time\n\n## TIME-01 — Order is real\n\n> First line\n> second line.\n\nBody.\n\n## TIME-02 — No quote\n\nBody only.\n"
    title, rules = gw.parse_rule_family(text)
    assert title == "Time"
    assert rules == [
        {"id": "TIME-01", "title": "Order is real", "statement": "First line second line."},
        {"id": "TIME-02", "title": "No quote", "statement": ""},
    ]


def test_cell_escapes_table_and_markup_characters():
    assert gw._cell("a | b <c> {d}\nnext") == "a \\| b &lt;c&gt; &#123;d&#125; next"
