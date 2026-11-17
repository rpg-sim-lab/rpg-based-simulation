"""What a body gives off (PERC-02): signals follow the body.

`emitted_signals(entity, body)` is the one function that turns a body into the signal levels the PerceptionGate scores against a sense.
Defaults are derived from the body, never from a kind name:
- visibility: by the body model's size band (small low, medium medium, large high; undeclared medium);
- noise and vibration: medium while it moved last step, low while still, very_low while asleep or lodged;
- scent: medium for a living body;
- life: medium for a living body.
A body model may declare any of visibility / noise / scent / vibration / life in its `signals` block; a declared level replaces the derived one
(an undead or spirit body declares life none). Magic and social signals are not derived from the body (none, as before).
"""

from __future__ import annotations

from typing import Any, Dict, Optional

_SIZE_VISIBILITY = {"small": "low", "medium": "medium", "large": "high"}
_UNDECLARED_VISIBILITY = "medium"  # a body with no declared size keeps the old default


def emitted_signals(entity: Any, body: Optional[Any]) -> Dict[str, str]:
    """The gate's signal levels for `entity`, whose body model is `body` (None when its species is not in content)."""
    from src.engine.sleep_debt import is_asleep  # local: sleep_debt imports engine modules

    lodged = getattr(entity.navigation, "lodged_in", None) is not None
    still_hidden = lodged or is_asleep(entity)
    moving = bool(getattr(entity.navigation, "moved_recently", False))
    activity = "very_low" if still_hidden else ("medium" if moving else "low")
    alive = bool(getattr(getattr(entity, "combat", None), "alive", True))
    size = getattr(body, "size", None)
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
        signals["life_signal" if key == "life" else key] = level
    return signals
