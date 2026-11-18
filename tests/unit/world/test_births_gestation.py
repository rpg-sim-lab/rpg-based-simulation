# Compliance IDs: WORLD-122
"""M1 reproduction: gestation, the litter draw, unplaced newborns, a father or mother lost before term, and the death clear for every cause (rows G1-G6)."""
import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Domain, EntityRole, PassiveDeathCause
from src.core.state import AuthoritativeState, LifeStage
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.domains.world_emergence.schema import WorldEventCategory
from src.engine.apply import ApplyPath
from src.engine.spatial_query import SpatialQueryService  # noqa: F401  (the births step reads it)
from src.systems.lifecycle_systems.lifecycle import LifecycleSystem
from src.systems.world_systems.generator import EntityGenerator, NoFreeSpawnTile
from src.world import births
from src.world.births import BirthService
from tests.unit.world.test_births import _Catalog, _body, _conceptions, _generator, _run, _state


@pytest.fixture
def certain(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Catalog(real, 1.0))


def _pregnant_at_term():
    """A pair that conceived at tick 30 and the state at the due tick 2430."""
    state = _state(_body(1), _body(2))
    after = ApplyPath.apply_generation(state, _run(state), 31, 31)
    return AuthoritativeState(tick=2430, seed=42, entities=after.entities, next_entity_id=after.next_entity_id)


def _replace(state, entity_id, **combat):
    body = state.entities[entity_id]
    return AuthoritativeState(tick=state.tick, seed=state.seed, next_entity_id=state.next_entity_id,
                              entities={**state.entities, entity_id: dataclasses.replace(body, combat=dataclasses.replace(body.combat, **combat))})


def test_the_litter_is_drawn_over_the_table_in_ascending_size_order():
    weights = {2: 0.5, 1: 0.5}
    assert births._draw_litter(weights, 0.0) == 1 and births._draw_litter(weights, 0.49) == 1
    assert births._draw_litter(weights, 0.5) == 2 and births._draw_litter(weights, 0.999) == 2
    assert births._draw_litter({3: 1.0}, 0.7) == 3


def test_the_litter_draw_is_keyed_by_tick_mother_and_world_seed_and_apart_from_the_chance_draw():
    def draw(seed, tick, mother):
        state = AuthoritativeState(tick=tick, seed=seed, entities={mother: _body(mother)}, next_entity_id=mother + 1)
        return EntityGenerator.for_state(state).rng.get_float(Domain.SPAWN, tick, mother, sub_id=births.LITTER_DRAW_SUB_ID)
    assert draw(42, 30, 1) == draw(42, 30, 1)
    assert len({draw(42, 30, 1), draw(43, 30, 1), draw(42, 60, 1), draw(42, 30, 2)}) == 4
    assert births.LITTER_DRAW_SUB_ID != births.BIRTH_DRAW_SUB_ID and births.LITTER_DRAW_SUB_ID < 65536


def test_g1_g3_g4_one_pregnancy_at_a_time_born_at_term_once_and_then_cleared(certain):
    state = _state(_body(1), _body(2))
    conceived = ApplyPath.apply_generation(state, _run(state), 31, 31)
    pregnancy = conceived.entities[1].lifecycle.pregnancy
    assert pregnancy.due_tick == pregnancy.conceived_tick + 2400 and pregnancy.father_entity_id == 2          # G3: due = conceived + gestation
    for tick in (60, 90, 2400):                                                                                # G3: no conception while pregnant
        later = AuthoritativeState(tick=tick, seed=42, entities=conceived.entities, next_entity_id=conceived.next_entity_id)
        assert not _conceptions(_run(later)) and not _run(later).entities_add
    at_term = AuthoritativeState(tick=2430, seed=42, entities=conceived.entities, next_entity_id=conceived.next_entity_id)
    term = _run(at_term)
    (child,) = term.entities_add
    assert child.lifecycle.birth_tick == pregnancy.due_tick and child.lifecycle.parent_b_entity_id == pregnancy.father_entity_id    # G1
    born = ApplyPath.apply_generation(at_term, term, 2431, 2431)
    assert born.entities[1].lifecycle.pregnancy is None                                                        # G4: cleared with the birth
    again = AuthoritativeState(tick=2460, seed=42, entities=born.entities, next_entity_id=born.next_entity_id)
    assert not _run(again).entities_add                                                                        # G4: no second birth


def test_g2_born_plus_unplaced_is_the_litter_drawn_and_an_unplaceable_newborn_is_recorded_not_born(certain, monkeypatch):
    state = _pregnant_at_term()
    pregnant = state.entities[1]
    litter = dataclasses.replace(pregnant.lifecycle.pregnancy, litter_size=3)
    state = AuthoritativeState(tick=2430, seed=42, next_entity_id=state.next_entity_id,
                               entities={**state.entities, 1: dataclasses.replace(pregnant, lifecycle=dataclasses.replace(pregnant.lifecycle, pregnancy=litter))})
    generator = _generator(state)
    spots = iter([(6.0, 5.0)])

    def free(pos, st):
        try:
            return next(spots)
        except StopIteration:
            raise NoFreeSpawnTile("no clear tile") from None

    monkeypatch.setattr(generator, "free_spawn_position", free)
    update = BirthService.process_births(state, generator)
    unplaced = [e for e in update.world_events_add if e.category == WorldEventCategory.NEWBORN_UNPLACED]
    assert len(update.entities_add) == 1 and len(unplaced) == 2 and len(update.entities_add) + len(unplaced) == litter.litter_size
    assert sorted(e.payload["litter_slot"] for e in unplaced) == [1, 2] and all(e.subject == "1" for e in unplaced)


def test_a_litter_with_no_free_tile_at_all_clears_the_pregnancy_and_charges_nothing(certain, monkeypatch):
    state = _pregnant_at_term()
    generator = _generator(state)
    monkeypatch.setattr(generator, "free_spawn_position", lambda pos, st: (_ for _ in ()).throw(NoFreeSpawnTile("no clear tile")))
    update = BirthService.process_births(state, generator)
    assert not update.entities_add and update.entity_updates[1].lifecycle.pregnancy_clear
    assert update.entity_updates[1].biological is None or update.entity_updates[1].biological.is_noop()
    assert not update.entity_updates[1].lifecycle.reproduction_cooldowns_add
    assert len([e for e in update.world_events_add if e.category == WorldEventCategory.NEWBORN_UNPLACED]) == 1


def test_a_father_who_dies_before_term_still_fathers_the_litter_from_the_snapshot_and_the_bond_goes_only_to_the_living_mother(certain):
    state = _replace(_pregnant_at_term(), 2, alive=False)
    update = BirthService.process_births(state, _generator(state))
    (child,) = update.entities_add
    assert (child.lifecycle.parent_a_entity_id, child.lifecycle.parent_b_entity_id) == (1, 2)
    assert 2 not in update.entity_updates or update.entity_updates[2].social is None
    assert update.entity_updates[1].social is not None


def test_a_mother_who_is_dead_at_term_bears_nothing(certain):
    state = _replace(_pregnant_at_term(), 1, alive=False)
    assert not BirthService.process_births(state, _generator(state)).entities_add


def test_a_mother_born_at_term_and_dying_on_the_same_tick_gives_the_newborn_and_no_pregnancy_ended(certain):
    state = _pregnant_at_term()
    births_update = BirthService.process_births(state, _generator(state))
    dying = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(outcome_kind="DEFEAT", alive_set=False))})
    update = LifecycleSystem.resolve_lifecycle(state, births_update.merge(dying))
    assert len(update.entities_add) == 1                                                                          # G2: born = the litter drawn
    assert not [e for e in update.world_events_add if e.category == WorldEventCategory.PREGNANCY_ENDED]
    after = ApplyPath.apply_generation(state, update, 2431, 2431)
    assert after.entities[1].lifecycle.pregnancy is None and after.entities[1].lifecycle.death_record is not None   # G6


@pytest.mark.parametrize("cause", ["STARVATION", "OLD_AGE", "KILL"])
def test_g6_every_death_cause_clears_the_pregnancy_in_that_tick_s_update(certain, cause):
    state = _pregnant_at_term()
    mother = state.entities[1]
    life = mother.lifecycle
    if cause == "STARVATION":
        life = dataclasses.replace(life, passive_death_cause=PassiveDeathCause.STARVATION, passive_death_cause_tick=state.tick - 1)
    if cause == "OLD_AGE":
        life = dataclasses.replace(life, age_ticks=life.max_age_ticks)
    mother = dataclasses.replace(mother, lifecycle=life)
    state = AuthoritativeState(tick=100, seed=42, entities={**state.entities, 1: mother}, next_entity_id=state.next_entity_id)
    combat = CombatUpdate(outcome_kind="KILL", alive_set=False) if cause == "KILL" else None
    update = LifecycleSystem.resolve_lifecycle(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=combat)}) if combat else StateUpdate())
    ended = [e for e in update.world_events_add if e.category == WorldEventCategory.PREGNANCY_ENDED]
    assert update.entity_updates[1].lifecycle.pregnancy_clear and len(ended) == 1 and ended[0].tick == 100
    assert ApplyPath.apply_generation(state, update, 101, 101).entities[1].lifecycle.pregnancy is None


def test_an_unrelated_runtime_error_from_the_placement_path_propagates_and_is_not_an_unplaced_newborn(certain, monkeypatch):
    state = _pregnant_at_term()
    generator = _generator(state)
    monkeypatch.setattr(generator, "free_spawn_position", lambda pos, st: (_ for _ in ()).throw(RuntimeError("a bug")))
    with pytest.raises(RuntimeError, match="a bug"):
        BirthService.process_births(state, generator)
