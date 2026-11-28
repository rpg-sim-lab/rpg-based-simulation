"""What a body gives off (PERC-02): signals follow the body.

`emitted_signals(entity, body)` is the one function that turns a body into the signal levels the PerceptionGate scores against a sense.
Defaults are derived from the body, never from a kind name:
- visibility: by the body model's size band, read from `data/content/perception/perception_settings.yaml` (size_visibility: small medium_high, medium high, large very_high; an undeclared size gives off the medium entry);
- noise and vibration: medium while it is MOVING (it moved within the last MOVING_WINDOW ticks: a step, a swap or a yield displacement, ``navigation.last_moved_tick``), low while still (never stepped, or
  not within the window), very_low while asleep or lodged;
- scent: medium for a living body;
- life: medium for a living body.
A body model may declare any of visibility / noise / scent / vibration / life / magic in its `signals` block; a declared level replaces the derived one
(an undead or spirit body declares life none). Magic and social signals are not derived from the body (none, as before).
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from src.content.perception_settings import perception_settings
from src.engine.sleep_debt import is_asleep

STILL_ACTIVITY_LEVEL = "low"  # noise and vibration of a body that has not stepped within MOVING_WINDOW (the still-body ceiling of the gate's threshold is computed from this)
MOVING_ACTIVITY_LEVEL = "medium"
HIDDEN_ACTIVITY_LEVEL = "very_low"  # asleep or lodged
LIVING_SCENT_LEVEL = "medium"  # scent and life of a living body
MOVING_WINDOW = 3  # provisional, rpg-designer 2026-11-18: a body that took a successful step within this many ticks is moving
_GATE_KEY = {"life": "life_signal", "magic": "magic_signal"}  # body-model signal key -> the gate's signal key


def emitted_signals(entity: Any, body: Optional[Any], tick: Optional[int] = None, size_visibility: Optional[Mapping[str, str]] = None) -> Dict[str, str]:
    """The gate's signal levels for `entity`, whose body model is `body` (None when its species is not in content), at the caller's `tick`.
    A caller that has no tick gets a body that reads still (no step can be dated)."""
    lodged = getattr(entity.navigation, "lodged_in", None) is not None
    still_hidden = lodged or is_asleep(entity)
    last_step = getattr(entity.navigation, "last_moved_tick", None)
    moving = tick is not None and last_step is not None and tick - last_step <= MOVING_WINDOW
    activity = HIDDEN_ACTIVITY_LEVEL if still_hidden else (MOVING_ACTIVITY_LEVEL if moving else STILL_ACTIVITY_LEVEL)
    alive = bool(getattr(getattr(entity, "combat", None), "alive", True))
    size: str = getattr(body, "size", None) or ""
    sizes = size_visibility if size_visibility is not None else perception_settings().size_visibility  # a caller without the gate's settings reads the warmed catalog
    signals = {
        "visibility": sizes.get(size, sizes["medium"]),  # an undeclared size gives off the medium entry (one value, in data)
        "noise": activity,
        "scent": LIVING_SCENT_LEVEL if alive else "none",
        "magic_signal": "none",
        "life_signal": LIVING_SCENT_LEVEL if alive else "none",
        "vibration": activity,
        "social_signal": "none",
    }
    declared = getattr(body, "signals", None) or {}
    for key, level in declared.items():
        signals[_GATE_KEY.get(key, key)] = level
    return signals
