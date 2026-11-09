"""
tests/unit/engine/test_near_death_hardening_hit_gate.py
───────────────────────────────────────────────────────────────────────────────
TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT.

The near-death grant (+5 max hp, durable accumulator, near_death emotion) needs the subject to survive a COMBAT HIT: this tick's CombatUpdate must record a hit
taken (attacker_id set, damage_taken > 0, hit_tick_set == this tick: the typed fact CombatPatch itself uses to write last_attacker_id / last_hit_tick).
The projected-hp test is unchanged (above 0 and at most 10% of max). A town heal, a hazard drain or nothing, while at or under the line, grants nothing.
All rows at max hp 100, line 10.
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.pipeline_phases.hardening import NearDeathHardeningPhase

TICK = 40


def _entity(hp: int):
    return (
        V2EntityBuilder(1)
        .kind("hero")
        .location(0.0, 0.0)
        .combat(hp=hp, max_hp=100, alive=True, readiness=100.0)
        .lifecycle(active=True)
        .build()
    )


def _apply(hp: int, combat: CombatUpdate):
    entity = _entity(hp)
    state = AuthoritativeState(tick=TICK, seed=1, entities={1: entity})
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, combat=combat)})
    refined = NearDeathHardeningPhase.apply(state, update).entity_updates[1]
    return entity, refined


def _hit(damage: int, **extra) -> CombatUpdate:
    return CombatUpdate(hp_delta=-damage, damage_taken=damage, attacker_id=2, hit_tick_set=TICK, **extra)


def _granted(refined) -> bool:
    return (
        refined.combat.max_hp_delta == 5
        and refined.combat.permanent_max_hp_bonus_delta == 5
        and "NEAR_DEATH_HARDENING" in refined.combat.trace
        and refined.cognition_bundle_set is not None
    )


def _nothing_granted(refined) -> bool:
    return (
        refined.combat.max_hp_delta == 0
        and refined.combat.permanent_max_hp_bonus_delta == 0
        and "NEAR_DEATH_HARDENING" not in refined.combat.trace
        and refined.cognition_bundle_set is None
    )


def test_a_hit_to_eight_grants_five():
    _, refined = _apply(50, _hit(42))  # 50 - 42 = 8, at the 10% line of 100
    assert _granted(refined)


def test_a_town_heal_of_one_at_eight_grants_nothing():
    _, refined = _apply(7, CombatUpdate(hp_delta=1))  # town heal (+1): 7 + 1 = 8, no hit recorded
    assert _nothing_granted(refined)


def test_a_hazard_to_eight_grants_nothing():
    _, refined = _apply(50, CombatUpdate(hp_delta=-42, hazard_damage=42, outcome_kind="HAZARD"))  # hazard drain: hp falls to 8, no attacker
    assert _nothing_granted(refined)


def test_a_hit_and_a_heal_netting_to_zero_at_eight_grants_five():
    # 8 hp, hit for 5 and healed 5 in the same tick: hp_delta 0, projected hp 8; the hit is still recorded
    _, refined = _apply(8, CombatUpdate(hp_delta=0, damage_taken=5, attacker_id=2, hit_tick_set=TICK))
    assert _granted(refined)


def test_a_hit_below_zero_grants_nothing():
    _, refined = _apply(10, _hit(20, alive_set=False))  # 10 - 20 < 0: the subject does not survive
    assert _nothing_granted(refined)


def test_a_hit_and_a_town_heal_merged_through_combat_update_merge_still_grant_five():
    # The phase reads the MERGED update for the tick: CombatUpdate.merge keeps the hit's attacker_id and hit_tick_set (a later writer with None leaves them) and sums
    # damage_taken and hp_delta, in either order. 50 hp, hit for 45 (-45), town heal +1: projected 6, at the line.
    hit = _hit(45)
    town_heal = CombatUpdate(hp_delta=1)
    for merged in (hit.merge(town_heal), town_heal.merge(hit)):
        assert (merged.attacker_id, merged.damage_taken, merged.hit_tick_set, merged.hp_delta) == (2, 45, TICK, -44)
        _, refined = _apply(50, merged)
        assert _granted(refined)
