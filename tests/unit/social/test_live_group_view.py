# Compliance IDs: SOC-278
"""TCK-20261101-DISSOLVED-GROUP-RECORDS-ARE-KEPT-AND-VISITED-EVERY-TICK, step (a): the groups and cooperation phases walk LIVE groups only.

The store keeps every dissolved record (ids stay taken, the canonical data holds them); a derived view (`live_group_items` / `live_group_ids`, one definition of
"live") is what the phases iterate. Readers that need every stored id (the id allocator, the counter seed, the hash) keep walking the store.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.dirty import DirtySet, due_bound_group_ids, get_relevant_group_ids
from src.core.group_record import GroupRecord, is_live_group, live_group_ids, live_group_items
from src.core.state import AuthoritativeState, seeded_next_group_id
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.updates import StateUpdate
from src.domains.cooperation.phase import CooperationPhase
from src.domains.cooperation.services import PartyCohesionService
from src.engine.apply import ApplyPath
from src.engine.pipeline_phases.groups import GroupPhase
from src.systems.social_systems.party_lifecycle import PartyLifecycleService
from src.systems.world_systems.groups import GroupSystem


def _g(gid, members=(1, 2), dissolved=None, **kw):
    return GroupRecord(id=gid, leader_id=members[0], member_ids=set(members), anchor=(0.0, 0.0), dissolution_tick=dissolved, **kw)


def _state(groups, tick=300, entities=None, **kw):
    return AuthoritativeState(tick=tick, seed=1, groups={g.id: g for g in groups}, entities=entities or {}, **kw)


def test_live_is_defined_once_and_the_view_keeps_the_stores_insertion_order():
    groups = {g.id: g for g in (_g(10005), _g(10001, dissolved=4), _g(10003), _g(10002, dissolved=9), _g(10004))}  # insertion order is not id order
    assert [is_live_group(g) for g in groups.values()] == [True, False, True, False, True]
    assert live_group_ids(groups) == [10005, 10003, 10004]
    assert [gid for gid, _g_ in live_group_items(groups)] == [10005, 10003, 10004]
    assert all(g is groups[gid] for gid, g in live_group_items(groups))  # the stored records themselves, not copies


def test_the_relevant_set_never_holds_a_dissolved_id_on_a_full_scan_and_is_otherwise_unchanged():
    state = _state([_g(10000), _g(10001, dissolved=5), _g(10002)])
    assert get_relevant_group_ids(state, StateUpdate(force_full_scan=True)) == {10000, 10002}
    assert get_relevant_group_ids(state, None) == {10000, 10002}
    dirty = StateUpdate(dirty_set=DirtySet(group_ids={10001, 10002}))  # a dissolved id in the dirty set is still passed through (read and skipped at the guard)
    assert get_relevant_group_ids(state, dirty) == {10001, 10002}


def test_due_bound_groups_scan_live_groups_only():
    c = ContractState(id="r", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.ACTIVE, expiry_tick=300)
    ents = {1: V2EntityBuilder(1).kind("actor").location(0, 0).strategic(contracts={"r": c}).build(), 2: V2EntityBuilder(2).kind("actor").location(0, 1).build()}
    live = _g(10000, contract_id="r", contract_holder_id=1)
    gone = replace(_g(10001, contract_id="r", contract_holder_id=1), dissolution_tick=7)
    assert due_bound_group_ids(_state([live, gone], entities=ents)) == {10000}


def test_the_election_and_defection_passes_never_visit_a_stored_dissolved_record(monkeypatch):
    seen = []
    orig = PartyLifecycleService.check_leadership
    monkeypatch.setattr(PartyLifecycleService, "check_leadership", staticmethod(lambda group, members, tick, *a, **k: (seen.append(group.id), orig(group, members, tick, *a, **k))[1]))
    ents = {i: V2EntityBuilder(i).kind("actor").location(float(i), 0.0).build() for i in (1, 2, 3, 4)}
    state = _state([_g(10000, (1, 2)), _g(10001, (3, 4), dissolved=7), _g(10002, (1, 2))], entities=ents)
    GroupPhase.resolve(state, StateUpdate(force_full_scan=True))
    assert seen and 10001 not in seen and set(seen) <= {10000, 10002}


def test_the_cohesion_loop_walks_live_groups_in_insertion_order_and_skips_dissolved_ones(monkeypatch):
    seen = []
    monkeypatch.setattr(PartyCohesionService, "evaluate", staticmethod(lambda g_id, st: (seen.append(g_id), type("R", (), {"status": "STABLE", "abandoning_member_ids": (), "drifting_member_ids": (), "issue_reasons": ()})())[1]))
    ents = {i: V2EntityBuilder(i).kind("actor").location(float(i), 0.0).build() for i in (1, 2, 3, 4)}
    # insertion order 10005, 10001 (dissolved), 10003, 10002 (dissolved), 10004: the order decides the order of the cohesion penalties
    groups = [_g(10005, (1, 2)), _g(10001, (3, 4), dissolved=4), _g(10003, (1, 2)), _g(10002, (3, 4), dissolved=9), _g(10004, (1, 2))]
    state = _state(groups, entities=ents)
    CooperationPhase.execute(state, StateUpdate())
    assert seen == [10005, 10003, 10004]


def test_the_allocator_and_the_counter_seed_still_see_the_whole_store_dissolved_records_included():
    # live 10000, dissolved 10007: the seed is past the highest id of ANY stored record, and a formation never takes a dissolved record's id
    assert seeded_next_group_id({g.id: g for g in (_g(10000), _g(10007, dissolved=3))}) == 10008
    ents = {1: V2EntityBuilder(1).kind("actor").location(0, 0).strategic(contracts={"r": ContractState(id="r", kind=ContractKind.RECRUITMENT, source_id=1, target_id=2, status=ContractStatus.ACTIVE)}).build(),
            2: V2EntityBuilder(2).kind("actor").location(0, 1).build()}
    state = _state([_g(10007, (8, 9), dissolved=3)], tick=10, entities=ents, next_group_id=10007)  # the counter sits ON the dissolved record's id
    new = ApplyPath.apply_generation(state, GroupSystem.update_groups(state))
    formed = [g for g in new.groups.values() if g.dissolution_tick is None]
    assert len(formed) == 1 and formed[0].id == 10008 and new.groups[10007].dissolution_tick == 3


def test_a_dissolved_record_stays_in_the_store_above_the_counter_and_in_the_hash_and_the_checkpoint():
    """What step (a) must not change: after a dissolve the record is still in the store, the allocator's next id is above it, and the canonical data, the replay
    fingerprint and a checkpoint (pickle) all still include it."""
    import pickle
    from src.core.updates import CombatUpdate, EntityUpdate
    from src.engine.checkpoint import CanonicalStateHasher
    from src.replay.fingerprint import StateFingerprinter
    ents = {i: V2EntityBuilder(i).kind("actor").location(float(i), 0.0).build() for i in (1, 2)}
    state = _state([_g(10000, (1, 2))], tick=20, entities=ents, next_group_id=10001)
    leader_dies = StateUpdate(force_full_scan=True, entity_updates={1: EntityUpdate(entity_id=1, combat=CombatUpdate(alive_set=False))})
    new = ApplyPath.apply_generation(state, GroupPhase.resolve(state, leader_dies))
    assert 10000 in new.groups and new.groups[10000].dissolution_tick == 20  # dissolved, kept
    assert new.next_group_id > 10000  # the allocator's next id is above the dissolved record
    assert 10000 not in live_group_ids(new.groups)  # the live view no longer lists it
    assert CanonicalStateHasher.to_canonical_data(new)["groups"]["10000"]["dissolution_tick"] == 20
    assert "10000:" in StateFingerprinter._group_identity(new)
    assert pickle.loads(pickle.dumps(new)).groups[10000].dissolution_tick == 20
