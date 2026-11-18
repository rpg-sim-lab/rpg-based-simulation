# Compliance IDs: WORLD-122
"""The one births system (M1): eligibility, the chance draw, what a birth writes, and the apply path."""
import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Domain, EntityRole
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
    """The warmed catalog with the birth chance forced and the mate gate off, so a test does not depend on a draw or on bonds (the gate has its own tests)."""

    def __init__(self, real, chance, litter=None):
        self._real, self._chance, self._litter = real, chance, litter or {1: 1.0}

    def get_reproduction_profile(self, profile_id):
        return self._real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": self._chance, "litter_weights": self._litter, "mate_gate": "none", "min_mutual_sentiment": None})

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


def _conceptions(update):
    """(mother, father) of every conception in the update, by mother id."""
    return sorted((m, u.lifecycle.pregnancy_set.father_entity_id) for m, u in update.entity_updates.items() if u.lifecycle and u.lifecycle.pregnancy_set)


def _conceive_then(state, at=None):
    """Conceive at `state.tick`, apply it, and return (state after, state at the first due tick)."""
    after = ApplyPath.apply_generation(state, _run(state), state.tick + 1, state.tick + 1)
    due = max(e.lifecycle.pregnancy.due_tick for e in after.entities.values() if e.lifecycle.pregnancy)
    at_term = AuthoritativeState(tick=at or due, seed=state.seed, entities=after.entities, next_entity_id=after.next_entity_id, regions=state.regions)
    return after, at_term


def _born(state):
    """The update of the check at term for a pair that conceived at `state.tick`."""
    return _run(_conceive_then(state)[1])


def test_cadence_is_one_field_of_30_ticks():
    cadence = SystemCadence()
    assert cadence.births == 30 and not hasattr(cadence, "reproduction_humanoid")
    assert should_run(60, None, cadence.births) and not should_run(61, None, cadence.births)


def test_a_fed_pair_in_range_conceives_and_bears_one_child_at_term_with_the_declared_shape(certain):
    state = _state(_body(1), _body(2, pos=(9.0, 5.0)))
    conception = _run(state)
    assert not conception.entities_add and _conceptions(conception) == [(1, 2)]
    pregnancy = conception.entity_updates[1].lifecycle.pregnancy_set
    assert (pregnancy.conceived_tick, pregnancy.due_tick, pregnancy.litter_size) == (30, 30 + 2400, 1)
    update = _born(state)
    (child,) = update.entities_add
    assert child.id == 3 and child.kind == "human"
    assert child.identity.life_stage == LifeStage.CHILD and child.identity.occupation is None
    assert (child.lifecycle.parent_a_entity_id, child.lifecycle.parent_b_entity_id, child.lifecycle.birth_tick) == (1, 2, 2430)
    assert child.inventory.gold == 0 and child.identity.role == EntityRole.CITIZEN
    source = update.entity_spawn_sources[3]
    assert source.kind == SpawnKind.BIRTH and source.parent_ids == (1, 2)
    assert update.entity_updates[1].lifecycle.pregnancy_clear


def test_chance_zero_gives_no_conception(never):
    assert not _conceptions(_run(_state(_body(1), _body(2))))


def test_a_mother_above_the_fed_line_does_not_conceive(certain):
    assert not _conceptions(_run(_state(_body(1, hunger=31.0), _body(2, hunger=31.0))))
    # only the mother's hunger counts: a hungry mate is fine when the lower id (visited first) is the fed mother
    assert len(_conceptions(_run(_state(_body(1, hunger=30.0), _body(2, hunger=90.0))))) == 1


def test_the_mother_pays_the_hunger_cost_once_per_birth_event_at_term_and_it_clamps_at_100(certain):
    update = _born(_state(_body(1, hunger=10.0), _body(2)))
    assert update.entity_updates[1].biological.hunger_delta == 25.0
    assert 2 not in update.entity_updates or update.entity_updates[2].biological is None or update.entity_updates[2].biological.is_noop()
    assert _born(_state(_body(1, hunger=0.0), _body(2))).entity_updates[1].biological.hunger_delta == 25.0
    _, at_term = _conceive_then(_state(_body(1, hunger=0.0), _body(2)))
    hungry = at_term.entities[1]
    hungry = dataclasses.replace(hungry, biological=dataclasses.replace(hungry.biological, hunger=90.0))
    starving = AuthoritativeState(tick=at_term.tick, seed=42, entities={**at_term.entities, 1: hungry}, next_entity_id=at_term.next_entity_id)
    assert _run(starving).entity_updates[1].biological.hunger_delta == 10.0, "hunger is not asked again at term, and the cost clamps at 100"


def test_a_non_eating_or_profile_less_kind_never_conceives(certain):
    assert not _conceptions(_run(_state(_body(1, kind="undead"), _body(2, kind="undead"))))


def test_children_dead_and_inactive_bodies_are_not_parents(certain):
    assert not _conceptions(_run(_state(_body(1, stage=LifeStage.CHILD), _body(2, stage=LifeStage.CHILD))))
    assert not _conceptions(_run(_state(_body(1), _body(2, alive=False))))


@pytest.mark.parametrize("mate_x, bears", [(15.0, True), (15.5, False), (16.0, False)])
def test_mate_radius_is_chebyshev_ten_tiles(certain, mate_x, bears):
    assert bool(_conceptions(_run(_state(_body(1, pos=(5.0, 5.0)), _body(2, pos=(mate_x, 14.0)))))) is bears


def test_the_mate_is_the_lowest_eligible_id_in_range_and_each_body_is_a_parent_once(certain):
    pairs = _conceptions(_run(_state(_body(1), _body(2), _body(3), _body(4), _body(5))))
    assert pairs == [(1, 2), (3, 4)]
    assert len({p for pair in pairs for p in pair}) == 4


def test_the_pair_interval_runs_from_the_conception_for_the_father_and_from_the_birth_for_the_mother(certain):
    state = _state(_body(1), _body(2))
    conception = _run(state)
    assert conception.entity_updates[2].lifecycle.reproduction_cooldowns_add == {1: 30 + 12000}
    assert conception.entity_updates[1].lifecycle.reproduction_cooldowns_add == {}
    after, at_term = _conceive_then(state)
    assert after.entities[2].lifecycle.reproduction_cooldowns == {1: 12030}
    assert not _conceptions(_run(AuthoritativeState(tick=60, seed=42, entities=after.entities, next_entity_id=after.next_entity_id)))
    term = _run(at_term)
    assert term.entity_updates[1].lifecycle.reproduction_cooldowns_add == {2: 2430 + 12000}
    born = ApplyPath.apply_generation(at_term, term, 2431, 2431)
    assert born.entities[1].lifecycle.pregnancy is None
    free = AuthoritativeState(tick=14430, seed=42, entities={1: born.entities[1], 2: born.entities[2]}, next_entity_id=born.next_entity_id)
    renewed = _run(free)
    assert _conceptions(renewed) == [(1, 2)]
    assert renewed.entity_updates[1].lifecycle.pregnancy_set.due_tick == 14430 + 2400
    assert renewed.entity_updates[2].lifecycle.reproduction_cooldowns_remove == (1,)


def test_the_draw_does_not_depend_on_entity_insertion_order(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Catalog(real, 0.5))
    bodies = [_body(i, pos=(float(i), 5.0)) for i in range(1, 9)]
    forward = _run(_state(*bodies))
    backward = _run(_state(*reversed(bodies)))
    key = _conceptions
    assert key(forward) == key(backward)


def test_a_birth_nudges_the_region_young_births_by_one_at_term_in_the_mothers_region(certain):
    region = RegionState(id="town", name="Town", kind="town", bounds=(0, 0, 100, 100), population_cohorts={})
    state = _state(_body(1), _body(2), regions={"town": region})
    assert not _run(state).world_updates
    assert _born(state).world_updates["town"].population_young_births_delta == 1


def test_the_hook_runs_births_on_its_own_30_tick_cadence_and_the_apply_path_adds_the_child_at_term(certain):
    state = _state(_body(1), _body(2), tick=60)
    cadence = SystemCadence()
    update = WorldDynamicsSystem.resolve_dynamics(state, StateUpdate(), _generator(state), cadence)
    nxt = ApplyPath.apply_generation(state, update, 61, 61, cadence=cadence)
    assert sorted(nxt.entities) == [1, 2] and nxt.entities[1].lifecycle.pregnancy.due_tick == 2460
    at_term = AuthoritativeState(tick=2460, seed=42, entities=nxt.entities, next_entity_id=nxt.next_entity_id)
    update = WorldDynamicsSystem.resolve_dynamics(at_term, StateUpdate(), _generator(at_term), cadence)
    born = ApplyPath.apply_generation(at_term, update, 2461, 2461, cadence=cadence)
    assert sorted(born.entities) == [1, 2, 3] and born.next_entity_id == 4
    off_beat = _state(_body(1), _body(2), tick=61)
    assert not WorldDynamicsSystem.resolve_dynamics(off_beat, StateUpdate(), _generator(off_beat), cadence).entity_updates


def test_a_parent_without_genes_gets_a_profile_keyed_by_world_seed_and_id(certain):
    def child(seed):
        state = AuthoritativeState(tick=30, seed=seed, entities={1: _body(1), 2: _body(2)}, next_entity_id=3)
        return _born(state).entities_add[0].lifecycle.genetic_profile
    assert child(42) == child(42) and child(42) != child(43)


def test_the_region_nudge_counts_newborns_not_pairs(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Catalog(real, 1.0, litter={2: 1.0}))
    region = RegionState(id="town", name="Town", kind="town", bounds=(0, 0, 100, 100), population_cohorts={})
    update = _born(_state(_body(1), _body(2), regions={"town": region}))
    assert len(update.entities_add) == 2 and update.world_updates["town"].population_young_births_delta == 2
    assert update.entity_updates[1].biological.hunger_delta == 25.0, "the cost is per birth event, not per newborn"


def _draw(seed, tick, mother_id=1):
    """The birth draw as BirthService makes it, from the tick's generator built by the one factory."""
    state = AuthoritativeState(tick=tick, seed=seed, entities={mother_id: _body(mother_id)}, next_entity_id=mother_id + 1)
    return EntityGenerator.for_state(state).rng.get_float(Domain.SPAWN, tick, mother_id, sub_id=births.BIRTH_DRAW_SUB_ID)


def test_two_world_seeds_give_different_birth_draws_for_the_same_tick_and_mother():
    assert _draw(42, 30) == _draw(42, 30)
    assert _draw(42, 30) != _draw(43, 30)


def test_the_birth_draw_does_not_alias_across_seed_and_tick_pairs_that_share_a_sum():
    # DeterministicRNG: base = seed + tick, then base ^ (domain << 48) ^ (tick << 32) ^ (id << 16) ^ sub_id; the tick term separates equal bases.
    assert 42 + 60 == 72 + 30
    assert _draw(42, 60) != _draw(72, 30)


def _mate_first(state, generator):
    """The previous order of the conception loop (mate search before the chance draw), kept here as the reference the reorder must equal; the births at term are the same."""
    catalog = births.get_catalog()
    profiles = births._Profiles(catalog)
    candidates = births._candidates(state, profiles)
    check = births._Check(state, generator, catalog)
    used, result = set(), StateUpdate()
    for mother in births._mothers_at_term(state, profiles):
        result = result.merge(births._birth_at_term(check, mother, profiles.of(births.species_of(mother))))
    for mother in candidates.values():
        profile = profiles.of(births.species_of(mother))
        if mother.id in used or profile is None or mother.biological.hunger > profile.fed_line or not births._past_interval(mother, state.tick):
            continue
        mate = births._find_mate(state, mother, candidates, used, profile.mate_radius_tiles, lambda m: births.passes_mate_gate(mother, m, profile))
        if mate is None:
            continue
        if generator.rng.get_float(Domain.SPAWN, state.tick, mother.id, sub_id=births.BIRTH_DRAW_SUB_ID) >= profile.birth_chance_per_check:
            continue
        used.update((mother.id, mate.id))
        result = result.merge(births._conceive(check, mother, mate, profile))
    return result


def _shape(update):
    return (
        [(c.id, c.kind, c.lifecycle.parent_a_entity_id, c.lifecycle.parent_b_entity_id, c.navigation.position) for c in update.entities_add],
        {k: repr(v) for k, v in sorted(update.entity_updates.items())},
        {k: repr(v) for k, v in sorted(update.world_updates.items())},
        sorted(update.entity_spawn_sources),
    )


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_drawing_before_the_mate_search_gives_the_same_births_as_searching_first(monkeypatch, seed):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Catalog(real, 0.3, litter={1: 0.5, 2: 0.5}))
    bodies = [_body(i, pos=(float(i % 5) * 3.0, float(i // 5) * 3.0), hunger=float((i * 7) % 45)) for i in range(1, 16)]
    bodies += [_body(20 + i, kind="wolf", pos=(30.0 + i, 30.0)) for i in range(4)] + [_body(30, kind="undead", pos=(5.0, 5.0))]
    total = conceived = 0
    state = AuthoritativeState(tick=0, seed=seed, entities={b.id: b for b in bodies}, next_entity_id=40)
    for tick in range(30, 3000, 30):
        state = AuthoritativeState(tick=tick, seed=seed, entities=state.entities, next_entity_id=state.next_entity_id)
        new = BirthService.process_births(state, _generator(state))
        old = _mate_first(state, _generator(state))
        assert _shape(new) == _shape(old)
        total += len(new.entities_add)
        conceived += len(_conceptions(new))
        state = ApplyPath.apply_generation(state, new, tick + 1, tick + 1)
    assert conceived > 0 and total > 0, "the equivalence is vacuous without conceptions and births"


def test_a_check_where_every_draw_fails_makes_no_spatial_query(never, monkeypatch):
    from src.engine.spatial_query import SpatialQueryService

    calls = []
    original = SpatialQueryService.nearby_entities
    monkeypatch.setattr(SpatialQueryService, "nearby_entities", staticmethod(lambda *a, **k: calls.append(1) or original(*a, **k)))
    assert not _run(_state(*[_body(i) for i in range(1, 9)])).entity_updates
    assert calls == []


def test_a_pregnant_body_is_never_a_mother_or_a_mate(certain):
    state = _state(_body(1), _body(2), _body(3))
    pregnant = ApplyPath.apply_generation(state, _run(state), 31, 31)
    assert pregnant.entities[1].lifecycle.pregnancy.father_entity_id == 2 and pregnant.entities[3].lifecycle.pregnancy is None
    later = AuthoritativeState(tick=60, seed=42, entities=pregnant.entities, next_entity_id=pregnant.next_entity_id)
    assert births._find_mate(later, later.entities[3], births._candidates(later, births._Profiles(births.get_catalog())), set(), 10.0, lambda m: True) is None
    assert not _conceptions(_run(later))
