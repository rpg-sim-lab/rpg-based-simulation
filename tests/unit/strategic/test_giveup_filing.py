"""F2 (TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON, divergence 2.220; rpg-designer v2.1b): the consume step files the ACCESS blocker of each give-up record, merging into
the stored one, with the doubling suppression, and the project current at the give-up that reaches ACCESS_GIVEUP_LIMIT ends DESTINATION_GIVEN_UP. The blocker belongs to the SUBJECT."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GiveUpRecord
from src.core.strategic import BlockerState, ProjectEnd, ProjectState, ProjectStatus
from src.core.updates import StrategicUpdate
from src.strategy.destination_suppression import access_blocker_id, destination_suppressed
from src.systems.strategic_systems.blocker_lifecycle import giveup_filing_update

LIMIT = 4


def _subject(records=(), blockers=(), projects=(ProjectState(id="A", kind="harvesting"),), current="A"):
    e = V2EntityBuilder(1).kind("HERO").location(5, 5).build()
    strat = replace(e.strategic, projects={p.id: p for p in projects}, blockers={b.id: b for b in blockers}, current_project_id=current)
    return replace(e, strategic=strat, navigation=replace(e.navigation, giveup_records=tuple(records)))


def _file(entity, tick, staged=None):
    return giveup_filing_update(entity, staged or StrategicUpdate(), tick, LIMIT)


def _apply(entity, up):
    """What the strategic apply would make of ``up`` for the fields this step writes."""
    blockers = {**entity.strategic.blockers, **{b.id: b for b in up.blockers_add_or_update}}
    projects = {**entity.strategic.projects, **{p.id: p for p in up.projects_add_or_update}}
    current = entity.strategic.current_project_id if up.current_project_id_set is None else (up.current_project_id_set or None)
    return replace(entity, strategic=replace(entity.strategic, blockers=blockers, projects=projects, current_project_id=current), navigation=replace(entity.navigation, giveup_records=()))


def test_the_first_second_and_fourth_give_up_on_one_anchor_suppress_100_200_800_and_the_fourth_ends_the_project():
    anchor = (9, 5)
    e = _subject()
    for n, (tick, expected) in enumerate(((100, 100), (300, 200), (700, 400), (1500, 800)), start=1):
        e = replace(e, navigation=replace(e.navigation, giveup_records=(GiveUpRecord(anchor, tick),)))
        up = _file(e, tick)
        b = next(x for x in up.blockers_add_or_update if x.id == access_blocker_id(anchor))
        assert b.failure_count == n and b.suppression_until_tick == tick + expected and b.kind == "access" and b.subject == "(9.0, 5.0)"
        if n < 4:
            assert not up.projects_add_or_update and up.current_project_id_set is None
        else:
            ended = up.projects_add_or_update[0]
            assert ended.status == ProjectStatus.ABANDONED and ended.ended_by == ProjectEnd.DESTINATION_GIVEN_UP and ended.ended_tick == tick
            assert up.current_project_id_set == "" and up.current_objective_id_set == ""
        e = _apply(e, up)


def test_a_different_anchor_has_its_own_count():
    e = _subject(records=(GiveUpRecord((9, 5), 10),))
    e = _apply(e, _file(e, 10))
    e = replace(e, navigation=replace(e.navigation, giveup_records=(GiveUpRecord((2, 2), 20),)))
    up = _file(e, 20)
    assert [b.failure_count for b in up.blockers_add_or_update] == [1] and up.projects_add_or_update == []


def test_a_stored_blocker_is_merged_not_replaced():
    stored = BlockerState(id=access_blocker_id((9, 5)), kind="access", subject="(9.0, 5.0)", severity=0.3, failure_count=2, suppression_until_tick=5)
    e = _subject(records=(GiveUpRecord((9, 5), 50),), blockers=(stored,))
    b = _file(e, 50).blockers_add_or_update[0]
    assert b.failure_count == 3 and b.suppression_until_tick == 50 + 400 and b.severity == 0.3  # an existing one gets n + 1; its other fields are kept


def test_two_records_on_one_anchor_in_one_pass_count_twice():
    e = _subject(records=(GiveUpRecord((9, 5), 40), GiveUpRecord((9, 5), 41)))
    up = _file(e, 45)
    assert len(up.blockers_add_or_update) == 1 and up.blockers_add_or_update[0].failure_count == 2


def test_nothing_is_filed_when_the_subject_has_no_current_project():
    e = _subject(records=(GiveUpRecord((9, 5), 10),), current=None)
    assert _file(e, 10) is None  # the caller still clears the records, so none outlives a pass


def test_a_blocker_filed_under_project_a_forbids_the_tile_after_the_switch_to_project_b_and_the_fourth_give_up_across_both_ends_the_current_one():
    a, b = ProjectState(id="A", kind="harvesting"), ProjectState(id="B", kind="hunger")
    e = _subject(projects=(a, b), current="A")
    anchor = (9, 5)
    for tick in (100, 300):  # two give-ups under A
        e = replace(e, navigation=replace(e.navigation, giveup_records=(GiveUpRecord(anchor, tick),)))
        e = _apply(e, _file(e, tick))
    e = replace(e, strategic=replace(e.strategic, current_project_id="B"))  # the subject switches to B
    assert destination_suppressed(e, (9, 5), 301) is not None  # the blocker is the subject's: still forbids the tile (suppressed until 300 + 200)
    for tick in (700, 1500):  # the 3rd and 4th give-ups happen under B
        e = replace(e, navigation=replace(e.navigation, giveup_records=(GiveUpRecord(anchor, tick),)))
        up = _file(e, tick)
        e = _apply(e, up)
    assert e.strategic.projects["B"].ended_by == ProjectEnd.DESTINATION_GIVEN_UP and e.strategic.projects["A"].ended_by is None
    assert e.strategic.current_project_id is None


def test_a_later_project_that_gives_up_the_same_anchor_ends_at_once_since_the_count_is_over_the_limit():
    over = BlockerState(id=access_blocker_id((9, 5)), kind="access", subject="(9.0, 5.0)", failure_count=4, suppression_until_tick=0)
    e = _subject(records=(GiveUpRecord((9, 5), 5000),), blockers=(over,))
    up = _file(e, 5000)
    assert up.blockers_add_or_update[0].failure_count == 5 and up.projects_add_or_update[0].ended_by == ProjectEnd.DESTINATION_GIVEN_UP


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

