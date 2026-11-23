"""When a navigation experience is due for another try (the #996 rework; design section 5): PURE rules over the subject's OWN state, no write and no world read.

A record is DUE when any one rule holds, checked in this order (the review reason is the first that holds): the tick has reached its ``next_review_tick`` (DUE_TICK), the subject has moved more than
``approach_change_radius`` from where it gave up (APPROACH_CHANGED), or it is at or past the starving or exhausted line and the place serves that need (NEED_SEVERE). The delay each cause and evidence earns
(`next_review_tick_of`) comes from the data values, never from the cycle number: nothing doubles. Every rule reads only the subject's own tick, position and needs, so the information boundary holds."""
from __future__ import annotations

from typing import Any, Optional

from src.content.navigation_experience_settings import NavigationExperienceSettings
from src.core.navigation_experience import NavCause, NavigationExperience, NeedService, RingEvidence, ReviewReason
from src.engine.need_pull import SLEEP_LINE
from src.engine.starvation import STARVING_LINE


def next_review_tick_of(cause: NavCause, evidence: tuple, observed_tick: int, settings: NavigationExperienceSettings) -> Optional[int]:
    """The tick a record filed at ``observed_tick`` is due by time, or None when only a trigger can make it due. An oscillation waits the oscillation delay; a ring block with BODIES among its evidence waits the
    (shorter) bodies delay; a ring block of STATIC evidence only is trigger-only (terrain does not change on its own); any other ring block (OTHER, or no evidence) takes the oscillation delay."""
    if cause == NavCause.RING_BLOCKED:
        if RingEvidence.BODIES in evidence:
            return observed_tick + settings.bodies_review_delay
        if tuple(evidence) == (RingEvidence.STATIC,):
            return None
    return observed_tick + settings.oscillation_review_delay


def due_reason(record: NavigationExperience, entity: Any, tick: int, settings: NavigationExperienceSettings) -> Optional[ReviewReason]:
    """The first rule that makes ``record`` due for ``entity`` at ``tick``, or None. A REVIEWED record is never due again (it no longer refuses)."""
    if record.next_review_tick is not None and tick >= record.next_review_tick:
        return ReviewReason.DUE_TICK
    x, y = entity.navigation.position
    if max(abs(int(x) - record.from_position[0]), abs(int(y) - record.from_position[1])) > settings.approach_change_radius:
        return ReviewReason.APPROACH_CHANGED
    if (NeedService.EAT in record.need_services and entity.biological.hunger >= STARVING_LINE) or (NeedService.REST in record.need_services and entity.biological.sleep_debt >= SLEEP_LINE):
        return ReviewReason.NEED_SEVERE
    return None
