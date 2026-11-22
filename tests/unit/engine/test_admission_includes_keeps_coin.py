"""Divergence 2.224 (TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT): the one admission rule includes the coin trait
(owner decision 43). A body without ``keeps_coin_and_trades`` is admitted to no inn meal or bed, so it has no INN_MEAL way, no inn bed target and is never dispatched EAT or REST at an
inn it would be refused at; a coin-keeping body with the same gold still is. The non-coin bodies are chosen by their PROPERTIES from the catalog (no trait, a diet that fits the inn meal),
never by a kind name."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.scorers import EatScorer, SleepScorer
from src.ai.goals.ways import WayKind, ways_in_reach
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.engine.behavior_consumers import get_kind_properties
from src.engine.building_arrival import building_arrival_update
from src.engine.building_services import service_delta
from src.engine.service_admission import admits, admits_at
from src.engine.service_prices import EAT_PRICE_GOLD, REST_PRICE_GOLD
from tests.unit.world.test_building_services_land_with_their_action import _hunger_project


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _species_ids():
    import yaml
    return [row["id"] for row in yaml.safe_load(open("data/content/living/species.yaml"))]


def _non_coin_kinds_that_would_eat_at_an_inn():
    """By properties: no `keeps_coin_and_trades` trait, and a diet that includes prepared food (so only the coin trait stands between the body and the meal)."""
    out = []
    for sid in _species_ids():
        sp, body = get_kind_properties(sid)
        diet = body.diet
        if "keeps_coin_and_trades" not in (sp.natural_traits or []) and diet is not None and "prepared" in diet:
            out.append(sid)
    return out


def _coin_kinds():
    return [sid for sid in _species_ids() if "keeps_coin_and_trades" in (get_kind_properties(sid)[0].natural_traits or [])]


def _world(kind, gold, at=(2.0, 5.0), **bio):
    ent = V2EntityBuilder(1).kind(kind).properties({"species_id": kind}).location(*at).inventory(gold=gold).build()
    ent = replace(ent, biological=replace(ent.biological, **bio))
    buildings = {10: BuildingState(id=10, kind="inn", position=(5.0, 5.0), functional=True)}
    state = AuthoritativeState(tick=1, seed=1, world_time=1000, entities={1: ent}, town_tiles={(5, 5)}, building_tiles={(5, 5): "inn"}, buildings=buildings)
    return state, ent


def test_the_content_has_a_non_coin_kind_that_would_eat_at_an_inn_so_the_cases_below_are_not_empty():
    assert _non_coin_kinds_that_would_eat_at_an_inn() != []
    assert _coin_kinds() != []


@pytest.mark.parametrize("gold", [EAT_PRICE_GOLD, REST_PRICE_GOLD, REST_PRICE_GOLD + 90])
def test_a_non_coin_body_with_the_price_is_admitted_to_no_inn_meal_or_bed_and_has_no_inn_way(gold):
    for kind in _non_coin_kinds_that_would_eat_at_an_inn():
        state, ent = _world(kind, gold, hunger=60.0, sleep_debt=60.0)
        assert admits(ent, "EAT") is False and admits(ent, "REST") is False, kind
        assert WayKind.INN_MEAL not in ways_in_reach(ent, state), kind
        assert EatScorer().score(ent, state).target_id != "10", kind  # never pulled to the inn meal
        assert SleepScorer().score(ent, state).target_id != "10", kind  # REST's twin: no inn bed target either


@pytest.mark.parametrize("gold", [EAT_PRICE_GOLD, REST_PRICE_GOLD])
def test_a_non_coin_body_standing_at_the_inn_is_never_dispatched_eat_or_rest(gold):
    for kind in _non_coin_kinds_that_would_eat_at_an_inn():
        state, ent = _world(kind, gold, at=(5.0, 5.0), hunger=60.0)
        update = building_arrival_update(state, ent, _hunger_project(10), 10)
        action = None if update.task is None else update.task.payload_set.get("action")
        assert action not in ("EAT", "REST"), (kind, action)
        assert service_delta(state, ent, "EAT", 1) is None and service_delta(state, ent, "REST", 1) is None, kind


def test_a_coin_keeping_body_with_the_same_gold_still_has_both_ways_and_is_dispatched_eat():
    for kind in _coin_kinds():
        if "prepared" not in (get_kind_properties(kind)[1].diet or []):
            continue
        state, ent = _world(kind, REST_PRICE_GOLD, hunger=60.0, sleep_debt=60.0)
        assert admits(ent, "EAT") is True and admits(ent, "REST") is True, kind
        assert WayKind.INN_MEAL in ways_in_reach(ent, state), kind
        assert SleepScorer().score(ent, state).target_id == "10", kind
        at_inn = replace(ent, navigation=replace(ent.navigation, position=(5.0, 5.0)))
        update = building_arrival_update(state, at_inn, _hunger_project(10), 10)
        assert update.task is not None and update.task.payload_set.get("action") == "EAT", kind


def test_admission_and_the_service_agree_for_every_kind_both_actions_and_enough_gold():
    for kind in _species_ids():
        for action in ("EAT", "REST"):
            state, ent = _world(kind, REST_PRICE_GOLD + EAT_PRICE_GOLD, at=(5.0, 5.0), hunger=60.0, sleep_debt=60.0)
            inn = state.buildings[10]
            delivered = service_delta(state, ent, action, 1) is not None
            assert admits_at(ent, inn, action, state) is delivered, (kind, action)


@pytest.mark.parametrize("gold", [EAT_PRICE_GOLD, REST_PRICE_GOLD + 90])
def test_the_hunger_scorer_reports_no_way_within_reach_for_a_non_coin_body_with_gold_and_an_inn_in_reach(gold):
    """The scorer level of 2.224 (asked by the gap-C ruling): the inn is in reach and the body holds the price, but a non-coin body (by properties) is admitted to no meal, so `EatScorer` names no
    target and says NO_WAY_WITHIN_REACH, while the same scene for a coin-keeping body names the inn."""
    from src.ai.goals.base import NeedAccess
    from src.engine.need_pull import HUNGER_LINE
    hunger = 0.75 * HUNGER_LINE
    for kind in _non_coin_kinds_that_would_eat_at_an_inn():
        state, ent = _world(kind, gold, hunger=hunger)
        score = EatScorer().score(ent, state)
        assert score.target_pos is None and score.need_access is NeedAccess.NO_WAY_WITHIN_REACH, (kind, score)
    for kind in _coin_kinds():
        if "prepared" not in (get_kind_properties(kind)[1].diet or []):
            continue
        state, ent = _world(kind, gold, hunger=hunger)
        score = EatScorer().score(ent, state)
        assert score.target_id == "10" and score.need_access is not NeedAccess.NO_WAY_WITHIN_REACH, (kind, score)
