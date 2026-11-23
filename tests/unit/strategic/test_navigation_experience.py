"""The #996 rework, step (c) (design section 2.2): the navigation experience memory. A record is typed, canonical and hashed; the one update applies reviews (only of the stored cycle, only while ACTIVE),
upserts (only over a lower stored cycle) and evictions, deterministically; the patch layers it over whatever cognition the same update stages; an older state loads empty. Each rule has a failing control."""
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.cognition import MemoryModel
from src.core.navigation_experience import (
    ExperienceReview,
    NavCause,
    NavExperienceStatus,
    NavigationExperience,
    NavigationExperienceMemory,
    NavigationExperienceUpdate,
    RingEvidence,
    ReviewReason,
    apply_experience_update,
    experience_id_of,
    ring_evidence_of,
)
from src.core.navigation_purpose import TargetPurpose
from src.core.state import AuthoritativeState
from src.core.enums import ReasonCode
from src.core.updates import EntityUpdate
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.checkpoint_fields import FIELD_RULES
from src.engine.patches import NavigationExperiencePatch, extract_patches

P = TargetPurpose("hunger", "WANDER")


def _rec(x=9, y=5, cycle=1, status=NavExperienceStatus.ACTIVE, purpose=P, cause=NavCause.OSCILLATION, observed=10):
    return NavigationExperience(
        experience_id=experience_id_of((x, y), purpose), anchor=(x, y), purpose=purpose, cause=cause, ring_evidence=(), from_position=(3, 3), target_tile=(x, y), need_services=frozenset(), project_id="p1",
        observed_tick=observed, cycle=cycle, next_review_tick=observed + 100, status=status, reviewed_tick=None, review_reason=None, project_giveups=1)


def test_the_id_is_built_from_the_tile_and_the_purpose_values_only():
    assert experience_id_of((9, 5), P) == "nx_9_5_hunger_WANDER"
    assert experience_id_of((9, 5), TargetPurpose("none", "PURSUE")) == "nx_9_5_none_PURSUE"


def test_ring_evidence_maps_each_refusal_code_and_orders_the_result():
    assert ring_evidence_of([ReasonCode.OCCUPANCY_VIOLATION, ReasonCode.IDEMPOTENCY_VIOLATION]) == (RingEvidence.BODIES,)
    assert ring_evidence_of([ReasonCode.ACTION_EXHAUSTION, ReasonCode.OCCUPANCY_VIOLATION]) == (RingEvidence.BODIES, RingEvidence.OTHER)
    assert ring_evidence_of([ReasonCode.LEGAL]) == ()
    static = [c for c in ReasonCode if c not in (ReasonCode.LEGAL, ReasonCode.OCCUPANCY_VIOLATION, ReasonCode.IDEMPOTENCY_VIOLATION, ReasonCode.ACTION_EXHAUSTION, ReasonCode.ATTACKER_STATUS_BLOCKED, ReasonCode.INSUFFICIENT_READINESS)]
    assert ring_evidence_of([static[0]]) == (RingEvidence.STATIC,)  # any other refusal is the static obstruction


def test_an_upsert_adds_and_a_higher_cycle_replaces_but_a_lower_or_equal_one_does_not():
    empty = NavigationExperienceMemory()
    one = apply_experience_update(empty, NavigationExperienceUpdate(upserts=(_rec(cycle=1),)))
    assert [r.cycle for r in one.records] == [1]
    two = apply_experience_update(one, NavigationExperienceUpdate(upserts=(_rec(cycle=2, observed=300),)))
    assert two.records[0].cycle == 2 and two.records[0].observed_tick == 300
    again = apply_experience_update(two, NavigationExperienceUpdate(upserts=(_rec(cycle=2, observed=999), _rec(cycle=1))))
    assert again == two  # failing control: an equal or lower cycle changes nothing


def test_a_review_applies_only_to_the_stored_cycle_and_only_while_active_and_a_new_cycle_supersedes_it():
    mem = apply_experience_update(NavigationExperienceMemory(), NavigationExperienceUpdate(upserts=(_rec(cycle=2),)))
    rid = mem.records[0].experience_id
    stale = apply_experience_update(mem, NavigationExperienceUpdate(reviews=(ExperienceReview(rid, 1, 50, ReviewReason.DUE_TICK),)))
    assert stale == mem  # a review of cycle 1 does not touch cycle 2
    reviewed = apply_experience_update(mem, NavigationExperienceUpdate(reviews=(ExperienceReview(rid, 2, 50, ReviewReason.DUE_TICK),)))
    r = reviewed.records[0]
    assert r.status == NavExperienceStatus.REVIEWED and r.reviewed_tick == 50 and r.review_reason == ReviewReason.DUE_TICK
    twice = apply_experience_update(reviewed, NavigationExperienceUpdate(reviews=(ExperienceReview(rid, 2, 99, ReviewReason.APPROACH_CHANGED),)))
    assert twice == reviewed  # idempotent: a review of a REVIEWED record changes nothing
    both = apply_experience_update(mem, NavigationExperienceUpdate(reviews=(ExperienceReview(rid, 2, 50, ReviewReason.DUE_TICK),), upserts=(_rec(cycle=3),)))
    assert both.records[0].cycle == 3 and both.records[0].status == NavExperienceStatus.ACTIVE  # the next cycle supersedes the review of the last


def test_evictions_remove_the_named_ids_and_records_come_out_sorted_by_id():
    a, b, c = _rec(9, 5), _rec(2, 2), _rec(4, 4)
    mem = apply_experience_update(NavigationExperienceMemory(), NavigationExperienceUpdate(upserts=(a, b, c)))
    assert [r.experience_id for r in mem.records] == sorted(r.experience_id for r in (a, b, c))
    after = apply_experience_update(mem, NavigationExperienceUpdate(evictions=(b.experience_id,)))
    assert b.experience_id not in [r.experience_id for r in after.records] and len(after.records) == 2


def test_the_update_merge_unions_and_a_noop_merges_to_itself():
    u = NavigationExperienceUpdate(upserts=(_rec(),))
    assert u.merge(NavigationExperienceUpdate()) is u and NavigationExperienceUpdate().is_noop() and not u.is_noop()
    merged = u.merge(NavigationExperienceUpdate(evictions=("nx_1_1_none_WANDER",)))
    assert len(merged.upserts) == 1 and merged.evictions == ("nx_1_1_none_WANDER",)


def _entity_with(*records):
    e = V2EntityBuilder(1).kind("HERO").location(5.0, 5.0).build()
    memory = replace(e.cognition.memory, navigation=NavigationExperienceMemory(tuple(records)))
    return replace(e, cognition=replace(e.cognition, memory=memory))


def test_the_memory_form_is_omitted_while_empty_and_hashed_once_it_holds_a_record():
    assert "navigation" not in MemoryModel().to_canonical_dict()
    e = _entity_with(_rec())
    assert e.cognition.memory.to_canonical_dict()["navigation"]["records"][0]["experience_id"] == "nx_9_5_hunger_WANDER"
    plain, held, held2 = (CanonicalStateHasher.get_hash(AuthoritativeState(entities={1: x}, tick=3, seed=1)) for x in (_entity_with(), _entity_with(_rec()), _entity_with(_rec(cycle=2))))
    assert plain != held and held != held2  # an in-type change of a field moves the hash


def test_the_patch_applies_the_update_to_the_entitys_memory_and_layers_over_a_staged_cognition():
    e = _entity_with()
    upd = EntityUpdate(entity_id=1, navigation_experience=NavigationExperienceUpdate(upserts=(_rec(),)))
    patches = [p for p in extract_patches(1, upd) if isinstance(p, NavigationExperiencePatch)]
    assert len(patches) == 1
    changes = {}
    patches[0].apply(e, changes)
    assert [r.experience_id for r in changes["cognition"].memory.navigation.records] == ["nx_9_5_hunger_WANDER"]
    staged = replace(e.cognition, memory=replace(e.cognition.memory, navigation=NavigationExperienceMemory((_rec(2, 2),))))
    layered = {"cognition": staged}
    patches[0].apply(e, layered)
    assert sorted(r.experience_id for r in layered["cognition"].memory.navigation.records) == ["nx_2_2_hunger_WANDER", "nx_9_5_hunger_WANDER"]
    assert not [p for p in extract_patches(1, EntityUpdate(entity_id=1)) if isinstance(p, NavigationExperiencePatch)]  # failing control: no update, no patch


def test_an_older_state_loads_the_empty_memory():
    rule = next(r for r in FIELD_RULES if r.record == "MemoryModel" and r.field == "navigation")
    assert rule.fill(None, None) == NavigationExperienceMemory() and rule.ruling


def test_need_services_are_a_sorted_list_of_values_in_the_canonical_form_and_move_the_hash():
    from src.core.navigation_experience import NeedService
    both = replace(_rec(), need_services=frozenset({NeedService.REST, NeedService.EAT}))
    assert both.to_canonical()["need_services"] == ["EAT", "REST"] and _rec().to_canonical()["need_services"] == []
    plain, with_need = (CanonicalStateHasher.get_hash(AuthoritativeState(entities={1: _entity_with(r)}, tick=3, seed=1)) for r in (_rec(), both))
    assert plain != with_need  # an in-type change of the set is hashed
