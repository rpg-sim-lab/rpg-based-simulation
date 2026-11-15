"""arm_child's pinned-runner check on older and newer arm trees (TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE).

``paired.py`` runs ``arm_child.py`` from THIS tool checkout with the ARM's source tree as the working directory and on PYTHONPATH. An arm tree older than the
``RunConditions`` record has no ``pinned_runner`` module and its kernel writes no ``run_conditions``; the path is chosen by what the tree contains, never by a
missing record. The runs below are tiny: world compile only (0 ticks), one process at a time, from a ``git archive`` of the named commit.

rpg-planner (u24) ruling, accepted by rpg-planner-ubuntu, 2026-11-15; ubuntu twin TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
ARM_CHILD = REPO / "tools" / "rpg_measure" / "arm_child.py"
# Both older than b6ac7dabb: no RunConditions model, no pinned_runner module. Full shas, because CI fetches them by sha (the unit-infra job's "Fetch the pre-record arm
# trees" step; tests/static/test_ci_paired_arms_workflow_shape.py holds the two lists equal).
PRE_RECORD = ("5ba65854c02ec9d132adb985a30b945fa8525d29", "96db1f5e8ddedc685d4bf56aa367cec512045bb6")
WORLD = "urban_political"


def _commit_exists(sha: str) -> bool:
    return subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=REPO, capture_output=True).returncode == 0


def _archive(sha: str, dest: Path) -> Path:
    dest.mkdir(parents=True)
    git = subprocess.Popen(["git", "archive", sha, "src", "tools", "tests", "data", "config", "content"], cwd=REPO, stdout=subprocess.PIPE)
    subprocess.run(["tar", "-x", "-C", str(dest)], stdin=git.stdout, check=True)
    assert git.wait() == 0
    return dest


def _run_child(tree: Path, out: Path, ticks: int = 0) -> subprocess.CompletedProcess:
    env = {**os.environ, "PYTHONHASHSEED": "0", "PYTHONPATH": str(tree)}
    return subprocess.run([sys.executable, str(ARM_CHILD), WORLD, "42", str(ticks), str(out)], cwd=tree, env=env, capture_output=True, text=True, timeout=300)


def _need_commit(sha: str) -> None:
    """In CI a missing arm tree FAILS (the control would otherwise be skipped and prove nothing); elsewhere a shallow clone may skip."""
    if _commit_exists(sha):
        return
    reason = f"{sha} is not in this clone"
    if os.environ.get("CI") == "true":
        pytest.fail(reason + ": the unit-infra job in .github/workflows/test.yml must run its 'Fetch the pre-record arm trees' step before this test, or the control proves nothing")
    pytest.skip(reason + " (outside CI a shallow clone may lack it; `git fetch origin <sha>`)")


def test_a_missing_arm_tree_fails_in_ci_and_skips_elsewhere(monkeypatch):
    absent = "0" * 40
    monkeypatch.setenv("CI", "true")
    with pytest.raises(pytest.fail.Exception, match="Fetch the pre-record arm trees"):
        _need_commit(absent)
    monkeypatch.delenv("CI")
    with pytest.raises(pytest.skip.Exception, match="not in this clone"):
        _need_commit(absent)


@pytest.fixture(scope="module", params=PRE_RECORD)
def old_tree(request, tmp_path_factory):
    _need_commit(request.param)
    return request.param, _archive(request.param, tmp_path_factory.mktemp("arm") / "tree")


def test_an_arm_tree_older_than_the_record_has_no_model_and_no_pinned_runner_module(old_tree):
    sha, tree = old_tree
    assert "class RunConditions" not in (tree / "src/observability/reporting/artifact_repository.py").read_text(encoding="utf-8")
    assert not (tree / "tools/test_architecture/pinned_runner.py").exists()
    assert (tree / "tools/test_architecture/rpg_gate_run.py").exists()  # the one tools module arm_child imports from the arm tree


def test_the_pinned_governor_has_the_same_qualified_name_in_both_old_trees_and_here(old_tree):
    sha, tree = old_tree
    for source in (tree / "tests/helpers/kernel_pinning.py", REPO / "tests/helpers/kernel_pinning.py"):
        assert "class PinnedNormalGovernor(ResourceGovernor):" in source.read_text(encoding="utf-8")


def test_an_old_arm_tree_passes_by_the_pre_record_path_and_says_so(old_tree, tmp_path):
    sha, tree = old_tree
    done = _run_child(tree, tmp_path / "out.json")
    assert done.returncode == 0, done.stderr[-800:]
    doc = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert doc["runner"] == "PINNED" and doc["run_conditions_source"] == "derived_from_kernel"
    assert doc["forced_flags"] == {"audit_mode": True, "no_frame_pacing": True}


def test_an_old_arm_tree_whose_kernel_has_a_threads_executor_is_refused(old_tree, tmp_path):
    """The negative control on the pre-record path: the same tree with its build_kernel on the concurrent executor."""
    sha, tree = old_tree
    run_py = tree / "tools/test_architecture/rpg_gate_run.py"
    text = run_py.read_text(encoding="utf-8")
    assert "executor=LocalSequentialExecutor()" in text
    run_py.write_text(
        text.replace("executor=LocalSequentialExecutor()",
                     "executor=__import__('src.engine.executor', fromlist=['x']).ConcurrentExecutionAdapter("
                     "__import__('src.engine.worker_manager', fromlist=['x']).WorkerManager(max_workers=2, max_queue_depth=8))"),
        encoding="utf-8")
    try:
        done = _run_child(tree, tmp_path / "out.json")
    finally:
        run_py.write_text(text, encoding="utf-8")
    assert done.returncode != 0 and "NotPinnedError" in done.stderr and "executor is" in done.stderr
    assert not (tmp_path / "out.json").exists()


def test_a_post_record_tree_passes_by_its_manifest_record(tmp_path):
    done = _run_child(REPO, tmp_path / "out.json")
    assert done.returncode == 0, done.stderr[-800:]
    doc = json.loads((tmp_path / "out.json").read_text(encoding="utf-8"))
    assert doc["runner"] == "PINNED" and doc["run_conditions_source"] == "manifest"


def test_a_post_record_tree_whose_kernel_withholds_the_record_is_refused_not_derived(monkeypatch, tmp_path):
    """The path is chosen by the tree's contents, not by a missing record: this tree HAS the model, so a manifest without the record refuses."""
    from src.observability.reporting.artifact_repository import RunArtifactRepository
    from tools.rpg_measure import arm_child
    from tools.test_architecture import pinned_runner

    import shutil

    import tools.test_architecture.rpg_gate_run as gate_run

    original = RunArtifactRepository.update_manifest
    monkeypatch.setattr(RunArtifactRepository, "update_manifest", lambda self, rid, **kw: original(self, rid, **{k: v for k, v in kw.items() if k != "run_conditions"}))
    built: list = []
    real_build = gate_run.build_kernel
    monkeypatch.setattr(gate_run, "build_kernel", lambda world, seed, run_id: built.append(real_build(world, seed, run_id)) or built[0])
    try:
        with pytest.raises(pinned_runner.NotPinnedError, match="no run_conditions record"):
            arm_child.main([WORLD, "42", "0", str(tmp_path / "out.json")])
        assert not (tmp_path / "out.json").exists()
    finally:
        for kernel in built:
            kernel.shutdown()
        shutil.rmtree(Path("data") / "runs" / f"rpgm_{WORLD}_42_{os.getpid()}", ignore_errors=True)


def test_arm_child_imports_only_one_tools_module_from_the_arm_tree_and_loads_pinned_runner_by_path():
    """The audit of arm_child's import path for ``tools.*`` modules an older arm tree lacks: only rpg_gate_run, which both old trees have."""
    tree = ast.parse(ARM_CHILD.read_text(encoding="utf-8"))
    tools_imports = sorted({n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and (n.module or "").startswith("tools")}
                           | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names if a.name.startswith("tools")})
    assert tools_imports == ["tools.test_architecture.rpg_gate_run"]
    source = ARM_CHILD.read_text(encoding="utf-8")
    assert 'parents[2] / "tools" / "test_architecture" / "pinned_runner.py"' in source and "spec_from_file_location" in source
    for sha in PRE_RECORD:
        if _commit_exists(sha):
            assert subprocess.run(["git", "cat-file", "-e", f"{sha}:tools/test_architecture/rpg_gate_run.py"], cwd=REPO).returncode == 0
