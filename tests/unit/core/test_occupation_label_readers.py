"""M1 step 3 (rpg-designer 665b9718): every LABEL compare moves from `kind` to `occupation`, with the same literal; only readers that mean species (or display) stay on `kind`.

K5 (static): no label compare is left on an entity's `kind` outside the rows below. A compare of an entity's `kind` (attribute or getattr) with anything is found by AST; each file that still
has one is listed with the ruling that keeps it. A new one fails here until it is ruled.
The moved readers are exercised through their own suites; this file also reads the moved sets and tables directly.
"""
from __future__ import annotations

import ast
from pathlib import Path

from src.observability.entity_kind_constants import BOSS_ENTITY_OCCUPATIONS, SPAWN_CADENCE_EXCLUDED_OCCUPATIONS
from src.world.creature_territory import CreatureTerritoryService

ROOT = Path(__file__).resolve().parents[3]
_ENTITY_NAMES = {"entity", "ent", "prior_ent", "new_ent", "e", "target", "hostile", "hero", "a", "candidate_b", "victim", "attacker"}

# file -> why a compare on an entity-typed `.kind` remains there (step-1 inventory A, rulings 665b9718)
_KEPT = {
    "src/engine/evolution.py": "row 8: species (the goblin substring) and an unreachable tier digit; step 4",
    "src/world/reproduction_humanoid.py": "row 24: pairs by kind = species at step 4",
    "src/engine/compactor.py": "rows 1-7 plumbing: KindPatch no-op test",
    "src/engine/patches.py": "rows 1-7 plumbing: KindPatch apply (and a status-effect `e.kind`)",
    "src/observability/event_shapers.py": "row 14 display: demographic_kind_change compares previous and new kind",
    "src/observability/extraction/progression.py": "row 14 display: kind change event",
    "src/engine/building_arrival.py": "not an entity kind: a building / project `kind` read through getattr",
    "src/engine/tactical_avoid.py": "not an entity kind: a project `kind` read through getattr",
    "src/observability/live/entity_inspector.py": "not an entity kind: concern and blocker kinds",
}


def _is_entity_kind(n):
    if isinstance(n, ast.Attribute) and n.attr == "kind" and isinstance(n.value, ast.Name) and n.value.id in _ENTITY_NAMES:
        return True
    return (isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "getattr" and len(n.args) >= 2
            and isinstance(n.args[1], ast.Constant) and n.args[1].value == "kind")


def test_k5_no_label_compare_is_left_on_an_entitys_kind_outside_the_ruled_files():
    files = set()
    for path in sorted((ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Compare):
                for o in [n.left, *n.comparators]:
                    inner = o.func.value if isinstance(o, ast.Call) and isinstance(o.func, ast.Attribute) and o.func.attr in ("lower", "upper") else o
                    if _is_entity_kind(inner):
                        files.add(str(path.relative_to(ROOT)))
    assert files == set(_KEPT), sorted(files ^ set(_KEPT))


def test_the_renamed_label_sets_keep_their_members():
    assert BOSS_ENTITY_OCCUPATIONS == frozenset(("world_boss", "ancient_sentinel", "dragonkin"))
    assert SPAWN_CADENCE_EXCLUDED_OCCUPATIONS == (None, "world_boss", "ancient_sentinel", "goblin_raider", "dragonkin")


def test_the_territory_rates_keep_their_keys_and_default():
    assert CreatureTerritoryService.TERRITORY_MATURITY_RATES == {"goblin_warrior": 0.04, "orc_warrior": 0.03}
    assert CreatureTerritoryService.DEFAULT_TERRITORY_MATURITY_RATE == 0.03
