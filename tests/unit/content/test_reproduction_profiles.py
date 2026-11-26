# Compliance IDs: WORLD-CAT-TEST
"""The reproduction profile content schema and the loader's typed refusals (M1 births, owner B2: only kinds that eat)."""
import os
import shutil
import tempfile

import pytest
import yaml
from pydantic import ValidationError

from src.content.repository import CatalogRepository, ReproductionProfileError
from src.content.schema import ReproductionProfileDefinition

_PROFILE = {
    "id": "test_births", "birth_chance_per_check": 0.01, "min_birth_interval_ticks": 100,
    "gestation_ticks": 60, "litter_weights": {1: 1.0}, "mate_radius_tiles": 5, "fed_line": 30, "birth_hunger_cost": 20,
}


def _repo_with(species_profile: dict, need_hunger: str, profiles: list | None) -> CatalogRepository:
    tmp = tempfile.mkdtemp()
    shutil.copytree("data/content", os.path.join(tmp, "c"))
    root = os.path.join(tmp, "c", "living")
    species = yaml.safe_load(open(os.path.join(root, "species.yaml")))
    needs = yaml.safe_load(open(os.path.join(root, "need_profiles.yaml")))
    target = next(s for s in species if s["id"] == "wolf")
    target.update({"newborn_archetype": "hungry_wolf", **species_profile} if "reproduction_profile" in species_profile else species_profile)
    next(n for n in needs if n["id"] == target["need_profile"])["needs"]["hunger"] = need_hunger
    yaml.safe_dump(species, open(os.path.join(root, "species.yaml"), "w"))
    yaml.safe_dump(needs, open(os.path.join(root, "need_profiles.yaml"), "w"))
    if profiles is not None:
        shipped = yaml.safe_load(open(os.path.join(root, "reproduction_profiles.yaml")))
        yaml.safe_dump([*shipped, *profiles], open(os.path.join(root, "reproduction_profiles.yaml"), "w"))
    return CatalogRepository(os.path.join(tmp, "c"))


def test_profile_loads_and_a_species_names_it():
    repo = _repo_with({"reproduction_profile": "test_births"}, "very_low", [_PROFILE])
    repo.load_all()
    assert repo.get_reproduction_profile("test_births").litter_weights == {1: 1.0}
    assert repo.species["wolf"].reproduction_profile == "test_births"


def test_a_species_with_no_profile_has_no_births():
    repo = CatalogRepository("data/content")
    repo.load_all()
    assert all(s.reproduction_profile is None or s.reproduction_profile in repo.reproduction_profiles for s in repo.species.values())


def test_profile_on_a_kind_that_does_not_eat_is_refused_with_a_typed_error():
    repo = _repo_with({"reproduction_profile": "test_births"}, "none", [_PROFILE])
    with pytest.raises(ReproductionProfileError, match="hunger 'none'"):
        repo.load_all()


def test_unknown_profile_id_is_refused_with_a_typed_error():
    repo = _repo_with({"reproduction_profile": "nope"}, "very_low", [_PROFILE])
    with pytest.raises(ReproductionProfileError, match="not declared"):
        repo.load_all()


@pytest.mark.parametrize("field,value", [
    ("birth_chance_per_check", 1.5), ("birth_chance_per_check", -0.1), ("min_birth_interval_ticks", 0), ("gestation_ticks", 0),
    ("mate_radius_tiles", 0), ("fed_line", 101), ("birth_hunger_cost", 0), ("birth_hunger_cost", 101),
])
def test_out_of_range_field_is_rejected(field, value):
    with pytest.raises(ValidationError):
        ReproductionProfileDefinition(**{**_PROFILE, field: value})


def test_every_field_is_required():
    for field in [k for k in _PROFILE if k != "id"]:
        with pytest.raises(ValidationError):
            ReproductionProfileDefinition(**{k: v for k, v in _PROFILE.items() if k != field})


def test_newborn_archetype_is_required_with_a_profile_and_refused_without_one():
    repo = _repo_with({"reproduction_profile": "test_births", "newborn_archetype": None}, "very_low", [_PROFILE])
    with pytest.raises(ReproductionProfileError, match="no newborn_archetype"):
        repo.load_all()
    repo = _repo_with({"reproduction_profile": None, "newborn_archetype": "hungry_wolf"}, "very_low", [_PROFILE])
    with pytest.raises(ReproductionProfileError, match="but no reproduction_profile"):
        repo.load_all()


def test_newborn_archetype_must_exist_and_belong_to_the_species():
    repo = _repo_with({"reproduction_profile": "test_births", "newborn_archetype": "no_such_archetype"}, "very_low", [_PROFILE])
    with pytest.raises(ReproductionProfileError, match="not declared"):
        repo.load_all()
    repo = _repo_with({"reproduction_profile": "test_births", "newborn_archetype": "goblin_scout"}, "very_low", [_PROFILE])
    with pytest.raises(ReproductionProfileError, match="belongs to species 'goblin'"):
        repo.load_all()


def test_species_without_a_profile_load_exactly_as_before():
    repo = CatalogRepository("data/content")
    repo.load_all()
    no_births = [s for s in repo.species.values() if s.reproduction_profile is None]
    assert {s.id for s in no_births} >= {"undead", "spirit", "slime", "dragonkin"}
    assert all(s.newborn_archetype is None for s in no_births)


def test_every_shipped_newborn_archetype_belongs_to_its_species_and_resolves():
    from src.content.resolver import EntityArchetypeResolver
    repo = CatalogRepository("data/content")
    repo.load_all()
    for species in repo.species.values():
        if species.reproduction_profile is not None:
            assert EntityArchetypeResolver(repo).resolve(species.newborn_archetype).species_id == species.id


@pytest.mark.parametrize("gestation", [45, 31, 1, 100])
def test_a_gestation_that_is_not_a_positive_multiple_of_30_is_a_typed_content_error(gestation):
    repo = _repo_with({"reproduction_profile": "test_births"}, "very_low", [{**_PROFILE, "gestation_ticks": gestation}])
    with pytest.raises(ReproductionProfileError, match="multiple of 30"):
        repo.load_all()


@pytest.mark.parametrize("weights", [{}, {0: 1.0}, {1: 0.0}, {2: -1.0}])
def test_a_litter_table_must_be_non_empty_with_sizes_at_least_1_and_positive_weights(weights):
    repo = _repo_with({"reproduction_profile": "test_births"}, "very_low", [{**_PROFILE, "litter_weights": weights}])
    with pytest.raises(ReproductionProfileError, match="litter_weights"):
        repo.load_all()


def test_the_check_interval_a_gestation_must_divide_is_the_cadence_default():
    from src.content.schema import BIRTH_CHECK_INTERVAL_TICKS
    from src.engine.cadence import SystemCadence
    assert BIRTH_CHECK_INTERVAL_TICKS == SystemCadence().births


def test_the_shipped_profiles_have_a_gestation_and_a_litter_table_in_the_declared_order():
    from src.content.repository import CatalogRepository as Repo
    repo = Repo()
    repo.load_all()
    gestation = {k: v.gestation_ticks for k, v in repo.reproduction_profiles.items()}
    assert gestation == {"humanoid_births": 2400, "carnivore_births": 1200, "goblin_births": 900, "plant_eater_births": 600}
    assert all(sum(v.litter_weights.values()) > 0 for v in repo.reproduction_profiles.values())


def test_a_species_with_a_newborn_archetype_and_no_usable_sense_profile_is_refused_at_load():
    """PERC-02 / senses (A'): the checked set is exactly the species that declare a newborn_archetype; each must resolve a usable sense profile at LOAD (SenseProfileError), before tick 0."""
    from src.core.species import SenseProfileError
    repo = CatalogRepository("data/content")
    repo.load_all()
    checked = {s.id for s in repo.species.values() if s.newborn_archetype is not None}
    assert checked >= {"human", "wolf", "goblin", "spider", "orc", "elf", "dwarf", "troll"}
    for species_id in checked:
        assert repo.get_sense_profile(repo.species[species_id].sense_profile) is not None
    planted = _repo_with({"reproduction_profile": "test_births", "newborn_archetype": "hungry_wolf", "sense_profile": "no_such_sense_profile"}, "very_low", [_PROFILE])
    with pytest.raises(SenseProfileError, match="wolf"):
        planted.load_all()


def test_a_species_with_no_newborn_archetype_is_not_asked_for_senses_by_the_birth_check():
    """The birth check only visits species that declare a reproduction profile: a species that never bears newborns loads with its own sense-profile rule unchanged (here the shipped, valid one)."""
    repo = CatalogRepository("data/content")
    repo.load_all()
    never_born = [s for s in repo.species.values() if s.newborn_archetype is None]
    assert {s.id for s in never_born} >= {"undead", "spirit", "slime", "dragonkin"}


def _first_breeding_archetype_id(root: str) -> str:
    species = {s["id"]: s for s in yaml.safe_load(open(os.path.join(root, "living", "species.yaml")))}
    archetypes = yaml.safe_load(open(os.path.join(root, "entities", "entity_archetypes.yaml")))
    return next(a["id"] for a in archetypes if species[a["species"]].get("reproduction_profile"))


def test_a_breeding_archetype_with_no_newborn_role_is_refused_at_load_and_a_job_role_is_refused_by_the_schema():
    repo = _repo_with({}, "very_low", None)
    root = os.path.join(repo.content_dir, "entities")
    archetypes = yaml.safe_load(open(os.path.join(root, "entity_archetypes.yaml")))
    victim = _first_breeding_archetype_id(repo.content_dir)
    for a in archetypes:
        if a["id"] == victim:
            del a["newborn_role"]
    yaml.safe_dump(archetypes, open(os.path.join(root, "entity_archetypes.yaml"), "w"))
    with pytest.raises(ReproductionProfileError, match=f"archetype '{victim}'.*no newborn_role"):
        repo.load_all()
    from src.content.schema import EntityArchetypeDefinition
    declared = next(a for a in yaml.safe_load(open("data/content/entities/entity_archetypes.yaml")) if a["id"] == victim)
    for job_role in ("GUARD", "WORKER", "HERO", "SHOPKEEPER", "guard"):
        with pytest.raises(ValidationError):
            EntityArchetypeDefinition(**{**declared, "newborn_role": job_role})
    assert EntityArchetypeDefinition(**{**declared, "newborn_role": "CITIZEN"}).newborn_role == "CITIZEN"


def test_every_shipped_breeding_archetype_declares_a_newborn_role_and_a_non_breeding_one_needs_none():
    repo = CatalogRepository("data/content")
    repo.load_all()
    breeding = [a for a in repo.entity_archetypes.values() if repo.species[a.species].reproduction_profile is not None]
    assert len(breeding) == 27 and all(a.newborn_role in ("MONSTER", "CITIZEN") for a in breeding)
    assert all(a.newborn_role is None for a in repo.entity_archetypes.values() if repo.species[a.species].reproduction_profile is None)


def test_no_shipped_population_without_an_archetype_spawns_monsters_of_a_breeding_species():
    import glob
    from src.content_semantics.role import RoleSemanticsService
    from src.core.enums import EntityRole
    repo = CatalogRepository("data/content")
    repo.load_all()
    roles = RoleSemanticsService(repo)
    paths = glob.glob("data/worlds/*/resolved/world.resolved.yaml") + glob.glob("data/content/world_modules/*.yaml") + glob.glob("data/world_modules/populations/*.yaml")
    seen = 0
    for path in paths:
        doc = yaml.safe_load(open(path)) or {}
        for entry in (doc.get("entities") or doc.get("populations") or []):
            if isinstance(entry, dict) and not entry.get("archetype_id"):
                seen += 1
                assert roles.get_legacy_entity_role(entry["role"]) != EntityRole.MONSTER, (path, entry.get("id"))
    assert seen > 0


def test_the_assembly_refuses_an_archetype_less_population_that_spawns_monsters_of_a_breeding_species_and_allows_the_rest():
    from src.worldassembly.resolver import CompileProfileResolver
    repo = CatalogRepository("data/content")
    repo.load_all()
    resolver = CompileProfileResolver(repo)
    with pytest.raises(ReproductionProfileError, match="newborn_role"):
        resolver._refuse_legacy_monster_breeder("pop_x", "monster", "wolf")
    resolver._refuse_legacy_monster_breeder("pop_x", "worker", "wolf")  # not MONSTER: the no-archetype default (CITIZEN) is today's outcome
    resolver._refuse_legacy_monster_breeder("pop_x", "monster", None)  # no species named: nothing breeds
