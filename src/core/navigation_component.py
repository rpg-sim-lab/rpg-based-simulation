"""NavigationComponent: the state for movement intent and pathfinding, moved out of src/core/state.py (TCK-20261124-NAVIGATION-STATE-MOVES-OUT-OF-STATE-PY).

A pure move: the class body is byte-identical to the one in state.py at 0d0141804. src/core/state.py re-exports the name, so every importer keeps working and an old checkpoint whose pickle names
`src.core.state.NavigationComponent` still restores."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.core.giveup_records import GiveUpRecord, giveup_canonical
from src.core.movement_modes import MovementMode
from src.core.navigation_purpose import TargetPurpose, purpose_canonical
from src.core.service_refusals import ServiceRefusal, service_refusal_canonical


@dataclass(frozen=True, slots=True)
class NavigationComponent:
    """State for movement intent and pathfinding."""
    position: tuple[float, float] = (0.0, 0.0)
    target: Optional[tuple[float, float]] = None
    path: List[tuple[float, float]] = field(default_factory=list)
    moved_recently: bool = False
    movement_mode: MovementMode = MovementMode.WANDER
    last_failure_reason: Optional[str] = None
    # Phase 4 additions: Movement Congestion Recovery
    wait_count: int = 0
    oscillation_count: int = 0
    last_position: Optional[tuple[float, float]] = None

    # Mob Leash fields
    home_position: Optional[tuple[float, float]] = None
    leash_radius: float = 0.0  # 0 = no leash
    
    # Phase 3 Hardening: Cache region_id to avoid O(N) scans
    region_id: Optional[str] = None
    chase_ticks: int = 0
    max_chase_ticks: int = 15
    returning_home: bool = False

    # Idea 66: cached place_id back-reference, same rationale as region_id above --
    # avoids an O(N) scan of PlaceState.entity_ids for fast Place lookup.
    place_id: Optional[str] = None

    # D75 (MOV-04): terrain cost is time. The earliest tick this entity may take its next step: a step onto a tile of cost N sets it to
    # (the carried previous value, or the step tick) + N, so cost N takes N ticks and the entity never takes more than one step per tick.
    # 0.0 = never stepped (free to step).
    step_ready_tick: float = 0.0

    lodged_in: Optional[int] = None  # F3 (2.155): the building this subject LODGES in (position is its tile, on no tile held); set and cleared only by the apply path; (an insert is refused by the checkpoint schema check; an append needs a FIELD_RULES row)
    last_moved_tick: Optional[int] = None  # PERC-02 (2.210): the tick of the last MOVE of this body: any position change by the movement apply path (a step, a swap or a yield displacement; not lodge entry/exit, not a failed attempt); None = never stepped; LAST field (an insert is refused by the checkpoint schema check; an append needs a FIELD_RULES row)

    # 2.213 (COMB-356) + F1: the way-round count belongs to the PURSUIT (count, best distance, the tile it opened on, the tick of its last event); set and reset only by the navigation patch, see MovementSystem.wayround_after_event
    wayround_count: int = 0
    wayround_best_distance: Optional[int] = None
    wayround_anchor: Optional[Tuple[int, int]] = None
    wayround_last_tick: Optional[int] = None
    giveup_records: Tuple[GiveUpRecord, ...] = ()  # F2 (2.220): the typed way-round give-up records, appended by movement and cleared by the strategic pass (src/core/giveup_records.py); omitted from the canonical form while empty
    target_purpose: Optional[TargetPurpose] = None  # the #996 rework (design section 2.1): what the stored target was chosen for, written by the navigation patch with every NEW target and cleared with it; None = unknown (a target restored from an old checkpoint); omitted from the canonical form while None
    target_gated: bool = False  # the #996 rework (design section 4, the latch): True only for a target whose position passed a destination gate call; every by-value own-tile write that skips the gate stores False; omitted from the canonical form while False
    arrived_this_attempt: bool = False  # the #996 rework (ruling 476631fe, owner #715 7130852946, "arrived this attempt"): True once the body stood within `has_arrived` of THIS stored target since the target last took its current value. SET by movement (`MovementSystem.resolve_move`, measured from the position BEFORE the step) as `arrived_this_attempt_set`; KEPT by the navigation patch while the stored target stays the same value (a same-value re-set by the objective step keeps it); CLEARED by the patch whenever the stored target is cleared or takes another value (the arrived and give-up outcomes drop the target, so they clear it). Read at the give-up moment: an attempt that arrived files nothing. Omitted from the canonical form while False.
    service_refusals: Tuple[ServiceRefusal, ...] = ()  # K2 fix part B (divergence 2.226+): the typed refusals of a building service (INSUFFICIENT_GOLD), appended and cleared by the service writer, read by `infer_blockers`; omitted from the canonical dict while none is held

    def to_canonical_dict(self) -> Dict[str, Any]:
        """The navigation block of the entity's canonical form. `step_ready_tick` (D75) is present only once non-zero, so the form of an
        entity that never stepped is unchanged; `lodged_in` (F3) likewise, only while lodged."""
        res: Dict[str, Any] = {
            "target": self.target,
            "path": self.path,
            "moved_recently": self.moved_recently,
            "place_id": self.place_id,
            "movement_mode": str(self.movement_mode),
            "last_failure_reason": self.last_failure_reason,
            "wait_count": self.wait_count,
            "oscillation_count": self.oscillation_count,
            "last_position": self.last_position,
            "home_position": self.home_position,
            "leash_radius": self.leash_radius,
            "region_id": self.region_id,
            "chase_ticks": self.chase_ticks,
            "max_chase_ticks": self.max_chase_ticks,
            "returning_home": self.returning_home,
        }
        if self.step_ready_tick:
            res["step_ready_tick"] = self.step_ready_tick
        if self.lodged_in is not None:
            res["lodged_in"] = self.lodged_in  # present only while lodged, so the form of a subject that never lodged is unchanged (F3)
        if self.last_moved_tick is not None:
            res["last_moved_tick"] = self.last_moved_tick  # present once the body has stepped, so the form of one that never stepped is unchanged (PERC-02)
        if self.wayround_count:
            res["wayround_count"] = self.wayround_count  # present only while a way-round count is open (2.213), so the form of a subject that never needed one is unchanged
        if self.wayround_best_distance is not None:
            res["wayround_best_distance"] = self.wayround_best_distance
        if self.wayround_anchor is not None:
            res["wayround_anchor"] = self.wayround_anchor  # F1 (2.213): present only while a count is open
        if self.wayround_last_tick is not None:
            res["wayround_last_tick"] = self.wayround_last_tick
        res.update({**giveup_canonical(self.giveup_records), **purpose_canonical(self.target_purpose, self.target_gated), **({"arrived_this_attempt": True} if self.arrived_this_attempt else {}), **service_refusal_canonical(self.service_refusals)})  # F2: the give-up records only while one is held; the #996 rework: the target's purpose and gate flag only while set
        return res
