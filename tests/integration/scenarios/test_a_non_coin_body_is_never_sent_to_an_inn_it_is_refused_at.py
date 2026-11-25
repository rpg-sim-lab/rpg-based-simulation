"""Divergence 2.224, through the real kernel (TCK-20261029-SHARED-ADMISSION-IGNORES-KEEPS-COIN-SO-A-NON-COIN-SUBJECT-IS-SENT-TO-A-SERVICE-THAT-REFUSES-IT, acceptance criterion 3).

A body whose PROPERTIES make it a non-coin eater (no ``keeps_coin_and_trades`` trait, a diet that fits the inn meal; picked from the catalog, never by a kind name), with a PLANTED purse of
the meal's price (a hungry twin) or the bed's price (a tired twin) and an inn within reach, is never dispatched EAT or REST at the inn over a run of ticks. Before the one admission rule
included the coin trait, the pull sent such a body to the inn, the dispatch fired, the service refused it (SOURCE_MISSING) and it repeated at every arrival."""
from __future__ import annotations

import pytest

from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState
from src.engine.behavior_consumers import get_kind_properties
from src.engine.domain.action_router import ActionRouter
from src.engine.kernel import Kernel
from src.engine.service_prices import EAT_PRICE_GOLD, REST_PRICE_GOLD
from src.platform.rng import DeterministicRNG

INN_ID, TICKS = 100, 300
_PROFILE = RuntimeProfile(name="non-coin-inn-test", hardware_class=HardwareClass.CLASS_B, max_ram_mb=512, max_cpu_percent=100.0, max_worker_count=1, max_queue_depth=500,
                          max_replay_buffer_kb=0, max_observability_budget_percent=0.0, max_tick_budget_ms=500.0)


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _non_coin_kinds_that_would_eat_at_an_inn():
    import yaml
    out = []
    for row in yaml.safe_load(open("data/content/living/species.yaml")):
        species, body = get_kind_properties(row["id"])
        if "keeps_coin_and_trades" not in (species.natural_traits or []) and body.diet is not None and "prepared" in body.diet:
            out.append(row["id"])
    return out


def _state(kind, gold, hunger, sleep_debt):
    entity = (V2EntityBuilder(1).kind(kind).properties({"species_id": kind}).location(0.0, 0.0).biological(hunger=hunger, sleep_debt=sleep_debt)
              .combat(readiness=100.0).inventory(gold=gold).build())
    inn = BuildingState(id=INN_ID, kind="inn", position=(5.0, 5.0), functional=True)
    return AuthoritativeState(tick=0, seed=42, world_time=0, entities={1: entity}, buildings={INN_ID: inn}, building_tiles={(5, 5): "inn"})


def _dispatches(monkeypatch, state):
    """Runs the real kernel and returns every EAT or REST the router was asked to execute for the subject at the inn."""
    seen = []
    real = ActionRouter.execute_action

    def spy(entity, payload=None, current_tick=0, *args, **kwargs):
        if entity.id == 1 and (payload or {}).get("action") in ("EAT", "REST") and (payload or {}).get("target_id") == INN_ID:
            seen.append((current_tick, payload.get("action")))
        return real(entity, payload, current_tick, *args, **kwargs)

    monkeypatch.setattr(ActionRouter, "execute_action", staticmethod(spy))
    kernel = Kernel(_PROFILE, state, DeterministicRNG(42), flags={"no_frame_pacing": True, "no_replay": True})
    try:
        for _ in range(TICKS):
            kernel.tick_once()
    finally:
        kernel.shutdown()
    return seen


def test_there_is_a_non_coin_kind_that_would_eat_at_an_inn_so_the_cases_below_are_not_empty():
    assert _non_coin_kinds_that_would_eat_at_an_inn() != []


def test_a_hungry_non_coin_body_with_the_price_of_a_meal_is_never_dispatched_eat_at_the_inn(monkeypatch):
    for kind in _non_coin_kinds_that_would_eat_at_an_inn():
        assert _dispatches(monkeypatch, _state(kind, EAT_PRICE_GOLD, hunger=60.0, sleep_debt=0.0)) == [], kind


def test_a_tired_non_coin_body_with_the_price_of_a_bed_is_never_dispatched_rest_at_the_inn(monkeypatch):
    for kind in _non_coin_kinds_that_would_eat_at_an_inn():
        assert _dispatches(monkeypatch, _state(kind, REST_PRICE_GOLD, hunger=0.0, sleep_debt=75.0)) == [], kind
