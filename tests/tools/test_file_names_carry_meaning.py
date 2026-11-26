"""File names say what the file does: no bare internal codes (owner direction #715 7181423761; guideline docs/engine/architecture_reference.md section 9).

A bare internal code is a whole underscore/dot/hyphen-separated token of a `.py` or `.sh` basename under `tools/` or `tests/` that is `k<N>`, `phase<N>`, `step<N>`, `s<N>` or `f<N>` or `m<N>` (digits only after the letters),
or a `v<N>` token that comes FIRST (after an optional `test_`), as in `test_v8_fires.py`. A `v<N>` later in the name (`report_v2`, `icon_v2_keys`) is a version, not a code, and is not flagged; neither is a token that merely
contains a code (`k2fix`, `phase_one`). Data files (`.json`, `.yaml`) are not scanned.

`KNOWN_OFFENDERS` is the explicit list of files that existed when the rule landed (sorted); each is renamed later (the `test_phase<N>_*` files in batches, the ticket
TCK-20261126-RENAME-THE-TEST-PHASE-N-FILES-TO-NAMES-THAT-SAY-WHAT-THEY-TEST). A NEW offender fails this test; a renamed one must be removed from the list (the list is exact).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterator, List

REPO = Path(__file__).resolve().parents[2]
ROOTS = ("tools", "tests")
SCANNED_SUFFIXES = (".py", ".sh")
_CODE = re.compile(r"^(?:k|phase|step|s|f|m)\d+$")
_VERSION = re.compile(r"^v\d+$")
_SEPARATORS = re.compile(r"[_.\-]")

KNOWN_OFFENDERS = (
    "tests/api/test_phase27_behavior_query_api.py",
    "tests/architecture/test_phase18_cognition_migration_linter.py",
    "tests/architecture/test_phase18_import_boundaries.py",
    "tests/architecture/test_phase19_hot_path_safety_contract.py",
    "tests/architecture/test_phase19_observability_boundaries.py",
    "tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py",
    "tests/certification/test_phase10_enhanced_determinism_parity.py",
    "tests/certification/test_phase28_behavior_observability_rollout_gate.py",
    "tests/docs/test_phase4_direct_tool_comparison_doc.py",
    "tests/docs/test_phase4_workflow_recommendation_doc.py",
    "tests/docs/test_phase5_repeated_demand_measurement_doc.py",
    "tests/integration/campaigns/test_phase9_campaign_runner.py",
    "tests/integration/campaigns/test_phase9_life_arc_campaigns.py",
    "tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py",
    "tests/integration/domains/combat_engagement/test_phase4_combat_engagement_phase.py",
    "tests/integration/domains/cooperation/test_phase7_cooperation_phase.py",
    "tests/integration/domains/information/test_phase5_branch_b_realworld.py",
    "tests/integration/domains/information/test_phase5_information_belief_phase.py",
    "tests/integration/domains/memory/test_phase13_memory_update_phase.py",
    "tests/integration/domains/perception/test_phase12_perception_phase.py",
    "tests/integration/domains/progression/test_phase6_progression_conversion_phase.py",
    "tests/integration/domains/world_emergence/test_phase8_world_emergence_phase.py",
    "tests/integration/kernel/test_phase10_replay.py",
    "tests/integration/kernel/test_phase2_determinism.py",
    "tests/integration/kernel/test_substrate_freeze_m1.py",
    "tests/integration/observability/test_phase20_phase_timing_integration.py",
    "tests/integration/observability/test_phase21_non_blocking_event_emission.py",
    "tests/integration/observability/test_phase21_worker_failure_isolation.py",
    "tests/integration/observability/test_phase22_behavior_worker_from_jsonl.py",
    "tests/integration/observability/test_phase22_behavior_worker_from_stream.py",
    "tests/integration/observability/test_phase23_behavior_timeline_episode_artifacts.py",
    "tests/integration/observability/test_phase24_behavior_metric_artifacts.py",
    "tests/integration/observability/test_phase25_postrun_behavior_analysis.py",
    "tests/integration/observability/test_phase26_behavior_scorecard_artifacts.py",
    "tests/integration/observability/test_phase27_behavior_dataset_builder.py",
    "tests/integration/observability/test_phase28_observability_degradation.py",
    "tests/integration/observability/test_phase28_observability_determinism.py",
    "tests/integration/observability/test_v1_counts_an_unbacked_hunger_drop_through_the_real_kernel.py",
    "tests/integration/observability/test_v4_counts_a_forbidden_meal_through_the_real_kernel.py",
    "tests/integration/pipeline/test_phase5_idempotency.py",
    "tests/integration/scenarios/test_phase12_perception_attention_scenarios.py",
    "tests/integration/scenarios/test_phase13_temporal_causal_spatial_memory_scenarios.py",
    "tests/integration/scenarios/test_phase15_commitment_reputation_scenarios.py",
    "tests/integration/scenarios/test_phase16_emotion_recovery_habit_scenarios.py",
    "tests/integration/scenarios/test_phase17_decision_trace_scenarios.py",
    "tests/integration/scenarios/test_phase18_cognition_hierarchy_e2e.py",
    "tests/integration/scenarios/test_phase2_self_model_scenarios.py",
    "tests/integration/scenarios/test_phase3_adventure_decision_scenarios.py",
    "tests/integration/scenarios/test_phase4_combat_engagement_scenarios.py",
    "tests/integration/scenarios/test_phase5_information_belief_scenarios.py",
    "tests/integration/scenarios/test_phase6_progression_conversion_scenarios.py",
    "tests/integration/scenarios/test_phase7_social_cooperation_scenarios.py",
    "tests/integration/scenarios/test_phase8_world_emergence_scenarios.py",
    "tests/integration/world/test_phase9_stability.py",
    "tests/perf/test_phase28_behavior_observability_overhead.py",
    "tests/perf/test_phase2_self_model_budget.py",
    "tests/perf/test_phase3_adventure_decision_budget.py",
    "tests/perf/test_phase4_combat_engagement_budget.py",
    "tests/perf/test_phase5_information_belief_budget.py",
    "tests/perf/test_phase6_progression_conversion_budget.py",
    "tests/perf/test_phase7_social_cooperation_budget.py",
    "tests/perf/test_phase8_world_emergence_budget.py",
    "tests/perf/test_phase9_campaign_semantic_budget.py",
    "tests/simulation_quality/rpg_gate/test_v8_fires.py",
    "tests/tools/test_step0_ts_orchestrator.py",
    "tests/unit/cognition/test_phase2_capability_estimate_service.py",
    "tests/unit/cognition/test_phase2_knowledge_model_service.py",
    "tests/unit/cognition/test_phase2_need_interpretation_service.py",
    "tests/unit/cognition/test_phase2_self_assessment_service.py",
    "tests/unit/cognition/test_phase2_self_model_phase.py",
    "tests/unit/combat/test_phase5_combat_legality.py",
    "tests/unit/combat/test_phase5_negative_cases.py",
    "tests/unit/config/test_phase10_feature_flags.py",
    "tests/unit/config/test_phase19_observability_feature_flags.py",
    "tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py",
    "tests/unit/domains/adventure/test_phase3_adventure_decision_service.py",
    "tests/unit/domains/adventure/test_phase3_objective_intent_resolver.py",
    "tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py",
    "tests/unit/domains/adventure/test_phase3_route_families.py",
    "tests/unit/domains/adventure/test_phase3_route_generator.py",
    "tests/unit/domains/adventure/test_phase3_route_scoring.py",
    "tests/unit/domains/campaigns/test_phase9_behavior_change_proof_detector.py",
    "tests/unit/domains/campaigns/test_phase9_campaign_report_generator.py",
    "tests/unit/domains/campaigns/test_phase9_campaign_spec.py",
    "tests/unit/domains/campaigns/test_phase9_forbidden_behavior_detector.py",
    "tests/unit/domains/campaigns/test_phase9_life_arc_classifier.py",
    "tests/unit/domains/campaigns/test_phase9_route_diversity_analyzer.py",
    "tests/unit/domains/campaigns/test_phase9_semantic_campaign_scorecard.py",
    "tests/unit/domains/combat_engagement/test_phase4_combat_engagement_boundary.py",
    "tests/unit/domains/combat_engagement/test_phase4_combat_engagement_events.py",
    "tests/unit/domains/combat_engagement/test_phase4_combat_learning.py",
    "tests/unit/domains/combat_engagement/test_phase4_combat_postures.py",
    "tests/unit/domains/combat_engagement/test_phase4_combat_reassessment.py",
    "tests/unit/domains/combat_engagement/test_phase4_engagement_risk.py",
    "tests/unit/domains/combat_engagement/test_phase4_opponent_perception.py",
    "tests/unit/domains/combat_engagement/test_phase4_posture_selector.py",
    "tests/unit/domains/combat_engagement/test_phase4_posture_to_intent.py",
    "tests/unit/domains/combat_engagement/test_phase4_self_combat_estimate.py",
    "tests/unit/domains/commitment/test_phase15_abandonment_evaluator.py",
    "tests/unit/domains/commitment/test_phase15_commitment_pressure.py",
    "tests/unit/domains/commitment/test_phase15_reputation_update.py",
    "tests/unit/domains/commitment/test_phase15_route_impact.py",
    "tests/unit/domains/cooperation/test_phase7_cooperation_boundary.py",
    "tests/unit/domains/cooperation/test_phase7_cooperation_decision_service.py",
    "tests/unit/domains/cooperation/test_phase7_cooperation_events.py",
    "tests/unit/domains/cooperation/test_phase7_cooperation_intent_bridge.py",
    "tests/unit/domains/cooperation/test_phase7_cooperation_learning.py",
    "tests/unit/domains/cooperation/test_phase7_cooperation_postures.py",
    "tests/unit/domains/cooperation/test_phase7_help_need_evaluator.py",
    "tests/unit/domains/cooperation/test_phase7_partner_candidate_provider.py",
    "tests/unit/domains/cooperation/test_phase7_partner_fit_evaluator.py",
    "tests/unit/domains/cooperation/test_phase7_party_cohesion_service.py",
    "tests/unit/domains/cooperation/test_phase7_party_objective_alignment.py",
    "tests/unit/domains/emotion/test_phase16_emotion_update_service.py",
    "tests/unit/domains/emotion/test_phase16_emotional_model.py",
    "tests/unit/domains/emotion/test_phase16_habit_bias_service.py",
    "tests/unit/domains/emotion/test_phase16_habit_memory_model.py",
    "tests/unit/domains/emotion/test_phase16_opportunity_cost_evaluator.py",
    "tests/unit/domains/emotion/test_phase16_recovery_readiness_service.py",
    "tests/unit/domains/emotion/test_phase16_recovery_state_model.py",
    "tests/unit/domains/information/test_phase5_belief_contradiction.py",
    "tests/unit/domains/information/test_phase5_belief_route_impact.py",
    "tests/unit/domains/information/test_phase5_information_assimilation.py",
    "tests/unit/domains/information/test_phase5_information_belief_phase.py",
    "tests/unit/domains/information/test_phase5_information_boundary.py",
    "tests/unit/domains/information/test_phase5_information_events.py",
    "tests/unit/domains/information/test_phase5_information_intent_resolver.py",
    "tests/unit/domains/information/test_phase5_information_query_router.py",
    "tests/unit/domains/information/test_phase5_information_response_normalizer.py",
    "tests/unit/domains/information/test_phase5_information_source_profile.py",
    "tests/unit/domains/information/test_phase5_observation_belief_bridge.py",
    "tests/unit/domains/information/test_phase5_source_trust_update.py",
    "tests/unit/domains/memory/test_phase13_causal_attribution_service.py",
    "tests/unit/domains/memory/test_phase13_spatial_memory_update_service.py",
    "tests/unit/domains/motivation/test_phase14_motivation_models.py",
    "tests/unit/domains/motivation/test_phase14_role_fit_evaluator.py",
    "tests/unit/domains/perception/test_phase12_attention_focus_service.py",
    "tests/unit/domains/perception/test_phase12_perception_filter_service.py",
    "tests/unit/domains/perception/test_phase12_signal_salience_evaluator.py",
    "tests/unit/domains/progression/test_phase6_conversion_decision_service.py",
    "tests/unit/domains/progression/test_phase6_conversion_intent_bridge.py",
    "tests/unit/domains/progression/test_phase6_conversion_option_generator.py",
    "tests/unit/domains/progression/test_phase6_growth_gap_evaluator.py",
    "tests/unit/domains/progression/test_phase6_possession_understanding_service.py",
    "tests/unit/domains/progression/test_phase6_progression_boundary.py",
    "tests/unit/domains/progression/test_phase6_progression_events.py",
    "tests/unit/domains/progression/test_phase6_reward_interpretation_service.py",
    "tests/unit/domains/progression/test_phase6_reward_ledger_service.py",
    "tests/unit/domains/time/test_phase13_temporal_pressure_service.py",
    "tests/unit/domains/world_emergence/test_phase8_dynamic_quest_seed_service.py",
    "tests/unit/domains/world_emergence/test_phase8_regional_pressure_model.py",
    "tests/unit/domains/world_emergence/test_phase8_rumor_seed_service.py",
    "tests/unit/domains/world_emergence/test_phase8_scarcity_model.py",
    "tests/unit/domains/world_emergence/test_phase8_service_state_pressure.py",
    "tests/unit/domains/world_emergence/test_phase8_trauma_concern_bridge.py",
    "tests/unit/domains/world_emergence/test_phase8_world_emergence_boundary.py",
    "tests/unit/domains/world_emergence/test_phase8_world_emergence_events.py",
    "tests/unit/domains/world_emergence/test_phase8_world_event_aggregator.py",
    "tests/unit/domains/world_emergence/test_phase8_world_opportunity_pressure.py",
    "tests/unit/domains/world_emergence/test_phase8_world_to_entity_signal_bridge.py",
    "tests/unit/entity/test_phase11_cognition_model_schema.py",
    "tests/unit/entity/test_phase12_perception_model.py",
    "tests/unit/entity/test_phase13_temporal_model.py",
    "tests/unit/entity/test_phase2_self_model_components.py",
    "tests/unit/entity/test_phase6_possession_understanding_component.py",
    "tests/unit/entity/test_phase6_reward_ledger_component.py",
    "tests/unit/movement/test_phase4_movement.py",
    "tests/unit/observability/behavior/test_phase22_behavior_event_model.py",
    "tests/unit/observability/behavior/test_phase22_behavior_event_normalizer.py",
    "tests/unit/observability/behavior/test_phase23_behavior_episode_model.py",
    "tests/unit/observability/behavior/test_phase23_behavior_timeline_store.py",
    "tests/unit/observability/behavior/test_phase23_episode_detector.py",
    "tests/unit/observability/behavior/test_phase24_behavior_metric_window.py",
    "tests/unit/observability/behavior/test_phase24_behavior_metrics_aggregator.py",
    "tests/unit/observability/behavior/test_phase25_behavior_insight_generator.py",
    "tests/unit/observability/behavior/test_phase25_behavior_pattern_detectors.py",
    "tests/unit/observability/behavior/test_phase26_cohort_analyzer.py",
    "tests/unit/observability/behavior/test_phase26_entity_behavior_scorecard.py",
    "tests/unit/observability/behavior/test_phase26_run_behavior_comparison.py",
    "tests/unit/observability/behavior/test_phase26_run_behavior_scorecard.py",
    "tests/unit/observability/budget/test_phase28_observability_budget_profile.py",
    "tests/unit/observability/budget/test_phase28_sampling_policy.py",
    "tests/unit/observability/performance/test_phase20_metric_window_extension.py",
    "tests/unit/observability/performance/test_phase20_phase_profiler.py",
    "tests/unit/observability/reporting/test_phase27_behavior_artifact_paths.py",
    "tests/unit/observability/stream/test_phase21_bounded_observability_queue.py",
    "tests/unit/observability/test_phase17_causality_chain_reporter.py",
    "tests/unit/observability/test_phase17_decision_trace_contract.py",
    "tests/unit/observability/test_phase17_decision_trace_validator.py",
    "tests/unit/observability/test_phase8_m46_m47_m48.py",
    "tests/unit/observability/test_phase9_mining.py",
    "tests/unit/observability/warehouse/test_phase24_behavior_metric_ingestion.py",
    "tests/unit/observability/warehouse/test_phase27_behavior_warehouse_schema.py",
    "tests/unit/progression/test_phase8_progression.py",
    "tests/unit/social/test_contract_lifecycle_phase7.py",
    "tests/unit/social/test_social_phase7.py",
    "tests/unit/strategic/test_phase6_strategic_cognition.py",
    "tests/unit/views/test_phase17_derived_readiness_views.py",
    "tests/visual_assets/test_v2_terrain_aliases.py",
)


def has_bare_code(filename: str) -> bool:
    """True when the basename carries a bare internal code token (rule in the module docstring)."""
    stem, suffix = os.path.splitext(filename)
    if suffix not in SCANNED_SUFFIXES:
        return False
    tokens = [t for t in _SEPARATORS.split(stem) if t]
    if any(_CODE.match(t) for t in tokens):
        return True
    rest = tokens[1:] if tokens and tokens[0] == "test" else tokens
    return bool(rest) and bool(_VERSION.match(rest[0]))


def scan(repo: Path = REPO) -> Iterator[str]:
    for root in ROOTS:
        for directory, subdirs, files in os.walk(repo / root):
            subdirs[:] = sorted(d for d in subdirs if not d.startswith(".") and d != "__pycache__")
            for name in sorted(files):
                if has_bare_code(name):
                    yield (Path(directory) / name).relative_to(repo).as_posix()


def test_the_known_list_is_sorted_and_has_no_duplicates():
    assert list(KNOWN_OFFENDERS) == sorted(set(KNOWN_OFFENDERS))


def test_no_new_file_name_carries_a_bare_internal_code():
    found = sorted(scan())
    new = [f for f in found if f not in KNOWN_OFFENDERS]
    assert not new, f"file names must say what the file does; no bare internal codes (k<N>, phase<N>, step<N>, s<N>, f<N>, m<N>, a leading v<N>): rename {new}"


def test_the_known_list_holds_only_files_that_still_exist_and_still_offend():
    found = set(scan())
    stale = [f for f in KNOWN_OFFENDERS if f not in found]
    assert not stale, f"renamed or deleted: remove from KNOWN_OFFENDERS: {stale}"


def test_the_renamed_measurement_and_release_files_are_not_known_offenders():
    for name in ("need_project_cleared_trace_spy.py", "escalated_need_switch_ownjob_spy.py", "inn_refusal_blocker_ownjob_spy.py", "service_refusal_and_need_switch_count_spy.py", "rollout_report_gate.py", "test_rollout_report_gate.py"):
        assert not has_bare_code(name)
        assert not any(k.endswith("/" + name) for k in KNOWN_OFFENDERS)


# ---- planted positives and negatives
def test_planted_positives_are_flagged():
    for name in ("test_phase10_enhanced_rollout_gate.py", "k3_switch_spy.py", "k2_probe.py", "run_step0.sh", "f2_gate.py", "m1_check.py", "s9_run.sh", "test_v8_fires.py", "v3_kit.py", "x.k4.y.py"):
        assert has_bare_code(name), name


def test_planted_negatives_are_not_flagged():
    for name in ("test_report_v2.py", "test_icon_v2_keys.py", "k2fix_probe.py", "phase_one_gate.py", "step_by_step.py", "need_project_cleared_trace_spy.py", "rollout_report_gate.py", "test_substrate_freeze.py",
                 "resource_100_local.v0001.json", "k3_notes.md", "pipeline.py", "stats.py", "schema_v.py", "test_vector.py"):
        assert not has_bare_code(name), name


def test_the_scan_sees_a_planted_new_offender_and_ignores_pycache(tmp_path):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__pycache__").mkdir()
    (tmp_path / "tests" / "__pycache__" / "test_phase3_x.py").write_text("")
    (tmp_path / "tests" / "test_phase3_new_thing.py").write_text("")
    (tmp_path / "tests" / "test_says_what_it_tests.py").write_text("")
    assert list(scan(tmp_path)) == ["tests/test_phase3_new_thing.py"]
