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


# ---- TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS: the class scan (rpg-designer u24, H2 ruling (a)) -----------------------------------------------
# DIRECT: an occupation read compared (==, !=, in, not in) with a string constant, or a literal tuple/list/set of them, that is a NON_LIVING_KIND_ALLOWLIST species id: FAILS outright.
# REPORTED, pinned: an occupation read tested for membership in a NAMED string set (a module or class constant, one alias level) that holds a species id, and the reverse, an entity's
# kind compared with an occupation-only literal (a literal written to or compared with an occupation and no species id). A NEW reported hit fails here until it is ruled.
# The known reported hits are the three readers of the observability label sets (entity_kind_constants.py: BOSS_ENTITY_OCCUPATIONS and SPAWN_CADENCE_EXCLUDED_OCCUPATIONS, which mix the species ids
# world_boss and dragonkin with real occupations); they are the follow-up P3 rpg-planner (u24) files, not part of this fix.

def _occupation_reads(node):
    """An occupation read: ``<x>.occupation``, a local named ``occupation``, or ``occupation_of(<x>)`` / ``<module>.occupation_of(<x>)``."""
    if isinstance(node, ast.Attribute) and node.attr == "occupation":
        return True
    if isinstance(node, ast.Name) and node.id == "occupation":
        return True
    if isinstance(node, ast.Call):
        func = node.func
        return (isinstance(func, ast.Name) and func.id == "occupation_of") or (isinstance(func, ast.Attribute) and func.attr == "occupation_of")
    return False


def _string_constants(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return [node.value]
    if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
        return [value for element in node.elts for value in _string_constants(element)]
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("frozenset", "set", "tuple", "list") and node.args:
        return _string_constants(node.args[0])
    return []


def _named_string_sets(trees):
    """Name -> string members for every module-level and class-level ``NAME = <strings>`` assignment, plus one alias level (``NAME = OTHER_NAME``)."""
    named = {}
    aliases = {}
    for tree in trees:
        bodies = [tree.body] + [node.body for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        for body in bodies:
            for node in body:
                if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    name = node.targets[0].id
                    if _string_constants(node.value):
                        named[name] = _string_constants(node.value)
                    elif isinstance(node.value, ast.Name):
                        aliases[name] = node.value.id
    for name, target in aliases.items():
        if target in named:
            named.setdefault(name, named[target])
    return named


def _species_ids():
    import yaml

    from src.core.species import NON_LIVING_KIND_ALLOWLIST

    listed = {row["id"] for row in yaml.safe_load((ROOT / "data" / "content" / "living" / "species.yaml").read_text(encoding="utf-8"))}
    return listed | set(NON_LIVING_KIND_ALLOWLIST)


def scan_occupation_species_id_compares(sources):
    """``sources`` is {path: text}. Returns {"direct": [(path, line, text)], "reported": [(path, text)], "reverse": [(path, text)]}."""
    from src.core.species import NON_LIVING_KIND_ALLOWLIST

    species = _species_ids()
    trees = {path: ast.parse(text) for path, text in sources.items()}
    named = _named_string_sets(trees.values())
    occupation_literals = set()
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword) and node.arg == "occupation" and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                occupation_literals.add(node.value.value)
            if isinstance(node, ast.Compare) and any(_occupation_reads(side) for side in [node.left, *node.comparators]):
                for side in [node.left, *node.comparators]:
                    if not _occupation_reads(side):
                        occupation_literals.update(_string_constants(side))
    occupation_only = occupation_literals - species
    out = {"direct": [], "reported": [], "reverse": []}
    for path, tree in trees.items():
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            sides = [node.left, *node.comparators]
            if any(_occupation_reads(side) for side in sides):
                for side in sides:
                    if _occupation_reads(side):
                        continue
                    literals = _string_constants(side)
                    if literals:
                        if any(value in NON_LIVING_KIND_ALLOWLIST for value in literals):
                            out["direct"].append((path, node.lineno, ast.unparse(node)))
                    elif isinstance(side, (ast.Name, ast.Attribute)):
                        members = named.get(side.id if isinstance(side, ast.Name) else side.attr, [])
                        if any(value in species for value in members):
                            out["reported"].append((path, ast.unparse(node)))
            if any(_is_entity_kind(side) or (isinstance(side, ast.Call) and isinstance(side.func, ast.Name) and side.func.id == "species_of") for side in sides):
                for side in sides:
                    if _is_entity_kind(side) or isinstance(side, ast.Call):
                        continue
                    literals = _string_constants(side)
                    if not literals and isinstance(side, (ast.Name, ast.Attribute)):
                        literals = named.get(side.id if isinstance(side, ast.Name) else side.attr, [])
                    if any(value in occupation_only for value in literals):
                        out["reverse"].append((path, ast.unparse(node)))
    return out


# the known REPORTED hits: (file, the compare as ast.unparse writes it). The follow-up P3 rpg-planner (u24) files covers them; a new one fails until ruled.
_KNOWN_REPORTED = {
    ("src/observability/event_shapers.py", "occupation in self._BOSS_KINDS"),
    ("src/observability/event_shapers.py", "occupation_of(e) not in SPAWN_CADENCE_EXCLUDED_OCCUPATIONS"),
    ("src/observability/extraction/resources.py", "occupation_of(e) not in SPAWN_CADENCE_EXCLUDED_OCCUPATIONS"),
    ("src/observability/extraction/world.py", "occupation in BOSS_ENTITY_OCCUPATIONS"),
}


def _src_sources():
    return {str(path.relative_to(ROOT)): path.read_text(encoding="utf-8") for path in sorted((ROOT / "src").rglob("*.py"))}


def test_no_src_read_compares_an_occupation_directly_with_a_non_living_species_id():
    found = scan_occupation_species_id_compares(_src_sources())["direct"]
    assert found == [], f"an occupation is compared with a species id (read species_of instead): {found}"


def test_the_reported_membership_and_reverse_hits_are_the_known_ones_and_a_new_one_fails():
    found = scan_occupation_species_id_compares(_src_sources())
    assert set(found["reported"]) == _KNOWN_REPORTED, sorted(set(found["reported"]) ^ _KNOWN_REPORTED)
    assert found["reverse"] == [], f"an entity kind is compared with an occupation-only literal: {found['reverse']}"


def test_the_scan_flags_the_two_pre_fix_sites_and_every_planted_shape_and_ignores_the_clean_forms():
    def direct(text):
        return [line for _, line, _ in scan_occupation_species_id_compares({"x.py": text})["direct"]]

    # the two lines as they stood on main a30847030 (navigation.py:41 and threat.py:30)
    assert direct('def f(e):\n    if e.identity.occupation == "world_boss":\n        return 1\n') == [2]
    assert direct('has_boss = any(e.identity.occupation == "world_boss" and e.lifecycle.active and e.combat.alive for e in state.entities.values())\n') == [1]
    # the other direct shapes
    assert direct('x = occupation_of(e) == "magical_demonic_entity"') == [1]
    assert direct('x = e.identity.occupation in ("hero", "world_boss")') == [1]
    assert direct('x = "world_boss" != e.identity.occupation') == [1]
    # clean forms
    assert direct('x = species_of(e) == "world_boss"') == [] and direct('x = e.identity.occupation == "ancient_sentinel"') == [] and direct('x = e.identity.occupation in ("hero", "guard")') == []
    assert direct('x = e.kind == "world_boss"') == []
    # reported: a named set that mixes a species id with occupations, tested against an occupation (module constant, class constant and one alias)
    module_set = 'LABELS = frozenset(("world_boss", "ancient_sentinel"))\nx = occupation_of(e) in LABELS\n'
    assert scan_occupation_species_id_compares({"x.py": module_set})["reported"] == [("x.py", "occupation_of(e) in LABELS")]
    class_alias = 'LABELS = ("dragonkin",)\nclass C:\n    KINDS = LABELS\n    def f(self, occupation):\n        return occupation in self.KINDS\n'
    assert scan_occupation_species_id_compares({"x.py": class_alias})["reported"] == [("x.py", "occupation in self.KINDS")]
    assert scan_occupation_species_id_compares({"x.py": 'OK = ("hero", "guard")\nx = occupation_of(e) in OK\n'})["reported"] == []  # a set of real occupations is clean
    # reverse: an entity kind compared with a literal that only ever appears as an occupation
    reverse = 'def f(e):\n    a = spawn(occupation="ancient_sentinel")\n    return e.kind == "ancient_sentinel"\n'
    assert scan_occupation_species_id_compares({"x.py": reverse})["reverse"] == [("x.py", "e.kind == 'ancient_sentinel'")]
    assert scan_occupation_species_id_compares({"x.py": 'x = e.kind == "wolf"'})["reverse"] == []
