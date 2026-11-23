"""Destination suppression (F2, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON; rpg-designer FINAL v2.1): READ-ONLY helpers over a subject's ACCESS blockers.

A way-round give-up files an ACCESS blocker ``blocker_access_<x>_<y>`` for the anchor tile (the strategic pass's consume step); while that blocker is suppressed no writer may re-target a tile within
Chebyshev 1 of its anchor. Everything here is pure: it reads the entity and a tick and returns a value; nothing is written, there is no RNG, and every comparison is on integer tiles by the id, never
by the subject text."""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Dict, Iterable, Mapping, Optional, Tuple

from src.core.giveup_records import GiveUpRecord, near_anchor
from src.core.movement_modes import MovementMode
from src.core.navigation_purpose import TargetPurpose, stored_purpose
from src.core.state import EntityState
from src.core.strategic import BlockerState
from src.core.updates import (
    EntityUpdate,
    InteractionUpdate,
    NavigationUpdate,
    StrategicUpdate,
    TaskUpdate,
)

ACCESS_BLOCKER_ID_PREFIX = "blocker_access_"
_ACCESS_ID = re.compile(r"^blocker_access_(-?\d+)_(-?\d+)$")


def access_blocker_id(tile: Tuple[float, float]) -> str:
    """The id of the ACCESS blocker for ``tile`` (integer tile), the one `infer_blockers` files for a navigation failure: ``blocker_access_<x>_<y>``."""
    return f"{ACCESS_BLOCKER_ID_PREFIX}{int(tile[0])}_{int(tile[1])}"


def access_subject(tile: Tuple[float, float]) -> str:
    """The subject text of an ACCESS blocker for ``tile`` in the format `infer_blockers` already writes (``f"{target_pos}"`` on float coordinates, e.g. ``"(9.0, 5.0)"``), so every existing reader of an
    ACCESS blocker's subject (resolution, detour, ResolveBlockerScorer, score modifiers) behaves as it does today. Normalising the format is another ticket's job (the material/partner subject ticket)."""
    return f"{(float(tile[0]), float(tile[1]))}"


def access_blocker_tile(blocker: BlockerState) -> Optional[Tuple[int, int]]:
    """The integer tile an ACCESS blocker names by its id, or None when it is not a ``blocker_access_<x>_<y>`` blocker (the congestion blocker, a material blocker)."""
    if blocker.kind != "access":
        return None
    m = _ACCESS_ID.match(blocker.id)
    return (int(m.group(1)), int(m.group(2))) if m else None


@dataclass(frozen=True, slots=True)
class SuppressionHit:
    """Why a tile is forbidden as a destination: the ACCESS blocker id of the anchor, the anchor tile, how long (``suppressed_until``, None while only PENDING), whether the forbidding record is a
    still-unconsumed give-up record (``pending``, v2.1c) or a filed blocker, and the blocker's ``giveup_count`` (0 while pending)."""
    blocker_id: str
    anchor: Tuple[int, int]
    suppressed_until: Optional[int]
    pending: bool
    giveup_count: int


def _blocker_hit(blockers: Mapping[str, BlockerState], tx: int, ty: int, tick: int) -> Optional[SuppressionHit]:
    """The lowest-id unresolved ACCESS blocker still suppressed at ``tick`` whose anchor is within Chebyshev 1 of (tx, ty), or None."""
    hit: Optional[SuppressionHit] = None
    for blocker in blockers.values():
        tile = access_blocker_tile(blocker)
        if tile is None or blocker.resolved or tick >= blocker.suppression_until_tick:
            continue
        if near_anchor((tx, ty), tile) and (hit is None or blocker.id < hit.blocker_id):
            hit = SuppressionHit(blocker.id, tile, blocker.suppression_until_tick, False, blocker.giveup_count)
    return hit


def _record_hit(records: Iterable[GiveUpRecord], tx: int, ty: int) -> Optional[SuppressionHit]:
    """The first pending give-up record whose anchor is within Chebyshev 1 of (tx, ty), as a pending hit, or None."""
    for record in records:
        anchor = (int(record.anchor[0]), int(record.anchor[1]))
        if near_anchor((tx, ty), anchor):
            return SuppressionHit(access_blocker_id(anchor), anchor, None, True, 0)
    return None


def destination_suppressed(entity: EntityState, pos: Tuple[float, float], tick: int, purpose: Optional[TargetPurpose], staged: Optional[EntityUpdate] = None) -> Optional[SuppressionHit]:
    """The reason ``pos`` is forbidden as a destination for this subject at ``tick``, or None. Sources, all within Chebyshev 1 of an anchor (integer tiles; the +-1 covers the task layer's one-tile
    jitter of the objective's target): (1) an unresolved ``blocker_access_<x>_<y>`` ACCESS blocker of the subject with ``tick`` before its ``suppression_until_tick``; (2) v2.1c, the subject's own PENDING
    give-up records (``navigation.giveup_records``, held until the strategic pass consumes them). v2.2 D1, the FUSED STRATEGIC PASS only: ``staged`` is the subject's update staged so far this tick, and
    its ``navigation.giveup_record_add`` (movement_routing stages it before the pass) and its ``strategic.blockers_add_or_update`` / ``blockers_remove`` (the pass's own consume step files them) count as (2)
    and (1) too, so a target cannot be re-set to the anchor in the pass that learns of the give-up. A filed blocker wins over a pending record, and the lowest blocker id wins among blockers, so the answer
    does not depend on dict order."""
    tx, ty = int(pos[0]), int(pos[1])
    blockers = entity.strategic.blockers
    records = entity.navigation.giveup_records
    if staged is not None:
        if staged.strategic is not None:
            blockers = {**blockers, **{b.id: b for b in staged.strategic.blockers_add_or_update}}
            for removed in staged.strategic.blockers_remove:
                blockers.pop(removed, None)
        if staged.navigation is not None and staged.navigation.giveup_record_add is not None:
            records = (*records, staged.navigation.giveup_record_add)
    return _blocker_hit(blockers, tx, ty, tick) or _record_hit(records, tx, ty)


@dataclass(frozen=True, slots=True)
class ObjectiveDestinationSuppressed(EntityUpdate):
    """The typed outcome OBJECTIVE_DESTINATION_SUPPRESSED (F2, divergence 2.220): the objective's destination lies within Chebyshev 1 of a give-up-filed ACCESS blocker that is still suppressed, so the
    step writes NO target and NO navigation update. It is an empty `EntityUpdate` (the tactical pass returns it as handled: the subject stays idle for the brain, as a held step does, and does
    not fall through to the role and cohesion branches), a subclass only so the own-job spy and the tests can tell it from any other empty update by type."""


@dataclass(frozen=True, slots=True)
class DestinationSuppressedEnd(EntityUpdate):
    """The typed end of an ENTITY_MOVE whose held target the executor refuses to re-emit (F2 v2.2a class X, divergence 2.220): the same update as `tracked_move_completion_update` (idle task, target
    cleared, so tactics re-decides), a subclass only so the own-job spy (G7) and the tests can tell it by type. No ReasonCode carries it: every carrier in `navigation` (a failure reason) is read by the
    information phase as a failed search, and the idle task's payload must stay empty (scheduler `is_idle_act`)."""


def suppressed_move_end(entity_id: int) -> DestinationSuppressedEnd:
    """The `DestinationSuppressedEnd` for ``entity_id``: target cleared, idle ENTITY_ACT task."""
    return DestinationSuppressedEnd(entity_id=entity_id, navigation=NavigationUpdate(target_clear=True), task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}))


def destination_open(entity: EntityState, pos: Tuple[float, float], tick: int, purpose: Optional[TargetPurpose], staged: Optional[EntityUpdate] = None) -> bool:
    """True when no suppressed give-up ACCESS blocker forbids ``pos`` as a destination."""
    return destination_suppressed(entity, pos, tick, purpose, staged) is None


def suppression_anchors(entity: EntityState, pos: Tuple[float, float], tick: int, purpose: Optional[TargetPurpose], staged: Optional[EntityUpdate] = None) -> Tuple[Tuple[int, int], ...]:
    """The anchor tile of the suppression that forbids ``pos`` for this subject at ``tick`` (what `destination_suppressed` found) as a one-tuple, or () when ``pos`` is open. The strategic pass's typed target clear carries it
    (`NavigationUpdate.target_clear_anchors`), so the navigation patch can let that clear beat a same-update set near the same anchor."""
    hit = destination_suppressed(entity, pos, tick, purpose, staged)
    return () if hit is None else (hit.anchor,)


def filed_suppression_anchors(entity: EntityState, staged: Optional[StrategicUpdate], tick: int) -> Tuple[Tuple[int, int], ...]:
    """The anchors of every ACCESS suppression the pass FILES or EXTENDS for this subject at ``tick`` (a staged ``blockers_add_or_update`` blocker, unresolved, not removed by the same update, suppressed past ``tick`` and past its
    stored suppression), sorted and de-duplicated: the filer's own fact. Written only by the strategic pass, which is the only writer of blocker extensions. () when the pass filed none."""
    if staged is None:
        return ()
    found = set()
    for blocker in staged.blockers_add_or_update:
        tile = access_blocker_tile(blocker)
        stored = entity.strategic.blockers.get(blocker.id)
        if tile is None or blocker.id in staged.blockers_remove or blocker.resolved or blocker.suppression_until_tick <= tick or (stored is not None and blocker.suppression_until_tick <= stored.suppression_until_tick):
            continue
        found.add(tile)
    return tuple(sorted(found))


def navigation_with_filing_anchor(entity: EntityState, nav: Optional[NavigationUpdate], staged: Optional[StrategicUpdate], tick: int) -> Optional[NavigationUpdate]:
    """``nav`` carrying the anchors of the suppressions the pass filed this tick in `target_clear_anchors` WITHOUT `target_clear` (the navigation patch then drops a same-update set near any of them and clears a stored target near
    any of them, and nothing else), united with the anchors it already carries (the refusal clear's). ``nav`` is returned as it is when the pass filed nothing."""
    filed = filed_suppression_anchors(entity, staged, tick)
    if not filed:
        return nav
    held = nav.target_clear_anchors if nav is not None else ()
    return replace(nav or NavigationUpdate(), target_clear_anchors=tuple(sorted(set(held) | set(filed))))


def propose_target(entity: EntityState, pos: Tuple[float, float], tick: int, purpose: TargetPurpose, staged: Optional[EntityUpdate] = None) -> Optional[Tuple[float, float]]:
    """THE proposal point of a place target (F2 v2.2 D2, owner scope #715 7062303482: every writer, combat and flight included, no exemption): ``pos`` when it may be a destination for this subject, None
    when `destination_suppressed` forbids it. A decision site writes ``NavigationUpdate(target_set=...)`` for a place only from a non-None return; what None means is per site class (rpg-designer v2.2a
    D2: flight tries its next candidate, a combat positioning branch does not fire, stalemate-break holds, an objective idles typed, the strategic bridge tries its next alternative, the executor ends
    the task). ``staged`` is passed by the fused strategic pass only. Pure: reads, never writes."""
    return pos if destination_suppressed(entity, pos, tick, purpose, staged) is None else None


def regroup_to_town_update(entity_id: int, staged: Optional[EntityUpdate], town_target: Tuple[float, float], purpose: TargetPurpose) -> EntityUpdate:
    """The update that walks a subject carrying items to the town tile (movement mode REGROUP, interaction reset), built on its staged update when it has one (the fused strategic pass's two town
    fallbacks, the fast path and the bridge, share it; the caller keeps the guards: `destination_open` and target != town_target). ``purpose`` is the caller's bound `purpose_of(...)` name, the same one it
    passed to the gate; the target is stored with it and as gated. Plain builder: reads nothing, writes nothing."""
    if staged is None:
        return EntityUpdate(entity_id=entity_id, navigation=NavigationUpdate(target_set=town_target, movement_mode_set=MovementMode.REGROUP, target_purpose_set=purpose, target_gated_set=True), interaction=InteractionUpdate(reset=True))
    return replace(staged, navigation=replace(staged.navigation or NavigationUpdate(), target_set=town_target, movement_mode_set=MovementMode.REGROUP, target_purpose_set=purpose, target_gated_set=True), interaction=InteractionUpdate(reset=True))


def reaffirm_move_update(subject: EntityState, target: Tuple[float, float], tick: int) -> EntityUpdate:
    """The re-emission of a held ENTITY_MOVE's target (the executor and the worker dispatch share it; F2 v2.2a class X): the typed `suppressed_move_end` when ``target`` is suppressed, else the update that
    re-affirms it. Never writes a refused target. The re-emission carries the subject's STORED purpose and gate flag (the pursuit's purpose does not change because its tracked position moved); a subject with no stored purpose
    (a target restored from an old checkpoint, or a payload left after a give-up cleared the target) ends the move typed and re-decides (the #996 rework, design section 4)."""
    purpose = stored_purpose(subject)
    if purpose is None or propose_target(subject, target, tick, purpose) is None:
        return suppressed_move_end(subject.id)
    return EntityUpdate(entity_id=subject.id, navigation=NavigationUpdate(target_set=target, target_purpose_set=purpose, target_gated_set=subject.navigation.target_gated))


def suppressed_move_to(entity: EntityState, intent_kind: str, position: Optional[Tuple[float, float]], tick: int, purpose: TargetPurpose) -> Optional[Dict[int, EntityUpdate]]:
    """The class-O outcome of a ``MOVE_TO`` intent (the investigate path, F2 v2.2a): ``{entity.id: ObjectiveDestinationSuppressed}`` when the intent is a MOVE_TO whose ``position`` is suppressed, else
    None (the intent runs as before). No target is written."""
    if intent_kind != "MOVE_TO" or position is None or propose_target(entity, position, tick, purpose) is not None:
        return None
    return {entity.id: ObjectiveDestinationSuppressed(entity_id=entity.id)}
