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
    "worker_manager": None,
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


# --------------------------------------------------------------------------------------------- worker_manager (TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE)
def _threads_kernel(run_id: str):
    """A pinned governor, budget and flags on the concurrent executor (a WorkerManager with threads): the one thing not pinned is the executor."""
    from src.engine.executor import ConcurrentExecutionAdapter
    from src.engine.worker_manager import WorkerManager

    profile = PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9})
    manager = WorkerManager(max_workers=2, max_queue_depth=profile.max_queue_depth)
    return Kernel(profile, compile_world("urban_political", 42), DeterministicRNG(42), governor=PinnedNormalGovernor(),
                  executor=ConcurrentExecutionAdapter(manager), flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id)


def _threads_run(run_id: str, *, drop_record: bool = False, monkeypatch=None):
    if drop_record:
        original = RunArtifactRepository.update_manifest
        monkeypatch.setattr(RunArtifactRepository, "update_manifest", lambda self, rid, **kw: original(self, rid, **{k: v for k, v in kw.items() if k != "run_conditions"}))
    kernel = _threads_kernel(run_id)
    try:
        repo = kernel._artifact_repo
        for _ in range(2):
            kernel.tick_once()
        digest = CanonicalStateHasher.get_hash(kernel.state)
    finally:
        kernel.shutdown()
    return json.loads(Path(repo.base_dir, run_id, "run_manifest.json").read_text(encoding="utf-8")), digest


def test_a_threads_built_kernel_records_its_worker_manager_and_a_sequential_one_records_none(tmp_path, cleanup):
    cleanup.extend(["rc_unit_threads", "rc_unit_seq_wm"])
    threads, _ = _threads_run("rc_unit_threads")
    assert threads["run_conditions"]["worker_manager"] == "src.engine.worker_manager.WorkerManager"
    assert threads["run_conditions"]["executor"] == "src.engine.executor.ConcurrentExecutionAdapter"
    sequential, _, _ = _run(tmp_path, pinned=True, run_id="rc_unit_seq_wm")
    assert sequential["run_conditions"]["worker_manager"] is None


def test_the_worker_manager_record_does_not_move_the_state_hash(cleanup, monkeypatch):
    cleanup.extend(["rc_unit_wm_with", "rc_unit_wm_without"])
    with_record, hash_with = _threads_run("rc_unit_wm_with")
    without_record, hash_without = _threads_run("rc_unit_wm_without", drop_record=True, monkeypatch=monkeypatch)
    assert with_record["run_conditions"]["worker_manager"] and without_record["run_conditions"] is None
    assert hash_with == hash_without


def test_a_threads_run_classifies_not_pinned_by_its_executor_alone(cleanup):
    cleanup.append("rc_unit_threads_cls")
    manifest, _ = _threads_run("rc_unit_threads_cls")
    verdict = pr.classify_manifest(manifest)
    assert verdict.verdict == "NOT_PINNED" and [d.split(" ")[0] for d in verdict.differences] == ["executor"]


def test_arm_child_refuses_a_build_on_the_concurrent_executor(monkeypatch, tmp_path, cleanup):
    """The executor case on its own: governor, budget and both flags are the pinned ones, so only the executor can be the reason."""
    import os

    from tools.rpg_measure import arm_child
    import tools.test_architecture.rpg_gate_run as gate_run

    cleanup.append(f"rpgm_urban_political_42_{os.getpid()}")
    built: list = []

    def threads_build(world, seed, run_id):
        built.append(_threads_kernel(run_id))
        return built[0]

    monkeypatch.setattr(gate_run, "build_kernel", threads_build)
    try:
        with pytest.raises(pr.NotPinnedError, match="executor") as raised:
            arm_child.main(["urban_political", "42", "1", str(tmp_path / "out.json")])
        assert "governor" not in str(raised.value) and "max_tick_budget_ms" not in str(raised.value)
    finally:
        for kernel in built:
            kernel.shutdown()
