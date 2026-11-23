"""The navigation experience consume step (the #996 rework; design section 6): the ONE writer of a subject's navigation experiences, run once per strategic pass for the subject.

In order: REVIEW every ACTIVE record whose due rule holds (`experience_due.due_reason`); FILE each pending give-up record as an upsert of its (anchor, purpose) record, a fresh cycle every time with every
field derived afresh from THAT give-up's evidence and the data values (nothing from the old record's timing survives); EVICT at the cap. It returns one typed `NavigationExperienceUpdate`; it writes nothing itself. A give-up
whose stored purpose is None files nothing and is counted. No kind, role, faction or name is read: the inputs are the subject's own position, needs, projects and records, and the building-kind service table."""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Tuple

from src.content.navigation_experience_settings import NavigationExperienceSettings
from src.core.navigation_experience import (
    ExperienceReview,
    NavExperienceStatus,
    NavigationExperience,
    NavigationExperienceCounts,
    NavigationExperienceMemory,
    NavigationExperienceUpdate,
    NeedService,
    apply_experience_update,
    experience_id_of,
)
from src.engine.building_services import SERVICE_KINDS
from src.engine.service_reach import service_tile
from src.strategy.experience_due import due_reason, next_review_tick_of


def need_services_at(state: Any, anchor: Tuple[int, int]) -> FrozenSet[NeedService]:
    """The needs the building in reach of ``anchor`` serves (an inn: EAT and REST; a home: REST), or the empty set. It reuses main's building-kind service table; no body's kind is read."""
    return frozenset(NeedService(action) for action in ("EAT", "REST") if service_tile(state, (int(anchor[0]), int(anchor[1])), SERVICE_KINDS[action]) is not None)


def _evictions(entity: Any, memory: NavigationExperienceMemory, kept_ids: set, tick: int, cap: int, settings: NavigationExperienceSettings) -> Tuple[str, ...]:
    """The ids to evict so the memory holds at most ``cap`` records, never one filed this pass: the REVIEWED record with the oldest reviewed tick (ties by id), else an ACTIVE record that is due now (oldest observed
    first), else the oldest ACTIVE record, which is counted because it ends a live refusal."""
    records = {r.experience_id: r for r in memory.records}
    out: List[str] = []
    while len(records) > cap:
        pool = [r for r in records.values() if r.experience_id not in kept_ids]
        if not pool:
            break
        reviewed = sorted((r for r in pool if r.status == NavExperienceStatus.REVIEWED), key=lambda r: (r.reviewed_tick if r.reviewed_tick is not None else -1, r.experience_id))
        due = sorted((r for r in pool if r.status == NavExperienceStatus.ACTIVE and due_reason(r, entity, tick, settings) is not None), key=lambda r: (r.observed_tick, r.experience_id))
        active = sorted((r for r in pool if r.status == NavExperienceStatus.ACTIVE), key=lambda r: (r.observed_tick, r.experience_id))
        victim = (reviewed or due or active)[0]
        if not (reviewed or due):
            NavigationExperienceCounts.note_live_eviction()
        out.append(victim.experience_id)
        del records[victim.experience_id]
    return tuple(out)


def navigation_experience_update(entity: Any, state: Any, tick: int, project_id: str, settings: NavigationExperienceSettings) -> NavigationExperienceUpdate:
    """The experience update of one strategic pass for ``entity``: reviews, the upserts its pending give-up records file, and the evictions the cap needs. ``project_id`` is the project current at this pass ("" when none)."""
    memory = entity.cognition.memory.navigation
    stored: Dict[str, NavigationExperience] = {r.experience_id: r for r in memory.records}
    reviews = tuple(
        ExperienceReview(r.experience_id, r.cycle, tick, reason)
        for r in memory.records
        if r.status == NavExperienceStatus.ACTIVE and (reason := due_reason(r, entity, tick, settings)) is not None
    )
    here = (int(entity.navigation.position[0]), int(entity.navigation.position[1]))
    filed: Dict[str, NavigationExperience] = {}
    for rec in entity.navigation.giveup_records:
        if rec.purpose is None:
            NavigationExperienceCounts.note_no_purpose()
            continue
        eid = experience_id_of(rec.anchor, rec.purpose)
        prev = filed.get(eid) or stored.get(eid)
        anchor = (int(rec.anchor[0]), int(rec.anchor[1]))
        filed[eid] = NavigationExperience(
            experience_id=eid, anchor=anchor, purpose=rec.purpose, cause=rec.cause, ring_evidence=tuple(rec.ring_evidence),
            from_position=rec.from_position if rec.from_position is not None else here, target_tile=rec.target_tile if rec.target_tile is not None else anchor,
            need_services=need_services_at(state, anchor), project_id=project_id, observed_tick=tick, cycle=(prev.cycle + 1) if prev is not None else 1,
            next_review_tick=next_review_tick_of(rec.cause, tuple(rec.ring_evidence), tick, settings), status=NavExperienceStatus.ACTIVE, reviewed_tick=None, review_reason=None,
            project_giveups=(prev.project_giveups + 1) if prev is not None and prev.project_id == project_id else 1)
    upserts = tuple(filed[k] for k in sorted(filed))
    after = apply_experience_update(memory, NavigationExperienceUpdate(reviews=reviews, upserts=upserts))
    evictions = _evictions(entity, after, set(filed), tick, settings.navigation_experience_cap, settings)
    return NavigationExperienceUpdate(reviews=reviews, upserts=upserts, evictions=evictions)
