"""TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE: `CombatComponent.last_hit_damage`, the blow a subject has felt.

Written by CombatPatch with `last_attacker_id` / `last_hit_tick` on a landed hit only; carried by `CombatUpdate.hit_damage_set`; hashed (flat-sha256-v4).
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.core.updates import CombatUpdate, EntityUpdate
from src.engine.apply import ApplyPath
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.movement import is_evasive_flight
from src.core.movement_modes import MovementMode

TICK = 500


def _subject():
    return V2EntityBuilder(1).kind("hero").location(0.0, 0.0).combat(hp=100, max_hp=100, alive=True).build()


def _apply(entity, update):
    return ApplyPath._apply_entity_update(entity, EntityUpdate(entity_id=entity.id, combat=update))


def test_never_hit_has_no_felt_blow():
    assert _subject().combat.last_hit_damage is None
    assert _subject().combat.to_canonical_dict()["last_hit_damage"] is None


def test_a_landed_hit_writes_damage_with_attacker_and_tick():
    hit = _apply(_subject(), CombatUpdate(damage_taken=17, hp_delta=-17, attacker_id=2, hit_tick_set=TICK, hit_damage_set=17))
    assert (hit.combat.last_attacker_id, hit.combat.last_hit_tick, hit.combat.last_hit_damage) == (2, TICK, 17)


def test_the_next_hit_overwrites_it():
    first = _apply(_subject(), CombatUpdate(damage_taken=17, hp_delta=-17, attacker_id=2, hit_tick_set=TICK, hit_damage_set=17))
    second = _apply(first, CombatUpdate(damage_taken=4, hp_delta=-4, attacker_id=3, hit_tick_set=TICK + 3, hit_damage_set=4))
    assert (second.combat.last_attacker_id, second.combat.last_hit_damage) == (3, 4)


@pytest.mark.parametrize("update", [
    CombatUpdate(hp_delta=-3, hazard_damage=3),
    CombatUpdate(attacker_id=7, outcome_kind="REJECTED", hit_tick_set=TICK + 5, hit_damage_set=9),
    CombatUpdate(attacker_id=7, damage_taken=0, hit_tick_set=TICK + 5, hit_damage_set=0),
])
def test_a_hazard_or_zero_damage_result_leaves_it_alone(update):
    base = _apply(_subject(), CombatUpdate(damage_taken=17, hp_delta=-17, attacker_id=2, hit_tick_set=TICK, hit_damage_set=17))
    assert _apply(base, update).combat.last_hit_damage == 17


def test_merge_takes_the_damage_from_the_same_hit_as_the_attacker():
    a = CombatUpdate(damage_taken=5, hp_delta=-5, attacker_id=2, hit_tick_set=TICK, hit_damage_set=5)
    b = CombatUpdate(damage_taken=8, hp_delta=-8, attacker_id=3, hit_tick_set=TICK, hit_damage_set=8)
    merged = a.merge(b)
    assert (merged.damage_taken, merged.attacker_id, merged.hit_damage_set) == (13, 3, 8)  # damage_taken sums; the felt blow is the last hit's


def test_every_resolution_site_stamps_the_hit_damage():
    from src.engine.combat import CombatResolutionSystem

    attacker = V2EntityBuilder(2).kind("monster").location(1.0, 0.0).identity(faction=Faction.MONSTER_HORDE).combat(hp=100, max_hp=100, alive=True, atk=50, readiness=100.0).build()
    state = AuthoritativeState(tick=TICK, seed=1, entities={1: _subject(), 2: attacker})
    update = CombatResolutionSystem.resolve_attack(attacker, state.entities[1], state)
    assert update.damage_taken > 0 and update.hit_damage_set == update.damage_taken


def test_it_is_in_the_proof_digest():
    s = AuthoritativeState(tick=TICK, seed=1, entities={1: _subject()})
    hurt = replace(s.entities[1], combat=replace(s.entities[1].combat, last_hit_damage=9))
    assert CanonicalStateHasher.get_hash(replace(s, entities={1: hurt})) != CanonicalStateHasher.get_hash(s)


@pytest.mark.parametrize("mode,style,expected", [
    (MovementMode.RETREAT, 2, True), (MovementMode.RETREAT, 1, False), (MovementMode.RETREAT, 0, False), (MovementMode.WANDER, 2, False),
])
def test_the_evasive_flight_predicate_is_the_one_movement_uses(mode, style, expected):
    assert is_evasive_flight(mode, style) is expected
