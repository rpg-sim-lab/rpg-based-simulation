# Compliance IDs: WORLD-122
"""ArchetypeEntityFactory.build_newborn: the species' newborn body at CHILD, none of the archetype's job (M1 births, rulings v2.2 D3)."""
import pytest

from src.content.repository import CatalogRepository
from src.content.resolver import EntityArchetypeResolver
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import LifeStage
from src.systems.lifecycle_systems.genetics import GeneticsSystem
from src.entities.archetype_factory import ArchetypeEntityFactory, NewbornBirth
from src.entities.contract_builder import resolved_archetype_to_contract


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def _parent(entity_id: int, kind: str, role: int, **properties):
    return (
        V2EntityBuilder(entity_id).kind(kind).location(3.0, 4.0)
        .identity(role=role, faction=Faction.TOWN_COUNCIL, properties=properties, occupation="worker")
        .navigation(home_position=(1.0, 2.0), leash_radius=6.0)
        .build()
    )


def _newborn(catalog, archetype_id="village_worker", entity_id=900, seed=42, mother_role=EntityRole.CITIZEN, **mother_props):
    contract = resolved_archetype_to_contract(EntityArchetypeResolver(catalog).resolve(archetype_id))
    mother = _parent(1, contract.species_id, mother_role, **mother_props)
    mate = _parent(2, contract.species_id, mother_role)
    child = ArchetypeEntityFactory().build_newborn(
        entity_id, contract, NewbornBirth(mother, mate, (3.0, 4.0), 120, seed, GeneticsSystem.generate_profile_from_seed(1), GeneticsSystem.generate_profile_from_seed(2), "r1"))
    return contract, mother, mate, child


def test_newborn_takes_the_archetype_body_and_none_of_its_job(catalog):
    contract, mother, mate, child = _newborn(catalog)
    assert child.kind == contract.species_id
    assert (child.combat.hp, child.combat.max_hp, child.combat.atk, child.combat.def_stat) == (contract.hp, contract.max_hp, contract.atk, contract.def_stat)
    assert child.identity.occupation is None
    assert child.identity.life_stage == LifeStage.CHILD
    assert child.inventory.gold == 0 and not child.inventory.items
    assert child.identity.traits == set(contract.species_trait_ids) and contract.species_trait_ids
    for job_key in ("role_id", "profession_id", "skill_profile_id", "archetype_id"):
        assert job_key not in child.identity.properties


def test_newborn_birth_record_and_faction_follow_the_parents(catalog):
    _, mother, mate, child = _newborn(catalog, faction_id="town_council")
    assert (child.lifecycle.parent_a_entity_id, child.lifecycle.parent_b_entity_id, child.lifecycle.birth_tick) == (1, 2, 120)
    assert child.identity.faction == mother.identity.faction
    assert child.identity.properties["faction_id"] == "town_council"
    assert child.strategic.home_region_id == "r1"
    assert child.navigation.home_position is None  # the anchor copy is held (_COPY_MOTHER_ANCHORS)


def test_newborn_role_is_monster_only_for_a_monster_mother(catalog):
    assert _newborn(catalog, mother_role=EntityRole.MONSTER)[3].identity.role == EntityRole.MONSTER
    assert _newborn(catalog, mother_role=EntityRole.WORKER)[3].identity.role == EntityRole.CITIZEN


def test_newborn_copies_the_mothers_population_id_and_spawn_region_and_never_writes_none(catalog):
    props = _newborn(catalog, population_id="p1", spawn_region="r0")[3].identity.properties
    assert (props["population_id"], props["spawn_region"]) == ("p1", "r0")
    bare = _newborn(catalog)[3].identity.properties
    assert "population_id" not in bare and "spawn_region" not in bare


def test_personality_is_keyed_by_world_seed_and_newborn_id(catalog):
    a = _newborn(catalog, entity_id=900, seed=42)[3].identity.personality
    assert a == _newborn(catalog, entity_id=900, seed=42)[3].identity.personality
    assert a != _newborn(catalog, entity_id=901, seed=42)[3].identity.personality
    assert a != _newborn(catalog, entity_id=900, seed=43)[3].identity.personality


def test_newborn_omits_the_home_anchor_and_home_region_when_there_is_none_and_copies_no_reputation(catalog):
    contract = resolved_archetype_to_contract(EntityArchetypeResolver(catalog).resolve("village_worker"))
    bare = V2EntityBuilder(1).kind("human").location(3.0, 4.0).build()
    child = ArchetypeEntityFactory().build_newborn(
        900, contract, NewbornBirth(bare, bare, (3.0, 4.0), 5, 42, GeneticsSystem.generate_profile_from_seed(1), GeneticsSystem.generate_profile_from_seed(2)))
    assert child.navigation.home_position is None and child.strategic.home_region_id is None
    assert child.social.public_reputation == V2EntityBuilder(900).build().social.public_reputation


def test_the_held_anchor_copy_restores_with_one_value(catalog, monkeypatch):
    from src.entities import archetype_factory

    monkeypatch.setattr(archetype_factory, "_COPY_MOTHER_ANCHORS", True)
    child = _newborn(catalog)[3]
    assert child.navigation.home_position == (1.0, 2.0) and child.navigation.leash_radius == 6.0
