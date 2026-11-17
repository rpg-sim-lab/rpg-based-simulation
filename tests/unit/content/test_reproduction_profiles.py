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
    "litter_size": 1, "mate_radius_tiles": 5, "fed_line": 30, "birth_hunger_cost": 20,
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
    assert repo.get_reproduction_profile("test_births").litter_size == 1
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
    ("birth_chance_per_check", 1.5), ("birth_chance_per_check", -0.1), ("min_birth_interval_ticks", 0), ("litter_size", 0),
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
