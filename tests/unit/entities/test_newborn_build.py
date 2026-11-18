# Compliance IDs: WORLD-122
"""ArchetypeEntityFactory.build_newborn: the species' newborn body at CHILD, none of the archetype's job (M1 births, rulings v2.2 D3)."""
import pytest

from src.core.species import SenseProfileError
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

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


def _troll_contract_and_birth(catalog, **mother_props):
    """The troll newborn contract resolved while the catalog is GOOD (a bad sense profile already fails in the resolver), and the birth for it."""
    contract = resolved_archetype_to_contract(EntityArchetypeResolver(catalog).resolve(catalog.species["troll"].newborn_archetype))
    mother, mate = _parent(1, contract.species_id, EntityRole.CITIZEN, **mother_props), _parent(2, contract.species_id, EntityRole.CITIZEN)
    birth = NewbornBirth(mother, mate, (3.0, 4.0), 120, 42, GeneticsSystem.generate_profile_from_seed(1), GeneticsSystem.generate_profile_from_seed(2), "r1")
    return contract, birth


@pytest.fixture()
def break_troll_senses(catalog):
    """Installs the module catalog as the warmed one the build paths read, then breaks the troll's sense profile; call the returned function AFTER the contract is resolved."""
    troll = catalog.species["troll"]
    configure_behavior_consumers(catalog)

    def _break():
        catalog.species["troll"] = troll.model_copy(update={"sense_profile": "nope"})
        configure_behavior_consumers(catalog)

    try:
        yield _break
    finally:
        catalog.species["troll"] = troll
        reset_behavior_consumers()


def test_a_newborn_of_a_species_with_no_usable_sense_profile_is_refused_at_build_newborn(catalog, break_troll_senses):
    contract, birth = _troll_contract_and_birth(catalog)
    break_troll_senses()
    with pytest.raises(SenseProfileError):
        ArchetypeEntityFactory().build_newborn(900, contract, birth)


def test_a_newborn_of_a_species_with_a_usable_sense_profile_is_built(catalog, break_troll_senses):
    contract, birth = _troll_contract_and_birth(catalog)
    child = ArchetypeEntityFactory().build_newborn(900, contract, birth)
    assert child.kind == contract.species_id == "troll"


def test_the_checked_contract_is_the_newborns_not_the_mothers(catalog, break_troll_senses, monkeypatch):
    """The mother names a different archetype in her own properties; the contract that build_newborn checks (recorded at the call) AND builds from is the NEWBORN's, whose archetype_id is the species' newborn_archetype. The
    SenseProfileError for a species with a declared-but-missing profile does not itself name the archetype, so the check is on the contract the guard received. Senses resolve by species, so the profile is the same either
    way: this proves which contract is checked and used, not per-archetype senses (out of scope, rpg-designer-ubuntu section 28)."""
    import src.entities.archetype_factory as factory
    contract, birth = _troll_contract_and_birth(catalog, mother_archetype_id="a_different_archetype")
    assert contract.archetype_id == catalog.species["troll"].newborn_archetype and birth.mother.identity.properties["mother_archetype_id"] == "a_different_archetype"
    seen = []
    real = factory.require_archetype_senses
    monkeypatch.setattr(factory, "require_archetype_senses", lambda c: (seen.append(c.archetype_id), real(c))[1])
    child = ArchetypeEntityFactory().build_newborn(900, contract, birth)
    assert seen == [contract.archetype_id] and child.kind == contract.species_id
    break_troll_senses()
    seen.clear()
    with pytest.raises(SenseProfileError):
        ArchetypeEntityFactory().build_newborn(901, contract, birth)
    assert seen == [contract.archetype_id]
