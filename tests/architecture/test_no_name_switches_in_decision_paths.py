"""No role, kind or faction name switch is added to a decision path (TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE).

Milestone 1 retires every place where a decision reads a role, kind or faction name. ``tools/test_architecture/name_switch_scan.py`` finds them with an AST scan;
this test holds the list from growing. It is a ratchet, like ``test_spawn_sites_declare_source.py``: green from day one because every switch found on the first
run is a row of ``name_switch_allowlist.yaml`` that cites the retirement ticket. A new switch fails. A row whose switch is gone, or whose count is lower, fails
too, so the list only shrinks. "Done" is an empty allowlist.

What the scan does not see, on purpose: a switch spelt some other way (``monster_type == "goblin"``), a name read through ``EntityRole.__members__``, and a
``kind`` on a receiver that is not entity-like. The report-only packages (src/world and src/core) are listed in the scan output
but do not gate until rpg-planner rules their rows.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Tuple

import pytest
import yaml

from tools.test_architecture import name_switch_scan as scan

pytestmark = pytest.mark.architecture

REPO = Path(__file__).resolve().parents[2]
ALLOWLIST = REPO / "tests" / "architecture" / "name_switch_allowlist.yaml"
RETIRE_TICKET = "TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES"


def _rows() -> list:
    return (yaml.safe_load(ALLOWLIST.read_text(encoding="utf-8")) or {}).get("rows") or []


def _allowlist() -> Dict[Tuple[str, str, str], int]:
    return {(r["file"], r["symbol"], r["name"]): int(r["count"]) for r in _rows()}


# --------------------------------------------------------------------------------------------- the real tree
def test_every_name_switch_in_a_gating_package_is_an_allowlist_row_and_every_row_is_a_switch():
    rows = scan.scan_tree(REPO)
    assert scan.check_allowlist(rows, _allowlist()) == []
    assert scan.check_rulings(rows) == []


def test_every_src_package_is_classified_once():
    assert scan.package_problems(scan.top_level_packages(REPO)) == []


def test_every_allowlist_row_has_a_reason_and_cites_the_retirement_ticket():
    rows = _rows()
    keys = [(r["file"], r["symbol"], r["name"]) for r in rows]
    assert len(keys) == len(set(keys)), "a (file, symbol, name) appears twice: merge the rows and add the counts"
    for r in rows:
        assert r["ticket"] == RETIRE_TICKET, r
        assert r["reason"].strip() and "\n" not in r["reason"], r
        assert int(r["count"]) >= 1, r
        assert (REPO / r["file"]).exists(), r


def test_the_real_scan_reports_report_only_rows_without_gating_on_them():
    rows = scan.scan_tree(REPO)
    assert {s.status for s in rows} == {"gating", "report-only", "excluded"}
    promoted = {(s.file, s.symbol) for s in rows if s.status == "gating" and s.file.split("/")[1] in scan.REPORT_ONLY}
    assert promoted == set(scan.PROMOTED_GATING)
    assert all(s.file.split("/")[1] in scan.SCAN for s in rows if s.status == "gating" and (s.file, s.symbol) not in promoted)
    assert all(s.file.split("/")[1] in scan.REPORT_ONLY for s in rows if s.status == "report-only")


def test_the_rulings_of_2026_11_15_hold_on_the_real_tree():
    rows = scan.scan_tree(REPO)
    # runtime is excluded; content_semantics gates; world and core report; the identity compat maps are excluded with a reason, as rows, by file and symbol
    assert "runtime" in scan.EXCLUDE and "content_semantics" in scan.SCAN and {"world", "core"} == set(scan.REPORT_ONLY)
    assert {(s.file, s.symbol) for s in rows if s.status == "excluded"} == set(scan.REASONED_EXCLUSIONS)
    assert not [s for s in rows if s.file.startswith("src/entities/") and s.status == "excluded" and "identity_resolver" not in s.file]
    assert any(s.file == "src/systems/social_systems/party_composition.py" and s.symbol.endswith("infer_party_role") and s.status == "gating" for s in rows)


# --------------------------------------------------------------------------------------------- the scan, on a synthetic package
def _tree(tmp_path: Path, files: Dict[str, str]) -> Path:
    for rel, body in files.items():
        target = tmp_path / "src" / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    return tmp_path


def _found(tmp_path: Path, body: str, pkg: str = "ai") -> list:
    root = _tree(tmp_path, {f"{pkg}/mod.py": body})
    return [(s.name, s.shape, s.status) for s in scan.scan_tree(root)]


@pytest.mark.parametrize(
    "body, expected",
    [
        ("def f(e):\n    if e.identity.role == 'hero':\n        return 1\n", [("'hero'", "compare", "gating")]),
        ("def f(e):\n    return e.identity.role != EntityRole.MONSTER\n", [("EntityRole.MONSTER", "compare", "gating")]),
        ("def f(e):\n    return e.identity.faction is Faction.HERO_GUILD\n", [("Faction.HERO_GUILD", "compare", "gating")]),
        ("def f(e):\n    return e.identity.role in (EntityRole.GUARD, EntityRole.WORKER)\n",
         [("EntityRole.GUARD", "compare", "gating"), ("EntityRole.WORKER", "compare", "gating")]),
        ("def f(e):\n    return 'goblin' in e.kind.lower()\n", [("'goblin'", "compare", "gating")]),
        ("def f(e):\n    return e.kind == 'wolf'\n", [("'wolf'", "compare", "gating")]),
        ("def f(role):\n    return role == 'GUARD'\n", [("'GUARD'", "compare", "gating")]),
        ("def f(e):\n    return getattr(e, 'role', None) == 'guard'\n", [("'guard'", "compare", "gating")]),
        ("def f(e):\n    return getattr(e, 'kind', '') in ('guard', 'mage')\n", [("'guard'", "compare", "gating"), ("'mage'", "compare", "gating")]),
        ("def f(entity):\n    kind = (getattr(entity, 'kind', '') or '').lower()\n    if kind in ('guard', 'sentinel'):\n        return 1\n",
         [("'guard'", "compare", "gating"), ("'sentinel'", "compare", "gating")]),
        ("def f(e):\n    kind = e.kind\n    return kind == 'wolf'\n", [("'wolf'", "compare", "gating")]),
        ("def f(e):\n    faction = e.identity.faction.name\n    return faction == 'GUILD'\n", [("'GUILD'", "compare", "gating")]),
        ("def f(e):\n    return e.role_id == 'guard'\n", [("'guard'", "compare", "gating")]),
        ("def f(a):\n    return a.identity.faction_id in ('hero_guild', 'town_council')\n", [("'hero_guild'", "compare", "gating"), ("'town_council'", "compare", "gating")]),
        ("def f(e):\n    return e.species_id == 'wolf'\n", [("'wolf'", "compare", "gating")]),
        ("def f(e):\n    return e.archetype_id != 'brute'\n", [("'brute'", "compare", "gating")]),
        ("def f(e):\n    return e.species == 'wolf' or e.archetype == 'brute'\n", [("'wolf'", "compare", "gating"), ("'brute'", "compare", "gating")]),
        ("def f(e):\n    return int(e.identity.role) == int(EntityRole.HERO)\n", [("EntityRole.HERO", "compare", "gating")]),
        ("def f(e):\n    match e.identity.faction:\n        case Faction.NEUTRAL:\n            return 0\n", [("Faction.NEUTRAL", "match", "gating")]),
        ("def f(e):\n    return W[EntityRole.HERO]\n", [("EntityRole.HERO", "lookup", "gating")]),
        ("T = {EntityRole.HERO: 1, EntityRole.GUARD: 2}\n", [("EntityRole.HERO", "table", "gating"), ("EntityRole.GUARD", "table", "gating")]),
        ("HOSTILITY_FACTION = {'orc': 1}\n", [("'orc'", "table", "gating")]),
        ("_CANDIDATE_ROLES = (EntityRole.WORKER, EntityRole.GUARD)\n", [("EntityRole.WORKER", "table", "gating"), ("EntityRole.GUARD", "table", "gating")]),
        ("_ROLES: frozenset = frozenset({EntityRole.WORKER})\n", [("EntityRole.WORKER", "table", "gating")]),
    ],
)
def test_each_switch_shape_is_found(tmp_path, body, expected):
    assert sorted(_found(tmp_path, body)) == sorted(expected)


@pytest.mark.parametrize(
    "body",
    [
        "def f(a, b):\n    return a.identity.faction_id == b.identity.faction_id\n",  # data by id, no name
        "def f(a, b):\n    return a.identity.role == b.identity.role\n",  # two reads, no name
        "def f(e, content):\n    return content.relations[e.identity.faction].hostile\n",  # content-declared relation by id
        "def f(lead):\n    return lead.kind == 'material_source'\n",  # another record's kind
        "def f(e):\n    return e.task.work_kind == 'REST'\n",  # not an entity kind
        "def f(e):\n    return e.identity.role == 3\n",  # a number is not a name
        "def f(e):\n    return e.identity.life_stage == 'adult'\n",  # not role, kind or faction
        "def f(e):\n    return build(role=EntityRole.HERO, faction=Faction.HERO_GUILD)\n",  # assigning a role is not a branch
        "ROLE_LABEL = 'hero'\n",  # a plain string constant
        "def f(lead):\n    kind = lead.kind\n    return kind == 'x'\n",  # a local bound to another record's kind
        "def f(lead):\n    return getattr(lead, 'kind', '') == 'x'\n",  # getattr of another record's kind
        "def f(e):\n    kind = e.task.work_kind\n    return kind == 'REST'\n",  # a local bound to a work kind
        "def f(e):\n    kind = e.kind\n    kind = compute()\n    return kind == 'x'\n",  # the binding is dropped when the local is reassigned
        "def f(entity):\n    kind = entity.kind\n\n\ndef g(x):\n    return kind == 'x'\n",  # a binding does not leak into another function
        "def f(kind):\n    return kind == 'x'\n",  # a bare parameter named kind, bound to nothing
    ],
)
def test_data_by_id_and_other_kinds_are_not_found(tmp_path, body):
    assert _found(tmp_path, body) == []


def test_symbol_and_line_name_the_enclosing_function(tmp_path):
    root = _tree(tmp_path, {"ai/mod.py": "class A:\n    def m(self, e):\n        x = 1\n        return e.identity.role == EntityRole.HERO\n\n\ndef top(e):\n    return e.identity.role == 'x'\n"})
    rows = [(s.symbol, s.line) for s in scan.scan_tree(root)]
    assert rows == [("A.m", 4), ("top", 8)]


def test_a_package_that_is_excluded_is_not_scanned(tmp_path):
    assert _found(tmp_path, "def f(e):\n    return e.identity.role == EntityRole.HERO\n", pkg="api") == []
    assert _found(tmp_path, "def f(e):\n    return e.identity.role == EntityRole.HERO\n", pkg="content") == []


def test_a_report_only_package_is_reported_but_not_gating(tmp_path):
    body = "def f(e):\n    return e.identity.role == EntityRole.HERO\n"
    root = _tree(tmp_path, {"world/mod.py": body})
    rows = scan.scan_tree(root)
    assert [(s.status, s.name) for s in rows] == [("report-only", "EntityRole.HERO")]
    assert scan.check_allowlist(rows, {}) == []


def test_runtime_is_excluded_and_content_semantics_gates(tmp_path):
    body = "def f(e):\n    return e.identity.role == EntityRole.HERO\n"
    assert _found(tmp_path, body, pkg="runtime") == []
    assert _found(tmp_path / "b", body, pkg="content_semantics") == [("EntityRole.HERO", "compare", "gating")]


def test_a_promoted_row_gates_inside_a_report_only_package_and_a_stale_promotion_fails(tmp_path):
    body = "class B:\n    def birth(self, a):\n        return a.role == EntityRole.HERO\n\n    def other(self, a):\n        return a.role == EntityRole.GUARD\n"
    root = _tree(tmp_path, {"core/b.py": body})
    promoted = frozenset({("src/core/b.py", "B.birth")})
    rows = scan.scan_tree(root, promoted=promoted)
    assert [(s.symbol, s.status) for s in rows] == [("B.birth", "gating"), ("B.other", "report-only")]
    assert scan.check_rulings(rows, promoted, {}) == []
    stale = scan.check_rulings(rows, frozenset({("src/core/b.py", "B.gone")}), {})
    assert len(stale) == 1 and "stale promotion src/core/b.py:B.gone" in stale[0]


def test_a_reasoned_exclusion_is_reported_not_gating_and_a_stale_one_fails(tmp_path):
    body = "_ROLE_COMPAT = {EntityRole.HERO: 'hero'}\n\n\ndef f(e):\n    return e.identity.role == EntityRole.HERO\n"
    root = _tree(tmp_path, {"entities/ident.py": body})
    exclusions = {("src/entities/ident.py", "<module>[_ROLE_COMPAT]"): "a projection"}
    rows = scan.scan_tree(root, exclusions=exclusions)
    assert sorted((s.symbol, s.status) for s in rows) == [("<module>[_ROLE_COMPAT]", "excluded"), ("f", "gating")]
    assert scan.check_allowlist(rows, {("src/entities/ident.py", "f", "EntityRole.HERO"): 1}) == []
    assert scan.check_rulings(rows, frozenset(), exclusions) == []
    assert "stale exclusion" in scan.check_rulings(rows, frozenset(), {("src/entities/ident.py", "gone"): "x"})[0]
    assert "has no reason" in scan.check_rulings(rows, frozenset(), {("src/entities/ident.py", "f"): " "})[0]


def test_every_domains_subpackage_is_gating(tmp_path):
    body = "def f(e):\n    return e.identity.role == EntityRole.HERO\n"
    root = _tree(tmp_path, {"domains/anything/mod.py": body})
    assert [s.status for s in scan.scan_tree(root)] == ["gating"]


# --------------------------------------------------------------------------------------------- the ratchet fires
BODY = "def f(e):\n    return e.identity.role == EntityRole.HERO\n"


def _gating(tmp_path: Path, body: str = BODY):
    return scan.scan_tree(_tree(tmp_path, {"ai/mod.py": body}))


def test_a_new_switch_fails(tmp_path):
    problems = scan.check_allowlist(_gating(tmp_path), {})
    assert len(problems) == 1 and "new name switch src/ai/mod.py:f on EntityRole.HERO" in problems[0]


def test_a_listed_switch_passes(tmp_path):
    assert scan.check_allowlist(_gating(tmp_path), {("src/ai/mod.py", "f", "EntityRole.HERO"): 1}) == []


def test_a_second_switch_under_an_existing_row_fails(tmp_path):
    two = _gating(tmp_path, "def f(e):\n    if e.identity.role == EntityRole.HERO:\n        return 1\n    return e.identity.role == EntityRole.HERO\n")
    problems = scan.check_allowlist(two, {("src/ai/mod.py", "f", "EntityRole.HERO"): 1})
    assert len(problems) == 1 and "2 found, the allowlist row counts 1" in problems[0]


def test_a_stale_row_fails_when_the_switch_is_gone(tmp_path):
    problems = scan.check_allowlist(_gating(tmp_path, "def f(e):\n    return 1\n"), {("src/ai/mod.py", "f", "EntityRole.HERO"): 1})
    assert len(problems) == 1 and "stale allowlist row" in problems[0] and "no such switch any more" in problems[0]


def test_a_row_that_counts_more_than_found_fails(tmp_path):
    problems = scan.check_allowlist(_gating(tmp_path), {("src/ai/mod.py", "f", "EntityRole.HERO"): 2})
    assert len(problems) == 1 and "lower the count" in problems[0]


def test_a_new_package_in_no_list_fails():
    assert scan.package_problems(["ai", "brand_new"], scan=("ai",), report_only=(), exclude=()) == [
        "src/brand_new is in no list: add it to SCAN, REPORT_ONLY or EXCLUDE in tools/test_architecture/name_switch_scan.py"
    ]
    assert scan.package_problems(["ai"], scan=("ai",), report_only=("ai",), exclude=()) == ["src/ai is in more than one list: SCAN, REPORT_ONLY"]
    assert scan.package_problems(["ai"], scan=("ai", "gone"), report_only=(), exclude=()) == ["SCAN names src/gone, which is not a package any more"]


# --------------------------------------------------------------------------------------------- the output
def test_text_and_json_rows_carry_file_line_symbol_and_name(tmp_path):
    rows = _gating(tmp_path)
    text = scan.render_text(rows).splitlines()
    assert text[0].startswith("src/ai/mod.py:2\tf\tEntityRole.HERO\tcompare\tgating")
    assert text[-1] == "# 1 switches: 1 gating, 0 report-only, 0 excluded"
    out = json.loads(scan.render_json(rows))
    assert out["counts"] == {"total": 1, "gating": 1, "report_only": 0, "excluded": 0}
    assert out["switches"][0]["file"] == "src/ai/mod.py" and out["switches"][0]["line"] == 2 and out["switches"][0]["name"] == "EntityRole.HERO"
