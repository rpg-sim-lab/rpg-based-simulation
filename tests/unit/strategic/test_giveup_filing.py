"""F2 (TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON, divergence 2.220; the #996 rework, design sections 6, 7 and 8): the consume step files each pending give-up record as a navigation
experience of its (anchor, purpose) and files NO ACCESS blocker. The give-ups of one place for one purpose within one project count in `project_giveups`; the project current at the give-up that reaches
ACCESS_GIVEUP_LIMIT ends DESTINATION_GIVEN_UP. The experience belongs to the SUBJECT."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GiveUpRecord
from src.core.navigation_experience import apply_experience_update
from src.core.navigation_purpose import TargetPurpose
from src.core.strategic import ProjectEnd, ProjectState, ProjectStatus
from src.core.updates import StrategicUpdate
from src.strategy.destination_suppression import destination_suppressed
from src.systems.strategic_systems.blocker_lifecycle import consume_giveup_records

LIMIT = 4  # data/content/strategy/blocker_settings.yaml: access_giveup_limit
P = TargetPurpose("none", "WANDER")


def _subject(records=(), projects=(ProjectState(id="A", kind="harvesting"),), current="A"):
    e = V2EntityBuilder(1).kind("HERO").location(5, 5).build()
    strat = replace(e.strategic, projects={p.id: p for p in projects}, current_project_id=current)
    return replace(e, strategic=strat, navigation=replace(e.navigation, giveup_records=tuple(records)))


def _give_up(anchor, tick, purpose=P):
    return GiveUpRecord(anchor, tick, purpose=purpose)


def _pass(entity, tick):
    """One consume pass: (the project-end update, the experience update, the entity after the strategic apply of what this step writes)."""
    strat, upd = consume_giveup_records(entity, StrategicUpdate(), None, tick)
    nx = upd.navigation_experience
    memory = apply_experience_update(entity.cognition.memory.navigation, nx) if nx is not None else entity.cognition.memory.navigation
    projects = {**entity.strategic.projects, **{p.id: p for p in strat.projects_add_or_update}}
    current = entity.strategic.current_project_id if strat.current_project_id_set is None else (strat.current_project_id_set or None)
    after = replace(entity, strategic=replace(entity.strategic, projects=projects, current_project_id=current), navigation=replace(entity.navigation, giveup_records=()),
                    cognition=replace(entity.cognition, memory=replace(entity.cognition.memory, navigation=memory)))
    return strat, nx, after


def _again(entity, anchor, tick, purpose=P):
    return replace(entity, navigation=replace(entity.navigation, giveup_records=(_give_up(anchor, tick, purpose),)))


def test_a_give_up_files_an_experience_and_no_access_blocker():
    e = _subject(records=(_give_up((9, 5), 100),))
    strat, nx, after = _pass(e, 100)
    assert strat.blockers_add_or_update == [] and len(nx.upserts) == 1 and nx.upserts[0].project_giveups == 1 and nx.upserts[0].project_id == "A"
    assert after.strategic.blockers == {} and len(after.cognition.memory.navigation.records) == 1


def test_the_fourth_give_up_of_one_plan_at_one_place_ends_the_project():
    anchor = (9, 5)
    e = _subject()
    for n, tick in enumerate((100, 300, 700, 1500), start=1):
        strat, nx, e = _pass(_again(e, anchor, tick), tick)
        assert nx.upserts[0].project_giveups == n
        if n < LIMIT:
            assert not strat.projects_add_or_update and strat.current_project_id_set is None
        else:
            ended = strat.projects_add_or_update[0]
            assert ended.status == ProjectStatus.ABANDONED and ended.ended_by == ProjectEnd.DESTINATION_GIVEN_UP and ended.ended_tick == tick
            assert strat.current_project_id_set == "" and strat.current_objective_id_set == ""
    assert strat.blockers_add_or_update == []  # no backoff and no blocker: only the experience remembers the place


def test_a_different_anchor_and_a_different_purpose_have_their_own_count():
    e = _subject()
    _, _, e = _pass(_again(e, (9, 5), 10), 10)
    _, nx_other_anchor, e = _pass(_again(e, (2, 2), 20), 20)
    assert nx_other_anchor.upserts[0].project_giveups == 1 and not e.strategic.projects["A"].ended_by
    _, nx_other_purpose, e = _pass(_again(e, (9, 5), 30, TargetPurpose("none", "PURSUE")), 30)
    assert nx_other_purpose.upserts[0].project_giveups == 1 and len(e.cognition.memory.navigation.records) == 3


def test_two_records_on_one_anchor_and_purpose_in_one_pass_count_twice_and_file_one_record():
    e = _subject(records=(_give_up((9, 5), 40), _give_up((9, 5), 41)))
    _, nx, after = _pass(e, 45)
    assert len(nx.upserts) == 1 and nx.upserts[0].project_giveups == 2 and nx.upserts[0].cycle == 2
    assert len(after.cognition.memory.navigation.records) == 1


def test_a_give_up_with_no_current_project_still_files_the_experience_and_ends_nothing():
    """v2.2 D3: the experience is the subject's, so it is filed even with no project; the DESTINATION_GIVEN_UP end applies only when a project exists, even at the limit."""
    e = _subject(current=None)
    for tick in (10, 20, 30, 40, 50):  # past the limit with no project
        strat, nx, e = _pass(_again(e, (9, 5), tick), tick)
        assert len(nx.upserts) == 1 and strat.projects_add_or_update == [] and strat.current_project_id_set is None
    assert nx.upserts[0].project_id == "" and len(e.cognition.memory.navigation.records) == 1


def test_an_experience_filed_under_project_a_still_refuses_the_tile_after_the_switch_to_project_b_and_the_count_restarts_under_b():
    a, b = ProjectState(id="A", kind="harvesting"), ProjectState(id="B", kind="hunger")
    e = _subject(projects=(a, b), current="A")
    anchor = (9, 5)
    for tick in (100, 300):  # two give-ups under A
        _, _, e = _pass(_again(e, anchor, tick), tick)
    e = replace(e, strategic=replace(e.strategic, current_project_id="B"))  # the subject switches to B
    assert destination_suppressed(e, (9, 5), 301, P) is not None  # the experience is the subject's: it still forbids the tile (the next review is at 300 + the oscillation delay)
    strat, nx, e = _pass(_again(e, anchor, 700), 700)  # the 3rd give-up of the place happens under B: section 8 counts per place and purpose within ONE project, so the count restarts at 1
    assert nx.upserts[0].project_giveups == 1 and nx.upserts[0].project_id == "B" and not strat.projects_add_or_update
    assert e.strategic.projects["A"].ended_by is None


def test_a_re_formed_project_restarts_the_count_and_a_new_project_does_not_end_at_once():
    a, b = ProjectState(id="A", kind="harvesting"), ProjectState(id="B", kind="harvesting")
    e = _subject(projects=(a, b), current="A")
    for tick in (100, 300, 700, 1500):
        _, _, e = _pass(_again(e, (9, 5), tick), tick)
    assert e.strategic.projects["A"].ended_by == ProjectEnd.DESTINATION_GIVEN_UP
    e = replace(e, strategic=replace(e.strategic, current_project_id="B"))  # a later project that wants the same place
    strat, nx, e = _pass(_again(e, (9, 5), 5000), 5000)
    assert nx.upserts[0].project_giveups == 1 and not strat.projects_add_or_update  # restarts: the retries are bounded by the due rule, not by the limit


def test_a_give_up_with_no_stored_purpose_files_no_experience_and_counts_towards_nothing():
    e = _subject(records=(GiveUpRecord((9, 5), 10),))  # purpose None: a target restored from an old checkpoint
    strat, nx, after = _pass(e, 10)
    assert nx is None or not nx.upserts
    assert strat.projects_add_or_update == [] and after.cognition.memory.navigation.records == ()


def test_a_held_target_at_a_consumed_anchor_is_counted_not_cleared():
    """v2.1c (report only): consume counts a stored target within Chebyshev 1 of a consumed anchor in HeldTargetAtAnchorCounts and changes no target."""
    from src.core.giveup_records import HeldTargetAtAnchorCounts
    from src.systems.strategic_systems.blocker_lifecycle import consume_giveup_records
    HeldTargetAtAnchorCounts.reset()
    try:
        e = _subject(records=(GiveUpRecord((9, 5), 10),))
        e = replace(e, navigation=replace(e.navigation, target=(10.0, 5.0)))
        strat, upd = consume_giveup_records(e, StrategicUpdate(), None, 10)
        assert HeldTargetAtAnchorCounts.held() == 1
        assert upd.navigation.giveup_records_clear is True and upd.navigation.target_clear is False and upd.navigation.clear_target is False and upd.navigation.target_set is None
        far = replace(e, navigation=replace(e.navigation, target=(20.0, 5.0)))
        consume_giveup_records(far, StrategicUpdate(), None, 11)
        assert HeldTargetAtAnchorCounts.held() == 1  # two tiles or more away is not counted
    finally:
        HeldTargetAtAnchorCounts.reset()

