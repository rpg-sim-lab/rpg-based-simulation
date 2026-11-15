"""A run records the conditions it was built under, and a classifier derives PINNED / NOT_PINNED from that record alone
(TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE).

The kernel writes ``run_conditions`` (governor, executor, tick budget, audit mode, frame pacing) into the manifest once, after it has chosen its executor. It is run
setup, not state: the record changes neither the state hash nor the event stream, an older manifest without it still loads, and
``tools/test_architecture/pinned_runner.py`` holds the one PINNED definition that the classifier, the evidence helper and ``tools/rpg_measure/arm_child.py`` read.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.config.profiles import PROD_SMALL
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.executor import LocalSequentialExecutor
from src.engine.governor import ResourceGovernor
from src.engine.kernel import Kernel
from src.observability.reporting.artifact_repository import RunArtifactRepository, RunConditions, RunManifest
from src.platform.rng import DeterministicRNG
from tests.helpers.kernel_pinning import PinnedNormalGovernor
from tests.helpers.scenario import compile_world
from tools.test_architecture import pinned_runner as pr


TICKS = 6
PINNED_RECORD = {
    "governor": "tests.helpers.kernel_pinning.PinnedNormalGovernor",
    "executor": "src.engine.executor.LocalSequentialExecutor",
    "max_tick_budget_ms": 1e9,
    "audit_mode": True,
    "no_frame_pacing": True,
}


def _run(tmp_path: Path, *, pinned: bool, run_id: str, ticks: int = TICKS):
    """One short run of a real world; returns (manifest as saved, final state hash, the kernel). The run directory is removed afterwards."""
    state = compile_world("urban_political", 42)
    if pinned:
        kernel = Kernel(PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state, DeterministicRNG(42), governor=PinnedNormalGovernor(),
                        executor=LocalSequentialExecutor(), flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id)
    else:  # the shape of tools.calibrate_simq._run_engine: default governor, default executor, the profile's own budget
        kernel = Kernel(PROD_SMALL, state, DeterministicRNG(42), governor=ResourceGovernor(), flags={"no_frame_pacing": True}, run_id=run_id)
    repo = kernel._artifact_repo
    for _ in range(ticks):
        kernel.tick_once()
    digest = CanonicalStateHasher.get_hash(kernel.state)
    kernel.shutdown()
    manifest = json.loads(Path(repo.base_dir, run_id, "run_manifest.json").read_text(encoding="utf-8"))
    return manifest, digest, kernel


@pytest.fixture
def cleanup():
    ids = []
    yield ids
    import shutil

    for run_id in ids:
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


# --------------------------------------------------------------------------------------------- the kernel writes the record
def test_a_pinned_build_records_its_conditions_and_classifies_pinned(tmp_path, cleanup):
    cleanup.append("rc_unit_pinned")
    manifest, _, _ = _run(tmp_path, pinned=True, run_id="rc_unit_pinned")
    assert manifest["run_conditions"] == PINNED_RECORD
    assert pr.classify_manifest(manifest).verdict == "PINNED"


def test_a_default_build_records_what_it_has_and_classifies_not_pinned(tmp_path, cleanup):
    cleanup.append("rc_unit_default")
    manifest, _, _ = _run(tmp_path, pinned=False, run_id="rc_unit_default")
    rc = manifest["run_conditions"]
    assert rc["governor"] == "src.engine.governor.ResourceGovernor"
    assert rc["executor"].startswith("src.engine.executor.") and rc["executor"] != PINNED_RECORD["executor"] or rc["executor"] == "src.engine.executor.LocalSequentialExecutor"
    assert rc["max_tick_budget_ms"] == PROD_SMALL.max_tick_budget_ms and rc["audit_mode"] is False
    verdict = pr.classify_manifest(manifest)
    assert verdict.verdict == "NOT_PINNED"
    assert any("governor" in d for d in verdict.differences) and any("max_tick_budget_ms" in d for d in verdict.differences) and any("audit_mode" in d for d in verdict.differences)


def test_the_record_is_run_setup_only_it_changes_neither_the_state_hash_nor_the_events(tmp_path, cleanup, monkeypatch):
    cleanup.extend(["rc_unit_with", "rc_unit_without"])
    with_record, hash_with, _ = _run(tmp_path, pinned=True, run_id="rc_unit_with")
    events_with = _events("rc_unit_with")
    original = RunArtifactRepository.update_manifest

    def without(self, run_id, **kwargs):  # the same kernel, with the one new write dropped
        kwargs.pop("run_conditions", None)
        return original(self, run_id, **kwargs)

    monkeypatch.setattr(RunArtifactRepository, "update_manifest", without)
    without_record, hash_without, _ = _run(tmp_path, pinned=True, run_id="rc_unit_without")
    assert with_record["run_conditions"] is not None and without_record["run_conditions"] is None
    assert hash_with == hash_without
    assert events_with and events_with == _events("rc_unit_without")


def _events(run_id: str) -> list:
    path = Path("data") / "runs" / run_id / "simulation_events.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []
    volatile = ("run_id", "event_id", "timestamp", "ts", "wall_time", "emitted_at", "created_at", "elapsed_ms", "compute_ms")

    def scrub(v):
        if isinstance(v, dict):
            return {k: scrub(x) for k, x in v.items() if k not in volatile and not k.endswith(("_ms", "_at"))}
        return [scrub(x) for x in v] if isinstance(v, list) else v

    return [scrub(r) for r in rows]


# --------------------------------------------------------------------------------------------- the manifest
def test_the_manifest_round_trips_the_record():
    rc = RunConditions(**PINNED_RECORD)
    manifest = RunManifest(run_id="r", scenario_name="s", scenario_type="t", seed=1, observability_mode="FULL", started_at="x", ticks_requested=1, run_conditions=rc)
    again = RunManifest.model_validate_json(manifest.model_dump_json())
    assert again.run_conditions == rc and again == manifest


def test_an_older_manifest_without_the_field_loads_and_classifies_not_pinned():
    old = {"run_id": "r", "scenario_name": "s", "scenario_type": "t", "seed": 1, "observability_mode": "FULL", "started_at": "x", "ticks_requested": 1}
    manifest = RunManifest.model_validate(old)
    assert manifest.run_conditions is None
    verdict = pr.classify_manifest(manifest.model_dump())
    assert verdict.verdict == "NOT_PINNED" and "no run_conditions record" in verdict.differences[0]


# --------------------------------------------------------------------------------------------- the one PINNED definition
@pytest.mark.parametrize(
    "change, word",
    [
        ({"governor": "src.engine.governor.ResourceGovernor"}, "governor"),
        ({"executor": "src.engine.executor.ConcurrentExecutionAdapter"}, "executor"),
        ({"max_tick_budget_ms": 100.0}, "max_tick_budget_ms"),
        ({"audit_mode": False}, "audit_mode"),
        ({"no_frame_pacing": False}, "no_frame_pacing"),
    ],
)
def test_each_condition_alone_makes_a_run_not_pinned(change, word):
    verdict = pr.classify({**PINNED_RECORD, **change})
    assert verdict.verdict == "NOT_PINNED" and len(verdict.differences) == 1 and word in verdict.differences[0]


def test_the_pinned_record_and_a_larger_budget_classify_pinned():
    assert pr.classify(PINNED_RECORD).pinned and pr.classify({**PINNED_RECORD, "max_tick_budget_ms": 5e9}).pinned


def test_a_missing_or_empty_record_is_not_pinned():
    assert pr.classify(None).verdict == "NOT_PINNED" and pr.classify({}).verdict == "NOT_PINNED"


def test_the_pinned_definition_matches_what_build_kernel_builds(cleanup):
    """PINNED is read by the classifier and arm_child alike; this ties it to the builder so the two cannot drift apart."""
    from tools.test_architecture.rpg_gate_run import build_kernel

    cleanup.append("rc_unit_build_kernel")
    kernel = build_kernel("urban_political", 42, "rc_unit_build_kernel")
    repo = kernel._artifact_repo
    kernel.shutdown()
    record = json.loads(Path(repo.base_dir, "rc_unit_build_kernel", "run_manifest.json").read_text(encoding="utf-8"))
    assert pr.classify_manifest(record).verdict == "PINNED"


# --------------------------------------------------------------------------------------------- the helper refuses
def test_the_evidence_helper_returns_a_pinned_run_and_refuses_the_other():
    pinned = {"run_id": "p", "run_conditions": PINNED_RECORD}
    assert pr.evidence_row(pinned, hits=3) == {"hits": 3, "runner": "PINNED", "run_id": "p"}
    other = {"run_id": "o", "run_conditions": {**PINNED_RECORD, "governor": "src.engine.governor.ResourceGovernor"}}
    with pytest.raises(pr.NotPinnedError, match="NOT_PINNED.*governor"):
        pr.evidence_row(other, hits=3)
    with pytest.raises(pr.NotPinnedError):
        pr.require_pinned({"run_id": "old"})


def test_the_command_line_exits_one_for_a_run_that_is_not_pinned(tmp_path, capsys):
    good, bad = tmp_path / "good.json", tmp_path / "bad.json"
    good.write_text(json.dumps({"run_conditions": PINNED_RECORD}), encoding="utf-8")
    bad.write_text(json.dumps({"run_conditions": {**PINNED_RECORD, "audit_mode": False}}), encoding="utf-8")
    assert pr.main([str(good)]) == 0
    assert pr.main([str(good), str(bad)]) == 1
    assert "NOT_PINNED" in capsys.readouterr().out


# --------------------------------------------------------------------------------------------- arm_child refuses an unpinned build
def test_arm_child_refuses_a_build_whose_governor_executor_or_budget_is_not_pinned(monkeypatch, tmp_path, cleanup):
    from tools.rpg_measure import arm_child
    import tools.test_architecture.rpg_gate_run as gate_run

    import os

    cleanup.append(f"rpgm_urban_political_42_{os.getpid()}")  # the run id arm_child gives its run

    def unpinned_build(world, seed, run_id):  # forces audit_mode and no_frame_pacing (the old check passes) but has the default governor and budget
        built.append(Kernel(PROD_SMALL, compile_world(world, seed), DeterministicRNG(seed), governor=ResourceGovernor(), flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id))
        return built[0]

    built: list = []

    monkeypatch.setattr(gate_run, "build_kernel", unpinned_build)
    try:
        with pytest.raises(pr.NotPinnedError, match="governor"):
            arm_child.main(["urban_political", "42", "1", str(tmp_path / "out.json")])
    finally:
        for kernel in built:
            kernel.shutdown()
