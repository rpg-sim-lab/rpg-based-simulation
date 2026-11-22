"""CONFLICT-03 (decisions 44 and 47): permission to attack is a fact about the pair and holds both ways. A prey may strike its predator whether or not the predator's task names it
that tick (a predator between blows carries no target); a pair where neither hunts the other, and no faction rates hostile, is refused both ways. Each case has a failing control: the
old rule (the target's task had to name the attacker) refuses the same scenario."""
from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.engine import behavior_consumers
from src.engine.hostility import ATTACK_RELATIONS, Relation, attack_allowed, is_wild_creature, relation
from src.engine.legality import LegalityServiceV2

FACTION_OF = {"wolf": "wild_beast_pack", "orc": "orc_clan", "troll": "orc_clan", "small_plant_eater": "wild_fauna"}
SEEDS = (11, 42, 97)
# (predator kind, prey kind), found by properties (a hungry body whose diet feeds on the other and whose power band outranks the other's believed danger), not by role:
# an orc hunts a wolf and a troll hunts a plant-eater. The reverse appraisals are WARY, never PREDATION, so the prey's strike is legal only through the pair rule.
PAIRS = (("orc", "wolf"), ("troll", "small_plant_eater"))


@pytest.fixture(scope="module", autouse=True)
def _content():
    repo = CatalogRepository("data/content")
    repo.load_all()
    behavior_consumers.configure_behavior_consumers(repo)
    yield
    behavior_consumers.reset_behavior_consumers()


def _body(eid, kind, pos, hunger=0.0):
    return (V2EntityBuilder(eid).kind(kind).location(*pos)
            .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, properties={"species_id": kind, "faction_id": FACTION_OF[kind]})
            .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).biological(hunger=hunger).build())


def _pair(predator_kind, prey_kind, seed, predator_hunger=90.0):
    """Predator and prey one tile apart, ids and tile from the seed; the predator carries no target (between blows)."""
    base = 100 + seed
    predator = _body(base, predator_kind, (10.0 + seed % 7, 10.0), predator_hunger)
    prey = _body(base + 1, prey_kind, (11.0 + seed % 7, 10.0))
    assert predator.task.payload.get("target_id") is None
    return predator, prey


def _old_rule(attacker, target, faction_verdict, *, night, tick):
    """The rule before this change: the attacker hunts the target, or the TARGET's task names the attacker and it holds an attack relation to it."""
    if is_wild_creature(attacker) or is_wild_creature(target):
        faction_verdict = False
    if faction_verdict or relation(attacker, target, night=night, tick=tick) is Relation.PREDATION:
        return True
    return target.task.payload.get("target_id") == attacker.id and relation(target, attacker, night=night, tick=tick) in ATTACK_RELATIONS


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("predator_kind,prey_kind", PAIRS)
def test_b0_a_prey_may_strike_its_predator_between_the_predators_blows(predator_kind, prey_kind, seed):
    predator, prey = _pair(predator_kind, prey_kind, seed)
    assert relation(predator, prey, night=False, tick=None) is Relation.PREDATION  # the predator hunts the prey: the setup is the stage-2 trace's shape
    assert attack_allowed(predator, prey, False, night=False, tick=None)
    assert attack_allowed(prey, predator, False, night=False, tick=None)  # B0: the prey's strike is legal with the predator's payload None


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("predator_kind,prey_kind", PAIRS)
def test_control_the_old_rule_refused_the_same_strike(predator_kind, prey_kind, seed):
    predator, prey = _pair(predator_kind, prey_kind, seed)
    assert not _old_rule(prey, predator, False, night=False, tick=None)
    assert _old_rule(predator, prey, False, night=False, tick=None)  # and it allowed the hunter's own strike: the asymmetry the ticket names


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("predator_kind,prey_kind", PAIRS)
def test_a_pair_where_neither_hunts_the_other_is_refused_both_ways(predator_kind, prey_kind, seed):
    predator, prey = _pair(predator_kind, prey_kind, seed, predator_hunger=0.0)  # a fed body does not hunt
    assert relation(predator, prey, night=False, tick=None) is not Relation.PREDATION
    assert not attack_allowed(predator, prey, False, night=False, tick=None)
    assert not attack_allowed(prey, predator, False, night=False, tick=None)
    hungry, _ = _pair(predator_kind, prey_kind, seed)
    assert attack_allowed(hungry, prey, False, night=False, tick=None)  # control: hunger alone is what flips the same pair to allowed


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("hunger", [0.0, 90.0])
@pytest.mark.parametrize("predator_kind,prey_kind", PAIRS)
def test_permission_is_symmetric_for_every_sampled_pair(predator_kind, prey_kind, hunger, seed):
    a, b = _pair(predator_kind, prey_kind, seed, predator_hunger=hunger)
    for verdict in (False,):
        assert attack_allowed(a, b, verdict, night=False, tick=None) == attack_allowed(b, a, verdict, night=False, tick=None)


def test_control_the_old_rule_was_not_symmetric_for_the_hungry_pair():
    a, b = _pair("orc", "wolf", 42)
    assert _old_rule(a, b, False, night=False, tick=None) != _old_rule(b, a, False, night=False, tick=None)


@pytest.mark.parametrize("seed", SEEDS)
def test_the_legality_entry_point_agrees_both_ways(seed):
    """The real verification path (LegalityServiceV2.verify_attack_legality), not just attack_allowed: the prey's strike is not refused as FRIENDLY_FIRE_ILLEGAL."""
    from src.core.enums import ReasonCode
    from src.core.state import AuthoritativeState

    predator, prey = _pair("orc", "wolf", seed)
    state = AuthoritativeState(tick=5, seed=seed, entities={predator.id: predator, prey.id: prey})
    assert LegalityServiceV2.verify_attack_legality(predator, prey, state, night=False)[1] is not ReasonCode.FRIENDLY_FIRE_ILLEGAL
    assert LegalityServiceV2.verify_attack_legality(prey, predator, state, night=False)[1] is not ReasonCode.FRIENDLY_FIRE_ILLEGAL
