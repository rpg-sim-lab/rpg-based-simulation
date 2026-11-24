"""Fixture builders for the tests of the destination gate (the #996 rework, step (e)): a subject that remembers a failed approach as a navigation experience. Not a test module.

The gate refuses a tile within Chebyshev 1 of an ACTIVE experience of the SAME purpose that is not yet due (`due_reason`) and not latched. The builders here make such a record in the shape a give-up of
THIS subject at its current position would file: `from_position` is the subject's own tile (so no approach change is due), `next_review_tick` is the explicit ``until`` (so the refusal ends exactly
at that tick), and no need is served (so no need line is due)."""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Optional, Tuple

from src.core.navigation_experience import (
    NavCause,
    NavExperienceStatus,
    NavigationExperience,
    NavigationExperienceMemory,
    experience_id_of,
)
from src.core.navigation_purpose import TargetPurpose

WANDER = TargetPurpose("none", "WANDER")


def an_experience(anchor: Tuple[int, int], purpose: TargetPurpose = WANDER, from_position: Tuple[int, int] = (5, 5), until: Optional[int] = 500, cycle: int = 1, status: NavExperienceStatus = NavExperienceStatus.ACTIVE,
                  project_id: str = "", project_giveups: int = 1, **fields: Any) -> NavigationExperience:
    """One experience of ``purpose`` at ``anchor``, filed at tick 1 from ``from_position``, due by time at ``until`` (None: trigger-only)."""
    base = dict(
        experience_id=experience_id_of(anchor, purpose), anchor=(int(anchor[0]), int(anchor[1])), purpose=purpose, cause=NavCause.OSCILLATION, ring_evidence=(), from_position=from_position, target_tile=(int(anchor[0]), int(anchor[1])),
        need_services=frozenset(), project_id=project_id, observed_tick=1, cycle=cycle, next_review_tick=until, status=status,
        reviewed_tick=None if status == NavExperienceStatus.ACTIVE else 2, review_reason=None, project_giveups=project_giveups)
    base.update(fields)
    return NavigationExperience(**base)


def with_experiences(entity: Any, *records: NavigationExperience) -> Any:
    """``entity`` holding exactly ``records`` as its navigation experience memory (sorted by id, as the memory is)."""
    memory = replace(entity.cognition.memory, navigation=NavigationExperienceMemory(tuple(sorted(records, key=lambda r: r.experience_id))))
    return replace(entity, cognition=replace(entity.cognition, memory=memory))


def refuse(entity: Any, *anchors: Tuple[int, int], purpose: TargetPurpose = WANDER, until: Optional[int] = 500) -> Any:
    """``entity`` remembering a failed approach to each of ``anchors`` for ``purpose``, filed from the subject's own tile, refusing until ``until``."""
    here = (int(entity.navigation.position[0]), int(entity.navigation.position[1]))
    return with_experiences(entity, *(an_experience(a, purpose, from_position=here, until=until) for a in anchors))
