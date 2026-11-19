# Compliance IDs: WORLD-122
"""The coin and world-boss counter kit (tools/rpg_measure/coin_boss_spy.py): unit tests on hand-built states with a fake ledger, no world build, no kernel."""
import dataclasses
import types

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.treasury import total_coin
from src.engine.apply import ApplyPath
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.run_ledger import RunLedger
from tools.rpg_measure import coin_boss_spy as kit


@pytest.fixture(autouse=True)
def _mode_off():
    """The kit asserts the global observability mode is OFF on every apply: every test runs with an OFF override and clears all overrides afterwards, so no override leaks to another test."""
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    yield
    ObservabilityConfig.clear_all_overrides()


class _Ledger:
    """A stand-in with the real ledger's public surface: reset_run_state, configure, observe and tally_event().payload (coin_first, coin_last, declared_coin)."""

    def __init__(self):
        self.reset_run_state()

    def reset_run_state(self):
        self.live, self.header, self.coin_first, self.coin_last, self.declared, self.calls = False, False, 0.0, 0.0, 0.0, 0
        self.declared_offset = 0.0  # a test plants a disagreement between the per-apply deltas and the end value through this

    def configure(self, live):
        self.live = live

    def observe(self, prior, current, update):
        assert self.live, "start_ledger() must switch the ledger on before the first observation"
        self.calls += 1
        if not self.header:
            self.header, self.coin_first = True, total_coin(prior)
        self.coin_last = total_coin(current)
        self.declared += sum(b.inventory.gold for b in (getattr(update, "entities_add", None) or []))
        return ["event the spy must discard"]

    def tally_event(self):
        return types.SimpleNamespace(payload={"coin_first": self.coin_first, "coin_last": self.coin_last, "declared_coin": self.declared + self.declared_offset})


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
    assert total_coin(start) == total_coin(moved) == 15.0 and report["coin_moving_ticks"] == 1 and report["total_change_rows_count"] == 0 and report["unexplained_total_count"] == 0
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
    assert not report["non_vacuous"] and report["total_change_rows_count"] == 1 and report["unexplained_total_count"] == 1
    assert report["unexplained_rows"] == [{"tick": 2, "delta": 4.0, "declared": 0.0, "unexplained": 4.0}]
    assert report["v6"] == 4.0 and report["ledger_declared"] == 0.0


def test_a_declared_add_is_taken_from_the_ledger_and_v6_stays_zero():
    start = _state(_body(1, gold=10), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, type("U", (), {"entities_add": [_body(2, gold=4)]})(), _state(_body(1, gold=10), _body(2, gold=4), tick=1))
    spy.finish()
    report = spy.report()
    assert report["ledger_declared"] == 4.0 and report["net_delta"] == 4.0 and report["v6"] == 0.0
    # the change is in total_change_rows with its declared amount, and it is NOT unexplained
    assert report["total_change_rows"] == [{"tick": 1, "delta": 4.0, "declared": 4.0, "unexplained": 0.0}]
    assert report["unexplained_rows"] == [] and report["unexplained_total_count"] == 0


def test_a_declared_add_that_does_not_show_up_in_the_total_and_a_partial_explanation_are_unexplained():
    start = _state(_body(1, gold=10), tick=0)
    spy, _ = _spy(start)
    # declared 4 but the world total did not move: unexplained = 0 - 4 = -4
    spy.observe(start, type("U", (), {"entities_add": [_body(9, gold=4)]})(), _state(_body(1, gold=10), tick=1))
    # +5 in the total, 2 declared: unexplained = 3
    prior = _state(_body(1, gold=10), tick=1)
    spy.observe(prior, type("U", (), {"entities_add": [_body(2, gold=2)]})(), _state(_body(1, gold=13), _body(2, gold=2), tick=2))
    spy.finish()
    report = spy.report()
    assert [(r["tick"], r["unexplained"]) for r in report["unexplained_rows"]] == [(1, -4.0), (2, 3.0)] and report["unexplained_total_count"] == 2
    assert [r["tick"] for r in report["total_change_rows"]] == [2]


def test_a_ledger_that_disagrees_with_the_spys_own_total_marks_the_cell_wiring_mismatch():
    start = _state(_body(1, gold=10), tick=0)
    spy, ledger = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=10), tick=1))
    ledger.coin_last += 1.0  # the ledger saw a different state than the spy
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
    assert ledger.live is False and ledger.coin_first == 0.0 and spy.ledger_snapshot["coin_last"] == 1.0  # snapshot kept, ledger cleared


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
    assert report["control_applied_count"] == 1 and report["apply_calls"] == 1 and report["distinct_ticks"] == 1
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


def test_the_real_ledger_class_exposes_the_public_payload_the_spy_reads_and_the_spy_never_reads_a_private_field():
    RunLedger.reset_run_state()
    try:
        payload = kit.ledger_payload(RunLedger)
        assert {"coin_first", "coin_last", "declared_coin"} <= set(payload)
    finally:
        RunLedger.reset_run_state()
    for name in ("reset_run_state", "configure", "observe", "tally_event"):
        assert callable(getattr(RunLedger, name))
    source = open(kit.__file__, encoding="utf-8").read()
    private = ("RunLedger" + "._", "ledger" + "._")  # built from parts so this test does not match its own search
    assert not any(token in source for token in private)


def test_a_ledger_move_between_applies_is_an_untracked_move_a_sum_mismatch_and_exit_5():
    start = _state(_body(1, gold=10), tick=0)
    spy, ledger = _spy(start)
    spy.observe(start, type("U", (), {"entities_add": [_body(2, gold=4)]})(), _state(_body(1, gold=10), _body(2, gold=4), tick=1))
    ledger.declared_offset = 2.5  # a second feeder moves the ledger between two of the spy's applies
    spy.observe(_state(_body(1, gold=10), _body(2, gold=4), tick=1), None, _state(_body(1, gold=10), _body(2, gold=4), tick=2))
    spy.finish()
    report = spy.report()
    assert report["untracked_ledger_moves_count"] == 1 and report["untracked_ledger_moves"] == [{"tick": 2, "previous_after": 4.0, "before": 6.5}]
    assert report["declared_per_apply_sum"] == 4.0 and report["ledger_declared"] == 6.5 and report["declared_sum_matches_end"] is False
    assert report["wiring"] == "WIRING_MISMATCH" and report["cell_valid"] is False
    code, message = kit.exit_status({**report, "control": None}, None)
    assert code == kit.EXIT_WIRING_MISMATCH == 5 and "WIRING_MISMATCH" in message


def test_a_clean_run_has_no_untracked_move_and_the_sum_equals_the_end_value_because_the_reads_bracket_each_observe():
    start = _state(_body(1, gold=10), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, type("U", (), {"entities_add": [_body(2, gold=4)]})(), _state(_body(1, gold=10), _body(2, gold=4), tick=1))
    spy.observe(_state(_body(1, gold=10), _body(2, gold=4), tick=1), None, _state(_body(1, gold=10), _body(2, gold=4), tick=2))
    spy.finish()
    report = spy.report()
    assert report["untracked_ledger_moves_count"] == 0 and report["declared_per_apply_sum"] == report["ledger_declared"] == 4.0 and report["wiring"] == "OK"


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


def test_apply_calls_and_distinct_ticks_are_reported_apart():
    start = _state(_body(1, gold=1), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=1), tick=1))
    spy.observe(_state(_body(1, gold=1), tick=1), None, _state(_body(1, gold=1), tick=1))  # a second apply on the same tick
    spy.finish()
    report = spy.report()
    assert report["apply_calls"] == 2 and report["distinct_ticks"] == 1


def test_a_control_whose_tick_never_matches_never_applies_and_the_child_exit_is_non_zero():
    start = _state(_body(1, gold=10), _body(2, gold=5), tick=0)
    spy, _ = _spy(start, control=("coin", 7.0), last_tick=99)  # no observed state has tick 99
    spy.observe(start, None, _state(_body(1, gold=7), _body(2, gold=8), tick=1))
    spy.finish()
    report = spy.report()
    assert report["control_applied_count"] == 0 and report["v6"] == 0.0  # it reads like a clean real run, which is why the exit code matters
    doc = {**report}
    code, message = kit.exit_status(doc, ("coin", 7.0))
    assert code == kit.EXIT_CONTROL_NOT_APPLIED == 6 and "CONTROL NOT APPLIED" in message and "99" in message


def test_the_exit_status_orders_control_then_wiring_then_vacuous_and_a_good_cell_is_zero():
    good = {"control_applied_count": 0, "control": None, "wiring": "OK", "non_vacuous": True}
    assert kit.exit_status(good, None) == (0, "")
    assert kit.exit_status({**good, "wiring": "WIRING_MISMATCH"}, None)[0] == kit.EXIT_WIRING_MISMATCH
    assert kit.exit_status({**good, "non_vacuous": False}, None)[0] == kit.EXIT_VACUOUS
    assert kit.exit_status({**good, "control_applied_count": 1}, ("coin", 1.0)) == (0, "")


def test_an_override_planted_mid_run_is_a_mode_breach_a_wiring_mismatch_and_exit_5_and_the_teardown_clears_it():
    start = _state(_body(1, gold=10), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=7), tick=1))
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)  # something switches the run to a recording mode between applies
    spy.observe(_state(_body(1, gold=7), tick=1), None, _state(_body(1, gold=5), tick=2))
    spy.finish()
    report = spy.report()
    assert report["mode_breach_count"] == 2 and report["mode_breaches"] == [{"tick": 2, "mode": "LIGHT"}, {"tick": 2, "mode": "LIGHT"}]  # the apply at tick 2 and the finish
    assert report["wiring"] == "WIRING_MISMATCH" and report["cell_valid"] is False
    code, message = kit.exit_status({**report, "control": None}, None)
    assert code == kit.EXIT_WIRING_MISMATCH == 5 and "WIRING_MISMATCH" in message
    # the autouse fixture clears every override at teardown, so the LIGHT override planted above cannot reach another test


def test_a_run_that_stays_off_has_no_mode_breach():
    start = _state(_body(1, gold=10), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=7), tick=1))
    spy.finish()
    assert spy.report()["mode_breach_count"] == 0 and spy.report()["wiring"] == "OK"


def _unexplained_run(rows, **spy_kwargs):
    """A spy that saw ``rows`` applies, each creating 1 coin at ticks 1..rows with nothing declared (unexplained = 1.0 each)."""
    start = _state(_body(1, gold=0), tick=0)
    spy, _ = _spy(start, **spy_kwargs)
    prior = start
    for tick in range(1, rows + 1):
        now = _state(_body(1, gold=tick), tick=tick)
        spy.observe(prior, None, now)
        prior = now
    spy.finish()
    return spy.report()


def test_last_tick_unexplained_and_its_flag_come_from_the_full_list_at_the_last_observed_tick():
    report = _unexplained_run(3)
    assert report["last_tick_unexplained"] == 1.0 and report["last_tick_has_unexplained_row"] is True and report["unexplained_total_count"] == 3
    start = _state(_body(1, gold=0), tick=0)
    spy, _ = _spy(start)
    spy.observe(start, None, _state(_body(1, gold=1), tick=1))  # +1 unexplained at tick 1
    spy.observe(_state(_body(1, gold=1), tick=1), None, _state(_body(1, gold=1), tick=2))  # nothing at the last tick
    spy.finish()
    report = spy.report()
    assert report["last_tick_unexplained"] == 0 and report["last_tick_has_unexplained_row"] is False and report["unexplained_total_count"] == 1


def test_the_cap_never_hides_the_last_tick_row_and_the_uncapped_flag_writes_the_full_list():
    capped = _unexplained_run(250)
    assert capped["unexplained_total_count"] == 250 and len(capped["unexplained_rows"]) == kit.ROW_CAP == 200 and capped["unexplained_rows_capped"] is True
    assert capped["last_tick_unexplained"] == 1.0 and capped["last_tick_has_unexplained_row"] is True  # the row at tick 250 is past the cap but still counted
    assert all(row["tick"] <= 200 for row in capped["unexplained_rows"])
    full = _unexplained_run(250, uncapped_rows=True)
    assert len(full["unexplained_rows"]) == 250 and full["unexplained_rows_capped"] is False and full["unexplained_rows"][-1]["tick"] == 250


def test_control_tick_is_reported_as_its_own_field_and_defaults_to_none():
    start = _state(_body(1), tick=0)
    spy, _ = _spy(start, control=("coin", 1.0), last_tick=99, control_tick=99)
    spy.observe(start, None, _state(_body(1), tick=1))
    spy.finish()
    assert spy.report()["control_tick"] == 99
    plain, _ = _spy(start)
    plain.observe(start, None, _state(_body(1), tick=1))
    plain.finish()
    assert plain.report()["control_tick"] is None
