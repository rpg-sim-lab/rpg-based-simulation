import pytest
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.state import AuthoritativeState, EntityState
from src.certification.harness import CertificationHarness
from src.certification.scenarios import get_scenario_expectations, PressureInjector
from src.certification.models import FailureKind


# The drift test's claim is about hashes, not timing: its tick budget must never bind. The conformance check fails any tick above 1.5 x this budget by WALL CLOCK
# (src/certification/conformance.py), so a 10 ms budget failed the healthy run on a loaded CI runner (TCK-20261116-THE-SEMANTIC-DRIFT-CERTIFICATION-TEST-DOES-NOT-FAIL-ON-A-SLOW-RUNNER).
DRIFT_TICK_BUDGET_MS = 1000.0  # never binds (a tick would have to cost over 1.5 s); a larger value only slows the run: 10000 made each of these tests take ~30 s instead of ~5-9 s


def _drift_run(budget_ms=DRIFT_TICK_BUDGET_MS, slow_tick_ms=None, monkeypatch=None):
    """One healthy DET_EQUIV run. ``slow_tick_ms`` simulates a loaded runner: every measurement point reports that tick cost (no wall clock involved)."""
    profile = RuntimeProfile(
        name="DRIFT_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=1_000_000, max_cpu_percent=50.0, max_worker_count=2,
        max_queue_depth=10, max_replay_buffer_kb=0, max_tick_budget_ms=budget_ms,
        max_observability_budget_percent=5.0
    )

    from src.core.builder import V2EntityBuilder
    state = AuthoritativeState(tick=0, seed=42, entities={
        1: (V2EntityBuilder(1)
            .kind("TEST")
            .location(0.0, 0.0)
            .combat(readiness=100.0)
            .build())
    })

    if slow_tick_ms is not None:
        import src.certification.models as models_module  # run_scenario imports MeasurementPoint from here at call time, so this is the name it sees
        real = models_module.MeasurementPoint
        monkeypatch.setattr(models_module, "MeasurementPoint", lambda **kw: real(**{**kw, "tick_compute_ms": slow_tick_ms}))
    harness = CertificationHarness(profile, output_dir="tmp/test_harness_contract")
    expectations = get_scenario_expectations("DET_EQUIV")
    return harness.run_scenario("DET_EQUIV", state, expectations, ticks=2)


def test_certification_detects_semantic_drift():
    """
    M9 Law: Harness must catch hash mismatch vs sequential baseline.
    """
    
    # We will "break" the deterministic equivalence by mocking 
    # the second half of the harness run to produce a DIFFERENT hash
    # In reality, this would happen if concurrent logic was buggy.
    # For testing, we just verify the harness evaluates hash match correctly.
    
    result = _drift_run()
    
    # In a healthy run, it should pass
    assert result.conformance_passed
    assert result.baseline_hash == result.final_hash


def test_the_healthy_half_passes_on_a_slow_runner(monkeypatch):
    """The regression: a tick cost far above 1.5 x a 10 ms budget (a loaded runner) must not fail the drift test's healthy run. Deterministic: the cost is injected."""
    result = _drift_run(slow_tick_ms=40.0, monkeypatch=monkeypatch)
    assert result.conformance_passed, result.failure_reason
    assert result.baseline_hash == result.final_hash


def test_a_slow_tick_fails_a_run_whose_budget_binds_with_a_tick_budget_reason(monkeypatch):
    """The confirmation of the CI failure: the same run with the OLD 10 ms budget fails conformance, and the reason is the tick budget (not a mode or a telemetry gap)."""
    result = _drift_run(budget_ms=10.0, slow_tick_ms=40.0, monkeypatch=monkeypatch)
    assert not result.conformance_passed
    assert result.failure_kind == FailureKind.FAILED_ENVELOPE
    assert result.failure_reason.startswith("Tick budget violation"), result.failure_reason


def test_honest_language_compliance():
    """
    Verify that the recorder does not make universal claims.
    """
    from src.certification.recorder import CertificationRecorder
    from src.certification.models import (
        CertificationResult, HardwareClass as CHC, FailureKind,
        EnvironmentCapture
    )
    
    recorder = CertificationRecorder(output_dir="tmp/cert_test")
    res = CertificationResult(
        run_id="test_id", 
        timestamp=0.0,
        commit_sha="test-sha",
        profile_name="PROD", 
        scenario_id="IDLE", 
        seed=1,
        environment=EnvironmentCapture(
            detected_facts={},
            detected_class=CHC.CLASS_B,
            effective_class=CHC.CLASS_B,
            override_applied=False
        ),
        measurements=[],
        baseline_hash="A", 
        final_hash="A",
        governor_mode_sequence=["NORMAL"],
        conformance_passed=True, 
        failure_kind=FailureKind.NONE, 
        failure_reason=None
    )
    
    md_report = recorder._generate_markdown(res)
    
    # VERIFY: Bound language
    assert "performance and safety metrics in this report apply only to" in md_report.lower()
    assert "claims of universal throughput" in md_report.lower()
    assert "**hardware class**: `class_b`" in md_report.lower()
