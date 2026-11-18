"""TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD, step 5: the `identity.properties["species_id"]` mirror is gone.

`EntityState.kind` is the species id (step 4); `species_of` is the one way to read it. K12 (static, rpg-designer ruling 67cc6f6d): production code that reads or writes the key
`"species_id"` of an entity's properties = 0. The only `"species_id"` string keys allowed in src are named below, each with the reason it is not the mirror.
"""
from __future__ import annotations

import ast
from pathlib import Path

from src.core.species import species_of
from src.entities.archetype_factory import ArchetypeEntityFactory, EntitySpawnContext
from src.entities.runtime_contract import ResolvedEntityRuntimeContract

SRC = Path(__file__).resolve().parents[3] / "src"

# (file relative to src, why it is not the mirror). The event payload key carries the VALUE `species_of(entity)`; it is an output field, not an entity property.
ALLOWED_KEY_SITES = {
    "observability/event_shapers.py": "combat participant snapshot payload field; its value is species_of(entity)",
}


def _sites_of_species_id_key():
    """Every place src names the string key "species_id" as a subscript, a dict-literal key, a keyword-free `.get/.pop/.setdefault` argument or a dict() key."""
    found = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            hit = False
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and node.slice.value == "species_id":
                hit = True
            elif isinstance(node, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "species_id" for k in node.keys):
                hit = True
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"get", "pop", "setdefault", "__getitem__"}
                  and node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == "species_id"):
                hit = True
            if hit:
                found.append((path.relative_to(SRC).as_posix(), node.lineno))
    return found


def test_k12_no_production_reader_or_writer_of_the_species_id_mirror():
    offenders = [(f, line) for f, line in _sites_of_species_id_key() if f not in ALLOWED_KEY_SITES]
    assert offenders == [], f"src names the mirror key 'species_id' at {offenders}; read species_of(entity) instead"


def test_the_allowed_key_sites_are_still_real_sites():
    files = {f for f, _ in _sites_of_species_id_key()}
    assert set(ALLOWED_KEY_SITES) <= files, "an allowed site no longer exists: delete its row"


def test_the_archetype_factory_no_longer_writes_the_mirror():
    contract = ResolvedEntityRuntimeContract(archetype_id="human_worker", species_id="human", faction_id="town_council", role_id="worker", kind="human",
                                             hp=80, max_hp=80, atk=8, def_stat=4, attack_range=1, readiness=100.0, inventory_items={}, starting_gold=0.0, traits=(), themes=())
    entity = ArchetypeEntityFactory().build_entity(1, contract, EntitySpawnContext())
    assert "species_id" not in entity.identity.properties
    assert species_of(entity) == "human"


# ---- step 5 ruling: needs come from the species; a set-but-unprofiled species runs on base rates and is counted ---------------------------------

class _Species:
    def __init__(self, need_profile):
        self.need_profile = need_profile


class _Catalog:
    def __init__(self):
        self._species = {"human": _Species("humanoid_survival"), "blob": _Species(None)}

    def get_species(self, species_id):
        return self._species.get(species_id)

    def get_need_profile(self, profile_id):
        return object() if profile_id == "humanoid_survival" else None


def _state(*kinds):
    from types import SimpleNamespace
    from src.core.builder import V2EntityBuilder
    entities = {i + 1: V2EntityBuilder(i + 1).kind(k).location(0.0, 0.0).build() for i, k in enumerate(kinds)}
    return SimpleNamespace(entities=entities)


def test_a_species_not_in_content_gets_no_profile_and_is_counted_per_species():
    from src.engine.biological_needs import profile_id_for, unprofiled_need_counts
    state = _state("human", "TEST", "TEST", "blob", "world_boss")
    catalog = _Catalog()
    assert profile_id_for(state.entities[1], catalog) == "humanoid_survival"
    assert profile_id_for(state.entities[2], catalog) is None  # no role fallback: needs come from the species
    assert unprofiled_need_counts(state, catalog) == {"TEST": 2, "blob": 1, "world_boss": 1}


def test_the_count_is_empty_when_every_species_has_a_profile():
    from src.engine.biological_needs import unprofiled_need_counts
    assert unprofiled_need_counts(_state("human", "human"), _Catalog()) == {}
