"""TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET.

In `target_score` a hostile that hit the entity within ATTACKED_RECENTLY_WINDOW_TICKS (D-13) outranks the group's shared target, ahead of `group_bias` and behind adjacency
(CONFLICT-04). The e10 t894 position: shared target 30 and attacker 27 both adjacent, trust 0.8, VANGUARD. The attacker here has MORE hp than the shared target, so hp
(which would have picked the weaker one) cannot be what picks it: only the new term can. The rows assert the PICK, not survival.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState, GroupRecord, SocialBond
from src.engine import tactical_threat
from src.engine.tactical import TacticalDecisionSystem

TICK = 900
SHARED, ATTACKER, SECOND = 30, 27, 28


def _monster(eid, at, hp):
    return V2EntityBuilder(eid).kind("monster").location(*at).identity(faction=Faction.MONSTER_HORDE).combat(hp=hp, max_hp=300, readiness=100.0).build()


def _scene(*, attackers=(ATTACKER,), hit_tick=TICK - 1, shared=SHARED, hp=None, at=None):
    hp = {SHARED: 50, ATTACKER: 200, SECOND: 120, **(hp or {})}
    at = {SHARED: (2.0, 1.0), ATTACKER: (1.0, 2.0), SECOND: (0.0, 1.0), **(at or {})}
    leader = V2EntityBuilder(10).kind("human").location(10, 10).identity(faction=Faction.HERO_GUILD).combat(readiness=100.0).build()
    member = (V2EntityBuilder(1).kind("human").location(1, 1).identity(faction=Faction.HERO_GUILD, group_id=100)
              .social(bonds={10: SocialBond(target_id=10, sentiment=0.6)}).combat(readiness=100.0, tactical_role="VANGUARD").build())
    if attackers:
        member = replace(member, combat=replace(member.combat, last_attacker_id=attackers[0], last_hit_tick=hit_tick,
                                                last_hit_attackers=tuple(attackers), last_hit_damages=tuple(1 for _ in attackers), last_hit_damage=len(attackers)))
    group = GroupRecord(id=100, leader_id=10, member_ids={1, 10}, shared_target_id=shared, anchor=(5, 5))
    entities = {1: member, 10: leader, **{i: _monster(i, at[i], hp[i]) for i in (SHARED, ATTACKER, SECOND)}}
    return AuthoritativeState(tick=TICK, seed=1, entities=entities, groups={100: group}), member


def _pick(state, member):
    return TacticalDecisionSystem.evaluate_entity_intent(state, member).task.payload_set["target_id"]


def test_an_adjacent_attacker_outranks_the_groups_shared_target():
    state, member = _scene()
    assert _pick(state, member) == ATTACKER


def test_plain_focus_fire_is_unchanged_when_nobody_is_attacking_the_member():
    state, member = _scene(attackers=())
    assert _pick(state, member) == SHARED


def test_when_the_attacker_is_the_shared_target_nothing_changes():
    state, member = _scene(attackers=(SHARED,))
    assert _pick(state, member) == SHARED


def test_the_window_is_the_named_constant_and_changing_it_changes_the_window(monkeypatch):
    window = tactical_threat.ATTACKED_RECENTLY_WINDOW_TICKS
    assert window == 10  # D-13's value; no test pins it equal to the row 88 act-test window
    assert _pick(*_scene(hit_tick=TICK - window)) == ATTACKER
    assert _pick(*_scene(hit_tick=TICK - window - 1)) == SHARED
    monkeypatch.setattr(tactical_threat, "ATTACKED_RECENTLY_WINDOW_TICKS", 3)
    assert _pick(*_scene(hit_tick=TICK - 3)) == ATTACKER
    assert _pick(*_scene(hit_tick=TICK - 4)) == SHARED


def test_every_attacker_of_a_group_hit_outranks_the_shared_target_then_the_rest_of_the_key_orders_them():
    state, member = _scene(attackers=(ATTACKER, SECOND))
    assert _pick(state, member) == SECOND  # both outrank 30; between them the lower hp (120 against 200) wins
    state, member = _scene(attackers=(SECOND,))
    assert _pick(state, member) == SECOND


def test_adjacency_still_comes_first():
    state, member = _scene(at={ATTACKER: (6.0, 6.0)})  # the attacker stepped back out of reach
    assert _pick(state, member) == SHARED
