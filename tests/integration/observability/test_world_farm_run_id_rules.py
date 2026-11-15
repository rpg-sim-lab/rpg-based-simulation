"""World farm step one (T6, T7): sweeps and mining refuse an id in use, and a run id is a name only."""

import json
import os
from pathlib import Path

import pytest

from src.observability.config import ObservabilityMode
from src.observability.mining.controller import MiningExperimentConfig, MiningExperimentController
from src.observability.sweeper import ScenarioSweepConfig, ScenarioSweeper
from src.observability.world_farm_io import RunDirectoryInUseError


def _sweep(sweep_id: str, output_dir: str, seeds=(1,), ticks: int = 3) -> ScenarioSweepConfig:
    return ScenarioSweepConfig(
        sweep_id=sweep_id,
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=list(seeds),
        ticks=ticks,
        observability_mode=ObservabilityMode.LIGHT,
        output_dir=output_dir,
    )


def _mining(experiment_id: str, output_dir: str) -> MiningExperimentConfig:
    return MiningExperimentConfig(
        experiment_id=experiment_id,
        experiment_type="multi_seed_sweep",
        scenario_name="idle",
        scenario_type="sandbox",
        seeds=[1],
        ticks=3,
        output_dir=output_dir,
    )


def test_sweep_refuses_an_existing_sweep_dir_and_keeps_its_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "sets" / "farm_sweep"
    existing.mkdir(parents=True)
    (existing / "keep.txt").write_text("first sweep", encoding="utf-8")
    with pytest.raises(RunDirectoryInUseError):
        ScenarioSweeper.run_sweep(_sweep("farm_sweep", str(tmp_path / "sets")))
    assert (existing / "keep.txt").read_text(encoding="utf-8") == "first sweep"


def test_sweep_refuses_an_existing_data_runs_dir_and_keeps_its_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    held = tmp_path / "data" / "runs" / "run_farm_sweep_seed_1"
    held.mkdir(parents=True)
    (held / "keep.txt").write_text("another run", encoding="utf-8")
    with pytest.raises(RunDirectoryInUseError):
        ScenarioSweeper.run_sweep(_sweep("farm_sweep", str(tmp_path / "sets")))
    assert (held / "keep.txt").read_text(encoding="utf-8") == "another run"
    assert not (tmp_path / "sets" / "farm_sweep").exists()  # nothing was created before the refusal


def test_mining_refuses_an_existing_experiment_dir_and_keeps_its_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "mining" / "farm_exp"
    existing.mkdir(parents=True)
    (existing / "keep.txt").write_text("first experiment", encoding="utf-8")
    with pytest.raises(RunDirectoryInUseError):
        MiningExperimentController.execute_experiment(_mining("farm_exp", str(tmp_path / "mining")))
    assert (existing / "keep.txt").read_text(encoding="utf-8") == "first experiment"


def test_mining_refuses_an_existing_data_runs_dir_and_keeps_its_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    held = tmp_path / "data" / "runs" / "run_farm_exp_seed_1"
    held.mkdir(parents=True)
    (held / "keep.txt").write_text("another run", encoding="utf-8")
    with pytest.raises(RunDirectoryInUseError):
        MiningExperimentController.execute_experiment(_mining("farm_exp", str(tmp_path / "mining")))
    assert (held / "keep.txt").read_text(encoding="utf-8") == "another run"
    assert not (tmp_path / "mining" / "farm_exp").exists()


def _final_state_hash(sets_dir: Path, sweep_id: str, seed: int) -> str:
    run_dir = sets_dir / sweep_id / "runs" / f"run_{sweep_id}_seed_{seed}"
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["state_hash"], "the run recorded no final state hash"
    return manifest["state_hash"]


def test_the_run_id_is_a_name_only_the_same_seed_gives_the_same_final_hash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("data/runs")
    hashes = []
    for sweep_id in ("farm_name_one", "farm_name_two_is_longer"):
        manifest = ScenarioSweeper.run_sweep(_sweep(sweep_id, str(tmp_path / "sets"), seeds=(7,), ticks=20))
        assert manifest.status == "COMPLETED"
        hashes.append(_final_state_hash(tmp_path / "sets", sweep_id, 7))
    assert hashes[0] == hashes[1]
