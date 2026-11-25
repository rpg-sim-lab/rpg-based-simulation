"""TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (decision 73, SURV-06; probe at d87b00a83): SEEK_WORK, the LAST opening step.

A subject that keeps coin and whose every earlier step is closed (no food node, no carcass, no prey, nothing to sell, no shift, no social path) is a hunger goal with NO target, so the
strategic pass skipped it and fell back to the generic ``TownScorer`` town_return, a candidate of another kind that the full-cap exemption (``escalated_need_wins``: HUNGER or FATIGUE only) did not
cover: at a full cap a broke, starving subject got no project at all. SEEK_WORK makes the hunger goal itself carry a target (the town centre), typed HUNGER, so the exemption covers it through the NEED
with no cap change and no kind-based bypass. The target is the town centre; a known-building target waits for a building-knowledge fact type (none exists in code)."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.ai.goals.base import NeedAccess, OpeningStepKind
from src.ai.goals.opening_steps import first_open_step, opening_steps
from src.ai.goals.scorers import EatScorer
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, BuildingState, ResourceNodeState
from src.core.strategic import ProjectState, ProjectStatus
from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

CENTRE = (20.0, 20.0)  # the subject stands at (0, 0), away from the centre
INN_AT = (5.0, 5.0)


def _project(pid, status, kind="harvesting"):
    return ProjectState(id=pid, kind=kind, status=status, objectives=[], active_objective_id=None)


def _full_cap():
    return [_project("a", ProjectStatus.SUSPENDED), _project("b", ProjectStatus.SUSPENDED), _project("c", ProjectStatus.SUSPENDED, "quest")]


def _subject(kind="human", hunger=80.0, gold=0, projects=()):
    ent = V2EntityBuilder(1).kind(kind).location(0.0, 0.0).cognition(max_active_projects=3).build()
    ent = replace(ent, biological=replace(ent.biological, hunger=hunger, sleep_debt=0.0), inventory=replace(ent.inventory, gold=gold))
    return replace(ent, strategic=replace(ent.strategic, projects={p.id: p for p in projects}))


def _state(ent, nodes=(), town_center=CENTRE):
    inn = BuildingState(id=7, kind="inn", position=INN_AT, functional=True)
    return AuthoritativeState(tick=500, seed=1, entities={ent.id: ent}, buildings={7: inn}, resource_nodes={n.id: n for n in nodes}, town_center=town_center)


def _created(ent, state):
    update = StrategicIntelligenceSystem.evaluate_strategic_intent(state, ent, force=True)
    return list(update.projects_add_or_update or [])


def _assert_no_hunger_project_and_only_town_return_fallback(projects):
    """Designer ruling B1 (a): 'no project' means NO HUNGER-typed project (so no SEEK_WORK project) and every OTHER created project is the unchanged generic TOWN_RETURN fallback.
    TOWN_RETURN is never required: the town-return hold is tracked in TCK-20261120-A-TOWN-RETURN-PROJECT-NEVER-COMPLETES-WHEN-ITS-TARGET-IS-REACHED (P2) and #781 does not fix it."""
    kinds = {getattr(p.kind, "value", p.kind) for p in projects}
    assert "hunger" not in kinds
    assert kinds <= {"town_return"}


def _kinds(projects):
    return [(getattr(p.kind, "value", p.kind), p.status) for p in projects]


def _berries():
    return ResourceNodeState(id=10, kind="berry_thicket", position=(3.0, 0.0), yields_item="wild_berries", remaining_charges=4, max_charges=8, required_ticks=8, cooldown_remaining=0)


# ---- the step itself ------------------------------------------------------------------------------------------------------------------------------

def test_seek_work_is_the_last_step_and_open_for_a_coin_keeper_with_every_earlier_step_closed():
    ent = _subject()
    steps = opening_steps(ent, _state(ent))
    assert [s.kind for s in steps] == [OpeningStepKind.FORAGE, OpeningStepKind.SCAVENGE, OpeningStepKind.HUNT, OpeningStepKind.EARN_THEN_BUY, OpeningStepKind.ASK, OpeningStepKind.SEEK_WORK]
    step = first_open_step(ent, _state(ent))
    assert step.kind is OpeningStepKind.SEEK_WORK and step.available and step.target_id == "town_center" and step.target_pos == CENTRE


def test_an_earlier_open_step_wins_over_seek_work():
    ent = _subject()
    state = _state(ent, nodes=[_berries()])
    steps = {s.kind: s for s in opening_steps(ent, state)}
    assert first_open_step(ent, state).kind is OpeningStepKind.FORAGE
    assert not steps[OpeningStepKind.SEEK_WORK].available and "earlier step" in steps[OpeningStepKind.SEEK_WORK].reason


def test_a_kind_that_does_not_keep_coin_has_no_seek_work():
    wolf = _subject("wolf")
    steps = {s.kind: s for s in opening_steps(wolf, _state(wolf))}
    assert not steps[OpeningStepKind.SEEK_WORK].available and "does not keep coin" in steps[OpeningStepKind.SEEK_WORK].reason
    assert first_open_step(wolf, _state(wolf)) is None or first_open_step(wolf, _state(wolf)).kind is not OpeningStepKind.SEEK_WORK


def test_a_subject_already_at_the_town_centre_has_no_seek_work_so_earn_then_buy_is_what_can_open():
    ent = _subject()
    steps = {s.kind: s for s in opening_steps(ent, _state(ent, town_center=(0.0, 0.0)))}
    assert not steps[OpeningStepKind.SEEK_WORK].available and "already at the town centre" in steps[OpeningStepKind.SEEK_WORK].reason


# ---- the hunger goal and the cap (the probe's cases) ----------------------------------------------------------------------------------------------

def test_B_a_broke_coin_keeper_past_the_onset_at_a_full_cap_gets_exactly_one_hunger_project_toward_the_town_centre():
    ent = _subject(hunger=80.0, projects=_full_cap())
    state = _state(ent)
    score = EatScorer().score(ent, state)
    assert score.opening_step is OpeningStepKind.SEEK_WORK and score.need_access is NeedAccess.NO_WAY_WITHIN_REACH and score.target_pos == CENTRE
    created = _created(ent, state)
    assert _kinds(created) == [("hunger", ProjectStatus.ACTIVE)]
    assert created[0].objectives[0].target == "town_center"


def test_A_below_the_onset_at_a_full_cap_it_is_an_ordinary_candidate_and_the_cap_refuses_it():
    ent = _subject(hunger=50.0, projects=_full_cap())
    assert _created(ent, _state(ent)) == []


def test_C1_with_room_it_is_a_hunger_seek_work_project_not_a_generic_town_return():
    ent = _subject(hunger=80.0)
    created = _created(ent, _state(ent))
    assert _kinds(created) == [("hunger", ProjectStatus.ACTIVE)]
    assert created[0].objectives[0].target == "town_center"


def test_C2_a_subject_that_can_pay_still_gets_a_hunger_project_toward_the_inn():
    ent = _subject(hunger=80.0, gold=10, projects=_full_cap())
    state = _state(ent)
    score = EatScorer().score(ent, state)
    assert score.need_access is NeedAccess.WAY_WITHIN_REACH and score.opening_step is None and score.target_pos == INN_AT
    assert _kinds(_created(ent, state)) == [("hunger", ProjectStatus.ACTIVE)]


def test_no_bypass_at_a_full_cap_with_no_escalated_need_there_is_no_town_return_and_no_seek_work():
    ent = _subject(hunger=10.0, projects=_full_cap())
    state = _state(ent)
    assert _created(ent, state) == []
    assert EatScorer().score(ent, state).opening_step is not OpeningStepKind.SEEK_WORK


def test_a_non_coin_kind_in_B_s_state_gets_no_project_at_a_full_cap():
    wolf = _subject("wolf", hunger=80.0, projects=_full_cap())
    assert _created(wolf, _state(wolf)) == []
    assert EatScorer().score(wolf, _state(wolf)).opening_step is not OpeningStepKind.SEEK_WORK


@pytest.mark.parametrize("hunger", [50.0, 80.0])
def test_the_exemption_is_the_needs_not_a_kind_a_town_return_candidate_is_still_capped(hunger):
    """The generic TownScorer fallback is untouched: with a hunger goal that has a target of its own nothing here changes for town_return."""
    ent = _subject(hunger=hunger, gold=10, projects=_full_cap())  # funded: the hunger goal points at the inn
    created = _kinds(_created(ent, _state(ent)))
    assert ("town_return", ProjectStatus.ACTIVE) not in created


# ---- the guard, the end on arrival and the leash (designer rulings B1, B2 and the leash) ---------------------------------------------------------

def _at(ent, pos):
    return replace(ent, navigation=replace(ent.navigation, position=pos))


def test_the_same_subject_AT_the_town_centre_has_no_seek_work_and_no_project():
    """B1: the guard (the existing RETREAT_ARRIVAL_RADIUS 'arrived' line, no new number) closes the step for a subject standing on the centre: no step, no hunger project, at a full cap or not."""
    for projects in ([], _full_cap()):
        ent = _at(_subject(hunger=80.0, projects=projects), CENTRE)
        state = _state(ent)
        assert first_open_step(ent, state) is None
        _assert_no_hunger_project_and_only_town_return_fallback(_created(ent, state))


def test_a_leashed_coin_keeper_whose_leash_excludes_the_centre_has_no_seek_work():
    """The leash closure stays as coded (designer): a range-bound subject's ways are inside its range (owner decision D57); M1 item 6 later replaces the hardcoded leash for every range reader."""
    ent = _subject(hunger=80.0)
    ent = replace(ent, navigation=replace(ent.navigation, home_position=(0.0, 0.0), leash_radius=5.0))
    steps = {s.kind: s for s in opening_steps(ent, _state(ent))}
    assert not steps[OpeningStepKind.SEEK_WORK].available and "outside its range" in steps[OpeningStepKind.SEEK_WORK].reason
    _assert_no_hunger_project_and_only_town_return_fallback(_created(ent, _state(ent)))


def _arrival(ent_far, state):
    """The SEEK_WORK project the strategic pass makes for the subject away from the centre, then the same subject standing on the centre pursuing it (the tactical objective step)."""
    from src.engine.tactical import TacticalDecisionSystem
    from src.engine.tactical_objective import pursue_objective

    project = _created(ent_far, state)[0]
    here = _at(ent_far, CENTRE)
    here = replace(here, strategic=replace(here.strategic, projects={**here.strategic.projects, project.id: project}, current_project_id=project.id,
                                           current_objective_id=project.active_objective_id))
    state2 = replace(state, entities={1: here})
    return here, state2, pursue_objective(state2, here, [], TacticalDecisionSystem._resolve_target_position)


def test_B2_on_arrival_at_the_town_centre_the_seek_work_project_ends_way_closed_and_the_subject_re_decides():
    from src.core.strategic import ProjectEnd
    ent = _subject(hunger=80.0)
    _, _, upd = _arrival(ent, _state(ent))
    (ended,) = upd.strategic.projects_add_or_update
    assert ended.status is ProjectStatus.ABANDONED and ended.ended_by is ProjectEnd.WAY_CLOSED and ended.kind == "hunger"
    assert upd.strategic.current_project_id_set == "" and upd.strategic.current_objective_id_set == ""


def test_B2_the_tick_after_arrival_with_a_hiring_building_in_reach_is_an_earn_then_buy_hunger_project():
    ent = _subject(hunger=80.0)
    here, state2, upd = _arrival(ent, _state(ent))
    hiring = BuildingState(id=8, kind="inn", position=(21.0, 20.0), functional=True, hires_for_pay=True)
    hiring = replace(hiring, inventory=replace(hiring.inventory, gold=50))
    # the arrival end applied: no current project; the subject re-decides with a building that hires in reach
    ended = upd.strategic.projects_add_or_update[0]
    again = replace(here, strategic=replace(here.strategic, projects={ended.id: ended}, current_project_id=None, current_objective_id=None))
    state3 = replace(state2, entities={1: again}, buildings={**state2.buildings, 8: hiring})
    step = first_open_step(again, state3)
    assert step.kind is OpeningStepKind.EARN_THEN_BUY and step.target_id == "8"
    assert _kinds(_created(again, state3)) == [("hunger", ProjectStatus.ACTIVE)]


def test_B2_the_tick_after_arrival_with_nothing_there_is_no_project():
    ent = _subject(hunger=80.0)
    here, state2, upd = _arrival(ent, _state(ent))
    ended = upd.strategic.projects_add_or_update[0]
    again = replace(here, strategic=replace(here.strategic, projects={ended.id: ended}, current_project_id=None, current_objective_id=None))
    state3 = replace(state2, entities={1: again})
    assert first_open_step(again, state3) is None
    _assert_no_hunger_project_and_only_town_return_fallback(_created(again, state3))
