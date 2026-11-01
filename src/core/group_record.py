"""GroupRecord: the authoritative record of a multi-entity coordination unit (moved out of state.py; src.core.state re-exports it so
checkpoints pickled with the old module path still load)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from src.core.enums import GroupDissolutionReason
from src.core.strategic import ContractStatus


class GroupBindingError(ValueError):
    """A GroupRecord names a contract (contract_id) but not the entity holding it (contract_holder_id)."""


class GroupCounterMissingError(RuntimeError):
    """`AuthoritativeState.next_group_id` is None where decision code needs it. The counter is seeded ONLY when a state is built or an older checkpoint is
    restored (`AuthoritativeState.__post_init__`, `checkpoint_fields.fill_missing_fields`); seeding anywhere else would silently recompute durable state and hide
    the corruption the counter exists to expose, so a missing counter here is an error."""


@dataclass(frozen=True, slots=True)
class GroupRecord:
    """Authoritative state for a multi-entity coordination unit.

    A group formed by a contract is bound to it: `contract_id` is the one stored id of that contract and `contract_holder_id` the entity
    whose strategic.contracts holds it (the formation scan's `entity_a`). The binding is written once, at formation, and never changes;
    a leadership change does not move it. A record with `contract_id` set and no `contract_holder_id` is invalid (GroupBindingError).
    Groups not formed by a contract (squads) have neither and are unaffected.
    """
    id: int
    leader_id: int
    member_ids: Set[int]
    anchor: tuple[float, float]
    shared_target_id: Optional[int] = None
    contract_id: Optional[str] = None
    cohesion_radius: float = 5.0
    last_updated_tick: int = 0
    roles: Dict[int, str] = field(default_factory=dict) # entity_id -> role_name
    str_apt: float = 1.0
    int_apt: float = 1.0
    agi_apt: float = 1.0
    vit_apt: float = 1.0
    end_apt: float = 1.0
    formation_tick: int = 0
    escort_target_id: Optional[int] = None
    grievance_log: Tuple[str, ...] = ()
    reward_pool: int = 0
    last_leadership_check_tick: int = 0
    dissolution_tick: Optional[int] = None
    composition_score: float = 0.0  # PartyCompositionScorer result at formation (SOC-232)
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
    # New fields go AFTER _canonical_cache: a slotted dataclass unpickles positionally, so an older checkpoint's tuple must keep lining up
    # with this class's field order (the added slots stay absent and are filled by checkpoint_fields.fill_missing_fields).
    contract_holder_id: Optional[int] = None  # entity holding `contract_id`; set once at formation, bound groups only
    dissolution_reason: Optional[GroupDissolutionReason] = None  # typed end reason; bound groups only, set with dissolution_tick
    dissolution_contract_status: Optional[ContractStatus] = None  # status the binding contract had when BINDING_CONTRACT_NOT_ACTIVE ended the group

    def __post_init__(self) -> None:
        if self.contract_id is not None and self.contract_holder_id is None:
            raise GroupBindingError(f"group {self.id}: contract_id {self.contract_id!r} has no contract_holder_id")

    def to_canonical_dict(self) -> Dict[str, Any]:
        """Canonical form for hashing and checkpoints; the binding and end-reason keys are present only when set."""
        cached: Optional[Dict[str, Any]] = self._canonical_cache
        if cached is not None:
            return cached
        res = {
            "id": self.id,
            "leader_id": self.leader_id,
            "member_ids": sorted(list(self.member_ids)),
            "anchor": self.anchor,
            "shared_target_id": self.shared_target_id,
            "contract_id": self.contract_id,
            "cohesion_radius": self.cohesion_radius,
            "last_updated_tick": self.last_updated_tick,
            "roles": {str(k): v for k, v in sorted(self.roles.items())},
            "aptitudes": {
                "str": self.str_apt,
                "int": self.int_apt,
                "agi": self.agi_apt,
                "vit": self.vit_apt,
                "end": self.end_apt
            },
            "formation_tick": self.formation_tick,
            "escort_target_id": self.escort_target_id,
            "grievance_log": list(self.grievance_log),
            "reward_pool": self.reward_pool,
            "last_leadership_check_tick": self.last_leadership_check_tick,
            "dissolution_tick": self.dissolution_tick,
            "composition_score": self.composition_score,
        }
        # Omitted when None: groups not formed by a contract (and every unfinished bound group's reason) canonicalise exactly as before.
        if self.contract_holder_id is not None:
            res["contract_holder_id"] = self.contract_holder_id
        if self.dissolution_reason is not None:
            res["dissolution_reason"] = self.dissolution_reason.value
        if self.dissolution_contract_status is not None:
            res["dissolution_contract_status"] = self.dissolution_contract_status.value
        object.__setattr__(self, "_canonical_cache", res)
        return res


def is_live_group(group: "GroupRecord") -> bool:
    """The one definition of a live group: not dissolved. The store keeps dissolved records (their ids stay taken and the canonical data holds them), so
    code that works on groups that still exist walks `live_group_items` / `live_group_ids`; code that needs every stored id (the id allocator, the
    counter seed, the hash, `find_group_for_contract`) walks the store itself."""
    return group.dissolution_tick is None


def live_group_items(groups: "Dict[int, GroupRecord]") -> "List[Tuple[int, GroupRecord]]":
    """(id, record) of every live group, in the store's insertion order (the cohesion loop's order decides the order of its penalties)."""
    return [(group_id, group) for group_id, group in groups.items() if is_live_group(group)]


def live_group_ids(groups: "Dict[int, GroupRecord]") -> "List[int]":
    """Ids of every live group, in the store's insertion order."""
    return [group_id for group_id, group in groups.items() if is_live_group(group)]
