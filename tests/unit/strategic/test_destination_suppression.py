"""F2 (rpg-designer FINAL v2.1): the read-only destination helpers. A suppressed ACCESS blocker forbids every tile within Chebyshev 1 of its anchor while tick < suppression_until_tick; nothing else does."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.strategic import BlockerState
from src.strategy.destination_suppression import access_blocker_id, access_blocker_tile, access_subject, destination_suppressed


def _subject(*blockers):
    e = V2EntityBuilder(1).kind("HERO").location(5, 5).build()
    return replace(e, strategic=replace(e.strategic, blockers={b.id: b for b in blockers}))


def _access(x, y, until=100, **kw):
    return BlockerState(id=access_blocker_id((x, y)), kind="access", subject=access_subject((x, y)), suppression_until_tick=until, **kw)


def test_the_id_and_the_subject_use_the_formats_infer_blockers_already_writes():
    assert access_blocker_id((9.0, 5.0)) == "blocker_access_9_5"
    assert access_subject((9, 5)) == "(9.0, 5.0)" == f"{(9.0, 5.0)}"


def test_a_tile_within_chebyshev_one_of_a_suppressed_anchor_is_forbidden_until_the_suppression_ends():
    e = _subject(_access(9, 5, until=100))
    for pos in ((9, 5), (8, 4), (10, 6), (9.4, 5.6)):
        assert destination_suppressed(e, pos, 99).blocker_id == "blocker_access_9_5"
    for pos in ((11, 5), (9, 7), (7, 5)):
        assert destination_suppressed(e, pos, 99) is None  # two tiles away
    assert destination_suppressed(e, (9, 5), 100) is None  # tick < suppression_until_tick is the whole window


def test_only_an_unresolved_access_blocker_named_by_its_id_forbids_a_tile():
    resolved = _access(9, 5, resolved=True)
    material = BlockerState(id="blocker_node_4", kind="material", subject="(9.0, 5.0)", suppression_until_tick=100)
    congestion = BlockerState(id="blocker_congestion", kind="access", subject="congestion", suppression_until_tick=100)
    assert destination_suppressed(_subject(resolved, material, congestion), (9, 5), 10) is None
    assert access_blocker_tile(congestion) is None and access_blocker_tile(material) is None and access_blocker_tile(_access(3, -4)) == (3, -4)


def test_the_lowest_id_wins_when_several_apply_so_the_answer_ignores_dict_order():
    a, b = _access(9, 5), _access(10, 5)
    assert destination_suppressed(_subject(a, b), (10, 5), 1).blocker_id == "blocker_access_10_5"
    assert destination_suppressed(_subject(b, a), (10, 5), 1).blocker_id == "blocker_access_10_5"


def _with_pending(entity, *anchors, tick=7):
    from src.core.giveup_records import GiveUpRecord
    return replace(entity, navigation=replace(entity.navigation, giveup_records=tuple(GiveUpRecord(a, tick) for a in anchors)))


def test_a_pending_give_up_record_forbids_the_tile_before_the_blocker_is_filed():
    """v2.1c: between the give-up and the strategic pass that consumes the record there is no blocker yet; the pending record itself forbids the anchor and its Chebyshev-1 ring."""
    e = _with_pending(_subject())  # no blocker
    e = _with_pending(replace(e, strategic=replace(e.strategic, blockers={})), (9, 5))
    hit = destination_suppressed(e, (10, 6), 1)
    assert hit is not None and hit.pending is True and hit.blocker_id == "blocker_access_9_5" and hit.suppressed_until is None
    assert destination_suppressed(e, (12, 5), 1) is None  # a different tile is unaffected


def test_after_the_consume_the_filed_blocker_takes_over_and_a_different_anchor_is_unaffected():
    consumed = _subject(_access(9, 5, until=500))  # blocker filed, records cleared
    hit = destination_suppressed(consumed, (9, 5), 100)
    assert hit is not None and hit.pending is False and hit.suppressed_until == 500
    other = _with_pending(consumed, (2, 2))
    assert destination_suppressed(other, (9, 5), 100).pending is False  # the filed blocker wins over a pending record elsewhere
    assert destination_suppressed(other, (2, 3), 100).pending is True
    assert destination_suppressed(_with_pending(replace(consumed, strategic=replace(consumed.strategic, blockers={})), (2, 2)), (9, 5), 100) is None

