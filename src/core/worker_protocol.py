from __future__ import annotations

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple, TYPE_CHECKING
import dataclasses
from src.core.state import AuthoritativeState
from src.core.updates import EntityUpdate
from src.core.work import WorkClass

if TYPE_CHECKING:
    from src.core.state import EntityState


class PacketFieldMissingError(RuntimeError):
    """An executor-side read of an ``AuthoritativeState`` field the ``WorkerPacket`` neither carries nor lists as a lazily derived cache.

    Domain logic gets the read-only state under ``LocalSequentialExecutor`` and a packet under ``ConcurrentExecutionAdapter``; a ``getattr(ctx, name, default)`` on a
    packet that lacks ``name`` used to answer the default silently, so the two executors gave different worlds on the same seed
    (TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS). It is not an ``AttributeError`` on purpose: ``getattr(x, n, d)`` and ``hasattr``
    swallow only ``AttributeError``. The worker manager lets it pass through (docs/engine/contracts/bounded_concurrency_contract.md section 4).
    """


# State names a packet may lack because the helper that reads them derives the same answer from fields the packet does carry. One reason each:
PACKET_DERIVED_CACHE_NAMES = frozenset({
    "_spatial_grid_cache",          # DomainView._get_cached_spatial_grid builds a SpatialGrid from the packet's entities (the packet also carries spatial_grid)
    "_region_list_cache",           # DomainView.get_region_for_position rebuilds the region list from the packet's regions (the packet also carries region_list)
    "_building_map_cache",          # SpatialQueryService._get_building_map uses the packet's building_map
    "_occupancy_map_cache",         # SpatialQueryService.get_occupancy_map uses the packet's occupancy_map
    "_has_hostiles_or_dead_cache",  # a short-circuit boolean over entities; absent means the helper scans the packet's entities
    "_has_contracts_cache",         # a short-circuit boolean over entity contracts; absent means the helper scans the packet's entities
    "occupancy_snapshot",           # the state-vs-packet switch in legality.py: the else branch reads the packet's occupancy_map (same occupants)
    "movement_cache",               # a step cache: a hit equals recomputation; None on the state in every gate run measured
    "route_plans",                  # a derived 10-tick plan store (route_search); no route call has come from an executor in the runs measured
})
_state_field_names: "frozenset[str] | None" = None


def _state_names() -> "frozenset[str]":
    global _state_field_names
    if _state_field_names is None:
        _state_field_names = frozenset({f.name for f in dataclasses.fields(AuthoritativeState)}
                                       | {n for n, v in vars(AuthoritativeState).items() if isinstance(v, property)})
    return _state_field_names


class ResultStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


@dataclass(frozen=True, slots=True)
class WorkerPacket:
    """
    Law: A worker must receive a compact, bounded, and read-only context.
    Tick-local deterministic identity: {tick}:{ordinal}
    """
    packet_id: str
    work_id: str
    tick: int
    world_time: int
    seed: int
    
    # Target Information (Read-Only Snapshot)
    # work_class included for policy-aware logic inside workers
    work_class: WorkClass
    subject: EntityState
    
    # Canonical Context (Sorted by EntityID)
    # M8 Law: Neighbor context must be deterministic regardless of dictionary hash.
    neighbor_view: List[Tuple[int, EntityState]]
    # Work Type details
    work_kind: str
    payload: Dict[str, Any]
    
    # Priority Metadata (M8 Law: Determinism requires sorting by priority)
    class_priority: int = 0
    local_priority: int = 0
    
    regions: Dict[str, Any] = field(default_factory=dict)
    resource_nodes: Dict[int, Any] = field(default_factory=dict)
    buildings: Dict[int, Any] = field(default_factory=dict)
    groups: Dict[int, Any] = field(default_factory=dict)
    corpses: Dict[int, Any] = field(default_factory=dict)
    ground_items: Dict[int, Any] = field(default_factory=dict)
    all_entities: Dict[int, EntityState] = field(default_factory=dict)
    spatial_grid: Optional[Any] = None
    occupancy_map: Optional[Dict[Tuple[int, int], int]] = None
    region_list: Optional[List[Any]] = None
    building_map: Optional[Dict[Tuple[int, int], Any]] = None
    _region_index_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _regions_global_bounds: Optional[Any] = field(default=None, repr=False, compare=False)
    _building_region_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _node_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _corpse_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)
    _ground_item_map_cache: Optional[Any] = field(default=None, repr=False, compare=False)

    # Deterministic Context (Defaulted for backwards compatibility/optional inclusion)
    blocked_tiles: List[Tuple[int, int]] = field(default_factory=list) # Spatial Law
    transient_claims: List[Tuple[int, int]] = field(default_factory=list) # Multi-agent conflict truth
    terrain: Dict[Tuple[int, int], str] = field(default_factory=dict) # Tile terrain types
    # The state's own answers for the questions domain logic asks of its context (set by the executor from the read-only state, not defaulted):
    feature_flags: Dict[str, Any] = field(default_factory=dict)          # the state's flag modes (ENABLE_COMBAT_ENGAGEMENT ...)
    building_tiles: Dict[Tuple[int, int], str] = field(default_factory=dict)  # tile -> building kind (service reach, line of sight)
    town_center: Tuple[float, float] = (0.0, 0.0)                        # the town centre (movement)
    clans: Dict[str, Any] = field(default_factory=dict)                  # the clan registry (join / leave clan)

    def __getattr__(self, name: str) -> Any:
        """Called only when normal lookup fails (so a present attribute costs nothing): an undeclared state field is an error, not a default."""
        if name in PACKET_DERIVED_CACHE_NAMES or name.startswith("__") or name not in _state_names():
            raise AttributeError(f"'WorkerPacket' object has no attribute '{name}'")
        raise PacketFieldMissingError(
            f"executor-side read of AuthoritativeState.{name}, which the WorkerPacket does not carry: carry it in worker_protocol.WorkerPacket and executor.py, "
            f"or add it to PACKET_DERIVED_CACHE_NAMES with the reason it is derived")

    @property
    def entities(self) -> Dict[int, EntityState]:
        """Milestone D Law: Property-based access to the canonical neighbor view."""
        if self.all_entities:
            return self.all_entities
        return {eid: ent for eid, ent in self.neighbor_view}

    def to_readonly(self) -> WorkerPacket:
        """
        Milestone D Law:Parity with AuthoritativeState for decision logic.
        Since WorkerPacket is already frozen, this returns self.
        """
        return self


@dataclass(frozen=True, slots=True)
class WorkerResult:
    """
    Law: Workers return compact authoritative deltas linked to their source packet.
    M8 Law (Option A): One result per entity per tick.
    """
    source_packet_id: str
    work_id: str
    entity_id: int
    work_class: WorkClass
    update: EntityUpdate
    status: ResultStatus = ResultStatus.SUCCESS
    
    # Sorting keys for frozen commit law
    class_priority: int = 0
    local_priority: int = 0
    
    # Metadata for verification/replay
    compute_time_ns: int = 0
