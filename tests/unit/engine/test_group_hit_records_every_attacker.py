"""TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER (memo row 88, hit test (b)).

A simultaneous group hit (`resolve_multi_attack`, called only by the opportunity-attack step) lowers the subject's hp once for all its attackers. Every attacker of
that hit took hp from the subject, so every one of them acts on it at the subject's next decision; before the fix only the first read as acting.
The rows run the real resolution, the real patch and the real act test, with the hostiles' tasks IDLE so only test (b) can make them acting.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, TaskComponent
from src.core.updates import CombatUpdate, EntityUpdate
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.combat import CombatResolutionSystem
from src.engine.scheduler import NEED_WAKE_CADENCE
from src.engine.tactical_threat import hostile_acts_on

TICK = 500


def _subject():
    return V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(hp=100, max_hp=100, alive=True).build()


def _hostile(eid, at):
    h = (V2EntityBuilder(eid).kind("monster").location(*at).identity(faction=Faction.MONSTER_HORDE)
         .combat(hp=100, max_hp=100, alive=True, atk=10, readiness=100.0).build())
    return replace(h, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "IDLE"}))


def _state(*hostiles):
    return AuthoritativeState(tick=TICK, seed=1, entities={1: _subject(), **{h.id: h for h in hostiles}})


def _hit(state, attackers, **kw):
    update = CombatResolutionSystem.resolve_multi_attack(attackers, state.entities[1], state, **kw)
    return update, ApplyPath._apply_entity_update(state.entities[1], EntityUpdate(entity_id=1, combat=update))


def test_every_attacker_of_a_group_opportunity_hit_acts_on_the_subject():
    a, b, c = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0)), _hostile(4, (-1.0, 0.0))
    state = _state(a, b, c)
    update, subject = _hit(state, [a, b, c], is_opportunity_attack=True, is_lethal=False)
    assert update.damage_taken > 0 and len(update.simultaneous_intents) == 3
    assert all(hostile_acts_on(h, subject, TICK) for h in (a, b, c))


def test_the_group_hit_acts_for_one_brain_cadence_for_every_attacker():
    a, b = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0))
    _, subject = _hit(_state(a, b), [a, b], is_opportunity_attack=True, is_lethal=False)
    assert all(hostile_acts_on(h, subject, TICK + NEED_WAKE_CADENCE) for h in (a, b))
    assert not any(hostile_acts_on(h, subject, TICK + NEED_WAKE_CADENCE + 1) for h in (a, b))


def test_a_body_that_did_not_attack_does_not_act_through_the_group_hit():
    a, b, bystander = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0)), _hostile(5, (0.0, -1.0))
    _, subject = _hit(_state(a, b, bystander), [a, b], is_opportunity_attack=True, is_lethal=False)
    assert not hostile_acts_on(bystander, subject, TICK)


def test_a_single_attacker_opportunity_hit_still_acts_alone():
    a, other = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0))
    _, subject = _hit(_state(a, other), [a], is_opportunity_attack=True, is_lethal=False)
    assert hostile_acts_on(a, subject, TICK) and not hostile_acts_on(other, subject, TICK)


def test_an_ordinary_attack_still_acts_alone():
    a, other = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0))
    state = _state(a, other)
    update = CombatResolutionSystem.resolve_attack(a, state.entities[1], state)
    subject = ApplyPath._apply_entity_update(state.entities[1], EntityUpdate(entity_id=1, combat=update))
    assert hostile_acts_on(a, subject, TICK) and not hostile_acts_on(other, subject, TICK)


@pytest.mark.parametrize("update", [CombatUpdate(hp_delta=-3, hazard_damage=3), CombatUpdate(hp_delta=-2)])
def test_a_hazard_or_passive_drain_makes_nobody_act(update):
    a = _hostile(2, (1.0, 0.0))
    subject = ApplyPath._apply_entity_update(_subject(), EntityUpdate(entity_id=1, combat=update))
    assert not hostile_acts_on(a, subject, TICK)


# ---- the record: shape, patch, digest, restore -------------------------------------------------------------------------------------------------

def test_a_group_hit_records_every_attacker_with_the_share_each_took_summing_to_the_blow():
    a, b, c = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0)), _hostile(4, (-1.0, 0.0))
    state = _state(a, b, c)
    update, subject = _hit(state, [a, b, c], is_opportunity_attack=True, is_lethal=False)
    assert subject.combat.last_hit_attackers == (2, 3, 4) and subject.combat.last_attacker_id == 2
    assert subject.combat.last_hit_damages == tuple(i.damage for i in update.simultaneous_intents)
    assert sum(subject.combat.last_hit_damages) == subject.combat.last_hit_damage == update.damage_taken
    assert subject.combat.last_hit_tick == TICK


def test_a_single_hit_records_a_one_tuple_and_the_next_damaging_hit_replaces_the_set():
    a, b, c = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0)), _hostile(4, (-1.0, 0.0))
    state = _state(a, b, c)
    _, subject = _hit(state, [a, b], is_opportunity_attack=True, is_lethal=False)
    assert subject.combat.last_hit_attackers == (2, 3)
    state = replace(state, entities={**state.entities, 1: subject}, tick=TICK + 1)
    update = CombatResolutionSystem.resolve_attack(c, state.entities[1], state)
    after = ApplyPath._apply_entity_update(state.entities[1], EntityUpdate(entity_id=1, combat=update))
    assert (after.combat.last_hit_attackers, after.combat.last_hit_damages) == ((4,), (update.damage_taken,))
    assert not hostile_acts_on(a, after, TICK + 1)  # the earlier set is gone: the stated limit of the single slot


def test_a_hazard_drain_leaves_the_last_hit_set_alone():
    a, b = _hostile(2, (1.0, 0.0)), _hostile(3, (0.0, 1.0))
    _, subject = _hit(_state(a, b), [a, b], is_opportunity_attack=True, is_lethal=False)
    after = ApplyPath._apply_entity_update(subject, EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-3, hazard_damage=3)))
    assert (after.combat.last_hit_attackers, after.combat.last_hit_damages) == (subject.combat.last_hit_attackers, subject.combat.last_hit_damages)


def test_merging_a_later_hit_replaces_the_whole_set_never_mixing_two_hits():
    group = CombatUpdate(damage_taken=9, hp_delta=-9, attacker_id=2, hit_tick_set=TICK, hit_damage_set=9, hit_attackers_set=(2, 3), hit_damages_set=(4, 5))
    single = CombatUpdate(damage_taken=6, hp_delta=-6, attacker_id=4, hit_tick_set=TICK, hit_damage_set=6)
    merged = group.merge(single)
    assert (merged.attacker_id, merged.hit_attackers_set, merged.hit_damages_set) == (4, None, None)  # the patch reads None as one attacker holding the whole blow


def test_the_two_fields_are_canonical_and_move_the_digest():
    never = _subject()
    assert never.combat.to_canonical_dict()["last_hit_attackers"] == [] and never.combat.to_canonical_dict()["last_hit_damages"] == []
    hit = replace(never, combat=replace(never.combat, last_hit_attackers=(2, 3), last_hit_damages=(4, 5)))
    assert hit.combat.to_canonical_dict()["last_hit_attackers"] == [2, 3]

    def digest(entity):
        return CanonicalStateHasher.get_hash(AuthoritativeState(tick=3, seed=1, entities={1: entity}))

    assert digest(hit) != digest(never)
    assert digest(replace(hit, combat=replace(hit.combat, last_hit_damages=(5, 4)))) != digest(hit)


def test_a_checkpoint_that_predates_the_record_restores_one_attacker_holding_the_whole_blow():
    from src.engine.checkpoint_fields import fill_missing_fields

    hurt = replace(_subject(), combat=replace(_subject().combat, last_attacker_id=2, last_hit_tick=TICK, last_hit_damage=9))
    never = _subject()
    state = AuthoritativeState(tick=3, seed=1, entities={1: hurt, 7: replace(never, id=7)})
    for e in state.entities.values():
        object.__delattr__(e.combat, "last_hit_attackers")
        object.__delattr__(e.combat, "last_hit_damages")
    fill_missing_fields(state)
    assert (state.entities[1].combat.last_hit_attackers, state.entities[1].combat.last_hit_damages) == ((2,), (9,))
    assert (state.entities[7].combat.last_hit_attackers, state.entities[7].combat.last_hit_damages) == ((), ())


# ---- felt_swing (divergence 2.204): the swing is the engaged attackers' summed shares --------------------------------------------------------------

def _felt_scene(hp, shares, engaged_ids, alive_ids=None):
    """A subject at `hp` that last took a group hit of `shares` {attacker id: damage}; the attackers in `engaged_ids` stand adjacent, the rest far away."""
    from src.engine.felt_swing import felt_lethal_attacker

    ids = tuple(shares)
    pos = {2: (1.0, 0.0), 3: (0.0, 1.0), 4: (-1.0, 0.0)}
    hostiles = []
    for i in ids:
        h = _hostile(i, pos[i] if i in engaged_ids else (30.0, 30.0))
        if alive_ids is not None and i not in alive_ids:
            h = replace(h, combat=replace(h.combat, alive=False))
        hostiles.append(h)
    subject = _subject()
    subject = replace(subject, combat=replace(subject.combat, hp=hp, last_attacker_id=ids[0], last_hit_tick=TICK, last_hit_damage=sum(shares.values()),
                                              last_hit_attackers=ids, last_hit_damages=tuple(shares.values())))
    state = _state(*hostiles)
    state = replace(state, entities={**state.entities, 1: subject})
    return felt_lethal_attacker(state, subject)


def test_a_group_hit_is_lethal_when_the_engaged_shares_sum_to_the_hp():
    got = _felt_scene(20, {2: 8, 3: 12}, engaged_ids=(2, 3))
    assert got is not None and got.id == 2


def test_the_summed_blow_is_not_credited_to_the_first_attacker_alone():
    """Only attacker 2 is still engaged: its share (8) alone does not finish a subject at 20 hp. The old reading credited it the whole 20."""
    assert _felt_scene(20, {2: 8, 3: 12}, engaged_ids=(2,)) is None


def test_the_hold_is_not_missed_when_the_first_attacker_left_and_the_others_stay():
    got = _felt_scene(20, {2: 8, 3: 12, 4: 5}, engaged_ids=(3, 4))
    assert got is None  # 12 + 5 = 17 < 20
    got = _felt_scene(17, {2: 8, 3: 12, 4: 5}, engaged_ids=(3, 4))
    assert got is not None and got.id == 3  # the first engaged attacker of the set


def test_a_dead_attacker_contributes_no_share():
    assert _felt_scene(20, {2: 8, 3: 12}, engaged_ids=(2, 3), alive_ids=(2,)) is None


def test_a_single_attack_hit_reads_as_before():
    got = _felt_scene(23, {2: 23}, engaged_ids=(2,))
    assert got is not None and got.id == 2
    assert _felt_scene(23, {2: 22}, engaged_ids=(2,)) is None
