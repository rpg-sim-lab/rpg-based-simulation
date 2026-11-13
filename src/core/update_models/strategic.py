"""The strategic-cognition update record, StrategicUpdate."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from src.core.strategic import (
        BlockerState,
        CandidateZone,
        CommittedIntention,
        ConcernState,
        ContractState,
        DirectiveState,
        HypothesisState,
        LeadState,
        MarriageState,
        ProjectState,
        SourceTrustEntry,
        TurningPointState,
    )


@dataclass(frozen=True, slots=True)
class StrategicUpdate:
    """Updates to strategic markers (blockers, leads, directives, projects, concerns, etc.)."""
    # Blockers
    blockers_add_or_update: list[BlockerState] = field(default_factory=list)
    blockers_remove: list[str] = field(default_factory=list)
    # Leads
    leads_add_or_update: list[LeadState] = field(default_factory=list)
    leads_remove: list[str] = field(default_factory=list)
    # Directives
    directives_add_or_update: list[DirectiveState] = field(default_factory=list)
    directives_remove: list[str] = field(default_factory=list)
    # Projects
    projects_add_or_update: list[ProjectState] = field(default_factory=list)
    projects_remove: list[str] = field(default_factory=list)
    current_project_id_set: Optional[str] = None
    current_objective_id_set: Optional[str] = None
    # Boredom (PH5 M2)
    boredom_delta: Dict[str, float] = field(default_factory=dict) # GoalKind -> delta
    # Concerns
    concerns_add_or_update: list[ConcernState] = field(default_factory=list)
    concerns_remove: list[str] = field(default_factory=list)
    # Candidate Zones
    candidate_zones_add_or_update: list[CandidateZone] = field(default_factory=list)
    candidate_zones_remove: list[str] = field(default_factory=list)
    # Hypotheses
    hypotheses_add_or_update: list[HypothesisState] = field(default_factory=list)
    hypotheses_remove: list[str] = field(default_factory=list)
    # Source Trust
    source_trust_updates: list[SourceTrustEntry] = field(default_factory=list)
    # Contracts
    contracts_add_or_update: list[ContractState] = field(default_factory=list)
    contracts_remove: list[str] = field(default_factory=list)
    # Marriages
    marriages_add_or_update: list[MarriageState] = field(default_factory=list)
    marriages_remove: list[str] = field(default_factory=list)
    # Turning Points
    turning_points_add: list[TurningPointState] = field(default_factory=list)
    # Overload
    overload_source_set: Optional[str] = None
    overload_tick_set: Optional[int] = None
    # Routing (adventure-route observability restore)
    last_routing_family_set: Optional[str] = None
    last_routing_tick_set: Optional[int] = None
    # Beliefs
    beliefs_add_or_update: list[Any] = field(default_factory=list)
    beliefs_remove: list[str] = field(default_factory=list)
    # Committed Intentions
    committed_intentions_add_or_update: list[CommittedIntention] = field(default_factory=list)
    committed_intentions_remove: list[str] = field(default_factory=list)  # by intention_id
    # Home/Exile (idea 59/65) -- set once at birth, or once at displacement if previously unset;
    # never overwrites an already-set value (a refugee's home_region_id is their *original* home).
    home_region_id_set: Optional[str] = None

    def is_noop(self) -> bool:
        """True when no blocker, lead, directive, project, concern, zone, hypothesis or intention change is staged."""
        return (not self.blockers_add_or_update and not self.blockers_remove and
                not self.leads_add_or_update and not self.leads_remove and
                not self.directives_add_or_update and not self.directives_remove and
                not self.projects_add_or_update and not self.projects_remove and
                self.current_project_id_set is None and self.current_objective_id_set is None and
                not self.boredom_delta and not self.concerns_add_or_update and
                not self.concerns_remove and not self.candidate_zones_add_or_update and
                not self.candidate_zones_remove and not self.hypotheses_add_or_update and
                not self.hypotheses_remove and not self.source_trust_updates and
                not self.contracts_add_or_update and not self.contracts_remove and
                not self.marriages_add_or_update and not self.marriages_remove and
                not self.turning_points_add and self.overload_source_set is None and
                self.overload_tick_set is None and self.last_routing_family_set is None and
                self.last_routing_tick_set is None and not self.beliefs_add_or_update and
                not self.beliefs_remove and not self.committed_intentions_add_or_update and
                not self.committed_intentions_remove and self.home_region_id_set is None)

    def merge(self, other: StrategicUpdate) -> StrategicUpdate:
        """Merges another StrategicUpdate into this one."""
        if not other or other.is_noop():
            return self
            
        # Dictionaries sum deltas
        new_boredom = dict(self.boredom_delta)
        for k, v in other.boredom_delta.items():
            new_boredom[k] = new_boredom.get(k, 0.0) + v
            
        return StrategicUpdate(
            blockers_add_or_update=self.blockers_add_or_update + other.blockers_add_or_update,
            blockers_remove=self.blockers_remove + other.blockers_remove,
            leads_add_or_update=self.leads_add_or_update + other.leads_add_or_update,
            leads_remove=self.leads_remove + other.leads_remove,
            directives_add_or_update=self.directives_add_or_update + other.directives_add_or_update,
            directives_remove=self.directives_remove + other.directives_remove,
            projects_add_or_update=self.projects_add_or_update + other.projects_add_or_update,
            projects_remove=self.projects_remove + other.projects_remove,
            current_project_id_set=other.current_project_id_set if other.current_project_id_set is not None else self.current_project_id_set,
            current_objective_id_set=other.current_objective_id_set if other.current_objective_id_set is not None else self.current_objective_id_set,
            boredom_delta=new_boredom,
            concerns_add_or_update=self.concerns_add_or_update + other.concerns_add_or_update,
            concerns_remove=self.concerns_remove + other.concerns_remove,
            candidate_zones_add_or_update=self.candidate_zones_add_or_update + other.candidate_zones_add_or_update,
            candidate_zones_remove=self.candidate_zones_remove + other.candidate_zones_remove,
            hypotheses_add_or_update=self.hypotheses_add_or_update + other.hypotheses_add_or_update,
            hypotheses_remove=self.hypotheses_remove + other.hypotheses_remove,
            source_trust_updates=self.source_trust_updates + other.source_trust_updates,
            contracts_add_or_update=self.contracts_add_or_update + other.contracts_add_or_update,
            contracts_remove=self.contracts_remove + other.contracts_remove,
            marriages_add_or_update=self.marriages_add_or_update + other.marriages_add_or_update,
            marriages_remove=self.marriages_remove + other.marriages_remove,
            turning_points_add=self.turning_points_add + other.turning_points_add,
            overload_source_set=other.overload_source_set if other.overload_source_set is not None else self.overload_source_set,
            overload_tick_set=other.overload_tick_set if other.overload_tick_set is not None else self.overload_tick_set,
            last_routing_family_set=other.last_routing_family_set if other.last_routing_family_set is not None else self.last_routing_family_set,
            last_routing_tick_set=other.last_routing_tick_set if other.last_routing_tick_set is not None else self.last_routing_tick_set,
            beliefs_add_or_update=self.beliefs_add_or_update + other.beliefs_add_or_update,
            beliefs_remove=self.beliefs_remove + other.beliefs_remove,
            committed_intentions_add_or_update=self.committed_intentions_add_or_update + other.committed_intentions_add_or_update,
            committed_intentions_remove=self.committed_intentions_remove + other.committed_intentions_remove,
            home_region_id_set=other.home_region_id_set if other.home_region_id_set is not None else self.home_region_id_set
        )
