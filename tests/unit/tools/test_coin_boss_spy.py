# Compliance IDs: WORLD-122
"""The coin and world-boss counter kit (tools/rpg_measure/coin_boss_spy.py): unit tests on hand-built states with a fake ledger, no world build, no kernel."""
import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.treasury import total_coin
from src.engine.apply import ApplyPath
from src.observability.run_ledger import RunLedger
from tools.rpg_measure import coin_boss_spy as kit


class _Ledger:
    """A stand-in with the real ledger's V6 inputs: the first prior's coin, the last current's coin, the declared amount of added entities."""

    def __init__(self):
        self.reset_run_state()

    def reset_run_state(self):
        self._live, self._header, self._coin_first, self._coin_last, self._declared_coin, self.calls = False, False, 0.0, 0.0, 0.0, 0

    def configure(self, live):
        self._live = live

    def observe(self, prior, current, update):
        assert self._live, "start_ledger() must switch the ledger on before the first observation"
        self.calls += 1
        if not self._header:
            self._header, self._coin_first = True, total_coin(prior)
        self._coin_last = total_coin(current)
        self._declared_coin += sum(b.inventory.gold for b in (getattr(update, "entities_add", None) or []))
        return ["event the spy must discard"]


def _body(entity_id, gold=0, alive=True, kind="human", occupation=None, active=None):
    builder = V2EntityBuilder(entity_id).kind(kind).location(1.0, 1.0).inventory(gold=gold).combat(alive=alive)
    body = builder.build()
    if occupation is not None:
        body = dataclasses.replace(body, identity=dataclasses.replace(body.identity, occupation=occupation))
    if active is not None:
        body = dataclasses.replace(body, lifecycle=dataclasses.replace(body.lifecycle, active=active))
    return body


def _state(*bodies, tick=1):
    return AuthoritativeState(tick=tick, seed=42, entities={b.id: b for b in bodies}, next_entity_id=max(b.id for b in bodies) + 1)


def _spy(start, **kwargs):
    ledger = _Ledger()
    return kit.CoinBossSpy(start, ledger=ledger, **kwargs).start_ledger(), ledger


def test_a_purse_move_is_a_coin_moving_tick_with_no_world_delta_and_the_ledger_agrees():
    start = _state(_body(1, gold=10), _body(2, gold=5), tick=0)
    moved = _state(_body(1, gold=7), _body(2, gold=8), tick=1)
    spy, ledger = _spy(start)
    spy.observe(start, None, moved)
    calls = ledger.calls  # finish() resets the ledger, so read the call count first
    spy.finish()
    report = spy.report()
    assert total_coin(start) == total_coin(moved) == 15.0 and report["coin_moving_ticks"] == 1 and report["delta_rows_total"] == 0
    assert report["non_vacuous"] and report["wiring"] == "OK" and report["cell_valid"] and report["v6"] == 0.0 and calls == 1


def test_a_world_with_no_purse_movement_is_vacuous_and_created_coin_not_declared_reads_as_v6():
    start = _state(_body(1, gold=10), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=10), tick=1))
    assert spy.coin_moving_ticks == 0
    created = _state(_body(1, gold=10), _body(2, gold=4), tick=2)
    spy.observe(_state(_body(1, gold=10), tick=1), None, created)  # +4 coin with no declared add
    spy.finish()
    report = spy.report()
    assert not report["non_vacuous"] and report["delta_rows_total"] == 1 and report["unexplained_delta_rows"] == [{"tick": 2, "delta": 4.0}]
    assert report["v6"] == 4.0 and report["ledger_declared"] == 0.0


def test_a_declared_add_is_taken_from_the_ledger_and_v6_stays_zero():
    start = _state(_body(1, gold=10), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, type("U", (), {"entities_add": [_body(2, gold=4)]})(), _state(_body(1, gold=10), _body(2, gold=4), tick=1))
    spy.finish()
    report = spy.report()
    assert report["ledger_declared"] == 4.0 and report["net_delta"] == 4.0 and report["v6"] == 0.0


def test_a_ledger_that_disagrees_with_the_spys_own_total_marks_the_cell_wiring_mismatch():
    start = _state(_body(1, gold=10), tick=0)
    spy, ledger = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=10), tick=1))
    ledger._coin_last += 1.0  # the ledger saw a different state than the spy
    spy.finish()
    report = spy.report()
    assert report["wiring"] == "WIRING_MISMATCH" and report["cell_valid"] is False


def test_the_report_refuses_to_run_before_finish_and_finish_resets_the_ledger():
    start = _state(_body(1, gold=1), tick=0)
    spy, ledger = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=1), tick=1))
    with pytest.raises(RuntimeError):
        spy.report()
    spy.finish()
    assert ledger._live is False and ledger._coin_first == 0.0 and spy.ledger_snapshot["coin_last"] == 1.0  # snapshot kept, ledger cleared


def test_the_three_boss_columns_count_differently_and_a_disagreement_row_names_the_ids():
    start = _state(_body(1), tick=0)
    spy, _ = _spy(start)
    inactive = _body(2, kind="world_boss", active=False)  # columns 1 and 3 do not see it (inactive / no occupation); column 2 does
    sentinel = _body(3, occupation=kit.BOSS_OCCUPATION)  # only column 3 sees it
    spy.observe(start, None, _state(_body(1), inactive, sentinel, tick=1))
    spy.finish()
    report = spy.report()
    assert report["boss_max"] == {"predicate_post_964": 0, "raw_kind_alive": 1, "occupation_alive": 1}
    row = report["boss_disagreements"][0]
    assert row["tick"] == 1 and row["ids"] == {"predicate_post_964": [], "raw_kind_alive": [2], "occupation_alive": [3]}
    assert report["boss_record_line"] == "the columns differ only on lifecycle.active; both read entity.kind, so not independent of the species field"


def test_a_dead_boss_counts_in_no_column_and_all_three_agree_on_two_living_active_bosses():
    live = [_body(i, kind="world_boss", occupation=kit.BOSS_OCCUPATION, active=True) for i in (1, 2)]
    dead = _body(3, kind="world_boss", occupation=kit.BOSS_OCCUPATION, active=True, alive=False)
    ids = kit.boss_ids(_state(*live, dead, _body(4)))
    assert ids == {"predicate_post_964": [1, 2], "raw_kind_alive": [1, 2], "occupation_alive": [1, 2]}


def test_the_coin_control_has_the_ledger_observe_the_copy_at_the_last_tick_and_v6_reads_n():
    start = _state(_body(1, gold=10), _body(2, gold=5), tick=0)
    real_last = _state(_body(1, gold=7), _body(2, gold=8), tick=1)
    spy, ledger = _spy(start, control=("coin", 7.0), last_tick=1)
    spy.observe(start, None, real_last)
    spy.finish()
    report = spy.report()
    assert report["v6"] == 7.0 and report["ledger_coin_last"] == 22.0 and report["wiring"] == "OK" and report["cell_valid"] is False  # a control cell never counts
    assert total_coin(real_last) == 15.0 and real_last.entities[1].inventory.gold == 7  # the state the kernel keeps is untouched


def test_the_boss_control_makes_every_column_read_k_on_a_copy():
    start = _state(_body(1), _body(2), _body(3), tick=0)
    real_last = _state(_body(1), _body(2), _body(3), tick=1)
    spy, _ = _spy(start, control=("boss", 2), last_tick=1)
    spy.observe(start, None, real_last)
    spy.finish()
    assert spy.report()["boss_max"] == {"predicate_post_964": 2, "raw_kind_alive": 2, "occupation_alive": 2} and spy.report()["boss_disagreements"] == []
    assert kit.boss_ids(real_last) == {"predicate_post_964": [], "raw_kind_alive": [], "occupation_alive": []}  # the real state has no boss
    assert kit.parse_control("coin:3") == ("coin", 3.0) and kit.parse_control("boss:2") == ("boss", 2) and kit.parse_control(None) is None
    with pytest.raises(ValueError):
        kit.parse_control("nope:1")


def test_the_real_ledger_class_has_the_counters_the_spy_reads():
    for name in ("_coin_first", "_coin_last", "_declared_coin", "reset_run_state", "configure", "observe"):
        assert hasattr(RunLedger, name)


def test_install_wraps_the_apply_path_and_restore_puts_the_original_back():
    original = ApplyPath.__dict__["apply_generation"]
    spy, _ = _spy(_state(_body(1), tick=0))
    spy.install()
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
