import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityState, IdentityComponent, CombatComponent, TaskComponent, BuildingState
from src.engine.service_prices import REST_PRICE_GOLD
from src.engine.domain.action_router import ActionRouter
from src.core.updates import StateUpdate, EntityUpdate, TaskUpdate

from src.core.builder import V2EntityBuilder

def create_mock_entity(eid, pos=(10, 10), hp=50):
    return (V2EntityBuilder(eid)
        .kind("human")
        .properties({"species_id": "human"})  # a person: the services serve a kind with the coin-and-trade trait (decision 43)
        .location(*pos)
        .combat(hp=hp)
        .build())

def _inn_rest_update(gold):
    entity = replace(create_mock_entity(1, pos=(5.0, 5.0), hp=50), inventory=replace(create_mock_entity(1).inventory, gold=gold))
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: entity},
        town_tiles={(5, 5)},
        building_tiles={(5, 5): "inn"},
        buildings={10: BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True)}
    )
    # The bed lands with the action (building_services.py), not in the cadence-gated town phase.
    return ActionRouter.execute_action(entity, {"action": "REST", "target_id": 10}, state.tick, None, state)[1]


def test_building_interaction_inn_rest_recovery():
    # [TAG B RESHAPE] Decision 73: the bed is ONE paid transfer (the price on gold_cost under ATOMIC, hp and readiness on the same transfer); same property, new place.
    upd = _inn_rest_update(gold=REST_PRICE_GOLD)
    (bed,) = upd.resource_transfers
    assert bed.gold_cost == REST_PRICE_GOLD
    assert bed.combat_upd.hp_delta == 5
    assert upd.biological.sleep_debt_delta == 0.0  # decision 41 (ruled): the debt falls per tick while asleep; a bed has no separate rate
    assert bed.readiness_delta == 10.0 and upd.readiness_delta == 0.0


def test_inn_rest_without_gold_recovers_nothing_under_atomic():  # [TAG C REMOVED LAW] was: ..._still_recovers_as_on_main (free beds stay on)
    """Decision 73: nothing is free, so a subject that cannot pay the bed gets no bed: no transfer, no readiness, no health."""
    upd = _inn_rest_update(gold=0)
    assert not upd.resource_transfers and upd.readiness_delta == 0.0 and upd.combat is None


def test_standing_on_a_building_tile_is_not_a_service_trigger():
    """Building interactions are explicit (TOWN-020): an entity on an inn tile that proposes no REST gets no bed, charge or recovery.

    Positive control: ``test_building_interaction_inn_rest_recovery`` shows the explicit REST action on the same inn does.
    """
    from src.engine.pipeline import AuthoritativeApplyPipeline
    entity = replace(create_mock_entity(1, pos=(5.0, 5.0), hp=50), inventory=replace(create_mock_entity(1).inventory, gold=100))
    state = AuthoritativeState(
        tick=1, seed=42,
        entities={1: entity},
        town_tiles={(5, 5)},
        building_tiles={(5, 5): "inn"},
        buildings={10: BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True)},
    )
    refined = AuthoritativeApplyPipeline.refine(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1)}))
    upd = refined.entity_updates.get(1)
    assert upd is None or (not upd.resource_transfers and upd.combat is None and upd.readiness_delta == 0.0)
