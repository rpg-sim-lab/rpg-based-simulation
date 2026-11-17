"""Night is read from the time of day, not the raw never-wrapping world_time
(TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT, divergence 2.209)."""
import re
from dataclasses import replace
from pathlib import Path

import pytest

from src.ai.goals.scorers import SleepScorer
from src.core.builder import V2EntityBuilder
from src.core.calendar import TICKS_PER_DAY, is_night, time_of_day
from src.core.state import AuthoritativeState
from src.systems.routine import RoutineService


@pytest.mark.parametrize("t,tod,night", [
    (0, 0, True), (599, 599, True), (600, 600, False), (1799, 1799, False), (1800, 1800, True),
    (2399, 2399, True), (2400, 0, True), (2999, 599, True), (3000, 600, False), (4200, 1800, True),
])
def test_time_of_day_and_night(t, tod, night):
    assert time_of_day(t) == tod
    assert is_night(t) is night


def test_night_is_half_of_every_day():
    for day in range(3):
        base = day * TICKS_PER_DAY
        assert sum(is_night(base + k) for k in range(TICKS_PER_DAY)) == TICKS_PER_DAY // 2


def _tired():
    return V2EntityBuilder(1).kind("HERO").location(0.0, 0.0).biological(sleep_debt=30.0).build()


@pytest.mark.parametrize("t", [0, 599, 600, 1200, 1799, 1800, 2399])
def test_readers_agree_one_day_later(t):
    ent = _tired()
    assert RoutineService.evaluate_biological_needs(ent, t) == RoutineService.evaluate_biological_needs(ent, t + TICKS_PER_DAY)
    assert RoutineService.get_routine_utility_boost(ent, "sleep", t) == RoutineService.get_routine_utility_boost(ent, "sleep", t + 2 * TICKS_PER_DAY)
    state = AuthoritativeState(tick=1, seed=42, entities={1: ent}, world_time=t)
    later = replace(state, world_time=t + 3 * TICKS_PER_DAY)
    assert SleepScorer().score(ent, state) == SleepScorer().score(ent, later)


def test_no_sleep_bias_at_midday_after_the_first_day():
    ent = _tired()
    assert not any(c.id == "concern_sleep" for c in RoutineService.evaluate_biological_needs(ent, TICKS_PER_DAY + 1200))
    assert any(c.id == "concern_sleep" for c in RoutineService.evaluate_biological_needs(ent, TICKS_PER_DAY + 2000))


def test_no_raw_night_literal_outside_calendar():
    """T1: no reader compares world_time with the night literals itself."""
    root = Path(__file__).resolve().parents[3] / "src"
    pat = re.compile(r"world_time\s*(>=|<)\s*(1800|600)\b|\b(1800|600)\s*(<=|>)\s*\w*world_time")
    offenders = [str(p.relative_to(root)) for p in root.rglob("*.py")
                 if p.name != "calendar.py" and pat.search(p.read_text(encoding="utf-8"))]
    assert offenders == []
    assert not hasattr(__import__("src.world.raid", fromlist=["RaidService"]).RaidService, "TICKS_PER_DAY")


def test_the_new_rule_agrees_with_the_old_raw_clock_rule_below_3000():
    """The raw rule (t >= 1800 or t < 600) and the time-of-day rule agree for every tick below 3000: a run shorter than 3000 ticks is unchanged; the first difference is 3000."""
    def raw(t):
        return t >= 1800 or t < 600
    assert all(is_night(t) is raw(t) for t in range(3000))
    assert is_night(3000) is False and raw(3000) is True
