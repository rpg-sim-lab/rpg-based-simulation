# Compliance IDs: SOC-025, SOC-145, SOC-146, SOC-147, SOC-148, SOC-149, SOC-150, SOC-151, SOC-152, SOC-153, SOC-154, SOC-155, SOC-156, SOC-157, SOC-160, SOC-162, SOC-163, SOC-164, SOC-172, SOC-173, SOC-174, SOC-176, SOC-177, SOC-178, SOC-179, SOC-183, SOC-184
# Compliance IDs: SOC-025
from __future__ import annotations
from dataclasses import replace
from typing import Callable, Dict, List, Set, Optional, TYPE_CHECKING

from src.core.enums import GroupDissolutionReason
from src.core.state import seeded_next_group_id
from src.core.strategic import ContractStatus
from src.systems.social_systems.contracts import contract_is_live

if TYPE_CHECKING:
    from src.core.state import AuthoritativeState, EntityState, GroupRecord
    from src.core.updates import StateUpdate, EntityUpdate
    from src.core.strategic import ContractState

class GroupSystem:
    """
    Authoritative logic for group formation, cohesion, and dissolution.
    Groups allow entities to cooperate on shared targets and stay spatially together.
    """

    @staticmethod
    def update_groups(state: AuthoritativeState, current_update: Optional[StateUpdate] = None) -> StateUpdate:
        """
        Main authoritative group coordination logic.
        Logic ID: SOC-182 (Party target propagation occurs inside authoritative tick pipeline)
        Logic ID: SOC-192 (Group coordination test runs through normal kernel tick)
        """
        from src.core.updates import StateUpdate, EntityUpdate
        from src.core.state import GroupRecord
        
        groups_add_or_update: List[GroupRecord] = []
        groups_add: List[GroupRecord] = []
        entity_updates: Dict[int, EntityUpdate] = {}
        # Group id allocation (TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP): start at the durable
        # counter and step past every id already taken (the store, adds already in this tick's update, ids
        # handed out in this call). The counter itself is advanced only by apply, via next_group_id_set.
        taken_ids = set(state.groups)
        if current_update is not None:
            taken_ids.update(g.id for g in current_update.groups_add)
            taken_ids.update(g.id for g in current_update.groups_add_or_update)
        next_free_id = state.next_group_id if state.next_group_id is not None else seeded_next_group_id(state.groups)

        def is_alive(e_id: int) -> bool:
            # Check for death in current update
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]
                if upd.combat and upd.combat.alive_set is False:
                    return False
            
            ent = state.entities.get(e_id)
            return ent.combat.alive if ent else False
        
        def is_active(e_id: int) -> bool:
            """
            Return whether an entity is active after applying same-tick updates.

            Group lifecycle must use the effective same-tick state, not only the
            start-of-tick state. Otherwise a leader/member that becomes inactive during
            the tick can incorrectly remain in a group until the next tick.
            """
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]

                if upd.active is False:
                    return False

            ent = state.entities.get(e_id)
            return ent.lifecycle.active if ent else False

        def get_pos(e_id: int) -> tuple[float, float]:
            # Check for move in current update
            if current_update and e_id in current_update.entity_updates:
                upd = current_update.entity_updates[e_id]
                if upd.new_position:
                    return upd.new_position
            
            ent = state.entities.get(e_id)
            return ent.navigation.position if ent else (0.0, 0.0)

        # 1. Process Existing Groups (Dissolution & Cohesion)
        # Optimization: Only process groups that were explicitly modified or had member changes
        # Logic ID: PERF-006 (Dirty Entity Tracking)
        from src.core.dirty import get_relevant_group_ids
        relevant_groups = get_relevant_group_ids(state, current_update)
        
        for g_id in sorted(relevant_groups):
            group = state.groups.get(g_id)
            if not group: continue
            # TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED: dissolved groups are now
            # retained in state.groups forever (dissolution_tick set in place, mirroring
            # ClanState.dissolved_tick/CampState.active), not removed -- get_relevant_group_ids()
            # falls back to ALL of state.groups.keys() on a force_full_scan tick or when no
            # dirty_set exists, which would otherwise re-run leadership/cohesion/dissolution logic
            # against every already-dissolved group, forever, on every such tick.
            if group.dissolution_tick is not None:
                continue

            leader = state.entities.get(group.leader_id)

            # Contract binding (highest precedence): a group formed by a contract lives while the contract that formed it is ACTIVE on the entity
            # that holds it. A leadership change never moves the binding, so the contract is read from `contract_holder_id`, never from the leader.
            # Holder-left > contract missing > contract not active > leader lost > defection > members below two (GroupDissolutionReason).
            if group.contract_holder_id is not None:
                binding_end = GroupSystem._binding_end(state, group, current_update, is_alive, is_active)
                if binding_end is not None:
                    b_reason, b_status = binding_end
                    groups_add_or_update.append(replace(
                        group, dissolution_tick=state.tick, dissolution_reason=b_reason, dissolution_contract_status=b_status,
                    ))
                    for m_id in group.member_ids:
                        if m_id in state.entities:
                            entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                    continue

            # Logic ID: SOC-176 (Party dissolves when leader is dead/missing)
            # Logic ID: SOC-189 (Group dissolution test covers dead leader)
            #
            # Important:
            #   Use is_alive(...) / is_active(...) instead of reading only the
            #   start-of-tick entity.
            #
            # Why:
            #   GroupSystem runs near the end of the authoritative pipeline and receives
            #   the current same-tick StateUpdate. If the leader died earlier in this same
            #   tick, the start-of-tick state may still show leader.combat.alive=True.
            #   Therefore same-tick CombatUpdate(alive_set=False) must be respected here.
            if (
                leader is None
                or not is_alive(group.leader_id)
                or not is_active(group.leader_id)
            ):
                # TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED: retain the record with an
                # in-place terminal marker instead of deleting it, mirroring ClanState.dissolved_tick
                # / CampState.active -- the only two real, live precedents for this shape in this
                # codebase. Enables find_group_for_contract() to answer "did this recruitment ever
                # produce a group, and how did it end" after dissolution, which it could not before.
                groups_add_or_update.append(replace(
                    group, dissolution_tick=state.tick,
                    dissolution_reason=GroupDissolutionReason.LEADER_LOST if group.contract_holder_id is not None else None,
                ))

                for m_id in group.member_ids:
                    # Logic ID: SOC-179 (Party dissolution updates member group IDs)
                    if m_id in state.entities:
                        entity_updates[m_id] = EntityUpdate(
                            entity_id=m_id,
                            group_id_set=-1,
                        )

                continue

            # Filter members (alive and within reasonable range)
            new_member_ids: Set[int] = {group.leader_id}
            member_positions: List[tuple[float, float]] = [get_pos(group.leader_id)]
            
            for m_id in group.member_ids:
                if m_id == group.leader_id:
                    continue
                
                if not is_alive(m_id) or not is_active(m_id):
                    entity_updates[m_id] = EntityUpdate(
                        entity_id=m_id,
                        group_id_set=-1,
                    )
                    continue
                
                # Cohesion check
                # VERIFIED v2: group_cohesion_check
                m_pos = get_pos(m_id)
                dx = m_pos[0] - group.anchor[0]
                dy = m_pos[1] - group.anchor[1]
                dist_sq = dx*dx + dy*dy
                
                # The group's contract is checked once per group above (contract_holder_id), not per member.
                if dist_sq > (group.cohesion_radius * 2)**2:
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                    continue
                
                new_member_ids.add(m_id)
                member_positions.append(m_pos)

            if len(new_member_ids) < 2:
                groups_add_or_update.append(replace(
                    group, dissolution_tick=state.tick,
                    dissolution_reason=GroupSystem._size_rule_reason(group, new_member_ids),
                ))
                for m_id in new_member_ids:
                    entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=-1)
                continue

            # Update Anchor
            # Logic ID: SOC-172 (Party anchor follows leader or agreed anchor rule)
            avg_x = sum(p[0] for p in member_positions) / len(member_positions)
            avg_y = sum(p[1] for p in member_positions) / len(member_positions)
            
            # Domain 7 Hardening: Shared Target Logic
            # Logic ID: SOC-183 (Shared target is valid and alive when assigned)
            # Logic ID: SOC-184 (Shared target clears when invalid/dead)
            new_shared_target_id = leader.task.payload.get("target_id")
            if not new_shared_target_id:
                new_shared_target_id = leader.navigation.target
            
            # Hysteresis: Keep old target if new one is None but leader is still acting
            if new_shared_target_id is None and group.shared_target_id is not None:
                if leader.task.work_kind in ("ENTITY_ACT", "COMBAT_ACT"):
                    new_shared_target_id = group.shared_target_id
            
            # Domain 4: Target Validity Check (Hardened)
            if new_shared_target_id:
                 target_ent = state.entities.get(new_shared_target_id)
                 if not target_ent or not target_ent.combat.alive or not target_ent.lifecycle.active:
                     new_shared_target_id = None
                 else:
                     # Range check
                     dx = target_ent.navigation.position[0] - avg_x
                     dy = target_ent.navigation.position[1] - avg_y
                     if (dx*dx + dy*dy) > (group.cohesion_radius * 2.0)**2:
                         new_shared_target_id = None
            else:
                 from src.systems.party import PartyCoordinationSystem
                 new_shared_target_id = PartyCoordinationSystem.validate_shared_target(g_id, state)
            
            # Update Roles
            new_roles = {group.leader_id: "LEADER"}
            for m_id in new_member_ids:
                if m_id == group.leader_id: continue
                existing_role = group.roles.get(m_id)
                if existing_role:
                    new_roles[m_id] = existing_role
                else:
                    member = state.entities.get(m_id)
                    role = member.combat.tactical_role if member and member.combat.tactical_role else "VANGUARD"
                    new_roles[m_id] = role

            updated_group = replace(
                group,
                member_ids=new_member_ids,
                anchor=(avg_x, avg_y),
                shared_target_id=new_shared_target_id if isinstance(new_shared_target_id, int) else None,
                roles=new_roles,
                last_updated_tick=state.tick
            )
            groups_add_or_update.append(updated_group)
            
            # Domain 7: Directive Propagation
            # Members inherit leader's project as a GROUP_OBJECTIVE directive
            if leader.strategic.current_project_id:
                project = leader.strategic.projects.get(leader.strategic.current_project_id)
                if project:
                    from src.core.strategic import DirectiveState, DirectivePriority
                    from src.core.updates import StrategicUpdate
                    for m_id in new_member_ids:
                        if m_id == leader.id: continue
                        
                        # Only propagate if member trusts leader
                        member = state.entities.get(m_id)
                        bond = member.social.bonds.get(leader.id)
                        trust = (bond.sentiment + 1.0) / 2.0 if bond else member.social.trust_history.get(leader.id, 0.5)
                        
                        if trust >= 0.3:
                            directive = DirectiveState(
                                id=f"group_obj_{group.id}_{m_id}",
                                kind="GROUP_OBJECTIVE",
                                target=project.kind,
                                priority=DirectivePriority.NORMAL,
                                salience=0.5,
                                created_tick=state.tick
                            )
                            m_upd = entity_updates.get(m_id, EntityUpdate(entity_id=m_id))
                            # Merge strategic updates
                            existing_strat = m_upd.strategic if m_upd.strategic else StrategicUpdate()
                            new_strat = replace(existing_strat,
                                directives_add_or_update=existing_strat.directives_add_or_update + [directive]
                            )
                            entity_updates[m_id] = replace(m_upd, strategic=new_strat)

        # 2. Group Formation (Purpose-Driven)
        # VERIFIED v2: group_formation_purpose_driven
        # Find entities without groups
        # Logic ID: PERF-006 (Dirty Entity Tracking - Relaxed for ungrouped entities)
        if getattr(state, "_has_contracts_cache", True):
            ungrouped_ids = sorted([e_id for e_id, e in state.entities.items() 
                                    if e.combat.alive and e.identity.group_id is None])
            
            # Purpose-Driven Formation: Check for active social contracts (Recruitment/Protection)
            already_forming: Set[int] = set()
            for i, id_a in enumerate(ungrouped_ids):
                if id_a in already_forming:
                    continue
                
                new_group_members, active_contract_id = GroupSystem._gather_formation(state, id_a, already_forming)
                
                if len(new_group_members) >= 2:
                    # Form new group
                    while next_free_id in taken_ids:
                        next_free_id += 1
                    new_g_id = next_free_id
                    taken_ids.add(new_g_id)
                    next_free_id = new_g_id + 1
                    # Simplified: the initiator (id_a) is leader and holds the binding contract.
                    new_group = GroupSystem._new_group_record(state, new_g_id, id_a, new_group_members, active_contract_id)
                    groups_add.append(new_group)
                    
                    for m_id in new_group_members:
                        already_forming.add(m_id)
                        entity_updates[m_id] = EntityUpdate(entity_id=m_id, group_id_set=new_g_id)

        return StateUpdate(
            entity_updates=entity_updates,
            groups_add_or_update=groups_add_or_update,
            groups_add=groups_add,
            next_group_id_set=next_free_id if groups_add else None,
        )

    @staticmethod
    def _size_rule_reason(group: GroupRecord, remaining: Set[int]) -> Optional[GroupDissolutionReason]:
        """The typed reason for a bound group that falls below two members this tick: the holder having left is the cause and outranks the size rule
        (a pair whose non-leader holder drifted away is BINDING_HOLDER_LEFT, not MEMBERS_BELOW_TWO). Unbound groups carry no reason."""
        if group.contract_holder_id is None:
            return None
        return GroupDissolutionReason.MEMBERS_BELOW_TWO if group.contract_holder_id in remaining else GroupDissolutionReason.BINDING_HOLDER_LEFT

    @staticmethod
    def _formation_partner(state: AuthoritativeState, entity_a: EntityState, contract: ContractState, already_forming: Set[int]) -> Optional[int]:
        """The partner `contract` offers `entity_a` for a new group, or None: the contract must be live, the partner alive, ungrouped, not already
        being assigned a group this tick, and within 10 tiles (Law: the cohesion check)."""
        if not contract_is_live(contract, state.tick):
            return None
        other_id = contract.target_id if contract.source_id == entity_a.id else contract.source_id
        other = state.entities.get(other_id)
        if other is None or not other.combat.alive or other.identity.group_id is not None or other_id in already_forming:
            return None
        dx = entity_a.navigation.position[0] - other.navigation.position[0]
        dy = entity_a.navigation.position[1] - other.navigation.position[1]
        return other_id if (dx * dx + dy * dy) < (10.0 ** 2) else None

    @staticmethod
    def _gather_formation(state: AuthoritativeState, id_a: int, already_forming: Set[int]) -> tuple:
        """The members a purpose-driven group around `id_a` would gather, and the contract that binds it.

        Check for contracts where id_a is source or target (Logic IDs SOC-160 party formation can be driven by an accepted social contract,
        SOC-187 covers the accepted contract, SOC-188 no contract / proximity-only rejection, SOC-164 proximity alone does not create a party).
        Only live contracts count (ACTIVE and not due: `contract_is_live`), so a contract due this tick, whose status the contracts phase has
        not written yet, forms no group that would end at once. The partner must be alive, ungrouped, not already being assigned a group this
        tick, and within 10 tiles.

        The binding is the live contract with the LATEST expiry among those that qualified a partner (expiry -1, no expiry, ranks latest); on a tie
        the lowest contract id (the scan is in sorted id order and replaces only on a strictly later expiry). The holder is `id_a`. The binding is
        chosen here, once; nothing rebinds a group to another contract later.
        """
        entity_a = state.entities[id_a]
        members = {id_a}
        best_id = None
        best_expiry = None
        for c_id in sorted(entity_a.strategic.contracts.keys()):
            contract = entity_a.strategic.contracts[c_id]
            other_id = GroupSystem._formation_partner(state, entity_a, contract, already_forming)
            if other_id is None:
                continue
            members.add(other_id)
            rank = float("inf") if contract.expiry_tick == -1 else contract.expiry_tick
            if best_expiry is None or rank > best_expiry:
                best_id, best_expiry = c_id, rank
        return members, best_id

    @staticmethod
    def _new_group_record(
        state: AuthoritativeState, group_id: int, leader_id: int, member_ids: Set[int], contract_id: Optional[str],
    ) -> GroupRecord:
        """The record of a group formed by `contract_id`, held by its leader (the initiator): anchor at the members' centre, roles from each
        member's tactical role, composition scored at formation, and the leadership cadence starting at the formation tick (the default 0 would
        open the election gate on the formation tick)."""
        from src.core.state import GroupRecord
        from src.systems.social_systems.party_composition import PartyCompositionScorer
        anchor_x = sum(state.entities[m_id].navigation.position[0] for m_id in member_ids) / len(member_ids)
        anchor_y = sum(state.entities[m_id].navigation.position[1] for m_id in member_ids) / len(member_ids)
        roles = {leader_id: "LEADER"}
        for m_id in member_ids:
            if m_id == leader_id:
                continue
            member = state.entities[m_id]
            # Derive role from combat component or default
            roles[m_id] = member.combat.tactical_role if member.combat.tactical_role else "VANGUARD"
        member_entities = [state.entities[mid] for mid in member_ids if mid in state.entities]
        return GroupRecord(
            id=group_id,
            leader_id=leader_id,
            member_ids=member_ids,
            anchor=(anchor_x, anchor_y),
            contract_id=contract_id,
            contract_holder_id=leader_id,
            roles=roles,
            last_updated_tick=state.tick,
            last_leadership_check_tick=state.tick,
            composition_score=PartyCompositionScorer.score(member_entities),
        )

    @staticmethod
    def _holder_contract(state: AuthoritativeState, group: GroupRecord, current_update: Optional[StateUpdate]) -> Optional[ContractState]:
        """The binding contract as its holder holds it: a same-tick update of the holder first, then the holder's own map; never the leader's."""
        holder_id = group.contract_holder_id
        if holder_id is None:
            return None
        if current_update and holder_id in current_update.entity_updates:
            holder_up = current_update.entity_updates[holder_id]
            if holder_up.strategic:
                pending = next((c for c in holder_up.strategic.contracts_add_or_update if c.id == group.contract_id), None)
                if pending is not None:
                    return pending
        if group.contract_id is None:
            return None
        return state.entities[holder_id].strategic.contracts.get(group.contract_id)

    @staticmethod
    def _binding_end(
        state: AuthoritativeState,
        group: GroupRecord,
        current_update: Optional[StateUpdate],
        is_alive: Callable[[int], bool],
        is_active: Callable[[int], bool],
    ) -> Optional[tuple[GroupDissolutionReason, Optional[ContractStatus]]]:
        """Why a contract-bound group's binding has ended this tick, or None while it holds.

        Returns (GroupDissolutionReason, ContractStatus | None). The contract is read from the holder's own map (a same-tick contract update first),
        never from the current leader's. Liveness is the shared `contract_is_live` (ACTIVE and not due), the same test the contracts phase and group
        formation use, so a contract that reaches its expiry tick ends the group on that tick as BINDING_CONTRACT_NOT_ACTIVE with status FULFILLED
        even when the contracts phase has not run yet (phase skipping); the group never records EXPIRED.
                """
        holder_id = group.contract_holder_id
        if holder_id not in group.member_ids or holder_id not in state.entities or not is_alive(holder_id) or not is_active(holder_id):
            return GroupDissolutionReason.BINDING_HOLDER_LEFT, None
        contract = GroupSystem._holder_contract(state, group, current_update)
        if contract is None:
            return GroupDissolutionReason.BINDING_CONTRACT_MISSING, None
        if not contract_is_live(contract, state.tick):
            # A contract that is due this tick ends the group ON its expiry tick as FULFILLED (the status the contracts phase writes for an ACTIVE
            # contract that reaches its expiry), whether or not that phase has written it yet. Never EXPIRED.
            status = ContractStatus.FULFILLED if contract.status == ContractStatus.ACTIVE else contract.status
            return GroupDissolutionReason.BINDING_CONTRACT_NOT_ACTIVE, status
        return None

    @staticmethod
    def find_group_for_contract(state: AuthoritativeState, contract_id: str) -> Optional[GroupRecord]:
        """
        O(n_groups) reverse lookup -- no contract_id -> group_id index exists in durable
        state. Matches the established precedent for this exact shape:
        ClanLifecycleService.find_clan_id_for_entity() (src/systems/social_systems/
        clan_lifecycle.py) -- no evidence in this repo that group counts warrant an index.
        Sorted iteration by group id for determinism.
        TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING: the forward direction
        (GroupRecord.contract_id, set at formation in update_groups() above) already
        existed; this is the missing reverse direction.

        TCK-20260913-GROUP-DISSOLUTION-OUTCOME-NOT-CAPTURED: dissolved groups are now retained in
        state.groups with `dissolution_tick` set (in place, never removed), so this DOES answer
        the question after dissolution too -- callers that need to distinguish "currently active"
        from "dissolved" must check the returned record's own `.dissolution_tick` (None = still
        alive). Previously dissolved groups were deleted outright and this could only ever answer
        "is this contract's recruitment currently a live group."
        """
        for group_id, group in sorted(state.groups.items()):
            if group.contract_id == contract_id:
                return group
        return None
