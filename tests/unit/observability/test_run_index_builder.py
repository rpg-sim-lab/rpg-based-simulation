import os
import pytest
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.config import ObservabilityMode
from src.observability.reporting.run_set_repository import RunSetArtifactRepository
from src.observability.world_farm_io import RunDirectoryInUseError
from tests.named_run_dirs import remove_named_run_dirs  # noqa: F401

# Run ids this module's tests name, removed by name after each test (see tests/named_run_dirs.py).
RUN_ID_PREFIXES = {
    "test_index_builder_with_missing_and_failed_runs": ('test_resilient_sweep',),
}
pytestmark = pytest.mark.usefixtures("remove_named_run_dirs")


def test_index_builder_with_missing_and_failed_runs(tmp_path):
    output_dir = str(tmp_path / "run_sets")
    sweep_id = "test_resilient_sweep"
    
    # We will construct a minimal sweep configuration
    config = ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1, 2],
        ticks=5,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir
    )

    # Let's run a sweep. We know "idle" will complete successfully, but we want to assert
    # that if we manually delete run_report.json or manipulate directories, the index builder
    # fallback paths handle it gracefully.
    
    # 1. Run sweep to generate valid directories
    manifest = ScenarioSweeper.run_sweep(config)
    assert manifest.status == "COMPLETED"

    # Verify run index was generated
    repo = RunSetArtifactRepository(base_dir=output_dir)
    records = repo.read_run_index(sweep_id)
    assert len(records) == 2
    assert records[0].health_score >= 90.0  # Success fallback (allows light warning variance under slow virtualized CPU execution)

    # 2. Let's delete a run's manifest and report files to simulate corruption
    sweep_dir = os.path.join(output_dir, sweep_id)
    run_dir_1 = os.path.join(sweep_dir, "runs", "run_test_resilient_sweep_seed_1")
    manifest_file = os.path.join(run_dir_1, "run_manifest.json")
    report_file = os.path.join(run_dir_1, "run_report.json")
    
    if os.path.exists(manifest_file):
        os.remove(manifest_file)
    if os.path.exists(report_file):
        os.remove(report_file)

    # World farm: a sweep id that is in use belongs to that sweep, so running the same sweep again is refused and
    # nothing is regenerated or deleted. (This step used to re-run the same sweep id to recreate the files; that is
    # exactly the reuse the refusal forbids.) The index already written must still read cleanly with run 1's
    # manifest and report gone, and the refused re-run must leave the corrupted run dir as it was.
    with pytest.raises(RunDirectoryInUseError):
        ScenarioSweeper.run_sweep(config)
    assert not os.path.exists(manifest_file)
    assert not os.path.exists(report_file)

    records2 = repo.read_run_index(sweep_id)
    assert len(records2) == 2
    assert records2[0].run_id == "run_test_resilient_sweep_seed_1"
