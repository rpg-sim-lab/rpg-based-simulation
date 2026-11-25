"""The typed record of a refused building service (TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER, part B; STRAT-191-194).

A service dispatch (EAT, REST) at a building the subject cannot pay is refused with a typed reason (``ReasonCode.INSUFFICIENT_GOLD``). The refusal is a finding about the WAY ("this building will not serve me now"),
and the way belongs to strategy, so the finding reaches the layer that owns it as this typed record on the subject's navigation, the same shape as the give-up records (`src/core/giveup_records.py`): the
service writer APPENDS one (`NavigationUpdate.service_refusal_add`, applied by the navigation patch) and the same writer CLEARS the matching ones when that (action, building) is delivered
(`NavigationUpdate.service_refusal_clear`). The strategic pass reads them (`blocker_lifecycle.infer_blockers`): ``service_refusal_limit`` consecutive records of one (action, building), each within
``service_refusal_window`` ticks of the previous and each with a counted reason, file ONE access blocker for that way. The limit, the window, the counted reasons and the blocker's severity are data
(data/content/strategy/blocker_settings.yaml), not constants here. At most `SERVICE_REFUSALS_CAP` records are kept, newest last (a structural bound, not a tuning value)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Tuple

#: The structural bound on held refusals per subject: more than any limit a settings file would hold (the limit is validated against it by the reader's schema).
SERVICE_REFUSALS_CAP = 8

#: The id prefix of a blocker filed by the refusal rule: ``blocker_service_<action>_<building>``. The quiet-spell removal recognises it by this prefix.
SERVICE_BLOCKER_PREFIX = "blocker_service_"


@dataclass(frozen=True, slots=True)
class ServiceRefusal:
    """One refused service: the ``action`` (EAT, REST), the ``building`` id, the ``tick`` of the refusal and the typed ``reason`` name (a ``ReasonCode`` value)."""
    action: str
    building: int
    tick: int
    reason: str

    def to_canonical(self) -> Dict[str, Any]:
        """The canonical-dict form of this refusal: every field."""
        return {"action": self.action, "building": int(self.building), "tick": int(self.tick), "reason": self.reason}


def service_refusal_canonical(records: Tuple[ServiceRefusal, ...]) -> Dict[str, Any]:
    """The canonical-dict entry of a navigation's held refusals: ``{"service_refusals": [...]}`` while any is held, ``{}`` while none (the form of a subject never refused is unchanged)."""
    return {"service_refusals": [r.to_canonical() for r in records]} if records else {}


def service_blocker_id(action: str, building: int) -> str:
    """The id of the blocker for the way (action, building)."""
    return f"{SERVICE_BLOCKER_PREFIX}{action}_{int(building)}"


def consecutive_refusals(records: Iterable[ServiceRefusal], action: str, building: int, window: int, reasons: Iterable[str]) -> int:
    """How many of the held ``records`` for (action, building) form the CURRENT streak: counted from the newest backwards while each earlier one is at most ``window`` ticks before the one after it
    and has a counted reason. Pure; a delivery already removed the records it ended (the writer's clear), so there is no delivered check here."""
    counted = set(reasons)
    mine = sorted((r for r in records if r.action == action and r.building == building), key=lambda r: r.tick)
    streak, last = 0, None
    for record in reversed(mine):
        if record.reason not in counted or (last is not None and last - record.tick > window):
            break
        streak += 1
        last = record.tick
    return streak
