"""FLAGGED INTERIM (rpg-designer 2026-11-19): a kind that is not a catalog species (a role word from a compile with no content context) takes main's person-role fallback for its needs;
a catalog species without a need profile keeps base rates and is not an interim hit. Retires with stage-4b item AC / the P3 typed load error."""
from types import SimpleNamespace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.engine.biological_needs import PERSON_FALLBACK_PROFILE_ID, interim_role_need_counts, profile_id_for, unprofiled_need_counts


_TEST_DOUBLE_SPECIES_WITHOUT_PROFILE = "test_double_species_without_profile"


class _Species:
    def __init__(self, need_profile):
        self.need_profile = need_profile


class _Catalog:
    # no real species lacks a need_profile today (species.yaml, 2026-11-19); this pins the defensive branch
    _species = {"human": _Species("humanoid_survival"), _TEST_DOUBLE_SPECIES_WITHOUT_PROFILE: _Species(None)}

    def get_species(self, species_id):
        return self._species.get(species_id)

    def get_need_profile(self, profile_id):
        return object() if profile_id == "humanoid_survival" else None


def _body(eid, kind, role):
    return V2EntityBuilder(eid).kind(kind).location(0.0, 0.0).identity(role=role).build()


def test_a_non_catalog_kind_in_a_person_role_gets_the_person_profile():
    for role in (EntityRole.HERO, EntityRole.SHOPKEEPER, EntityRole.CITIZEN, EntityRole.WORKER, EntityRole.GUARD):
        assert profile_id_for(_body(1, "worker", role), _Catalog()) == PERSON_FALLBACK_PROFILE_ID


def test_a_non_catalog_kind_in_a_non_person_role_gets_base_rates():
    assert profile_id_for(_body(1, "world_boss", EntityRole.MONSTER), _Catalog()) is None


def test_a_catalog_species_without_a_need_profile_keeps_base_rates_whatever_its_role_and_is_no_interim_hit():
    body = _body(1, _TEST_DOUBLE_SPECIES_WITHOUT_PROFILE, EntityRole.CITIZEN)
    assert profile_id_for(body, _Catalog()) is None
    state = SimpleNamespace(entities={1: body})
    assert unprofiled_need_counts(state, _Catalog()) == {_TEST_DOUBLE_SPECIES_WITHOUT_PROFILE: 1} and interim_role_need_counts(state, _Catalog()) == {}


def test_the_interim_counter_counts_only_non_catalog_kinds():
    state = SimpleNamespace(entities={1: _body(1, "human", EntityRole.CITIZEN), 2: _body(2, "worker", EntityRole.WORKER), 3: _body(3, "worker", EntityRole.GUARD),
                                      4: _body(4, "world_boss", EntityRole.MONSTER), 5: _body(5, _TEST_DOUBLE_SPECIES_WITHOUT_PROFILE, EntityRole.CITIZEN)})
    assert interim_role_need_counts(state, _Catalog()) == {"worker|WORKER": 1, "worker|GUARD": 1, "world_boss|MONSTER": 1}
