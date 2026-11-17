# Compliance IDs: WORLD-122
"""The one births system (M1): eligibility, the chance draw, what a birth writes, and the apply path."""
import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole
from src.core.spawn_source import SpawnKind
from src.core.state import AuthoritativeState, LifeStage, RegionState
from src.core.updates import StateUpdate
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence, should_run
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.world_systems.generator import EntityGenerator
from src.world import births
from src.world.births import BirthService


class _Catalog:
    """The warmed catalog with the birth chance forced, so a test does not depend on a draw."""

    def __init__(self, real, chance):
        self._real, self._chance = real, chance

    def get_reproduction_profile(self, profile_id):
        return self._real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": self._chance})

    def __getattr__(self, name):
        return getattr(self._real, name)


@pytest.fixture
def certain(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Catalog(real, 1.0))


@pytest.fixture
def never(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Catalog(real, 0.0))


def _body(entity_id, kind="human", pos=(5.0, 5.0), hunger=0.0, role=EntityRole.CITIZEN, stage=LifeStage.ADULT, alive=True):
    return (
        V2EntityBuilder(entity_id).kind(kind).location(*pos).identity(role=role, life_stage=stage)
        .biological(hunger=hunger).combat(alive=alive).build()
    )


def _state(*entities, tick=30, regions=None):
    return AuthoritativeState(
        tick=tick, seed=42, entities={e.id: e for e in entities}, next_entity_id=max(e.id for e in entities) + 1, regions=regions or {},
    )


def _generator(state):
    generator = EntityGenerator(seed=state.seed + state.tick)
    generator._last_id = state.next_entity_id - 1
    return generator


def _run(state):
    return BirthService.process_births(state, _generator(state))


def test_cadence_is_one_field_of_30_ticks():
    cadence = SystemCadence()
    assert cadence.births == 30 and not hasattr(cadence, "reproduction_humanoid")
    assert should_run(60, None, cadence.births) and not should_run(61, None, cadence.births)


def test_a_fed_pair_in_range_bears_one_child_with_the_declared_shape(certain):
    state = _state(_body(1), _body(2, pos=(9.0, 5.0)))
    update = _run(state)
    (child,) = update.entities_add
    assert child.id == 3 and child.kind == "human"
    assert child.identity.life_stage == LifeStage.CHILD and child.identity.occupation is None
    assert (child.lifecycle.parent_a_entity_id, child.lifecycle.parent_b_entity_id, child.lifecycle.birth_tick) == (1, 2, 30)
    assert child.inventory.gold == 0 and child.identity.role == EntityRole.CITIZEN
    source = update.entity_spawn_sources[3]
    assert source.kind == SpawnKind.BIRTH and source.parent_ids == (1, 2)


def test_chance_zero_gives_no_birth(never):
    assert not _run(_state(_body(1), _body(2))).entities_add


def test_a_mother_above_the_fed_line_does_not_bear(certain):
    assert not _run(_state(_body(1, hunger=31.0), _body(2, hunger=31.0))).entities_add
    # only the mother's hunger counts: a hungry mate is fine when the lower id (visited first) is the fed mother
    assert len(_run(_state(_body(1, hunger=30.0), _body(2, hunger=90.0))).entities_add) == 1


def test_mother_pays_the_hunger_cost_once_and_it_clamps_at_100(certain):
    update = _run(_state(_body(1, hunger=10.0), _body(2)))
    assert update.entity_updates[1].biological.hunger_delta == 25.0
    assert 2 not in update.entity_updates or update.entity_updates[2].biological is None or update.entity_updates[2].biological.is_noop()


def test_a_non_eating_or_profile_less_kind_never_bears(certain):
    assert not _run(_state(_body(1, kind="undead"), _body(2, kind="undead"))).entities_add


def test_children_dead_and_inactive_bodies_are_not_parents(certain):
    assert not _run(_state(_body(1, stage=LifeStage.CHILD), _body(2, stage=LifeStage.CHILD))).entities_add
    assert not _run(_state(_body(1), _body(2, alive=False))).entities_add


@pytest.mark.parametrize("mate_x, bears", [(15.0, True), (15.5, False), (16.0, False)])
def test_mate_radius_is_chebyshev_ten_tiles(certain, mate_x, bears):
    assert bool(_run(_state(_body(1, pos=(5.0, 5.0)), _body(2, pos=(mate_x, 14.0)))).entities_add) is bears


def test_the_mate_is_the_lowest_eligible_id_in_range_and_each_body_is_a_parent_once(certain):
    update = _run(_state(_body(1), _body(2), _body(3), _body(4), _body(5)))
    parents = sorted(p for c in update.entities_add for p in (c.lifecycle.parent_a_entity_id, c.lifecycle.parent_b_entity_id))
    assert [(c.lifecycle.parent_a_entity_id, c.lifecycle.parent_b_entity_id) for c in update.entities_add] == [(1, 2), (3, 4)]
    assert len(parents) == len(set(parents))


def test_the_pair_interval_blocks_both_parents_until_it_expires_and_expired_entries_are_pruned(certain):
    state = _state(_body(1), _body(2))
    update = _run(state)
    assert update.entity_updates[1].lifecycle.reproduction_cooldowns_add == {2: 30 + 12000}
    after = ApplyPath.apply_generation(state, update, 31, 31)
    assert after.entities[1].lifecycle.reproduction_cooldowns == {2: 12030}
    later = AuthoritativeState(tick=60, seed=42, entities={1: after.entities[1], 2: after.entities[2]}, next_entity_id=after.next_entity_id)
    assert not _run(later).entities_add
    due = AuthoritativeState(tick=12030, seed=42, entities={1: after.entities[1], 2: after.entities[2]}, next_entity_id=after.next_entity_id)
    renewed = _run(due)
    assert len(renewed.entities_add) == 1
    assert renewed.entity_updates[1].lifecycle.reproduction_cooldowns_remove == (2,)
    assert renewed.entity_updates[1].lifecycle.reproduction_cooldowns_add == {2: 12030 + 12000}


def test_the_draw_does_not_depend_on_entity_insertion_order(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Catalog(real, 0.5))
    bodies = [_body(i, pos=(float(i), 5.0)) for i in range(1, 9)]
    forward = _run(_state(*bodies))
    backward = _run(_state(*reversed(bodies)))
    key = lambda u: [(c.id, c.lifecycle.parent_a_entity_id, c.lifecycle.parent_b_entity_id) for c in u.entities_add]
    assert key(forward) == key(backward)


def test_a_birth_nudges_the_region_young_births_by_one(certain):
    region = RegionState(id="town", name="Town", kind="town", bounds=(0, 0, 100, 100), population_cohorts={})
    update = _run(_state(_body(1), _body(2), regions={"town": region}))
    assert update.world_updates["town"].population_young_births_delta == 1


def test_the_hook_runs_births_on_its_own_30_tick_cadence_and_the_apply_path_adds_the_child(certain):
    state = _state(_body(1), _body(2), tick=60)
    cadence = SystemCadence()
    update = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), _generator(state), cadence)
    nxt = ApplyPath.apply_generation(state, update, 61, 61, cadence=cadence)
    assert sorted(nxt.entities) == [1, 2, 3] and nxt.next_entity_id == 4
    off_beat = _state(_body(1), _body(2), tick=61)
    assert not WorldDynamicsSystem.resolve_dynamics(off_beat, StateUpdate(), _generator(off_beat), cadence).entities_add


def test_a_parent_without_genes_gets_a_profile_keyed_by_world_seed_and_id(certain):
    def child(seed):
        state = AuthoritativeState(tick=30, seed=seed, entities={1: _body(1), 2: _body(2)}, next_entity_id=3)
        return _run(state).entities_add[0].lifecycle.genetic_profile
    assert child(42) == child(42) and child(42) != child(43)


def test_the_region_nudge_counts_newborns_not_pairs(monkeypatch):
    real = births.get_catalog()
    litter = real.get_reproduction_profile("humanoid_births").model_copy(update={"birth_chance_per_check": 1.0, "litter_size": 2})

    class _Litter:
        def get_reproduction_profile(self, profile_id):
            return litter

        def __getattr__(self, name):
            return getattr(real, name)

    monkeypatch.setattr(births, "get_catalog", lambda: _Litter())
    region = RegionState(id="town", name="Town", kind="town", bounds=(0, 0, 100, 100), population_cohorts={})
    update = _run(_state(_body(1), _body(2), regions={"town": region}))
    assert len(update.entities_add) == 2 and update.world_updates["town"].population_young_births_delta == 2
