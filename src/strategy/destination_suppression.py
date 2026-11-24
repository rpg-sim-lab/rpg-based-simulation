"""Destination suppression (F2, TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON; reworked by TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON): READ-ONLY helpers over a subject's give-up records and navigation experiences.

A way-round give-up is held as a PENDING record until the strategic pass consumes it into a navigation experience (design section 4). No writer may re-target a tile within Chebyshev 1 of a pending record's anchor, nor of an ACTIVE
experience's anchor of the SAME purpose that is not yet due and not latched. Everything here is pure: it reads the entity and a tick and returns a value; nothing is written, there is no RNG, and every comparison is on
integer tiles and typed purposes, never on the subject text."""
from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Dict, FrozenSet, Iterable, Optional, Tuple

from src.content.navigation_experience_settings import navigation_experience_settings
from src.core.giveup_records import GiveUpRecord, near_anchor
from src.core.movement_modes import MovementMode
from src.core.navigation_experience import (
    NavExperienceStatus,
    NavigationExperience,
    NavigationExperienceUpdate,
)
from src.core.navigation_purpose import TargetPurpose, stored_purpose
from src.core.state import EntityState
from src.core.strategic import BlockerState
from src.core.updates import (
    EntityUpdate,
    InteractionUpdate,
    NavigationUpdate,
    TaskUpdate,
)
from src.strategy.experience_due import due_reason

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
    """Why a tile is forbidden as a destination: the id of the refusing record (``blocker_access_<x>_<y>`` for a pending give-up record, the ``nx_`` experience id for an experience), the anchor tile, the tick
    the refusal ends (``suppressed_until``; None while only PENDING or while the experience is trigger-only), and whether the refusing record is a still-unconsumed give-up record (``pending``)."""
    blocker_id: str
    anchor: Tuple[int, int]
    suppressed_until: Optional[int]
    pending: bool


def _record_hit(records: Iterable[GiveUpRecord], tx: int, ty: int) -> Optional[SuppressionHit]:
    """The first pending give-up record whose anchor is within Chebyshev 1 of (tx, ty), as a pending hit, or None."""
    for record in records:
        anchor = (int(record.anchor[0]), int(record.anchor[1]))
        if near_anchor((tx, ty), anchor):
            return SuppressionHit(access_blocker_id(anchor), anchor, None, True)
    return None


def _latched(entity: EntityState, record: NavigationExperience) -> bool:
    """True when the subject's STORED target was accepted through the gate at this record's anchor with this record's purpose (design section 4, the latch): a target accepted while the record was due, which a later
    non-monotone rule must not re-refuse."""
    target = entity.navigation.target
    return target is not None and entity.navigation.target_gated and near_anchor(target, record.anchor) and stored_purpose(entity) == record.purpose


def _experience_hit(entity: EntityState, tile: Tuple[int, int], tick: int, purpose: Optional[TargetPurpose], reviewed: FrozenSet[Tuple[str, int]]) -> Optional[SuppressionHit]:
    """The lowest-id ACTIVE experience of the subject with this ``purpose`` whose anchor is within Chebyshev 1 of ``tile``, that is not due at ``tick`` (`due_reason`, a pure read of the subject's own state), not
    latched, and not reviewed by the staged update (``reviewed``: ids and cycles), or None. A REVIEWED record never refuses; a call with no purpose (an old checkpoint's target) is refused by no experience."""
    records = entity.cognition.memory.navigation.records
    if purpose is None or not records:
        return None
    settings = navigation_experience_settings()
    for record in sorted(records, key=lambda r: r.experience_id):
        if record.status != NavExperienceStatus.ACTIVE or record.purpose != purpose or (record.experience_id, record.cycle) in reviewed or not near_anchor(tile, record.anchor):
            continue
        if due_reason(record, entity, tick, settings) is None and not _latched(entity, record):
            return SuppressionHit(record.experience_id, (int(record.anchor[0]), int(record.anchor[1])), record.next_review_tick, False)
    return None


def destination_suppressed(entity: EntityState, pos: Tuple[float, float], tick: int, purpose: Optional[TargetPurpose], staged: Optional[EntityUpdate] = None) -> Optional[SuppressionHit]:
    """The reason ``pos`` is forbidden as a destination for this subject at ``tick``, or None. Sources, all within Chebyshev 1 of an anchor (integer tiles; the +-1 covers the task layer's one-tile jitter of the
    objective's target), in order: (1) the subject's own PENDING give-up records (``navigation.giveup_records``, held until the strategic pass consumes them), any purpose; (2) an ACTIVE navigation experience of
    the SAME ``purpose`` that is not yet due and not latched (`_experience_hit`). The FUSED STRATEGIC PASS only: ``staged`` is the subject's update staged so far this tick; its ``navigation.giveup_record_add``
    (movement_routing stages it before the pass) counts as (1), and the reviews on its ``navigation_experience`` lift the refusal of the records they review for the pass. A staged experience UPSERT does not refuse
    in the pass that files it (it applies from the next read). Pure: reads, never writes."""
    tx, ty = int(pos[0]), int(pos[1])
    records = entity.navigation.giveup_records
    reviewed: FrozenSet[Tuple[str, int]] = frozenset()
    if staged is not None:
        if staged.navigation is not None and staged.navigation.giveup_record_add is not None:
            records = (*records, staged.navigation.giveup_record_add)
        if staged.navigation_experience is not None:
            reviewed = frozenset((r.experience_id, r.cycle) for r in staged.navigation_experience.reviews)
    return _record_hit(records, tx, ty) or _experience_hit(entity, (tx, ty), tick, purpose, reviewed)


@dataclass(frozen=True, slots=True)
class ObjectiveDestinationSuppressed(EntityUpdate):
    """The typed outcome OBJECTIVE_DESTINATION_SUPPRESSED (F2, divergence 2.220): the objective's destination lies within Chebyshev 1 of a pending give-up record, or of an active navigation experience of its purpose, so the
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
    """True when no pending give-up record or active experience forbids ``pos`` as a destination."""
    return destination_suppressed(entity, pos, tick, purpose, staged) is None


def suppression_anchors(entity: EntityState, pos: Tuple[float, float], tick: int, purpose: Optional[TargetPurpose], staged: Optional[EntityUpdate] = None) -> Tuple[Tuple[int, int], ...]:
    """The anchor tile of the suppression that forbids ``pos`` for this subject at ``tick`` (what `destination_suppressed` found) as a one-tuple, or () when ``pos`` is open. The strategic pass's typed target clear carries it
    (`NavigationUpdate.target_clear_anchors`), so the navigation patch can let that clear beat a same-update set near the same anchor."""
    hit = destination_suppressed(entity, pos, tick, purpose, staged)
    return () if hit is None else (hit.anchor,)


def filed_suppression_anchors(entity: EntityState, experience: Optional[NavigationExperienceUpdate]) -> Tuple[Tuple[int, int], ...]:
    """The anchors of every experience the pass FILES or RENEWS for this subject (an upsert of ``experience``, ACTIVE, not evicted by the same update) whose purpose equals the subject's STORED target purpose (design
    section 7, the purpose-scoped filing source), sorted and de-duplicated: the filer's own fact. A stored target moving for ANOTHER purpose stays. () when the pass filed none."""
    if experience is None or not experience.upserts:
        return ()
    held = stored_purpose(entity)
    if held is None:
        return ()
    return tuple(sorted({(int(r.anchor[0]), int(r.anchor[1])) for r in experience.upserts if r.status == NavExperienceStatus.ACTIVE and r.experience_id not in experience.evictions and r.purpose == held}))


def navigation_with_filing_anchor(entity: EntityState, nav: Optional[NavigationUpdate], experience: Optional[NavigationExperienceUpdate]) -> Optional[NavigationUpdate]:
    """``nav`` carrying the anchors of the experiences the pass filed this tick in `target_clear_anchors` WITHOUT `target_clear` (the navigation patch then drops a same-update set near any of them and clears a stored
    target near any of them, and nothing else), united with the anchors it already carries (the refusal clear's). ``nav`` is returned as it is when the pass filed nothing."""
    filed = filed_suppression_anchors(entity, experience)
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
