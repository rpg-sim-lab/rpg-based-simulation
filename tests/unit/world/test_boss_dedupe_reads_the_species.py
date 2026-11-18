"""TCK-20261118-A-SECOND-WORLD-BOSS-SPAWNS-BECAUSE-THE-DEDUPE-READS-THE-OCCUPATION.

M1 step 4 (#952) made `kind` the species and moved the label into `identity.occupation`. BossService's "is there already a living boss / lair occupant" dedupe
read the occupation, but the region boss spawns with species "world_boss" and occupation "ancient_sentinel", so the existing boss was never found and a second spawned.
A body alive across two spawn ticks must leave exactly one boss (and exactly one lair occupant).
"""
from __future__ import annotations

from dataclasses import replace

from src.core.species import species_of
from src.core.state import PlaceKind, PlaceState, RegionState
from src.systems.world_systems.generator import EntityGenerator
from src.world.boss import WORLD_BOSS_SPAWN_FLAG, BossService
from src.core.state import AuthoritativeState


def _state(with_lair=False):
    region = RegionState(id="region_1", name="Dark Forest", bounds=(0, 0, 100, 100), kind="FOREST",
                         trauma_score=BossService.BOSS_SPAWN_TRAUMA_THRESHOLD)
    places = {"lair_1": PlaceState(place_id="lair_1", region_id="region_1", kind=PlaceKind.LAIR, position=(50.0, 50.0))} if with_lair else {}
    return AuthoritativeState(tick=2000, seed=42, maturity=BossService.BOSS_SPAWN_THRESHOLD, regions={"region_1": region}, places=places,
                              feature_flags={WORLD_BOSS_SPAWN_FLAG: "ON"})


def _with(state, update):
    return replace(state, entities={**state.entities, **{e.id: e for e in update.entities_add}}, tick=state.tick + 1)


def _living(state, species):
    return [e for e in state.entities.values() if species_of(e) == species and e.lifecycle.active and e.combat.alive]


def test_one_world_boss_alive_across_two_spawn_ticks_stays_one_boss():
    gen = EntityGenerator(42)
    state = _with(_state(), BossService.check_for_boss_spawn(_state(), gen))
    assert len(_living(state, "world_boss")) == 1
    second = BossService.check_for_boss_spawn(state, gen)
    assert second.entities_add == []
    assert len(_living(_with(state, second), "world_boss")) == 1


def test_one_dragonkin_alive_across_two_spawn_ticks_stays_one_occupant():
    gen = EntityGenerator(42)
    state = _with(_state(with_lair=True), BossService.check_for_lair_spawn(_state(with_lair=True), gen))
    assert len(_living(state, "dragonkin")) == 1
    second = BossService.check_for_lair_spawn(state, gen)
    assert second.entities_add == []
    assert len(_living(_with(state, second), "dragonkin")) == 1


def test_the_dedupe_does_not_follow_the_occupation_label():
    """A body that merely carries the label "world_boss" is not a boss; one whose species is "world_boss" is, whatever its label."""
    gen = EntityGenerator(42)
    boss = BossService.check_for_boss_spawn(_state(), gen).entities_add[0]
    assert species_of(boss) == "world_boss" and boss.identity.occupation != "world_boss"
