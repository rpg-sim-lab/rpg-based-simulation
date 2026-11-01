# Compliance IDs: SOC-176
"""TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS: a contract-formed group is bound to the contract that formed it.

All on the real GroupSystem / GroupPhase / ApplyPath / PartyLifecycleService code. The binding is `contract_holder_id` (the entity whose
strategic.contracts holds `contract_id`); a leadership change does not move it; every end of a bound group carries a typed reason.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import GroupDissolutionReason as R
from src.core.state import AuthoritativeState, GroupBindingError, GroupRecord
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate, StrategicUpdate
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.pipeline_phases.groups import GroupPhase
from src.replay.fingerprint import StateFingerprinter
from src.systems.social_systems.party_lifecycle import PartyLifecycleService
from src.systems.world_systems.groups import GroupSystem

GATE = PartyLifecycleService.LEADERSHIP_CHECK_INTERVAL


def _contract(cid="r1", a=1, b=2, status=ContractStatus.ACTIVE, expiry=-1):
    return ContractState(id=cid, kind=ContractKind.RECRUITMENT, source_id=a, target_id=b, status=status, expiry_tick=expiry)


def _ent(i, x, sociability=0.5, contracts=None, group_id=None):
    b = V2EntityBuilder(i).kind("actor").location(x, 0.0).combat(readiness=100.0)
    if contracts:
        b = b.strategic(contracts=contracts)
    if group_id is not None:
        b = b.identity(group_id=group_id)
    e = b.build()
    pers = replace(e.identity.personality, sociability=sociability)
    return replace(e, identity=replace(e.identity, personality=pers))


def _bound_group(gid=10000, leader=1, holder=1, members=(1, 2), cid="r1", **kw):
    return GroupRecord(id=gid, leader_id=leader, member_ids=set(members), anchor=(0.0, 0.0), contract_id=cid, contract_holder_id=holder, **kw)


def _state(tick, contract=None, group=None, extra=None, c_holder=1):
    """Pair 1 (holder, source of the contract) and 2; entity 1 holds the contract; both already in the group."""
    group = group or _bound_group(last_leadership_check_tick=tick - 1)
    c = contract if contract is not None else _contract()
    ents = {1: _ent(1, 0.0, 0.1, {c.id: c} if c_holder == 1 else None, group.id), 2: _ent(2, 0.5, 0.9, None, group.id)}
    ents.update(extra or {})
    return AuthoritativeState(tick=tick, seed=1, entities=ents, groups={group.id: group})


def _tick(state, update=None):
    """One real group step: GroupPhase.resolve (dissolution, election, defection) then apply."""
    upd = GroupPhase.resolve(state, update or StateUpdate(force_full_scan=True))
    return ApplyPath.apply_generation(replace(state, tick=state.tick), upd), upd


def _old_lookup_invalid(state, group):
    """The removed lookup, kept here only as a positive control: the contract is read from the CURRENT LEADER's map."""
    leader = state.entities[group.leader_id]
    contract = leader.strategic.contracts.get(group.contract_id)
    return contract is None or contract.status != ContractStatus.ACTIVE


# --- the defect and its positive control -----------------------------------------------------------------------------------------------------

def test_election_that_moves_the_leader_off_the_holder_does_not_dissolve_a_bound_group():
    state = _state(GATE + 5, group=_bound_group(last_leadership_check_tick=0))  # gate open; entity 2 is far more sociable than leader 1
    new, _ = _tick(state)
    g = new.groups[10000]
    assert g.leader_id == 2 and g.contract_holder_id == 1  # elected off the holder; the binding did not move
    assert g.dissolution_tick is None
    # POSITIVE CONTROL: on the identical post-election state the removed leader-map lookup finds no contract and would dissolve the group.
    assert _old_lookup_invalid(new, g) is True
    again, _ = _tick(replace(new, tick=new.tick))  # the next tick: the old lookup's dissolution point
    assert again.groups[10000].dissolution_tick is None


def test_a_group_formed_at_tick_t_holds_no_election_before_t_plus_100():
    ents = {1: _ent(1, 0.0, 0.1, {"r1": _contract()}), 2: _ent(2, 0.5, 0.9)}
    state = AuthoritativeState(tick=GATE + 7, seed=1, entities=ents)
    formed = ApplyPath.apply_generation(state, GroupSystem.update_groups(state))
    g = next(iter(formed.groups.values()))
    assert g.formation_tick is not None and g.last_leadership_check_tick == state.tick
    assert (g.contract_id, g.contract_holder_id, g.leader_id) == ("r1", 1, 1)
    for t in (state.tick, state.tick + 1, state.tick + GATE - 1):
        assert PartyLifecycleService.check_leadership(g, list(formed.entities.values()), t) == (None, None)
    updated, event = PartyLifecycleService.check_leadership(g, list(formed.entities.values()), state.tick + GATE)
    assert event is not None and updated.leader_id == 2


def test_a_pair_keeps_its_group_until_the_contract_ends_across_many_ticks():
    c = _contract(expiry=GATE + 40)
    state = _state(GATE + 1, contract=c, group=_bound_group(last_leadership_check_tick=GATE + 1))
    ids = set()
    for _ in range(35):
        state, _u = _tick(state)
        live = [g for g in state.groups.values() if g.dissolution_tick is None]
        assert len(live) == 1
        ids.add(live[0].id)
    assert ids == {10000} and len(state.groups) == 1  # no re-forming, no extra records


# --- the three contract reasons, the three consequence reasons, precedence -------------------------------------------------------------------

def _dissolved(state, update=None):
    new, _ = _tick(state, update)
    return new.groups[10000]


def test_contract_removed_from_the_holder_is_BINDING_CONTRACT_MISSING():
    state = _state(50)
    state = replace(state, entities={**state.entities, 1: replace(state.entities[1], strategic=replace(state.entities[1].strategic, contracts={}))})
    g = _dissolved(state)
    assert (g.dissolution_tick, g.dissolution_reason, g.dissolution_contract_status) == (50, R.BINDING_CONTRACT_MISSING, None)
    freed = ApplyPath.apply_generation(state, GroupPhase.resolve(state, StateUpdate(force_full_scan=True)))
    assert all(e.identity.group_id is None for e in freed.entities.values())  # every member released with the group


@pytest.mark.parametrize("status", [ContractStatus.FULFILLED, ContractStatus.FAILED, ContractStatus.CANCELLED])
def test_contract_not_active_is_BINDING_CONTRACT_NOT_ACTIVE_with_the_typed_status(status):
    g = _dissolved(_state(50, contract=_contract(status=status)))
    assert (g.dissolution_reason, g.dissolution_contract_status) == (R.BINDING_CONTRACT_NOT_ACTIVE, status)


def test_a_contract_due_this_tick_ends_the_group_on_its_expiry_tick_as_FULFILLED_even_when_the_contracts_phase_did_not_run():
    """The contracts phase is not in this step (GroupPhase.resolve alone), so no status write exists: the shared predicate still ends the group."""
    on_the_tick = _dissolved(_state(50, contract=_contract(expiry=50)))
    assert (on_the_tick.dissolution_tick, on_the_tick.dissolution_reason, on_the_tick.dissolution_contract_status) == (
        50, R.BINDING_CONTRACT_NOT_ACTIVE, ContractStatus.FULFILLED)
    after = _dissolved(_state(50, contract=_contract(expiry=49)))
    assert after.dissolution_contract_status is ContractStatus.FULFILLED  # never EXPIRED for an ACTIVE contract that reached its expiry
    assert _dissolved(_state(50, contract=_contract(expiry=51))).dissolution_tick is None  # alive the tick before
    assert _dissolved(_state(50, contract=_contract(expiry=-1))).dissolution_tick is None  # no expiry: never due


def test_a_same_tick_status_write_on_the_holder_is_seen_the_same_tick():
    upd = StateUpdate(force_full_scan=True, entity_updates={1: EntityUpdate(entity_id=1, strategic=StrategicUpdate(
        contracts_add_or_update=[_contract(status=ContractStatus.FULFILLED)]))})
    g = _dissolved(_state(50), upd)
    assert g.dissolution_reason is R.BINDING_CONTRACT_NOT_ACTIVE


def test_holder_dead_is_BINDING_HOLDER_LEFT_even_when_it_is_the_leader():
    upd = StateUpdate(force_full_scan=True, entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(alive_set=False))})
    assert _dissolved(_state(50), upd).dissolution_reason is R.BINDING_HOLDER_LEFT
    leader_not_holder = _state(50, group=_bound_group(leader=2, holder=1))
    assert _dissolved(leader_not_holder, upd).dissolution_reason is R.BINDING_HOLDER_LEFT


def test_a_dead_leader_who_is_not_the_holder_is_LEADER_LOST():
    state = _state(50, group=_bound_group(leader=2, holder=1))
    upd = StateUpdate(force_full_scan=True, entity_updates={2: EntityUpdate(entity_id=2, combat=CombatUpdate(alive_set=False))})
    assert _dissolved(state, upd).dissolution_reason is R.LEADER_LOST


def test_members_below_two_is_MEMBERS_BELOW_TWO_when_nothing_else_applies():
    far = {3: _ent(3, 400.0, group_id=10000), 4: _ent(4, 410.0, group_id=10000)}
    state = _state(50, group=_bound_group(members=(1, 3, 4), last_leadership_check_tick=49), extra=far)
    assert _dissolved(state).dissolution_reason is R.MEMBERS_BELOW_TWO


def test_defection_of_the_last_other_member_is_DEFECTION_and_of_the_holder_is_HOLDER_LEFT():
    g = _bound_group(grievance_log=("a", "b", "c"))
    other = _ent(2, 0.5)
    upd_g, _e, _u = PartyLifecycleService.check_defection(g, other, 60)
    assert (upd_g.dissolution_tick, upd_g.dissolution_reason) == (60, R.DEFECTION)
    holder = _ent(1, 0.0)
    upd_h, _e, _u = PartyLifecycleService.check_defection(g, holder, 60)
    assert upd_h.dissolution_reason is R.BINDING_HOLDER_LEFT
    three = _bound_group(members=(1, 2, 3), grievance_log=("a", "b", "c"))
    still, _e, _u = PartyLifecycleService.check_defection(three, other, 60)
    assert still.dissolution_tick is None and still.dissolution_reason is None
    unbound = GroupRecord(id=9, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0), grievance_log=("a", "b", "c"))
    ub, _e, _u = PartyLifecycleService.check_defection(unbound, other, 60)
    assert ub.dissolution_tick == 60 and ub.dissolution_reason is None


def test_one_tick_with_several_reasons_records_the_highest_precedence_only():
    dead_everyone = StateUpdate(force_full_scan=True, entity_updates={
        1: EntityUpdate(entity_id=1, combat=CombatUpdate(alive_set=False)),
        2: EntityUpdate(entity_id=2, combat=CombatUpdate(alive_set=False))})
    # holder dead + contract gone with it + leader dead + below two  ->  HOLDER_LEFT
    assert _dissolved(_state(50, contract=_contract(status=ContractStatus.FULFILLED)), dead_everyone).dissolution_reason is R.BINDING_HOLDER_LEFT
    # contract not active AND leader (not the holder) dead -> the contract reason outranks LEADER_LOST
    upd = StateUpdate(force_full_scan=True, entity_updates={2: EntityUpdate(entity_id=2, combat=CombatUpdate(alive_set=False))})
    state = _state(50, contract=_contract(status=ContractStatus.FULFILLED), group=_bound_group(leader=2, holder=1))
    assert _dissolved(state, upd).dissolution_reason is R.BINDING_CONTRACT_NOT_ACTIVE


def test_a_holder_that_drifts_out_of_a_group_of_three_is_HOLDER_LEFT_on_the_next_tick():
    ents = {1: _ent(1, 400.0, 0.1, {"r1": _contract()}, 10000), 2: _ent(2, 0.0, 0.5, None, 10000), 3: _ent(3, 0.5, 0.5, None, 10000)}
    group = _bound_group(leader=2, holder=1, members=(1, 2, 3), last_leadership_check_tick=49)
    state = AuthoritativeState(tick=50, seed=1, entities=ents, groups={10000: group})
    after, _ = _tick(state)
    assert after.groups[10000].dissolution_tick is None and 1 not in after.groups[10000].member_ids  # dropped in the member loop
    nxt, _ = _tick(replace(after, tick=51))
    assert (nxt.groups[10000].dissolution_tick, nxt.groups[10000].dissolution_reason) == (51, R.BINDING_HOLDER_LEFT)


def test_a_group_whose_binding_contract_ends_dissolves_and_does_not_rebind_to_the_next_active_contract():
    c1, c2 = _contract("r1"), _contract("r2")
    state = _state(50, contract=replace(c1, status=ContractStatus.FULFILLED))
    state = replace(state, entities={**state.entities, 1: replace(state.entities[1], strategic=replace(
        state.entities[1].strategic, contracts={"r1": replace(c1, status=ContractStatus.FULFILLED), "r2": c2}))})
    new, _ = _tick(state)
    old = new.groups[10000]
    assert old.dissolution_tick == 50 and (old.contract_id, old.contract_holder_id) == ("r1", 1)  # still r1, never rebound to r2
    assert [g.id for g in new.groups.values() if g.dissolution_tick is None] == []  # nothing took over this tick
    assert 10000 in new.groups  # kept as a record


# --- shape: record, canonical, fingerprint, byte identity -----------------------------------------------------------------------------------

def test_contract_id_without_a_holder_is_invalid_with_a_typed_error():
    with pytest.raises(GroupBindingError):
        GroupRecord(id=1, leader_id=1, member_ids={1}, anchor=(0.0, 0.0), contract_id="r1")
    GroupRecord(id=1, leader_id=1, member_ids={1}, anchor=(0.0, 0.0))  # a group formed by no contract has neither


def test_binding_fields_are_in_the_canonical_dict_only_when_set_and_round_trip():
    bound = _bound_group(dissolution_tick=5, dissolution_reason=R.BINDING_CONTRACT_NOT_ACTIVE, dissolution_contract_status=ContractStatus.EXPIRED)
    d = bound.to_canonical_dict()
    assert (d["contract_holder_id"], d["dissolution_reason"], d["dissolution_contract_status"]) == (1, "BINDING_CONTRACT_NOT_ACTIVE", "EXPIRED")
    assert R(d["dissolution_reason"]) is R.BINDING_CONTRACT_NOT_ACTIVE and ContractStatus(d["dissolution_contract_status"]) is ContractStatus.EXPIRED
    assert replace(bound).to_canonical_dict() == d
    live = _bound_group().to_canonical_dict()
    assert "contract_holder_id" in live and "dissolution_reason" not in live and "dissolution_contract_status" not in live


def test_a_group_not_formed_by_a_contract_is_byte_identical_to_before():
    legacy_keys = {"id", "leader_id", "member_ids", "anchor", "shared_target_id", "contract_id", "cohesion_radius", "last_updated_tick", "roles",
                   "aptitudes", "formation_tick", "escort_target_id", "grievance_log", "reward_pool", "last_leadership_check_tick",
                   "dissolution_tick", "composition_score"}
    squad = GroupRecord(id=7, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0), roles={1: "LEADER", 2: "FACTION_SQUAD"})
    assert set(squad.to_canonical_dict()) == legacy_keys
    # and its dissolution (leader gone) records no reason
    ents = {2: _ent(2, 0.5, group_id=7)}
    st = AuthoritativeState(tick=9, seed=1, entities=ents, groups={7: squad})
    out = GroupSystem.update_groups(st)
    assert [g.dissolution_reason for g in out.groups_add_or_update] == [None]


def test_the_fingerprint_and_canonical_hash_change_with_the_holder_and_not_for_unbound_groups():
    a = _state(50, group=_bound_group(holder=1))
    b_group = replace(a.groups[10000], contract_holder_id=2)
    b = replace(a, groups={10000: b_group})
    assert StateFingerprinter._group_identity(a) != StateFingerprinter._group_identity(b)
    assert CanonicalStateHasher.to_canonical_data(a) != CanonicalStateHasher.to_canonical_data(b)
    unbound = AuthoritativeState(tick=1, seed=1, groups={7: GroupRecord(id=7, leader_id=1, member_ids={1}, anchor=(0.0, 0.0))})
    assert ":holder=" not in StateFingerprinter._group_identity(unbound)


# --- dirty-set reach: the law is "dissolves ON THE TICK the binding contract stops being ACTIVE", dirty or not --------------------------------

def _refine_without_full_scan(state):
    from src.engine.pipeline import AuthoritativeApplyPipeline
    return AuthoritativeApplyPipeline.refine(state, StateUpdate())


def _live_after(state, steps):
    for _ in range(steps):
        upd = _refine_without_full_scan(state)
        state = ApplyPath.apply_generation(state, upd)
    return state


def test_pure_time_expiry_with_idle_members_dissolves_the_bound_group_on_the_tick_through_the_pipeline_without_a_full_scan():
    c = _contract(expiry=60, a=1, b=2)
    state = _state(61, contract=c, group=_bound_group(last_leadership_check_tick=61))
    out = _live_after(state, 1)
    g = out.groups[10000]
    assert g.dissolution_tick is not None, "bound group outlived its expired contract on a non-full-scan tick"
    assert g.dissolution_reason is R.BINDING_CONTRACT_NOT_ACTIVE


def test_a_status_change_on_the_holders_map_dissolves_the_group_through_the_pipeline_without_a_full_scan():
    state = _state(50, contract=_contract(status=ContractStatus.FULFILLED))
    out = _live_after(state, 1)
    assert out.groups[10000].dissolution_reason is R.BINDING_CONTRACT_NOT_ACTIVE


# --- shared predicate, formation pick, holder drift ----------------------------------------------------------------------------------------

def test_contract_is_live_is_active_and_not_due_and_minus_one_never_expires():
    from src.systems.social_systems.contracts import contract_is_due, contract_is_live
    assert contract_is_live(_contract(expiry=51), 50) and not contract_is_live(_contract(expiry=50), 50) and not contract_is_live(_contract(expiry=49), 50)
    assert contract_is_live(_contract(expiry=-1), 10**9) and not contract_is_due(_contract(expiry=-1), 10**9)
    assert not contract_is_live(_contract(expiry=99, status=ContractStatus.FULFILLED), 50)
    assert contract_is_due(_contract(expiry=50, status=ContractStatus.OFFERED), 50)  # due is about time only; live also needs ACTIVE


def _formation_state(contracts, tick=50, extra=None):
    ents = {1: _ent(1, 0.0, 0.1, contracts), 2: _ent(2, 0.5, 0.9)}
    ents.update(extra or {})
    return AuthoritativeState(tick=tick, seed=1, entities=ents)


def _formed(state):
    new = ApplyPath.apply_generation(state, GroupSystem.update_groups(state))
    return [g for g in new.groups.values() if g.dissolution_tick is None]


def test_formation_binds_the_live_contract_with_the_latest_expiry_and_it_lasts_until_that_expiry():
    cs = {"r_a": _contract("r_a", expiry=60), "r_b": _contract("r_b", expiry=90)}
    [g] = _formed(_formation_state(cs))
    assert (g.contract_id, g.contract_holder_id, g.leader_id) == ("r_b", 1, 1)  # the later-expiring one, holder stays id_a
    state = ApplyPath.apply_generation(_formation_state(cs), GroupSystem.update_groups(_formation_state(cs)))
    for _ in range(35):  # through r_a's expiry at 60: the group stays, bound to r_b
        state, _u = _tick(state)
    assert state.tick > 60 and state.groups[g.id].dissolution_tick is None
    while state.groups[g.id].dissolution_tick is None and state.tick < 100:
        state, _u = _tick(state)
    assert state.groups[g.id].dissolution_tick == 90 and state.groups[g.id].contract_id == "r_b"


def test_formation_tie_on_expiry_takes_the_lowest_contract_id_and_no_expiry_ranks_latest():
    [g] = _formed(_formation_state({"r_z": _contract("r_z", expiry=70), "r_c": _contract("r_c", expiry=70), "r_m": _contract("r_m", expiry=70)}))
    assert g.contract_id == "r_c"
    [g2] = _formed(_formation_state({"r_a": _contract("r_a", expiry=500), "r_n": _contract("r_n", expiry=-1)}))
    assert g2.contract_id == "r_n"


def test_formation_binds_among_contracts_that_actually_gathered_a_partner_and_refuses_a_due_contract():
    # the later-expiring contract names a partner who is far away (no member gathered), so the nearer partner's contract binds
    far = {3: _ent(3, 400.0)}
    cs = {"r_near": _contract("r_near", 1, 2, expiry=60), "r_far": _contract("r_far", 1, 3, expiry=99)}
    [g] = _formed(_formation_state(cs, extra=far))
    assert g.contract_id == "r_near" and g.member_ids == {1, 2}
    # a contract due this tick (status not yet written by the contracts phase) forms nothing; one tick earlier it forms
    assert _formed(_formation_state({"r_due": _contract("r_due", expiry=50)}, tick=50)) == []
    assert len(_formed(_formation_state({"r_due": _contract("r_due", expiry=51)}, tick=50))) == 1


def test_a_pair_whose_non_leader_holder_drifts_away_ends_BINDING_HOLDER_LEFT_not_MEMBERS_BELOW_TWO():
    ents = {1: _ent(1, 0.0, 0.1, None, 10000), 2: _ent(2, 400.0, 0.5, {"r1": _contract("r1", 2, 1)}, 10000)}
    group = _bound_group(leader=1, holder=2, members=(1, 2), cid="r1", last_leadership_check_tick=49)
    state = AuthoritativeState(tick=50, seed=1, entities=ents, groups={10000: group})
    g = _dissolved(state)
    assert (g.dissolution_tick, g.dissolution_reason) == (50, R.BINDING_HOLDER_LEFT)


def test_a_group_of_three_that_loses_two_non_holders_to_distance_is_still_MEMBERS_BELOW_TWO():
    far = {3: _ent(3, 400.0, group_id=10000), 4: _ent(4, 410.0, group_id=10000)}
    state = _state(50, group=_bound_group(members=(1, 3, 4), last_leadership_check_tick=49), extra=far)
    assert _dissolved(state).dissolution_reason is R.MEMBERS_BELOW_TWO


def test_the_contracts_phase_agrees_with_the_predicate_on_the_expiry_tick():
    from src.engine.pipeline_phases.contracts import ContractLifecyclePhase
    state = _state(50, contract=_contract(expiry=50))
    upd = ContractLifecyclePhase.resolve_expirations(state, StateUpdate())
    assert any(c.status is ContractStatus.FULFILLED for c in upd.entity_updates[1].strategic.contracts_add_or_update)
    early = ContractLifecyclePhase.resolve_expirations(_state(49, contract=_contract(expiry=50)), StateUpdate())
    assert 1 not in early.entity_updates or not early.entity_updates[1].strategic


# --- relevance: a bound group is relevant on the tick its binding contract is due, dirty or not -----------------------------------------------

def _update_with_dirty_groups(group_ids):
    from src.core.dirty import DirtySet
    return StateUpdate(dirty_set=DirtySet(group_ids=set(group_ids)))


def test_a_due_bound_group_outside_the_dirty_set_dissolves_on_the_tick_with_FULFILLED_when_the_contracts_phase_was_skipped():
    state = _state(53, contract=_contract(expiry=50), group=_bound_group(last_leadership_check_tick=53))
    rows = GroupSystem.update_groups(state, _update_with_dirty_groups([])).groups_add_or_update  # not dirty; no contracts phase ran (no status write)
    assert [(g.dissolution_tick, g.dissolution_reason, g.dissolution_contract_status) for g in rows] == [(53, R.BINDING_CONTRACT_NOT_ACTIVE, ContractStatus.FULFILLED)]


def test_only_live_bound_groups_with_a_due_binding_contract_are_added_to_the_relevant_set():
    from src.core.dirty import due_bound_group_ids, get_relevant_group_ids
    due = _bound_group(gid=10000, cid="r_due")
    notdue = _bound_group(gid=10001, cid="r_live")
    gone = replace(_bound_group(gid=10002, cid="r_due"), dissolution_tick=40)  # dissolved records are skipped first
    unbound = GroupRecord(id=10003, leader_id=1, member_ids={1, 2}, anchor=(0.0, 0.0))
    ents = {1: _ent(1, 0.0, 0.1, {"r_due": _contract("r_due", expiry=50), "r_live": _contract("r_live", expiry=51)}), 2: _ent(2, 0.5)}
    state = AuthoritativeState(tick=50, seed=1, entities=ents, groups={g.id: g for g in (due, notdue, gone, unbound)})
    assert due_bound_group_ids(state) == {10000}
    assert get_relevant_group_ids(state, _update_with_dirty_groups([10003])) == {10000, 10003}
    assert get_relevant_group_ids(state, _update_with_dirty_groups([])) == {10000}
    assert get_relevant_group_ids(state, StateUpdate(force_full_scan=True)) == set(state.groups)  # a full-scan tick stays as it is
    assert due_bound_group_ids(replace(state, tick=49)) == set()
    no_expiry = replace(state, entities={1: _ent(1, 0.0, 0.1, {"r_due": _contract("r_due", expiry=-1), "r_live": _contract("r_live", expiry=-1)}), 2: ents[2]})
    assert due_bound_group_ids(no_expiry) == set()  # -1 never due
