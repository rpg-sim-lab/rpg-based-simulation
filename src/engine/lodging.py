"""Lodging: a subject served a bed at a building lodges INSIDE it (F3, divergence 2.155; Bible 04 section 1, local_world_interaction_contract 2.1).

While a subject lodges it stands on no tile: ``navigation.lodged_in`` is the building's id, its ``position`` is the building's own tile, and it is in no occupancy map, spatial
index or perception, so no one outside can reach or see it, and it sees no one outside. The building lodges at most its content-declared ``beds``; the count of lodgers is
DERIVED from the entities (never stored on the building), so there is one source of truth. ``lodged_in`` is set and cleared only by the apply path (a NavigationUpdate).

This module holds the pure predicates every consumer reads (`is_lodged`, `lodgers_of`, `has_free_bed`), the claim a bed service makes, the bed grant (`grant_beds`) and where a
leaver steps out (`leave_tile`). It writes no state.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Iterable, List, Optional, Tuple

from src.core.enums import ReasonCode
from src.core.lodging_rules import is_lodged, is_lodged_stayer, keeps_lodging  # noqa: F401  (the stay-or-leave predicates live in core so the decision layers can read them)
from src.core.strategic import ObjectiveStatus, ProjectEnd, ProjectStatus, end_record
from src.core.updates import (
    CombatUpdate,
    EntityUpdate,
    NavigationUpdate,
    RejectionEvent,
    ResourceTransferIntent,
    StrategicUpdate,
)
from src.engine.legality import static_obstruction
from src.engine.serves import keeps_coin
from src.engine.service_prices import REST_PRICE_GOLD
from src.engine.spatial_query import SpatialQueryService

Tile = Tuple[int, int]

# The orthogonal reach tiles beside a building tile, in the fixed order of ``service_reach._REACH_OFFSETS`` without (0, 0): a leaver takes the first free one.
LEAVE_OFFSETS: Tuple[Tile, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))
CLAIM_MARKER = "LODGE_CLAIM"  # the transfer kind of the marker a lodge claim carries; `grant_beds` removes every marker and delivers the bed once per marker
LEAVE_RING_RADIUS = 3  # then the nearest free walkable tile within this many tiles, by a fixed ring order


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
    return any(is_lodge_claim(u) for u in update.entity_updates.values())


def lodging_triggers_phase(phase_name: str, state: Any, update: Any) -> bool:
    """The phase gate (F3): a lodger leaves the tick its rest ends, which marks no movement, and a bed claim must be granted before its service is delivered, so the occupancy phase runs
    while anyone lodges and the transactions phase runs when a claim is on the update."""
    if phase_name == "occupancy_resolution":
        return anyone_lodges(state)
    return phase_name == "resource_transactions" and has_claims(update)


def is_lodge_claim(entity_update: Any) -> bool:
    """True when ``entity_update`` carries a lodge claim (a position move onto the building's tile that is not vetted as a move: no occupant holds that tile)."""
    return entity_update.navigation is not None and entity_update.navigation.lodged_in_set is not None


def proposes_move(entity_update: Any) -> bool:
    """True when ``entity_update`` proposes a concrete final position that the occupancy phase must vet as a move (a granted lodge claim is no contender for a tile)."""
    return entity_update.new_position is not None and not is_lodge_claim(entity_update)


def stays_lodged_on_refusal(nav_update: Any) -> Any:
    """A leaver whose step was refused (occupancy) stays lodged and tries again next tick: the leave is taken off its navigation update."""
    return replace(nav_update, lodged_in_clear=False) if nav_update.lodged_in_clear else nav_update


def lodges(building: Any) -> bool:
    """True when ``building`` lodges anyone at all (content ``beds`` > 0). Zero or absent: its rest is served on the reach tile exactly as before."""
    return int(getattr(building, "beds", 0) or 0) > 0


def bed_free(beds: int, held: int, holds_one: bool) -> bool:
    """The ONE bed rule: a bed is free when the subject already holds one, or fewer than ``beds`` are held. `has_free_bed` (the counted state) and `grant_beds` (the in-tick counter) both read it."""
    return holds_one or held < beds


def has_free_bed(state: Any, building: Any, entity: Any = None) -> bool:
    """True when ``building`` can take one more lodger: it has no beds declared (main's behaviour, nothing to count), or a bed is free, or ``entity`` already holds one."""
    if not lodges(building):
        return True
    held = lodgers_of(state, building.id)
    return bed_free(int(building.beds), len(held), entity is not None and entity.id in held)


def finds_no_bed(state: Any, entity: Any, building: Any) -> bool:
    """THE 'no bed' predicate (F3, divergence 2.155): a subject the building would serve (`keeps_coin`, the trait; no kind name) finds NO free bed at a functional building that declares
    beds. Every caller asks this one function: the first execution of a REST (`building_services.with_service`), the arrival of a fatigue project (`building_arrival`). A non-person, a
    building with no beds and a building that is not functional are not refused here: their rest runs as on main."""
    return building is not None and building.functional and lodges(building) and keeps_coin(entity) and not has_free_bed(state, building, entity)


def way_closed_end(entity: Any, update: Any = None) -> Any:
    """The typed end of a fatigue project that found no bed: ``ProjectEnd.WAY_CLOSED`` through `end_record`, the current project and objective cleared. None when the subject has no
    fatigue project, or when ``update`` already carries that project's end (the claim path and the first-execution path may both refuse the same REST)."""
    project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
    if project is None or str(getattr(project.kind, "value", project.kind)).lower() != "fatigue" or project.ended_by is not None:
        return None
    if update is not None and update.strategic is not None and any(p.id == project.id and p.ended_by is not None for p in update.strategic.projects_add_or_update):
        return None
    return EntityUpdate(entity_id=entity.id, strategic=StrategicUpdate(
        projects_add_or_update=[end_record(project, ProjectStatus.ABANDONED, ProjectEnd.WAY_CLOSED)], current_project_id_set="", current_objective_id_set=""))


def refuse_rest(entity: Any) -> Any:
    """The update of a REST that found no bed at its first execution: no rest, no charge, no claim, no move. The typed failure reason ``NO_BED_FREE`` is what the actions phase counts and
    annotates (and what ends the held REST task, see ``_ENDS_HELD_REASONS_BY_ACTION``); a fatigue project ends WAY_CLOSED through `way_closed_end`. The subject re-decides."""
    refusal = EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(failure_reason=ReasonCode.NO_BED_FREE.value))
    ended = way_closed_end(entity)
    return refusal.merge(ended) if ended is not None else refusal


def resolve_arrival(entity: Any) -> Any:
    """Lodging IS arrival (F3, Q-B): when a subject is granted a bed, its fatigue project's active reach objective RESOLVES in the same apply, so no fallback has a walk to re-issue. The
    project stays ACTIVE (it completes through its own debt test when the need is met). None when the subject has no fatigue project with an active objective."""
    project = entity.strategic.projects.get(entity.strategic.current_project_id or "")
    if project is None or str(getattr(project.kind, "value", project.kind)).lower() != "fatigue" or project.ended_by is not None:
        return None
    if not any(o.id == project.active_objective_id and o.status == ObjectiveStatus.ACTIVE for o in project.objectives):
        return None
    objectives = [replace(o, status=ObjectiveStatus.RESOLVED) if o.id == project.active_objective_id else o for o in project.objectives]
    return EntityUpdate(entity_id=entity.id, strategic=StrategicUpdate(projects_add_or_update=[replace(project, objectives=objectives)]))


def lodge_claim(entity: Any, building: Any) -> EntityUpdate:
    """The CLAIM a bed service makes for ``entity`` at ``building``: lodge from this tick, standing on the building's tile. No bed is delivered by the claim; `grant_beds` grants
    it (the lowest entity id first, up to the beds) and only then adds the bed's service. Idempotent: the same claim merged twice is one claim."""
    # One marker per execution of the REST. Updates of one subject are merged by concatenating their transfers, so the number of markers on the merged update is the number of
    # times main would have delivered the bed (today a REST is executed by the worker and again by the actions phase, a defect tracked on its own ticket): `grant_beds` delivers
    # the bed that many times, so F3 changes where the subject sleeps and not what a bed costs.
    marker = ResourceTransferIntent(source_id=building.id, source_kind="TOWN_SERVICE", transfer_kind=CLAIM_MARKER)
    return EntityUpdate(entity_id=entity.id, navigation=NavigationUpdate(lodged_in_set=building.id, target_clear=True, clear_path=True), resource_transfers=[marker],
                        new_position=(float(building.position[0]), float(building.position[1])), moved_this_tick=True)


def bed_delta(entity: Any, building: Any) -> EntityUpdate:
    """What a bed delivers: readiness, a little health and the charge for it (the bed is paid for, and heals, once per hold). The one definition, read by the rough-rest service
    (a building with no beds, on the reach tile) and by `grant_beds` (a granted lodging)."""
    charge = ResourceTransferIntent(source_id=building.id, source_kind="TOWN_SERVICE", gold_delta=-REST_PRICE_GOLD, transfer_kind="REST", is_group_required=True)
    return EntityUpdate(entity_id=entity.id, readiness_delta=10.0, combat=CombatUpdate(hp_delta=5), resource_transfers=[charge])


def _current_project(entity: Any) -> Any:
    """The subject's current project record, or None."""
    return entity.strategic.projects.get(entity.strategic.current_project_id or "")


def _without_walk(nav: Any) -> Any:
    """``nav`` with the walk target, mode and path dropped and cleared (the typed clear fields, not just unset)."""
    return replace(nav, target_set=None, movement_mode_set=None, path_set=None, target_clear=True, clear_path=True)


class _DropLog:
    """The typed, counted record of the walk targets and moves dropped from lodgers' updates in one pass (F3): each is counted under ``LODGER_TARGET_DROPPED`` (and under its reason) and
    recorded as a typed rejection event naming the proposer's movement mode, the subject's project kind and the target."""

    def __init__(self, state: Any, update: Any) -> None:
        self.tick = state.tick
        self.events: List[Any] = list(update.rejection_events)
        self.counts: Dict[str, int] = dict(update.rejections_delta)

    def note(self, e_id: int, mode: Any, project: Any, target: Any, why: Optional[str] = None) -> None:
        key = ReasonCode.LODGER_TARGET_DROPPED.value
        self.counts[key] = self.counts.get(key, 0) + 1
        if why is not None:   # the same drop, by reason: CLAIM_TICK or LEAVE_REFUSED; a drop with neither (a stayer after the claim tick) is the finding the arm asserts is zero
            self.counts[why] = self.counts.get(why, 0) + 1
        self.events.append(RejectionEvent(tick=self.tick, actor_id=e_id, action_kind="LODGE", reason=ReasonCode.LODGER_TARGET_DROPPED,
                                          target_id=f"{mode}|{getattr(getattr(project, 'kind', None), 'value', None)}|{target}"))

    def into(self, update: Any, entity_updates: Dict[int, Any]) -> Any:
        return replace(update, entity_updates=entity_updates, rejection_events=self.events, rejections_delta=self.counts)


def _claims_by_building(update: Any) -> Dict[int, List[int]]:
    claims: Dict[int, List[int]] = {}
    for eid, upd in update.entity_updates.items():
        nav = upd.navigation
        if nav is not None and nav.lodged_in_set is not None:
            claims.setdefault(nav.lodged_in_set, []).append(eid)
    return claims


def _take_markers(upd: Any) -> Tuple[Any, int]:
    """``upd`` without its claim markers, and how many it carried (one per execution of the REST)."""
    markers = sum(1 for t in upd.resource_transfers if t.transfer_kind == CLAIM_MARKER)
    return replace(upd, resource_transfers=[t for t in upd.resource_transfers if t.transfer_kind != CLAIM_MARKER]), markers


def _granted(entity: Any, upd: Any, building: Any, markers: int, drops: _DropLog) -> Any:
    """The update of a GRANTED claim: the bed delivered once per marker, the arrival objective resolved, the subject standing on the building's tile with no walk target."""
    for _ in range(max(1, markers)):
        upd = upd.merge(bed_delta(entity, building))
    arrived = resolve_arrival(entity)
    upd = upd.merge(arrived) if arrived is not None else upd
    # A granted claim stands on the building's tile: another writer's step merged into the same update (a walk onto the reach tile) must not decide where the lodger stands.
    tile = (float(building.position[0]), float(building.position[1]))
    if upd.new_position is not None and (float(upd.new_position[0]), float(upd.new_position[1])) != tile:
        # The claim wins the merge whatever its order: the step another writer merged into the claim's update is refused, typed and counted.
        drops.note(entity.id, None, _current_project(entity), upd.new_position, "LODGER_DROP_CLAIM_TICK")
    upd = replace(upd, new_position=tile, moved_this_tick=True)
    nav = upd.navigation
    if nav is not None and (nav.target_set is not None or nav.path_set is not None or nav.movement_mode_set is not None):
        # The claim tick: another writer's walk target in the same update must not survive the grant (the subject is indoors from now on); dropped, counted, typed.
        if nav.target_set is not None:
            drops.note(entity.id, nav.movement_mode_set, _current_project(entity), nav.target_set, "LODGER_DROP_CLAIM_TICK")
        upd = replace(upd, navigation=_without_walk(nav))
    return upd


def _refused(entity: Any, upd: Any) -> Any:
    """The update of a REFUSED claim: no lodging, no move, its REST task ended (an idle act), its fatigue project ended WAY_CLOSED."""
    ended = way_closed_end(entity, upd)
    task = replace(upd.task, payload_set={}) if upd.task is not None else upd.task
    out = replace(upd, navigation=replace(upd.navigation, lodged_in_set=None), new_position=None, moved_this_tick=False, task=task)
    return out.merge(ended) if ended is not None else out


def _settle_building(state: Any, building_id: int, claimants: List[int], refined: Dict[int, Any], drops: _DropLog) -> None:
    """Grant or refuse the claims at one building, lowest entity id first (TOWN-006 order): a subject that already lodges there keeps its bed, others take a free bed while one is left."""
    building = state.buildings.get(building_id)
    usable = building is not None and building.functional and lodges(building)
    held = set(lodgers_of(state, building_id)) if usable else set()
    free = int(building.beds) - len(held) if usable else 0
    for eid in sorted(claimants):
        entity = state.entities.get(eid)
        if entity is None:
            continue
        upd, markers = _take_markers(refined[eid])
        if usable and bed_free(int(building.beds), int(building.beds) - free, eid in held):
            free -= 0 if eid in held else 1
            refined[eid] = _granted(entity, upd, building, markers, drops)
        else:
            refined[eid] = _refused(entity, upd)


def grant_beds(state: Any, update: Any) -> Any:
    """Grant or refuse every lodge claim of this tick's ``update``, BEFORE any service is delivered (F3, divergence 2.155).

    Per building the claimants are taken in ascending entity id (TOWN-006 order): a subject that already lodges there keeps its bed, others take a free bed while one is left, and a
    building that is gone or not functional refuses everyone. A GRANTED claim gets the bed service (`building_services.bed_delta`: readiness, health, the charge) merged into its
    update. A REFUSED claim loses the claim (no lodging, no move), its REST task ends (an idle act, the brain re-decides) and its fatigue project ends with
    `ProjectEnd.WAY_CLOSED`; it never has a charge, readiness or heal applied because none was ever put on its update. A tick with no claim returns ``update`` unchanged."""
    claims = _claims_by_building(update)
    if not claims:
        return update
    refined = dict(update.entity_updates)
    drops = _DropLog(state, update)
    for building_id in sorted(claims):
        _settle_building(state, building_id, claims[building_id], refined, drops)
    return drops.into(update, refined)


def suppress_stayer_movement(entity: Any, update: Any) -> Any:
    """The tactical entry's one check (F3): a decision for a lodger that keeps it resting or eating (the update changes no task, or sets a resting or eating one) carries no walk target, mode or path.
    A decision that ends the stay (any other task) is a leaver's and is left whole. The decision itself still runs, so a lodger woken by hunger or a threat decides normally."""
    nav = update.navigation
    if entity.navigation.lodged_in is None or nav is None or (nav.target_set is None and nav.path_set is None and nav.movement_mode_set is None):
        return update
    task = update.task
    work_kind = task.work_kind_set if task is not None and task.work_kind_set is not None else entity.task.work_kind
    payload = task.payload_set if task is not None and task.payload_set is not None else entity.task.payload
    if not keeps_lodging(work_kind, payload):
        return update
    return replace(update, navigation=replace(nav, target_set=None, movement_mode_set=None, path_set=None))


def leave_tile(state: Any, origin: Tile, taken: Iterable[Tile]) -> Optional[Tile]:
    """Where a leaver steps out: the first free orthogonal tile beside ``origin`` in the fixed reach order (without the building tile itself), else the nearest free walkable tile
    within ``LEAVE_RING_RADIUS`` (Manhattan distance, then row, then column), else None. Free = not statically obstructed (world extent, terrain, building) and not in ``taken``."""
    blocked = set(taken)

    def free(tile: Tile) -> bool:
        return tile not in blocked and static_obstruction(tile, state) is None

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


def _drop_for_leaver(e_id: int, entity: Any, upd: Any, drops: _DropLog) -> Optional[Any]:
    """A leaver's own step is placed by `place_leavers` (it moves on from the next tick); a walk target proposed for it now is dropped too, so a refused leave (occupancy) cannot leave a
    lodger holding a target. None when there is nothing to drop."""
    nav = upd.navigation if upd is not None else None
    if nav is None or (nav.target_set is None and nav.path_set is None):
        return None
    if nav.target_set is not None:
        drops.note(e_id, nav.movement_mode_set, _current_project(entity), nav.target_set, "LODGER_DROP_LEAVE_REFUSED")
    return replace(upd, navigation=_without_walk(nav))


def _drop_for_stayer(e_id: int, entity: Any, upd: Any, claiming: bool, drops: _DropLog) -> Optional[Any]:
    """A walk target or a move proposed for a lodger who stays (or whose claim is granted this tick) is dropped. None when there is nothing to drop."""
    nav = upd.navigation if upd is not None else None
    walking = nav is not None and (nav.target_set is not None or nav.path_set is not None)
    moving = upd is not None and upd.new_position is not None and not claiming   # a claim's own move onto the building tile is not a drop
    if not (walking or moving):
        return None
    # A lodger re-claiming its own bed (a REST executes every tick) re-emits the claim's building-tile position: it is already standing there, so stripping it is no move and no drop.
    real_move = moving and tuple(float(c) for c in upd.new_position) != tuple(float(c) for c in entity.navigation.position)
    if (nav is not None and nav.target_set is not None) or real_move:
        drops.note(e_id, getattr(nav, "movement_mode_set", None), _current_project(entity), getattr(nav, "target_set", None), "LODGER_DROP_CLAIM_TICK" if claiming else None)
    return replace(upd, navigation=_without_walk(nav) if nav is not None else None, new_position=upd.new_position if claiming else None,
                   moved_this_tick=upd.moved_this_tick if claiming else False)


def drop_lodger_targets(state: Any, update: Any, leaving: Iterable[int]) -> Any:
    """The guard for a lodger who STAYS (F3, Q-B): a walk target or a move proposed for it this tick is dropped, so it can never be carried off its building's tile while it is lodged. A drop
    is never silent: each is counted under the rejection reason ``LODGER_TARGET_DROPPED`` and recorded as a typed rejection event naming the proposer's movement mode, the subject's project kind and the
    target. After lodging resolves the arrival objective the count must be zero; a non-zero count names the next writer of a lodger's target."""
    leaving = set(leaving)
    refined: Optional[Dict[int, Any]] = None
    drops = _DropLog(state, update)
    for e_id, e in state.entities.items():
        upd = update.entity_updates.get(e_id)
        nav = upd.navigation if upd is not None else None
        claiming = not is_lodged(e) and nav is not None and nav.lodged_in_set is not None   # granted this tick: indoors from now on (the writers after the grant land here)
        if not is_lodged(e) and not claiming:
            continue
        fixed = _drop_for_leaver(e_id, e, upd, drops) if e_id in leaving else _drop_for_stayer(e_id, e, upd, claiming, drops)
        if fixed is not None:
            refined = dict(update.entity_updates) if refined is None else refined
            refined[e_id] = fixed
    return update if refined is None else drops.into(update, refined)


def _is_leaving(state: Any, entity: Any, upd: Any) -> bool:
    """True when ``entity`` (a lodger) leaves this tick: its resulting task does not keep it resting or eating, or its building is gone or no longer functional."""
    building = state.buildings.get(entity.navigation.lodged_in)
    task = upd.task if upd is not None else None
    work_kind = task.work_kind_set if task is not None and task.work_kind_set is not None else entity.task.work_kind
    payload = task.payload_set if task is not None and task.payload_set is not None else entity.task.payload
    return building is None or not building.functional or not keeps_lodging(work_kind, payload)


def _step_out(state: Any, update: Any, leavers: List[Tuple[int, Any]]) -> Any:
    """Place the leavers, in ascending id, on free tiles (two leavers for one tile give it to the lowest id; the other takes its next tile)."""
    leaving_ids = {e_id for e_id, _ in leavers}
    taken = set(SpatialQueryService.get_occupancy_map(state))
    taken.update((int(u.new_position[0]), int(u.new_position[1])) for e_id, u in update.entity_updates.items() if e_id not in leaving_ids and u.new_position is not None)
    refined = dict(update.entity_updates)
    rejections = dict(update.rejections_delta)
    for e_id, e in leavers:
        tile = leave_tile(state, (int(e.navigation.position[0]), int(e.navigation.position[1])), taken)
        upd = refined.get(e_id, EntityUpdate(entity_id=e_id))
        if tile is None:
            rejections["LODGE_EXIT_BLOCKED"] = rejections.get("LODGE_EXIT_BLOCKED", 0) + 1
            refined[e_id] = replace(upd, new_position=None, moved_this_tick=False)
            continue
        taken.add(tile)
        leave = EntityUpdate(entity_id=e_id, navigation=NavigationUpdate(lodged_in_clear=True), new_position=(float(tile[0]), float(tile[1])), moved_this_tick=True)
        refined[e_id] = replace(upd, new_position=None, moved_this_tick=False).merge(leave)
    return replace(update, entity_updates=refined, rejections_delta=rejections)


def place_leavers(state: Any, update: Any) -> Any:
    """Step every lodger that is leaving out of its building, through the same position update a move uses (F3, divergence 2.155).

    A lodger leaves the tick its held rest ends: when its resulting task is not to keep resting or eating (`keeps_lodging`; an ended rest leaves no task), or when its building is gone or no
    longer functional (the one eject today). A walk target proposed for a lodger who stays does NOT make it leave: it is dropped and counted (`drop_lodger_targets`). It takes the first free orthogonal tile beside the building (fixed reach order), else the nearest free walkable tile within three tiles, else it stays lodged
    and awake and tries again next tick (counted under the rejection reason ``LODGE_EXIT_BLOCKED``). Leavers are placed in ascending id, so two leavers for one tile give it to the
    lowest id and the other takes its next tile. It moves on from the next tick: any move this tick's update already proposes for a leaver is dropped. Returns ``update`` unchanged when
    nobody lodges."""
    lodged = [(e_id, e) for e_id, e in state.entities.items() if is_lodged(e) and e.combat.alive and e.lifecycle.active]
    if not lodged:
        return drop_lodger_targets(state, update, ())   # nobody lodged yet, but a claim granted this tick must not keep another writer's walk target
    leavers = [(e_id, e) for e_id, e in sorted(lodged, key=lambda kv: kv[0]) if _is_leaving(state, e, update.entity_updates.get(e_id))]
    update = drop_lodger_targets(state, update, {e_id for e_id, _ in leavers})
    return _step_out(state, update, leavers) if leavers else update
