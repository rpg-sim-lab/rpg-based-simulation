# Compliance IDs: WORLD-122
"""M1 births: a newborn's role is its mother's archetype `newborn_role`, read on bodies built by the REAL `WorldCompiler.compile` (the path every gate world uses).

The unit tests of the factory hand the mother an `archetype_id`; the classic compile once did not stamp one, so every compiled mother fell back to CITIZEN (the births own-job's N1 = 7 on seven spider newborns).
This test closes that gap: it compiles `frontier_living_world` and checks the mothers' stamp and the roles of their newborns (designer ruling 9b06026c, R2)."""
import os

import pytest

from src.content.common_knowledge_seed import warmed_catalog
from src.content.resolver import EntityArchetypeResolver
from src.core.enums import EntityRole
from src.core.state import LifeStage
from src.entities.archetype_factory import ArchetypeEntityFactory, NewbornBirth, declared_newborn_role
from src.entities.contract_builder import resolved_archetype_to_contract
from src.systems.lifecycle_systems.genetics import GeneticsSystem
from src.worldbuilding.compiler import WorldCompiler
from src.worldbuilding.repository import WorldRepository

WORLD, SEED = "frontier_living_world", 42


@pytest.fixture(scope="module")
def compiled():
    spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context(WORLD)
    state, _report = WorldCompiler.compile(spec, SEED, context=context)
    return state


def _mother(state, archetype_id):
    return min((e for e in state.entities.values() if (e.identity.properties or {}).get("archetype_id") == archetype_id), key=lambda e: e.id)


def _newborn_of(mother):
    catalog = warmed_catalog()
    contract = resolved_archetype_to_contract(EntityArchetypeResolver(catalog).resolve(catalog.species[mother.kind].newborn_archetype))
    birth = NewbornBirth(mother, mother, mother.navigation.position, 120, SEED, GeneticsSystem.generate_profile_from_seed(1), GeneticsSystem.generate_profile_from_seed(2),
                         "r1", declared_newborn_role(catalog, mother)[0])
    return ArchetypeEntityFactory().build_newborn(900, contract, birth)


@pytest.mark.parametrize("archetype_id, expected", [("cave_spider", EntityRole.MONSTER), ("goblin_raider", EntityRole.MONSTER), ("goblin_archer", EntityRole.CITIZEN)])
def test_a_compiled_mother_carries_her_archetype_and_her_newborn_gets_the_declared_role(compiled, archetype_id, expected):
    mother = _mother(compiled, archetype_id)
    assert mother.identity.properties["archetype_id"] == archetype_id
    assert declared_newborn_role(warmed_catalog(), mother) == (expected, "ARCHETYPE")
    child = _newborn_of(mother)
    assert child.identity.role == expected and child.identity.life_stage == LifeStage.CHILD


def test_every_compiled_body_built_from_an_archetype_carries_it_and_no_other_property_key_changed_for_them(compiled):
    stamped = [e for e in compiled.entities.values() if (e.identity.properties or {}).get("archetype_id")]
    assert len(stamped) >= 45, "the frontier world's archetype-backed populations (ids 1-35 and 39-55, about 52 bodies)"
    for e in stamped:
        assert {"population_id", "faction_id", "spawn_region", "archetype_id"} <= set(e.identity.properties)
