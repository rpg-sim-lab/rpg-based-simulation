# Compliance IDs: SOC-280
"""A social update keeps the rejection counts it does not name, and the merge sums the increment.

TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME.
Before the fix, RelationshipService.process_update rebuilt `rejection_count` from the update's increment alone, so any
applied SocialUpdate (a trust-only one included) dropped every other offerer's count, and SocialUpdate.merge kept only the
last writer's increment per key.
"""
from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState
from src.core.strategic import ContractKind, ContractState, ContractStatus
from src.core.updates import EntityUpdate, SocialUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.systems.social_systems.appraisal import SocialAppraisalSystem


def _apply(state: AuthoritativeState, social: SocialUpdate) -> AuthoritativeState:
    update = StateUpdate(entity_updates={1: EntityUpdate(entity_id=1, social=social)})
    return ApplyPath.apply_generation(state, update)


def _state(rejection_count):
    entity = V2EntityBuilder(1).kind("human").location(0, 0).social(rejection_count=rejection_count).build()
    return AuthoritativeState(tick=1, seed=1, entities={1: entity})


def test_a_trust_only_update_leaves_the_rejection_counts_intact():
    state = _state({10: 3, 11: 1})
    after = _apply(state, SocialUpdate(trust_delta={99: 0.2}))
    assert after.entities[1].social.rejection_count == {10: 3, 11: 1}


def test_an_increment_for_one_offerer_keeps_the_other_offerers_count():
    state = _state({10: 3, 11: 1})
    after = _apply(state, SocialUpdate(rejection_increment={10: 1}))
    assert after.entities[1].social.rejection_count == {10: 4, 11: 1}


def test_an_increment_for_a_new_offerer_is_added_beside_the_existing_counts():
    state = _state({10: 3})
    after = _apply(state, SocialUpdate(rejection_increment={12: 1}))
    assert after.entities[1].social.rejection_count == {10: 3, 12: 1}


def test_merge_sums_two_same_tick_rejections_from_one_offerer():
    merged = SocialUpdate(rejection_increment={10: 1}).merge(SocialUpdate(rejection_increment={10: 1}))
    assert merged.rejection_increment == {10: 2}


def test_merge_keeps_two_offerers_separate():
    merged = SocialUpdate(rejection_increment={10: 1}).merge(SocialUpdate(rejection_increment={11: 1}))
    assert merged.rejection_increment == {10: 1, 11: 1}


def test_two_merged_same_tick_rejections_apply_as_two():
    state = _state({10: 1})
    merged = SocialUpdate(rejection_increment={10: 1}).merge(SocialUpdate(rejection_increment={10: 1}))
    after = _apply(state, merged)
    assert after.entities[1].social.rejection_count == {10: 3}


def test_merge_does_not_sum_the_other_fields():
    # familiarity stays last-writer-wins per key; only the rejection increment sums (designer ruling).
    merged = SocialUpdate(familiarity_delta={5: 0.1}).merge(SocialUpdate(familiarity_delta={5: 0.1}))
    assert merged.familiarity_delta == {5: 0.1}


def test_kept_counts_round_trip_through_the_canonical_dict():
    state = _state({10: 3, 11: 1})
    after = _apply(state, SocialUpdate(trust_delta={99: 0.2}, rejection_increment={11: 1}))
    canon = after.entities[1].to_canonical_dict()["social"]["rejection_count"]
    assert canon == {"10": 3, "11": 2}


def test_the_fatigue_penalty_reads_the_count_kept_across_an_unrelated_update():
    state = _state({10: 3})
    state = _apply(state, SocialUpdate(trust_delta={99: 0.2}))
    recruiter = V2EntityBuilder(10).kind("human").location(1, 1).combat(readiness=100.0).build()
    state = AuthoritativeState(tick=1, seed=1, entities={1: state.entities[1], 10: recruiter})
    contract = ContractState(
        id="rec", kind=ContractKind.RECRUITMENT, source_id=10, target_id=1,
        terms={"daily_pay": 10}, status=ContractStatus.OFFERED,
    )
    status, _reason, _ = SocialAppraisalSystem.appraise_contract(state.entities[1], contract, state)
    assert status == ContractStatus.CANCELLED  # 3 kept rejections: penalty 0.3 cancels a fair-pay offer
