# Compliance IDs: WORLD-122
"""The coin and world-boss counter kit (tools/rpg_measure/coin_boss_spy.py): pure unit tests on hand-built states, no world build, no kernel."""
import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.treasury import total_coin
from src.engine.apply import ApplyPath
from tools.rpg_measure import coin_boss_spy as kit


def _body(entity_id, gold=0, alive=True, kind="human"):
    return V2EntityBuilder(entity_id).kind(kind).location(1.0, 1.0).inventory(gold=gold).combat(alive=alive).build()


def _state(*bodies, tick=1):
    return AuthoritativeState(tick=tick, seed=42, entities={b.id: b for b in bodies}, next_entity_id=max(b.id for b in bodies) + 1)


def test_the_total_is_the_treasury_partition_and_a_purse_move_is_a_coin_moving_tick_with_no_world_delta():
    start = _state(_body(1, gold=10), _body(2, gold=5), tick=0)
    moved = _state(_body(1, gold=7), _body(2, gold=8), tick=1)
    spy = kit.CoinBossSpy(start)
    spy.observe(start, None, moved)
    report = spy.report()
    assert total_coin(start) == total_coin(moved) == 15.0 and report["coin_moving_ticks"] == 1 and report["delta_rows_total"] == 0
    assert report["non_vacuous"] is True and report["net_delta_before_declared"] == 0.0


def test_a_world_with_no_purse_movement_is_vacuous_and_a_created_coin_is_a_delta_row():
    start = _state(_body(1, gold=10), tick=0)
    still = _state(_body(1, gold=10), tick=1)
    spy = kit.CoinBossSpy(start)
    spy.observe(start, None, still)
    assert spy.report()["non_vacuous"] is False and spy.report()["coin_moving_ticks"] == 0
    created = _state(_body(1, gold=10), _body(2, gold=4), tick=2)
    spy.observe(still, None, created)
    report = spy.report()
    assert report["delta_rows_total"] == 1 and report["unexplained_delta_rows"] == [{"tick": 2, "delta": 4.0, "declared": None}]
    assert report["net_delta_before_declared"] == 4.0


def test_declared_and_both_boss_columns_are_stubs_until_ruled():
    start = _state(_body(1, gold=1), tick=0)
    spy = kit.CoinBossSpy(start)
    spy.observe(start, None, _state(_body(1, gold=1), tick=1))
    report = spy.report()
    assert report["declared"] is None and report["v6"] is None and report["declared_source"] == "STUB"
    assert report["boss_state_source"] == "STUB" and report["boss_predicate_source"] == "STUB"
    assert report["boss_state_max"] is None and report["boss_predicate_max"] is None and report["boss_disagreements"] == []


def test_the_wired_columns_count_bosses_report_a_disagreement_and_a_declared_source_forms_v6(monkeypatch):
    start = _state(_body(1, gold=1), tick=0)
    monkeypatch.setattr(kit, "BOSS_STATE_COUNT", kit.state_boss_count)
    monkeypatch.setattr(kit, "BOSS_PY_PREDICATE", lambda body: False)  # a drifted copy of the predicate: sees no boss
    monkeypatch.setattr(kit, "DECLARED_SOURCE", lambda prior, update, state: 3.0)
    spy = kit.CoinBossSpy(start)
    spy.observe(start, None, _state(_body(1, gold=4), _body(2, kind="world_boss"), tick=1))
    report = spy.report()
    assert report["boss_state_max"] == 1 and report["boss_predicate_max"] == 0
    assert report["boss_disagreements"] == [{"tick": 1, "state": 1, "predicate": 0}]
    assert report["declared"] == 3.0 and report["net_delta_before_declared"] == 3.0 and report["v6"] == 0.0


def test_two_living_bosses_read_two_and_a_dead_one_does_not_count():
    state = _state(_body(1, kind="world_boss"), _body(2, kind="world_boss"), _body(3, kind="world_boss", alive=False), _body(4))
    assert kit.state_boss_count(state) == 2


def test_the_coin_control_observes_a_copy_and_the_original_state_is_untouched():
    start = _state(_body(1, gold=10), _body(2, gold=5), tick=0)
    spy = kit.CoinBossSpy(start)
    spy.observe(start, None, start)
    out = spy.control_report("coin:7")
    assert out["net_delta_before_declared"] == 7.0 == out["expected"]
    assert total_coin(start) == 15.0 and start.entities[1].inventory.gold == 10  # the observed state never changed


def test_the_boss_control_rekinds_a_copy_and_reads_k_on_the_candidate_count(monkeypatch):
    start = _state(_body(1), _body(2), _body(3), tick=0)
    monkeypatch.setattr(kit, "BOSS_STATE_COUNT", kit.state_boss_count)
    spy = kit.CoinBossSpy(start)
    spy.observe(start, None, start)
    out = spy.control_report("boss:2")
    assert out["state"] == 2 == out["expected"] == out["candidate_state_count"]
    assert kit.state_boss_count(start) == 0  # the original has no boss
    with pytest.raises(ValueError):
        spy.control_report("nope:1")


def test_install_wraps_the_apply_path_and_restore_puts_the_original_back():
    original = ApplyPath.__dict__["apply_generation"]
    spy = kit.CoinBossSpy(_state(_body(1), tick=0)).install()
    try:
        assert ApplyPath.__dict__["apply_generation"] is not original
    finally:
        spy.restore()
    assert ApplyPath.__dict__["apply_generation"].__func__ is original.__func__


def test_the_logging_handler_turns_error_records_into_rows():
    import logging
    handler = kit.LoggingErrors()
    log = logging.getLogger("coin_boss_spy_test")
    log.addHandler(handler)
    try:
        log.warning("not a row")
        log.error("boom %s", 1)
    finally:
        log.removeHandler(handler)
    assert [r["message"] for r in handler.rows] == ["boom 1"]
