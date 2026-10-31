"""Lodging: a subject served a bed at a building lodges INSIDE it (F3, divergence 2.155; Bible 04 section 1, local_world_interaction_contract 2.1).

While a subject lodges it stands on no tile: ``navigation.lodged_in`` is the building's id, its ``position`` is the building's own tile, and it is in no occupancy map, spatial
index or perception, so no one outside can reach or see it, and it sees no one outside. The building lodges at most its content-declared ``beds``; the count of lodgers is
DERIVED from the entities (never stored on the building), so there is one source of truth. ``lodged_in`` is set and cleared only by the apply path (a NavigationUpdate).

This module holds the pure predicates every consumer reads (`is_lodged`, `lodgers_of`, `has_free_bed`), the claim a bed service makes, the bed grant (`grant_beds`) and where a
leaver steps out (`leave_tile`). It writes no state.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

Tile = Tuple[int, int]

# The orthogonal reach tiles beside a building tile, in the fixed order of ``service_reach._REACH_OFFSETS`` without (0, 0): a leaver takes the first free one.
LEAVE_OFFSETS: Tuple[Tile, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))
CLAIM_MARKER = "LODGE_CLAIM"  # the transfer kind of the marker a lodge claim carries; `grant_beds` removes every marker and delivers the bed once per marker
LEAVE_RING_RADIUS = 3  # then the nearest free walkable tile within this many tiles, by a fixed ring order


def is_lodged(entity: Any) -> bool:
    """True while ``entity`` lodges in a building. The one predicate every spatial index, perception and targeting filter reads."""
    return entity.navigation.lodged_in is not None


def lodgers_of(state: Any, building_id: int) -> Tuple[int, ...]:
    """The ids of the living entities lodged in ``building_id``, ascending. Derived from the entities; a worker packet without entities answers ()."""
    entities = getattr(state, "entities", None) or {}
    return tuple(sorted(e_id for e_id, e in entities.items() if e.navigation.lodged_in == building_id and e.combat.alive))


def anyone_lodges(state: Any) -> bool:
    """True when at least one living entity lodges (the phase gate for the leave step: a leaver's rest ended, which marks no movement)."""
    entities = getattr(state, "entities", None) or {}
    return any(e.navigation.lodged_in is not None for e in entities.values())


def has_claims(update: Any) -> bool:
    """True when ``update`` carries a lodge claim (the phase gate for the bed grant)."""
    return any(u.navigation is not None and u.navigation.lodged_in_set is not None for u in update.entity_updates.values())


def lodges(building: Any) -> bool:
    """True when ``building`` lodges anyone at all (content ``beds`` > 0). Zero or absent: its rest is served on the reach tile exactly as before."""
    return int(getattr(building, "beds", 0) or 0) > 0


def has_free_bed(state: Any, building: Any, entity: Any = None) -> bool:
    """True when ``building`` can take one more lodger: it has no beds declared (main's behaviour, nothing to count), or a bed is free, or ``entity`` already holds one."""
    if not lodges(building):
        return True
    held = lodgers_of(state, building.id)
    return (entity is not None and entity.id in held) or len(held) < int(building.beds)


def lodge_claim(entity: Any, building: Any) -> Any:
    """The CLAIM a bed service makes for ``entity`` at ``building``: lodge from this tick, standing on the building's tile. No bed is delivered by the claim; `grant_beds` grants
    it (the lowest entity id first, up to the beds) and only then adds the bed's service. Idempotent: the same claim merged twice is one claim."""
    from src.core.updates import EntityUpdate, NavigationUpdate, ResourceTransferIntent
    # One marker per execution of the REST. Updates of one subject are merged by concatenating their transfers, so the number of markers on the merged update is the number of
    # times main would have delivered the bed (today a REST is executed by the worker and again by the actions phase, a defect tracked on its own ticket): `grant_beds` delivers
    # the bed that many times, so F3 changes where the subject sleeps and not what a bed costs.
    marker = ResourceTransferIntent(source_id=building.id, source_kind="LODGING", transfer_kind=CLAIM_MARKER)
    return EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(lodged_in_set=building.id), resource_transfers=[marker],
                        new_position=(float(building.position[0]), float(building.position[1])), moved_this_tick=True)


def grant_beds(state: Any, update: Any) -> Any:
    """Grant or refuse every lodge claim of this tick's ``update``, BEFORE any service is delivered (F3, divergence 2.155).

    Per building the claimants are taken in ascending entity id (TOWN-006 order): a subject that already lodges there keeps its bed, others take a free bed while one is left, and a
    building that is gone or not functional refuses everyone. A GRANTED claim gets the bed service (`building_services.bed_delta`: readiness, health, the charge) merged into its
    update. A REFUSED claim loses the claim (no lodging, no move), its REST task ends (an idle act, the brain re-decides) and its fatigue project ends with
    `ProjectEnd.WAY_CLOSED`; it never has a charge, readiness or heal applied because none was ever put on its update. A tick with no claim returns ``update`` unchanged."""
    from dataclasses import replace
    from src.core.strategic import ProjectEnd, ProjectStatus, end_record
    from src.core.updates import EntityUpdate, StrategicUpdate, TaskUpdate
    from src.engine.building_services import bed_delta

    claims: Dict[int, List[int]] = {}
    for eid, upd in update.entity_updates.items():
        nav = upd.navigation
        if nav is not None and nav.lodged_in_set is not None:
            claims.setdefault(nav.lodged_in_set, []).append(eid)
    if not claims:
        return update
    entities = state.entities
    refined = dict(update.entity_updates)
    for building_id in sorted(claims):
        building = state.buildings.get(building_id)
        usable = building is not None and building.functional and lodges(building)
        held = set(lodgers_of(state, building_id)) if usable else set()
        free = int(building.beds) - len(held) if usable else 0
        for eid in sorted(claims[building_id]):
            entity = entities.get(eid)
            if entity is None:
                continue
            upd = refined[eid]
            markers = sum(1 for t in upd.resource_transfers if t.transfer_kind == CLAIM_MARKER)
            upd = replace(upd, resource_transfers=[t for t in upd.resource_transfers if t.transfer_kind != CLAIM_MARKER])
            if usable and (eid in held or free > 0):
                if eid not in held:
                    free -= 1
                for _ in range(max(1, markers)):
                    upd = upd.merge(bed_delta(entity, building))
                refined[eid] = upd
                continue
            project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
            ended = EntityUpdate(entity_id=eid, strategic=StrategicUpdate(
                projects_add_or_update=[end_record(project, ProjectStatus.ABANDONED, ProjectEnd.WAY_CLOSED)], current_project_id_set="", current_objective_id_set="")) if project is not None else None
            task = replace(upd.task, payload_set={}) if upd.task is not None else upd.task
            refined[eid] = replace(upd, navigation=replace(upd.navigation, lodged_in_set=None), new_position=None, moved_this_tick=False, task=task)
            if ended is not None:
                refined[eid] = refined[eid].merge(ended)
    return replace(update, entity_updates=refined)


def keeps_lodging(work_kind: Optional[str], payload: Any) -> bool:
    """True when a lodger's resulting task keeps it indoors: it is still resting or sleeping, or it is eating (only EAT was ruled, scope 7). Anything else, including no task at all
    (the held rest ended this tick), means it leaves: a lodger holds a bed only while it uses it, so the bed is free the tick its rest ends and no lodger can be stranded
    awake indoors waiting for a decision (risk R5). The brain then decides from the reach tile, where the building's services are still in reach."""
    action = (payload or {}).get("action") if isinstance(payload, dict) else None
    if not action:
        return False
    from src.engine.sleep_debt import SLEEP_ACTIONS
    return action in SLEEP_ACTIONS or action == "EAT"


def leave_tile(state: Any, origin: Tile, taken: Iterable[Tile]) -> Optional[Tile]:
    """Where a leaver steps out: the first free orthogonal tile beside ``origin`` in the fixed reach order (without the building tile itself), else the nearest free walkable tile
    within ``LEAVE_RING_RADIUS`` (Manhattan distance, then row, then column), else None. Free = not statically obstructed (world extent, terrain, building) and not in ``taken``."""
    from src.engine.legality import _static_obstruction
    blocked = set(taken)

    def free(tile: Tile) -> bool:
        return tile not in blocked and _static_obstruction(tile, state) is None

    for dx, dy in LEAVE_OFFSETS:
        tile = (origin[0] + dx, origin[1] + dy)
        if free(tile):
            return tile
    ring = sorted(((abs(dx) + abs(dy), dy, dx) for dx in range(-LEAVE_RING_RADIUS, LEAVE_RING_RADIUS + 1) for dy in range(-LEAVE_RING_RADIUS, LEAVE_RING_RADIUS + 1)
                   if 2 <= abs(dx) + abs(dy) <= LEAVE_RING_RADIUS))
    for _, dy, dx in ring:
        tile = (origin[0] + dx, origin[1] + dy)
        if free(tile):
            return tile
    return None


def place_leavers(state: Any, update: Any) -> Any:
    """Step every lodger that is leaving out of its building, through the same position update a move uses (F3, divergence 2.155).

    A lodger leaves the tick its held rest ends: when its resulting task is not to keep resting or eating (`keeps_lodging`; an ended rest leaves no task), when this tick's update gives it a
    walk target, or when its building is gone or no longer functional. It takes the first free orthogonal tile beside the building (fixed reach order), else the nearest free walkable tile within three tiles, else it stays lodged
    and awake and tries again next tick (counted under the rejection reason ``LODGE_EXIT_BLOCKED``). Leavers are placed in ascending id, so two leavers for one tile give it to the
    lowest id and the other takes its next tile. It moves on from the next tick: any move this tick's update already proposes for a leaver is dropped. Returns ``update`` unchanged when
    nobody lodges."""
    from dataclasses import replace
    from src.core.updates import EntityUpdate, NavigationUpdate

    lodged = [(e_id, e) for e_id, e in state.entities.items() if e.navigation.lodged_in is not None and e.combat.alive and e.lifecycle.active]
    if not lodged:
        return update
    leavers: List[Tuple[int, Any]] = []
    for e_id, e in sorted(lodged, key=lambda kv: kv[0]):
        upd = update.entity_updates.get(e_id)
        building = state.buildings.get(e.navigation.lodged_in)
        gone = building is None or not building.functional
        task = upd.task if upd is not None else None
        work_kind = task.work_kind_set if task is not None and task.work_kind_set is not None else e.task.work_kind
        payload = task.payload_set if task is not None and task.payload_set is not None else e.task.payload
        walking = upd is not None and upd.navigation is not None and upd.navigation.target_set is not None
        if gone or walking or not keeps_lodging(work_kind, payload):
            leavers.append((e_id, e))
    if not leavers:
        return update
    from src.engine.spatial_query import SpatialQueryService
    leaving_ids = {e_id for e_id, _ in leavers}
    taken = set(SpatialQueryService.get_occupancy_map(state))
    for e_id, upd in update.entity_updates.items():
        if e_id not in leaving_ids and upd.new_position is not None:
            taken.add((int(upd.new_position[0]), int(upd.new_position[1])))
    refined = dict(update.entity_updates)
    rejections = dict(update.rejections_delta)
    for e_id, e in leavers:
        origin = (int(e.navigation.position[0]), int(e.navigation.position[1]))
        tile = leave_tile(state, origin, taken)
        upd = refined.get(e_id, EntityUpdate(entity_id=e_id))
        if tile is None:
            rejections["LODGE_EXIT_BLOCKED"] = rejections.get("LODGE_EXIT_BLOCKED", 0) + 1
            refined[e_id] = replace(upd, new_position=None, moved_this_tick=False)
            continue
        taken.add(tile)
        leave = EntityUpdate(entity_id=e_id, navigation=NavigationUpdate(lodged_in_clear=True), new_position=(float(tile[0]), float(tile[1])), moved_this_tick=True)
        refined[e_id] = replace(upd, new_position=None, moved_this_tick=False).merge(leave)
    return replace(update, entity_updates=refined, rejections_delta=rejections)
