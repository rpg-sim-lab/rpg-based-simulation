"""Two conformance verdicts that nothing in ``tests/`` proved (TCK-20261116-THE-SEMANTIC-DRIFT-CERTIFICATION-TEST-DOES-NOT-FAIL-ON-A-SLOW-RUNNER, Scope 5 and 6).

A search of ``tests/`` found no test naming "Tick budget violation", "Authoritative divergence" or FAILED_SEMANTIC_DRIFT; ``test_certification_detects_semantic_drift`` asserted only
its healthy half. These call ``ConformanceEvaluator.evaluate`` directly with injected measurements and hashes: no kernel, no wall clock."""
from __future__ import annotations

from src.certification.conformance import ConformanceEvaluator
from src.certification.models import FailureKind, MeasurementPoint
from src.certification.scenarios import get_scenario_expectations
from src.config.profiles import HardwareClass, RuntimeProfile


def _profile(budget_ms: float) -> RuntimeProfile:
    return RuntimeProfile(name="P", hardware_class=HardwareClass.CLASS_B, max_ram_mb=1_000_000, max_cpu_percent=50.0, max_worker_count=2, max_queue_depth=10,
                          max_replay_buffer_kb=0, max_tick_budget_ms=budget_ms, max_observability_budget_percent=5.0)


def _points(tick_ms: float):
    return [MeasurementPoint(tick=t, mode="NORMAL", memory_rss_mb=10.0, memory_trend_mb_per_tick=0.0, tick_compute_ms=tick_ms, tick_compute_ms_avg=tick_ms,
                             worker_utilization=0.0, queue_utilization=0.0, replay_pressure=0.0, active_workers=0) for t in (1, 2)]


def _evaluate(budget_ms: float, tick_ms: float, baseline: str = "h", final: str = "h", secondary: str = "h"):
    return ConformanceEvaluator.evaluate(_profile(budget_ms), get_scenario_expectations("DET_EQUIV"), _points(tick_ms), ["NORMAL", "NORMAL"], baseline, final, secondary)


def test_a_healthy_run_passes():
    passed, kind, reason, _allowed = _evaluate(10.0, 5.0)
    assert passed and kind == FailureKind.NONE, reason


def test_a_tick_above_one_and_a_half_budgets_fails_with_a_tick_budget_reason():
    passed, kind, reason, _allowed = _evaluate(10.0, 16.0)
    assert not passed and kind == FailureKind.FAILED_ENVELOPE and reason.startswith("Tick budget violation"), reason
    assert _evaluate(10.0, 15.0)[0], "15 ms is the limit itself (1.5 x 10)"


def test_a_budget_that_never_binds_passes_the_same_slow_tick():
    assert _evaluate(10000.0, 40.0)[0]


def test_a_final_hash_that_differs_from_the_baseline_fails_as_semantic_drift():
    passed, kind, reason, _allowed = _evaluate(10000.0, 1.0, baseline="aaa", final="bbb", secondary="bbb")
    assert not passed and kind == FailureKind.FAILED_SEMANTIC_DRIFT
    assert reason.startswith("Authoritative divergence from baseline") and "baseline=aaa" in reason and "final=bbb" in reason


def test_a_missing_hash_also_fails_as_semantic_drift():
    passed, kind, _reason, _allowed = _evaluate(10000.0, 1.0, baseline="", final="bbb", secondary="bbb")
    assert not passed and kind == FailureKind.FAILED_SEMANTIC_DRIFT
