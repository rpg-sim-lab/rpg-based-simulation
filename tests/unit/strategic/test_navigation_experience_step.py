"""The #996 rework, step (d1) (design sections 5 and 6): when a record is due, and the one consume step that reviews, files and evicts. Every rule reads only the subject's own state; every rule has a failing control."""
from dataclasses import replace

import pytest

from src.content.navigation_experience_settings import NavigationExperienceSettings
from src.core.builder import V2EntityBuilder
from src.core.giveup_records import GiveUpRecord
from src.core.navigation_experience import (
    NavCause,
    NavExperienceStatus,
    NavigationExperience,
    NavigationExperienceCounts,
    NavigationExperienceMemory,
    NeedService,
    ReviewReason,
    RingEvidence,
    apply_experience_update,
    experience_id_of,
)
from src.core.navigation_purpose import TargetPurpose
from src.engine.need_pull import SLEEP_LINE
from src.engine.starvation import STARVING_LINE
from src.strategy.experience_due import due_reason, next_review_tick_of
from src.systems.strategic_systems import navigation_experience_step as step

S = NavigationExperienceSettings(oscillation_review_delay=100, bodies_review_delay=50, approach_change_radius=5, navigation_experience_cap=8, occupied_review_delay=10)
P = TargetPurpose("hunger", "WANDER")


def _rec(x=9, y=5, cycle=1, status=NavExperienceStatus.ACTIVE, observed=10, nxt=110, need=frozenset(), frm=(3, 3), purpose=P, reviewed=None, project="p1", giveups=1, cause=NavCause.OSCILLATION, ev=()):
    return NavigationExperience(
        experience_id=experience_id_of((x, y), purpose), anchor=(x, y), purpose=purpose, cause=cause, ring_evidence=ev, from_position=frm, target_tile=(x, y), need_services=need, project_id=project,
        observed_tick=observed, cycle=cycle, next_review_tick=nxt, status=status, reviewed_tick=reviewed, review_reason=None, project_giveups=giveups)


def _subject(records=(), giveups=(), pos=(3.0, 3.0), hunger=0.0, sleep_debt=0.0):
    e = V2EntityBuilder(1).kind("HERO").location(*pos).build()
    memory = replace(e.cognition.memory, navigation=NavigationExperienceMemory(tuple(records)))
    return replace(e, cognition=replace(e.cognition, memory=memory), navigation=replace(e.navigation, giveup_records=tuple(giveups)),
                   biological=replace(e.biological, hunger=hunger, sleep_debt=sleep_debt))


# --- the delays each cause and evidence earns -----------------------------------------------------------------------------------------------------------
def test_the_review_delay_follows_the_cause_and_the_evidence_never_the_cycle():
    assert next_review_tick_of(NavCause.OSCILLATION, (), 10, S) == 110
    assert next_review_tick_of(NavCause.RING_BLOCKED, (RingEvidence.BODIES,), 10, S) == 60
    assert next_review_tick_of(NavCause.RING_BLOCKED, (RingEvidence.BODIES, RingEvidence.STATIC), 10, S) == 60
    assert next_review_tick_of(NavCause.RING_BLOCKED, (RingEvidence.STATIC,), 10, S) is None  # terrain: only a trigger makes it due
    assert next_review_tick_of(NavCause.RING_BLOCKED, (RingEvidence.OTHER,), 10, S) == 110
    assert next_review_tick_of(NavCause.RING_BLOCKED, (), 10, S) == 110
    assert next_review_tick_of(NavCause.OCCUPIED, (RingEvidence.BODIES,), 10, S) == 20  # waiting, not failure: the short occupied delay (owner #715 7130979190), whatever the cycle
    assert next_review_tick_of(NavCause.OCCUPIED, (), 10, S) == 20


# --- the due rule, in the table's order -----------------------------------------------------------------------------------------------------------
def test_a_record_is_due_by_time_by_a_changed_approach_or_by_a_severe_need_and_not_otherwise():
    e = _subject()
    r = _rec()
    assert due_reason(r, e, 109, S) is None and due_reason(r, e, 110, S) == ReviewReason.DUE_TICK
    far = _subject(pos=(9.0, 3.0))  # Chebyshev 6 from (3, 3): past the radius 5
    assert due_reason(r, far, 20, S) == ReviewReason.APPROACH_CHANGED
    assert due_reason(r, _subject(pos=(8.0, 3.0)), 20, S) is None  # exactly 5 is not a changed approach (strictly more)


def test_a_static_record_is_never_time_due_only_a_changed_approach_makes_it_due():
    r = _rec(nxt=None, cause=NavCause.RING_BLOCKED, ev=(RingEvidence.STATIC,))
    assert due_reason(r, _subject(), 10_000_000, S) is None
    assert due_reason(r, _subject(pos=(20.0, 3.0)), 5, S) == ReviewReason.APPROACH_CHANGED


def test_a_severe_need_at_a_place_that_serves_it_makes_the_record_due_at_once():
    food = _rec(need=frozenset({NeedService.EAT}))
    assert due_reason(food, _subject(hunger=STARVING_LINE - 0.1), 20, S) is None
    assert due_reason(food, _subject(hunger=STARVING_LINE), 20, S) == ReviewReason.NEED_SEVERE
    assert due_reason(food, _subject(sleep_debt=SLEEP_LINE), 20, S) is None  # EAT does not answer an exhausted body
    home = _rec(need=frozenset({NeedService.REST}))
    assert due_reason(home, _subject(sleep_debt=SLEEP_LINE), 20, S) == ReviewReason.NEED_SEVERE and due_reason(home, _subject(hunger=100.0), 20, S) is None  # a tired body is due at a home
    inn = _rec(need=frozenset({NeedService.EAT, NeedService.REST}))
    assert due_reason(inn, _subject(hunger=STARVING_LINE), 20, S) == ReviewReason.NEED_SEVERE and due_reason(inn, _subject(sleep_debt=SLEEP_LINE), 20, S) == ReviewReason.NEED_SEVERE
    assert due_reason(_rec(need=frozenset()), _subject(hunger=100.0, sleep_debt=100.0), 20, S) is None  # a place that serves no need is not rushed by one


@pytest.mark.parametrize("purpose", [TargetPurpose("recovery", "WANDER"), TargetPurpose("none", "WANDER"), TargetPurpose("hunger", "PURSUE")])
def test_a_starving_body_is_due_at_the_inn_whatever_purpose_the_record_was_filed_under(purpose):
    """The need rule keys on the body's need line and the place's service, not on the project kind: a survival walk filed under RECOVERY or under no project is covered too."""
    inn = _rec(need=frozenset({NeedService.EAT, NeedService.REST}), purpose=purpose)
    assert due_reason(inn, _subject(hunger=STARVING_LINE), 20, S) == ReviewReason.NEED_SEVERE
    assert due_reason(inn, _subject(hunger=STARVING_LINE - 1.0), 20, S) is None  # failing control: below the line the same record is not due


# --- the consume step ----------------------------------------------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _reset_counts():
    NavigationExperienceCounts.reset()


def _giveup(x=9, y=5, tick=10, purpose=P, cause=NavCause.OSCILLATION, ev=(), frm=(3, 3), need=frozenset()):
    return GiveUpRecord((x, y), tick, cause, ev, frm, (x, y), purpose, need)


def test_a_give_up_files_cycle_one_and_the_next_give_up_at_the_place_files_a_fresh_cycle_from_that_give_ups_evidence():
    e = _subject(giveups=(_giveup(),))
    first = step.navigation_experience_update(e, 10, "p1", S)
    assert [(r.cycle, r.next_review_tick, r.project_giveups, r.project_id) for r in first.upserts] == [(1, 110, 1, "p1")]
    held = _subject(records=first.upserts, giveups=(_giveup(tick=200, cause=NavCause.RING_BLOCKED, ev=(RingEvidence.BODIES,)),))
    second = step.navigation_experience_update(held, 200, "p1", S)
    r = second.upserts[0]
    assert (r.cycle, r.next_review_tick, r.project_giveups, r.cause) == (2, 250, 2, NavCause.RING_BLOCKED)  # nothing doubled: 50 is the BODIES delay, whatever the cycle


def test_a_new_project_restarts_the_project_give_up_count_but_not_the_cycle():
    held = _subject(records=(_rec(giveups=3, project="p1"),), giveups=(_giveup(tick=300),))
    r = step.navigation_experience_update(held, 300, "p2", S).upserts[0]
    assert (r.cycle, r.project_giveups) == (2, 1)


def test_a_give_up_with_no_stored_purpose_files_nothing_and_is_counted():
    e = _subject(giveups=(_giveup(purpose=None),))
    out = step.navigation_experience_update(e, 10, "", S)
    assert out.is_noop() and NavigationExperienceCounts.no_purpose() == 1


def test_two_purposes_at_one_place_are_two_records_and_the_review_names_the_first_rule_that_holds():
    other = TargetPurpose("none", "PURSUE")
    e = _subject(giveups=(_giveup(), _giveup(purpose=other)))
    out = step.navigation_experience_update(e, 10, "", S)
    assert [r.experience_id for r in out.upserts] == sorted(["nx_9_5_hunger_WANDER", "nx_9_5_none_PURSUE"])
    due = _subject(records=(_rec(),), pos=(30.0, 3.0))
    reviews = step.navigation_experience_update(due, 500, "", S).reviews
    assert [(r.cycle, r.reviewed_tick, r.reason) for r in reviews] == [(1, 500, ReviewReason.DUE_TICK)]  # time holds first in the table's order, though the approach changed too


def test_a_reviewed_record_is_not_reviewed_again():
    done = _rec(status=NavExperienceStatus.REVIEWED, reviewed=50)
    assert step.navigation_experience_update(_subject(records=(done,), pos=(30.0, 3.0)), 500, "", S).reviews == ()


def test_the_cap_evicts_the_oldest_reviewed_then_a_due_active_then_the_oldest_active_and_counts_only_that_last():
    small = NavigationExperienceSettings(100, 50, 5, 2, 10)
    reviewed_old = _rec(1, 1, status=NavExperienceStatus.REVIEWED, reviewed=40, observed=1)
    reviewed_new = _rec(2, 2, status=NavExperienceStatus.REVIEWED, reviewed=60, observed=2)
    e = _subject(records=(reviewed_old, reviewed_new), giveups=(_giveup(),))
    assert step.navigation_experience_update(e, 100, "", small).evictions == (reviewed_old.experience_id,)
    due_active = _rec(3, 3, observed=5, nxt=60)
    fresh_active = _rec(4, 4, observed=90, nxt=900)
    e2 = _subject(records=(due_active, fresh_active), giveups=(_giveup(),))
    assert step.navigation_experience_update(e2, 100, "", small).evictions == (due_active.experience_id,) and NavigationExperienceCounts.live_evictions() == 0
    live1, live2 = _rec(5, 5, observed=20, nxt=900), _rec(6, 6, observed=30, nxt=900)
    e3 = _subject(records=(live1, live2), giveups=(_giveup(),))
    assert step.navigation_experience_update(e3, 100, "", small).evictions == (live1.experience_id,) and NavigationExperienceCounts.live_evictions() == 1


def test_a_record_filed_this_pass_is_never_the_one_evicted():
    small = NavigationExperienceSettings(100, 50, 5, 1, 10)
    e = _subject(records=(_rec(1, 1, status=NavExperienceStatus.REVIEWED, reviewed=40),), giveups=(_giveup(),))
    out = step.navigation_experience_update(e, 100, "", small)
    assert out.evictions == ("nx_1_1_hunger_WANDER",) and [r.experience_id for r in out.upserts] == ["nx_9_5_hunger_WANDER"]


def test_the_filed_record_keeps_the_needs_the_give_up_record_carries():
    """The step no longer looks a building up: the producer froze the needs at the give-up on the record, and the filed experience copies them."""
    e = _subject(giveups=(_giveup(need=frozenset({NeedService.EAT, NeedService.REST})),))
    out = step.navigation_experience_update(e, 10, "", S)
    assert out.upserts[0].need_services == frozenset({NeedService.EAT, NeedService.REST})
    assert step.navigation_experience_update(_subject(giveups=(_giveup(),)), 10, "", S).upserts[0].need_services == frozenset()


def test_a_reviewed_record_is_evicted_before_a_due_active_one_even_when_the_active_one_is_older():
    """New with the #996 `_evictions` split: the reviewed-first preference holds against a due ACTIVE record that was observed earlier, and the eviction is not counted as a live one."""
    small = NavigationExperienceSettings(100, 50, 5, 2, 10)
    NavigationExperienceCounts.reset()
    due_active = _rec(3, 3, observed=1, nxt=60)
    reviewed = _rec(2, 2, status=NavExperienceStatus.REVIEWED, reviewed=90, observed=50)
    e = _subject(records=(due_active, reviewed), giveups=(_giveup(),))
    assert step.navigation_experience_update(e, 100, "", small).evictions == (reviewed.experience_id,)
    assert NavigationExperienceCounts.live_evictions() == 0


# --- OCCUPIED: waiting, not failure (owner #715 7130979190; ruling 476631fe) ------------------------------------------------------------------------
OCC_EV = (RingEvidence.BODIES,)


def test_an_occupied_record_is_due_at_observed_plus_the_occupied_delay_at_cycle_one_and_cycle_five_and_the_early_rules_still_apply():
    e = _subject()
    for cycle in (1, 5):
        r = _rec(cycle=cycle, observed=10, nxt=20, cause=NavCause.OCCUPIED, ev=OCC_EV)
        assert due_reason(r, e, 19, S) is None and due_reason(r, e, 20, S) == ReviewReason.DUE_TICK
    r = _rec(observed=10, nxt=20, cause=NavCause.OCCUPIED, ev=OCC_EV)
    assert due_reason(r, _subject(pos=(9.0, 3.0)), 12, S) == ReviewReason.APPROACH_CHANGED  # failing control for the time rule: the approach rule is still first-come
    food = _rec(observed=10, nxt=20, cause=NavCause.OCCUPIED, ev=OCC_EV, need=frozenset({NeedService.EAT}))
    assert due_reason(food, _subject(hunger=STARVING_LINE), 12, S) == ReviewReason.NEED_SEVERE and due_reason(food, _subject(hunger=STARVING_LINE - 1.0), 12, S) is None


def _file(entity, rec, tick, project="p1"):
    """The subject after the consume step filed ``rec`` at ``tick`` (the experience applied)."""
    out = step.navigation_experience_update(replace(entity, navigation=replace(entity.navigation, giveup_records=(rec,))), tick, project, S)
    memory = apply_experience_update(entity.cognition.memory.navigation, out)
    return replace(entity, cognition=replace(entity.cognition, memory=replace(entity.cognition.memory, navigation=memory))), out.upserts[0]


def test_an_occupied_filing_keeps_project_giveups_unchanged_zero_on_a_first_record_and_the_stored_count_after_a_failure():
    occ = _giveup(cause=NavCause.OCCUPIED, ev=OCC_EV)
    first = step.navigation_experience_update(_subject(giveups=(occ,)), 10, "p1", S).upserts[0]
    assert (first.cause, first.ring_evidence, first.project_giveups, first.next_review_tick) == (NavCause.OCCUPIED, OCC_EV, 0, 20)
    held = _subject(records=(_rec(giveups=3, project="p1"),), giveups=(_giveup(tick=300, cause=NavCause.OCCUPIED, ev=OCC_EV),))
    kept = step.navigation_experience_update(held, 300, "p1", S).upserts[0]
    assert (kept.cycle, kept.project_giveups, kept.cause) == (2, 3, NavCause.OCCUPIED)  # carried, not +1
    other_project = step.navigation_experience_update(held, 300, "p2", S).upserts[0]
    assert other_project.project_giveups == 0  # a new project starts from 0; the control for the same-project carry above


def test_six_occupied_give_ups_in_one_project_never_reach_the_limit_and_failures_around_them_count_only_themselves():
    e = _subject()
    for k in range(6):
        e, rec = _file(e, _giveup(tick=10 + 20 * k, cause=NavCause.OCCUPIED, ev=OCC_EV), 10 + 20 * k)
    assert (rec.cycle, rec.project_giveups) == (6, 0)
    mixed = _subject()
    counts = []
    for k, cause in enumerate((NavCause.OSCILLATION, NavCause.OSCILLATION, NavCause.OSCILLATION, NavCause.OCCUPIED, NavCause.OCCUPIED, NavCause.OSCILLATION)):
        mixed, rec = _file(mixed, _giveup(tick=10 + 5 * k, cause=cause, ev=OCC_EV if cause == NavCause.OCCUPIED else ()), 10 + 5 * k)
        counts.append(rec.project_giveups)
    assert counts == [1, 2, 3, 3, 3, 4]  # 3 OSCILLATION + 2 OCCUPIED + 1 OSCILLATION reaches the limit 4 at the 4th failure


def test_a_fresh_occupied_cycle_replaces_an_oscillation_record_and_a_later_oscillation_replaces_it_and_counts():
    e, osc = _file(_subject(), _giveup(tick=10), 10)
    assert osc.next_review_tick == 110
    e, occ = _file(e, _giveup(tick=20, cause=NavCause.OCCUPIED, ev=OCC_EV), 20)
    assert (occ.cause, occ.next_review_tick, occ.cycle, occ.project_giveups) == (NavCause.OCCUPIED, 30, 2, 1)  # the latest evidence decides the wait; the earlier failure stays counted
    _, again = _file(e, _giveup(tick=40), 40)
    assert (again.cause, again.next_review_tick, again.project_giveups) == (NavCause.OSCILLATION, 140, 2)
