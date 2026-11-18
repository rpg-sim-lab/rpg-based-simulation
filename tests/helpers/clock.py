"""One day-band world_time for tests that need it to be day: derived from the production night definition, never a bare number."""
from src.core.calendar import NIGHT_END_TICK, NIGHT_START_TICK, TICKS_PER_DAY, is_night

DAY_WORLD_TIME = (NIGHT_END_TICK + NIGHT_START_TICK) // 2  # the middle of the day: tick 1200 of 600..1799

assert not is_night(DAY_WORLD_TIME), "DAY_WORLD_TIME must be day under the production is_night"
assert not is_night(DAY_WORLD_TIME + TICKS_PER_DAY)  # the same time on the next day is day too
