"""F2 (rpg-designer FINAL v2.1; the #996 rework): the read-only destination helpers. A pending give-up record forbids every tile within Chebyshev 1 of its anchor, and so does an ACTIVE navigation experience of the SAME purpose until it is due; a filed ACCESS blocker forbids nothing."""
from dataclasses import replace

from src.core.navigation_purpose import TargetPurpose
from src.core.builder import V2EntityBuilder
from src.core.strategic import BlockerState
from src.core.navigation_experience import NavExperienceStatus, NavigationExperienceMemory
from src.strategy.destination_suppression import access_blocker_id, access_blocker_tile, access_subject, destination_suppressed
from tests.unit.strategic.experience_fixture import an_experience, refuse, with_experiences


def _subject(*blockers):
    e = V2EntityBuilder(1).kind("HERO").location(5, 5).build()
    return replace(e, strategic=replace(e.strategic, blockers={b.id: b for b in blockers}))


def _access(x, y, until=100, **kw):
    return BlockerState(id=access_blocker_id((x, y)), kind="access", subject=access_subject((x, y)), suppression_until_tick=until, **kw)


def test_the_id_and_the_subject_use_the_formats_infer_blockers_already_writes():
    assert access_blocker_id((9.0, 5.0)) == "blocker_access_9_5"
    assert access_subject((9, 5)) == "(9.0, 5.0)" == f"{(9.0, 5.0)}"


W = TargetPurpose("none", "WANDER")


def test_a_tile_within_chebyshev_one_of_an_active_experience_of_the_same_purpose_is_refused_until_it_is_due():
    e = refuse(_subject(), (9, 5), until=100)
    for pos in ((9, 5), (8, 4), (10, 6), (9.4, 5.6)):
        hit = destination_suppressed(e, pos, 99, W)
        assert hit is not None and hit.blocker_id == "nx_9_5_none_WANDER" and hit.anchor == (9, 5) and hit.pending is False and hit.suppressed_until == 100
    for pos in ((11, 5), (9, 7), (7, 5)):
        assert destination_suppressed(e, pos, 99, W) is None  # two tiles away
    assert destination_suppressed(e, (9, 5), 100, W) is None  # tick >= next_review_tick is due: the exact edge of the window


def test_an_experience_of_a_different_purpose_at_the_same_tile_is_open():
    e = refuse(_subject(), (9, 5), purpose=TargetPurpose("hunger", "WANDER"))
    assert destination_suppressed(e, (9, 5), 99, TargetPurpose("hunger", "WANDER")) is not None
    for other in (W, TargetPurpose("hunger", "PURSUE"), None):  # another project kind, another mode, no purpose at all
        assert destination_suppressed(e, (9, 5), 99, other) is None


def test_a_reviewed_experience_refuses_nothing_and_a_trigger_only_one_does_until_the_approach_changes():
    reviewed = with_experiences(_subject(), an_experience((9, 5), status=NavExperienceStatus.REVIEWED))
    assert destination_suppressed(reviewed, (9, 5), 99, W) is None
    static_only = with_experiences(_subject(), an_experience((9, 5), until=None))  # a trigger-only record: no time rule
    assert destination_suppressed(static_only, (9, 5), 10_000, W) is not None
    moved = replace(static_only, navigation=replace(static_only.navigation, position=(20.0, 5.0)))  # the subject is now past the approach radius from where it gave up
    assert destination_suppressed(moved, (9, 5), 10_000, W) is None


def test_a_stored_target_accepted_through_the_gate_at_the_anchor_with_the_records_purpose_is_latched_open():
    e = refuse(_subject(), (9, 5), until=100)
    held = replace(e, navigation=replace(e.navigation, target=(9.0, 5.0), target_purpose=W, target_gated=True))
    assert destination_suppressed(held, (9, 5), 99, W) is None  # the latch: it was accepted while the record was due
    assert destination_suppressed(replace(held, navigation=replace(held.navigation, target_gated=False)), (9, 5), 99, W) is not None  # control: an ungated hold does not latch
    assert destination_suppressed(replace(held, navigation=replace(held.navigation, target_purpose=TargetPurpose("none", "PURSUE"))), (9, 5), 99, W) is not None  # control: another stored purpose does not
    assert destination_suppressed(replace(held, navigation=replace(held.navigation, target=(30.0, 5.0))), (9, 5), 99, W) is not None  # control: a target elsewhere does not


def test_only_an_unresolved_access_blocker_named_by_its_id_forbids_a_tile():
    resolved = _access(9, 5, resolved=True)
    material = BlockerState(id="blocker_node_4", kind="material", subject="(9.0, 5.0)", suppression_until_tick=100)
    congestion = BlockerState(id="blocker_congestion", kind="access", subject="congestion", suppression_until_tick=100)
    assert destination_suppressed(_subject(resolved, material, congestion), (9, 5), 10, TargetPurpose("none", "WANDER")) is None
    assert access_blocker_tile(congestion) is None and access_blocker_tile(material) is None and access_blocker_tile(_access(3, -4)) == (3, -4)


def test_the_answer_does_not_depend_on_record_order():
    a, b = an_experience((9, 5)), an_experience((10, 5))
    base = _subject()
    for order in ((a, b), (b, a)):  # the memory holds its records sorted by id, but the answer must not rely on it
        memory = replace(base.cognition.memory, navigation=NavigationExperienceMemory(order))
        e = replace(base, cognition=replace(base.cognition, memory=memory))
        assert destination_suppressed(e, (10, 5), 1, W).blocker_id == "nx_10_5_none_WANDER"  # the lowest id wins when several apply


def _with_pending(entity, *anchors, tick=7):
    from src.core.giveup_records import GiveUpRecord
    return replace(entity, navigation=replace(entity.navigation, giveup_records=tuple(GiveUpRecord(a, tick) for a in anchors)))


def test_a_pending_give_up_record_forbids_the_tile_before_the_blocker_is_filed():
    """v2.1c: between the give-up and the strategic pass that consumes the record there is no blocker yet; the pending record itself forbids the anchor and its Chebyshev-1 ring."""
    e = _with_pending(_subject())  # no blocker
    e = _with_pending(replace(e, strategic=replace(e.strategic, blockers={})), (9, 5))
    hit = destination_suppressed(e, (10, 6), 1, TargetPurpose("none", "WANDER"))
    assert hit is not None and hit.pending is True and hit.blocker_id == "blocker_access_9_5" and hit.suppressed_until is None
    assert destination_suppressed(e, (12, 5), 1, TargetPurpose("none", "WANDER")) is None  # a different tile is unaffected


def test_after_the_consume_the_experience_takes_over_from_the_pending_record_and_a_different_anchor_is_unaffected():
    consumed = refuse(_subject(), (9, 5), until=500)  # experience filed, records cleared
    hit = destination_suppressed(consumed, (9, 5), 100, W)
    assert hit is not None and hit.pending is False and hit.suppressed_until == 500
    other = _with_pending(consumed, (2, 2))
    assert destination_suppressed(other, (9, 5), 100, W).pending is False  # the experience refuses its own anchor beside a pending record elsewhere
    assert destination_suppressed(other, (2, 3), 100, W).pending is True
    assert destination_suppressed(_with_pending(_subject(), (2, 2)), (9, 5), 100, W) is None  # the pending-only half: a pending record elsewhere forbids nothing here


def test_a_filed_access_blocker_forbids_nothing_any_more():
    assert destination_suppressed(_subject(_access(9, 5, until=500)), (9, 5), 100, W) is None  # main's ACCESS blockers refuse no destination, as on main
