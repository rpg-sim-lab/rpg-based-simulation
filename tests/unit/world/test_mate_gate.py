# Compliance IDs: WORLD-122
"""The reproduction mate gate (M1): none reads nothing, bond passes on an accepted marriage or both directed sentiments at the named line."""
import dataclasses
from types import SimpleNamespace

import pytest

from src.content.repository import CatalogRepository
from src.content.schema import ReproductionProfileDefinition, SentimentThreshold
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, SocialBond
from src.core.strategic import MarriageState, MarriageStatus
from src.systems.social_systems.relationships import RelationshipService
from src.world import births
from src.world.mate_gate import passes_mate_gate
from tests.unit.world.test_births import _Catalog, _body, _conceptions, _run

_BOND = ReproductionProfileDefinition(
    id="t", birth_chance_per_check=1.0, min_birth_interval_ticks=100, gestation_ticks=60, litter_weights={1: 1.0}, mate_radius_tiles=10, fed_line=30,
    birth_hunger_cost=25, mate_gate="bond", min_mutual_sentiment=SentimentThreshold.FRIEND,
)
_NONE = _BOND.model_copy(update={"mate_gate": "none", "min_mutual_sentiment": None})
_LINE = RelationshipService.FRIEND_SENTIMENT_THRESHOLD


def _with(body, bonds=None, marriages=None):
    social = dataclasses.replace(body.social, bonds=bonds or {})
    strategic = dataclasses.replace(body.strategic, marriages=marriages or {})
    return dataclasses.replace(body, social=social, strategic=strategic)


def _bond(sentiment):
    return SocialBond(target_id=0, sentiment=sentiment)


def test_the_humanoid_line_is_the_named_constant_not_a_copied_number():
    repo = CatalogRepository()
    repo.load_all()
    humanoid = repo.get_reproduction_profile("humanoid_births")
    assert humanoid.mate_gate == "bond" and humanoid.min_mutual_sentiment == SentimentThreshold.FRIEND
    assert all(repo.get_reproduction_profile(p).mate_gate == "none" for p in ("carnivore_births", "goblin_births", "plant_eater_births"))
    from src.world.mate_gate import _THRESHOLDS
    assert _THRESHOLDS[humanoid.min_mutual_sentiment] == RelationshipService.FRIEND_SENTIMENT_THRESHOLD


def test_both_directed_sentiments_at_the_line_pass_and_one_below_or_missing_fails():
    a, b = _body(1), _body(2)
    assert passes_mate_gate(_with(a, {2: _bond(_LINE)}), _with(b, {1: _bond(_LINE)}), _BOND)
    assert not passes_mate_gate(_with(a, {2: _bond(_LINE)}), _with(b, {1: _bond(_LINE - 0.01)}), _BOND)
    assert not passes_mate_gate(_with(a, {2: _bond(1.0)}), b, _BOND), "one directed bond is not mutual"
    assert not passes_mate_gate(a, b, _BOND)


def test_an_accepted_marriage_held_by_either_party_passes_and_a_proposed_one_or_a_stranger_does_not():
    a, b = _body(1), _body(2)
    accepted = {"m": MarriageState(id="m", proposer_entity_id=2, target_entity_id=1, status=MarriageStatus.ACCEPTED, married_tick=5)}
    assert passes_mate_gate(_with(a, marriages=accepted), b, _BOND) and passes_mate_gate(a, _with(b, marriages=accepted), _BOND)
    proposed = {"m": dataclasses.replace(accepted["m"], status=MarriageStatus.PROPOSED)}
    assert not passes_mate_gate(_with(a, marriages=proposed), b, _BOND)
    other = {"m": dataclasses.replace(accepted["m"], target_entity_id=9)}
    assert not passes_mate_gate(_with(a, marriages=other), b, _BOND)


def test_a_none_gate_reads_no_social_state():
    class _Guard:
        def __getattr__(self, name):
            if name in ("social", "strategic"):
                raise AssertionError(f"a none gate read {name}")
            return 1

    guard = _Guard()
    assert passes_mate_gate(guard, guard, _NONE)


def test_bond_needs_a_named_line_and_none_has_none_and_an_unknown_name_is_refused():
    with pytest.raises(Exception, match="friend|input"):
        _BOND.model_copy(update={"min_mutual_sentiment": "loyal"}).model_validate({**_BOND.model_dump(), "min_mutual_sentiment": "loyal"})
    from src.content.repository import ReproductionProfileError, _check_gestation_and_litter
    with pytest.raises(ReproductionProfileError, match="disagree"):
        _check_gestation_and_litter("t", _BOND.model_copy(update={"min_mutual_sentiment": None}))
    with pytest.raises(ReproductionProfileError, match="disagree"):
        _check_gestation_and_litter("t", _NONE.model_copy(update={"min_mutual_sentiment": SentimentThreshold.FRIEND}))


class _Gated(_Catalog):
    def get_reproduction_profile(self, profile_id):
        return self._real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": 1.0, "litter_weights": {1: 1.0}})


def test_bond_conceives_only_for_a_fond_or_married_pair_and_the_mate_search_skips_a_blocked_lowest_id(monkeypatch):
    real = births.get_catalog()
    monkeypatch.setattr(births, "get_catalog", lambda: _Gated(real, 1.0))
    state = lambda *e: AuthoritativeState(tick=30, seed=42, entities={x.id: x for x in e}, next_entity_id=10)
    assert not _conceptions(_run(state(_body(1), _body(2))))
    fond = lambda i, j: _with(_body(i), {j: _bond(_LINE)})
    assert _conceptions(_run(state(fond(1, 2), fond(2, 1)))) == [(1, 2)]
    # mate 2 is blocked (no bond to 1); mate 3 is fond of 1 and 1 of 3: the search moves on past the lowest id
    assert _conceptions(_run(state(_with(_body(1), {3: _bond(_LINE)}), _body(2), _with(_body(3), {1: _bond(_LINE)})))) == [(1, 3)]
