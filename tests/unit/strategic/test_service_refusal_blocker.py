"""TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER, part B (STRAT-191-194): N consecutive TYPED payment refusals of the same (action, building) file ONE access blocker.

The refusal is a typed record on the subject's navigation (`src/core/service_refusals.py`), appended by the service writer and cleared when the same (action, building) is delivered; `infer_blockers` files the blocker
when `service_refusal_limit` of them form a streak (each within `service_refusal_window` ticks of the previous, each with a counted reason); the quiet spell removes it. The limit, the window, the counted reasons and the
severity are data (data/content/strategy/blocker_settings.yaml). It counts only: it sets no failure reason and does not end a REST.
"""
import pickle
from dataclasses import replace

import pytest

from src.ai.goals.base import GoalScore
from src.ai.score_modifiers import ScoreModifierSystem
from src.content.blocker_settings import BlockerSettingsError, service_refusal_settings
from src.core.builder import V2EntityBuilder
from src.core.service_refusals import SERVICE_BLOCKER_PREFIX, SERVICE_REFUSALS_CAP, ServiceRefusal, consecutive_refusals, service_blocker_id
from src.core.state import AuthoritativeState
from src.core.strategic import BLOCKER_QUIET_SPELL_TICKS, BlockerState, quiet_blockers
from src.core.updates import EntityUpdate, NavigationUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.building_services import with_service
from src.engine.checkpoint import CanonicalStateHasher
from src.systems.strategic_systems.blocker_lifecycle import infer_blockers
from tests.unit.engine.lodging_kernel import INN_ID, REACH, hero, kernel

SETTINGS = service_refusal_settings()
N, WINDOW = SETTINGS.limit, SETTINGS.window


def refusal(tick, action="EAT", building=INN_ID, reason="INSUFFICIENT_GOLD"):
    return ServiceRefusal(action, building, tick, reason)


def holder(*records):
    entity = V2EntityBuilder(1).kind("human").location(0.0, 0.0).build()
    return replace(entity, navigation=replace(entity.navigation, service_refusals=tuple(records)))


def filed(entity, tick):
    return {b.id: b for b in infer_blockers(entity, "ENTITY_ACT", {}, tick=tick).blockers_add_or_update}


# ---------------------------------------------------------------- the data
def test_the_rule_reads_its_values_from_the_data_file_and_has_no_code_default():
    assert (SETTINGS.limit, SETTINGS.window, SETTINGS.reasons, SETTINGS.severity) == (4, 20, ("INSUFFICIENT_GOLD",), 0.5)
    class Empty:
        blocker_settings = {}
    with pytest.raises(BlockerSettingsError):
        service_refusal_settings(Empty())


# ---------------------------------------------------------------- the streak and the filing
def test_n_consecutive_typed_refusals_file_one_access_blocker_for_that_way():
    entity = holder(*[refusal(10 * i) for i in range(1, N + 1)])                                  # one every 10 ticks, as in the v6 rows
    blockers = filed(entity, tick=10 * N)
    assert list(blockers) == [service_blocker_id("EAT", INN_ID)]
    blocker = blockers[service_blocker_id("EAT", INN_ID)]
    assert blocker.kind == "access" and blocker.subject == str(INN_ID) and blocker.severity == SETTINGS.severity and blocker.id.startswith(SERVICE_BLOCKER_PREFIX)


def test_fewer_than_n_a_gap_over_the_window_or_an_uncounted_reason_file_nothing():
    assert filed(holder(*[refusal(10 * i) for i in range(1, N)]), tick=10 * N) == {}                  # N - 1
    assert filed(holder(refusal(10), refusal(20), refusal(70), refusal(80)), tick=80) == {}          # the streak is broken by a gap of 50 > the window: the current streak is 2
    assert filed(holder(*[refusal(10 * i, reason="NO_BED_FREE") for i in range(1, N + 1)]), tick=10 * N) == {}   # a transient reason is not counted
    assert filed(holder(*[refusal(10 * i, action="REST") for i in range(1, N)] + [refusal(10 * N, action="EAT")]), tick=10 * N) == {}   # another action is another way


def test_a_streak_whose_newest_refusal_is_older_than_the_window_is_not_reinferred():
    entity = holder(*[refusal(10 * i) for i in range(1, N + 1)])
    assert filed(entity, tick=10 * N + WINDOW) != {} and filed(entity, tick=10 * N + WINDOW + 1) == {}


def test_one_blocker_per_way_not_per_refusal_and_two_ways_file_two():
    entity = holder(*[refusal(10 * i) for i in range(1, N + 3)], *[refusal(10 * i, building=INN_ID + 1) for i in range(1, N + 1)])
    assert sorted(filed(entity, tick=10 * (N + 2))) == sorted([service_blocker_id("EAT", INN_ID), service_blocker_id("EAT", INN_ID + 1)])


def test_the_pure_streak_count():
    records = [refusal(10), refusal(20), refusal(30, reason="NO_BED_FREE"), refusal(40), refusal(50)]
    assert consecutive_refusals(records, "EAT", INN_ID, WINDOW, ("INSUFFICIENT_GOLD",)) == 2        # counted from the newest back until the uncounted one
    assert consecutive_refusals(records, "REST", INN_ID, WINDOW, ("INSUFFICIENT_GOLD",)) == 0


# ---------------------------------------------------------------- the patch: add, clear, cap, round trip
def _state(entity):
    return AuthoritativeState(tick=1, seed=1, entities={entity.id: entity})


def _apply(state, nav_update):
    return ApplyPath.apply_generation(state, StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, navigation=nav_update)}), 2, 2)


def test_the_navigation_patch_appends_clears_the_matching_way_only_and_caps():
    state = _state(holder())
    state = _apply(state, NavigationUpdate(service_refusal_add=refusal(5)))
    state = _apply(state, NavigationUpdate(service_refusal_add=refusal(6, action="REST")))
    assert [r.action for r in state.entities[1].navigation.service_refusals] == ["EAT", "REST"]
    cleared = _apply(state, NavigationUpdate(service_refusal_clear=("EAT", INN_ID)))
    assert [r.action for r in cleared.entities[1].navigation.service_refusals] == ["REST"]
    for t in range(SERVICE_REFUSALS_CAP + 3):
        state = _apply(state, NavigationUpdate(service_refusal_add=refusal(100 + t)))
    assert len(state.entities[1].navigation.service_refusals) == SERVICE_REFUSALS_CAP and state.entities[1].navigation.service_refusals[-1].tick == 100 + SERVICE_REFUSALS_CAP + 2


def test_a_clear_and_an_add_of_the_same_update_keep_the_new_refusal():
    state = _apply(_state(holder(refusal(5))), NavigationUpdate(service_refusal_clear=("EAT", INN_ID), service_refusal_add=refusal(9)))
    assert [r.tick for r in state.entities[1].navigation.service_refusals] == [9]


def test_the_field_is_omitted_from_the_canonical_dict_while_empty_and_round_trips_when_held():
    empty, held = holder(), holder(refusal(5))
    assert "service_refusals" not in empty.navigation.to_canonical_dict()
    assert held.navigation.to_canonical_dict()["service_refusals"] == [{"action": "EAT", "building": INN_ID, "tick": 5, "reason": "INSUFFICIENT_GOLD"}]
    restored = pickle.loads(pickle.dumps(_state(held), protocol=pickle.HIGHEST_PROTOCOL))
    assert restored.entities[1].navigation.service_refusals == (refusal(5),)
    assert CanonicalStateHasher.get_hash(restored) == CanonicalStateHasher.get_hash(_state(held)) != CanonicalStateHasher.get_hash(_state(empty))


def test_the_update_merge_and_noop_see_the_new_fields():
    assert NavigationUpdate().is_noop() and not NavigationUpdate(service_refusal_add=refusal(1)).is_noop() and not NavigationUpdate(service_refusal_clear=("EAT", 1)).is_noop()
    merged = NavigationUpdate(service_refusal_add=refusal(1)).merge(NavigationUpdate(service_refusal_clear=("REST", 2)))
    assert merged.service_refusal_add == refusal(1) and merged.service_refusal_clear == ("REST", 2)


# ---------------------------------------------------------------- the writers
def test_a_rest_refused_for_payment_is_counted_with_the_typed_reason_and_sets_no_failure_reason():
    k = kernel([hero(1, REACH[0], gold=0, action=None)], beds=0)               # an inn that declares no beds serves REST on the reach tile (main's behaviour); the subject cannot pay
    try:
        st = k._state
        base = {1: EntityUpdate(entity_id=1)}
        out = with_service(base, st.entities[1], "REST", st.tick, st)[1]
        assert out.navigation is not None and out.navigation.service_refusal_add == ServiceRefusal("REST", INN_ID, st.tick, "INSUFFICIENT_GOLD") and out.navigation.failure_reason is None
    finally:
        k.shutdown()


def test_a_delivered_service_clears_the_held_refusals_of_that_way_and_a_subject_never_refused_is_untouched():
    k = kernel([hero(1, REACH[0], gold=50, action=None)], beds=0)
    try:
        st = k._state
        funded = replace(st.entities[1], navigation=replace(st.entities[1].navigation, service_refusals=(ServiceRefusal("REST", INN_ID, 3, "INSUFFICIENT_GOLD"),)))
        out = with_service({1: EntityUpdate(entity_id=1)}, funded, "REST", st.tick, st)[1]
        assert out.navigation.service_refusal_clear == ("REST", INN_ID)
        plain = with_service({1: EntityUpdate(entity_id=1)}, st.entities[1], "REST", st.tick, st)[1]
        assert plain.navigation is None or plain.navigation.service_refusal_clear is None
    finally:
        k.shutdown()


def test_an_eat_refused_for_payment_keeps_its_typed_failure_reason_and_is_also_counted():
    from src.engine.domain.action_router import _survival_action
    k = kernel([hero(1, REACH[0], gold=0, action="EAT")], beds=2)
    try:
        st = k._state
        out = _survival_action(st.entities[1], "EAT", {"action": "EAT", "target_id": INN_ID}, st.tick, st)[1]
        assert out.navigation.failure_reason.value == "INSUFFICIENT_GOLD" and out.navigation.service_refusal_add == ServiceRefusal("EAT", INN_ID, st.tick, "INSUFFICIENT_GOLD")
    finally:
        k.shutdown()


# ---------------------------------------------------------------- the effect and the expiry
def test_the_filed_blocker_closes_the_way_softly_with_the_existing_suppression_and_floor():
    entity = holder()
    blocker = BlockerState(id=service_blocker_id("EAT", INN_ID), kind="access", subject=str(INN_ID), severity=SETTINGS.severity)
    entity = replace(entity, strategic=replace(entity.strategic, blockers={blocker.id: blocker}))
    state = _state(entity)
    scores = [GoalScore(kind="hunger", utility=80.0, target_id=str(INN_ID)), GoalScore(kind="hunger", utility=80.0, target_id="999")]
    out = ScoreModifierSystem.apply_modifiers(entity, state, scores)
    assert out[0].utility == pytest.approx(80.0 * 0.2) and out[1].utility == pytest.approx(80.0)      # the existing x0.1, floored at 0.2 of the raw value for a need; another target is untouched


def test_the_service_blocker_is_removed_by_the_existing_quiet_spell_and_not_before():
    blocker = BlockerState(id=service_blocker_id("EAT", INN_ID), kind="access", subject=str(INN_ID), severity=0.5, last_seen_tick=100)
    blockers = {blocker.id: blocker}
    assert quiet_blockers(blockers, {}, 100 + BLOCKER_QUIET_SPELL_TICKS - 1) == [] and quiet_blockers(blockers, {}, 100 + BLOCKER_QUIET_SPELL_TICKS) == [blocker.id]


# ---------------------------------------------------------------- the real kernel
def _hungry_broke_eater(gold, seeded):
    """A hungry subject on the inn's reach tile holding an EAT task and a hunger project at the inn, `seeded` earlier refusals of the way (tick 0) already held, and `gold`."""
    from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
    h = hero(1, REACH[0], gold=gold, action="EAT", project=False)
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target=str(INN_ID), status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="p1", kind=GoalKind.HUNGER, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id="o1")
    return replace(h, biological=replace(h.biological, hunger=80.0, sleep_debt=10.0), strategic=replace(h.strategic, projects={"p1": project}, current_project_id="p1", current_objective_id="o1"),
                   navigation=replace(h.navigation, service_refusals=tuple(ServiceRefusal("EAT", INN_ID, 0, "INSUFFICIENT_GOLD") for _ in range(seeded))))


def _run_kernel(entity, ticks=25):
    k = kernel([entity], beds=2)
    try:
        for _ in range(ticks):
            k.tick_once()
        return k._state.entities[1]
    finally:
        k.shutdown()


def test_real_kernel_n_typed_refusals_file_the_blocker_and_the_way_is_closed_softly():
    e = _run_kernel(_hungry_broke_eater(gold=0, seeded=N - 1))                      # the N-th refusal is a real EAT at the inn with no coin
    assert len(e.navigation.service_refusals) == N and e.inventory.gold == 0
    assert list(e.strategic.blockers) == [service_blocker_id("EAT", INN_ID)] and e.strategic.blockers[service_blocker_id("EAT", INN_ID)].subject == str(INN_ID)
    scores = ScoreModifierSystem.apply_modifiers(e, _state(e), [GoalScore(kind="hunger", utility=80.0, target_id=str(INN_ID))])
    assert scores[0].utility <= 80.0 * 0.2 + 1e-9                                   # the existing suppression (x0.1 under the need floor of 0.2 of the raw value)


def test_real_kernel_n_minus_one_refusals_file_nothing():
    e = _run_kernel(_hungry_broke_eater(gold=0, seeded=N - 2))
    assert len(e.navigation.service_refusals) == N - 1 and e.strategic.blockers == {}


def test_real_kernel_a_delivered_meal_clears_the_streak_and_files_nothing():
    e = _run_kernel(_hungry_broke_eater(gold=50, seeded=N - 1))                      # the same subject with the price: the meal is served and paid
    assert e.navigation.service_refusals == () and e.strategic.blockers == {} and e.inventory.gold < 50
