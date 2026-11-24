"""F2 (divergence 2.220; rpg-designer v2.1b), the tactical writer: a destination within Chebyshev 1 of a pending give-up record or an active navigation experience of its purpose sets no target and returns the typed outcome
OBJECTIVE_DESTINATION_SUPPRESSED (an empty update the tactical pass returns as handled, so the subject does not fall through to the role and cohesion branches)."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.movement_modes import MovementMode
from src.core.navigation_purpose import purpose_of
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState
from src.engine.tactical_objective import ObjectiveDestinationSuppressed, pursue_objective
from tests.unit.strategic.experience_fixture import refuse

TARGET = (12.0, 5.0)


def _resolve(state, obj):
    return TARGET, None, None


def _subject(suppressed_until=None, anchor=(12, 6)):
    obj = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target="town_center", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="p1", kind="harvesting", objectives=[obj], active_objective_id="o1")
    e = V2EntityBuilder(1).kind("HERO").location(5, 5).build()
    e = replace(e, strategic=replace(e.strategic, projects={"p1": project}, current_project_id="p1", current_objective_id="o1"))
    return e if suppressed_until is None else refuse(e, anchor, purpose=purpose_of(e, None, MovementMode.WANDER), until=suppressed_until)  # the objective walk's purpose: its project kind and WANDER


def _state(e, tick):
    return AuthoritativeState(entities={1: e}, tick=tick, seed=1)


def test_a_suppressed_destination_sets_no_target_and_returns_the_typed_outcome():
    e = _subject(suppressed_until=200)
    out = pursue_objective(_state(e, 100), e, None, _resolve)
    assert isinstance(out, ObjectiveDestinationSuppressed) and out.entity_id == 1
    assert out.navigation is None and out.task is None  # no NavigationUpdate, nothing else


def test_the_same_objective_walks_normally_once_the_suppression_has_passed_or_when_none_was_filed():
    for e, tick in ((_subject(suppressed_until=200), 200), (_subject(), 100)):
        out = pursue_objective(_state(e, tick), e, None, _resolve)
        assert not isinstance(out, ObjectiveDestinationSuppressed)
        assert out.navigation is not None and tuple(out.navigation.target_set) == TARGET


def test_an_experience_two_tiles_from_the_destination_does_not_suppress_it():
    e = _subject(suppressed_until=200, anchor=(14, 5))
    out = pursue_objective(_state(e, 100), e, None, _resolve)
    assert not isinstance(out, ObjectiveDestinationSuppressed) and out.navigation is not None


def test_a_pending_give_up_record_makes_the_tactical_step_idle_before_the_experience_exists():
    """v2.1c: the give-up cleared the stored target and the record is not consumed until the next strategic pass; the objective step must not re-set the target to the anchor meanwhile."""
    from src.core.giveup_records import GiveUpRecord
    e = _subject()  # no experience
    e = replace(e, navigation=replace(e.navigation, target=None, giveup_records=(GiveUpRecord((12, 6), 90),)))
    out = pursue_objective(_state(e, 91), e, None, _resolve)
    assert isinstance(out, ObjectiveDestinationSuppressed) and out.navigation is None
    after = replace(e, navigation=replace(e.navigation, giveup_records=()))  # the pass consumed the record without filing: nothing forbids it any more
    assert not isinstance(pursue_objective(_state(after, 92), after, None, _resolve), ObjectiveDestinationSuppressed)

