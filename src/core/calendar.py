"""Single source of truth for the World Evolution Bible's calendar authority
(docs/mechanics/05_world_evolution.md; decided in TCK-20260829-TEMPORAL-CALENDAR-AUTHORITY):
2,400 ticks/day, a 120-day fantasy year (4 seasons of 30 days each). Any code converting
between raw ticks and fantasy-calendar units should import these constants rather than
hardcoding a second copy of the conversion.
"""

import math

TICKS_PER_DAY = 2400
DAYS_PER_SEASON = 30
SEASONS_PER_YEAR = 4
TICKS_PER_FANTASY_YEAR = TICKS_PER_DAY * DAYS_PER_SEASON * SEASONS_PER_YEAR  # 288,000

# Night is the last quarter of the day plus the first quarter: [NIGHT_START_TICK, TICKS_PER_DAY) and
# [0, NIGHT_END_TICK) of the time of day, so night is half of every day.
NIGHT_START_TICK = 1800
NIGHT_END_TICK = 600


def time_of_day(world_time: int) -> int:
    """Tick within the current day. `world_time` never wraps, so every day-cycle reader goes through here."""
    return world_time % TICKS_PER_DAY


def is_night(world_time: int) -> bool:
    """True in the night half of the day, on any day (tick 2400+k is classified as tick k)."""
    tod = time_of_day(world_time)
    return tod >= NIGHT_START_TICK or tod < NIGHT_END_TICK


def fantasy_years_to_ticks(years: float) -> int:
    """Converts a fantasy-year duration into whole ticks, rounding up (a fractional tick
    cannot elapse, and rounding down would let an entity cross a boundary early)."""
    return math.ceil(years * TICKS_PER_FANTASY_YEAR)
