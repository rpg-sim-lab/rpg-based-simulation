"""What a body gives off (PERC-02): signals follow the body.

`emitted_signals(entity, body)` is the one function that turns a body into the signal levels the PerceptionGate scores against a sense.
Defaults are derived from the body, never from a kind name:
- visibility: by the body model's size band (small low, medium medium, large high; undeclared medium);
- noise and vibration: medium while it is MOVING (it took a successful step within the last MOVING_WINDOW ticks: ``navigation.last_moved_tick``), low while still (never stepped, or
  not within the window), very_low while asleep or lodged;
- scent: medium for a living body;
- life: medium for a living body.
A body model may declare any of visibility / noise / scent / vibration / life / magic in its `signals` block; a declared level replaces the derived one
(an undead or spirit body declares life none). Magic and social signals are not derived from the body (none, as before).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.engine.sleep_debt import is_asleep

_SIZE_VISIBILITY = {"small": "low", "medium": "medium", "large": "high"}
_UNDECLARED_VISIBILITY = "medium"  # a body with no declared size keeps the old default
MOVING_WINDOW = 3  # provisional, rpg-designer 2026-11-18: a body that took a successful step within this many ticks is moving
_GATE_KEY = {"life": "life_signal", "magic": "magic_signal"}  # body-model signal key -> the gate's signal key


def emitted_signals(entity: Any, body: Optional[Any], tick: Optional[int] = None) -> Dict[str, str]:
    """The gate's signal levels for `entity`, whose body model is `body` (None when its species is not in content), at the caller's `tick`.
    A caller that has no tick gets a body that reads still (no step can be dated)."""
    lodged = getattr(entity.navigation, "lodged_in", None) is not None
    still_hidden = lodged or is_asleep(entity)
    last_step = getattr(entity.navigation, "last_moved_tick", None)
    moving = tick is not None and last_step is not None and tick - last_step <= MOVING_WINDOW
    activity = "very_low" if still_hidden else ("medium" if moving else "low")
    alive = bool(getattr(getattr(entity, "combat", None), "alive", True))
    size: str = getattr(body, "size", None) or ""
    signals = {
        "visibility": _SIZE_VISIBILITY.get(size, _UNDECLARED_VISIBILITY),
        "noise": activity,
        "scent": "medium" if alive else "none",
        "magic_signal": "none",
        "life_signal": "medium" if alive else "none",
        "vibration": activity,
        "social_signal": "none",
    }
    declared = getattr(body, "signals", None) or {}
    for key, level in declared.items():
        signals[_GATE_KEY.get(key, key)] = level
    return signals
