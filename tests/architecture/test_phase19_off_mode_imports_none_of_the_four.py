"""An OFF-mode Kernel imports none of the four heavy observability modules (phase19 runtime check).

TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK. The import-linter contract
``c06_hot_path_not_heavy`` (codebase/structure/importlinter.toml) ignores four
``src.engine.kernel -> src.observability...`` edges on rpg-planner's condition (#547): every edge is
a function-local import behind an ``obs_mode != ObservabilityMode.OFF`` branch, so an OFF-mode
kernel never imports the four modules and an edge that moves out of the guard becomes a violation.
The static contract cannot see that condition; this test enforces it at runtime.

Each run is a FRESH interpreter (``sys.modules`` of the pytest process is already polluted), builds
a Kernel from the compiled ``sandbox_world``, runs one ``tick_once`` and ``shutdown``, and reports
which of the four modules are in ``sys.modules``.

Parity proof (both parts live in this file):
* an unguarded top-level import injected into a scratch copy of ``src/`` (never the repo) makes the
  OFF-mode run report the module, so the OFF assertion would fail;
* an ON-mode control run loads all four, so the probe can see them at all.

Stated limit (the ticket scoped it this way): one tick on sandbox_world does not cover imports that
are reached only on later ticks or by other worlds.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

FOUR_MODULES = (
    "src.observability.reporting.artifact_repository",
    "src.observability.reporting.metric_recorder",
    "src.observability.cognition.recorder",
    "src.observability.cognition.decision_trace_writer",
)

_PROBE = r"""
import json, os, sys, tempfile
FOUR = json.loads(sys.argv[1])
from src.worldbuilding.repository import WorldRepository
from src.worldbuilding.compiler import WorldCompiler
from src.config.profiles import PROD_SMALL
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG

state, _ = WorldCompiler.compile(WorldRepository("data/worlds").load_world("sandbox_world"), seed=42)
kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True, "no_replay": True})
kernel.tick_once()
kernel.shutdown()
from src.observability.config import ObservabilityConfig
print("PROBE_RESULT " + json.dumps({"mode": ObservabilityConfig.get_mode().name, "loaded": [m for m in FOUR if m in sys.modules]}))
"""


def _loaded_after_tick(mode: str, root: Path) -> list[str]:
    """Run the probe in a fresh interpreter rooted at ``root`` and return the four modules it loaded."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("SIM_OBS", "RPG_OBS"))}
    env["SIM_OBS_MODE"] = mode
    env["PYTHONPATH"] = str(root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    done = subprocess.run(
        [sys.executable, "-c", _PROBE, json.dumps(list(FOUR_MODULES))],
        cwd=root, env=env, capture_output=True, text=True, timeout=300,
    )
    assert done.returncode == 0, f"probe failed (mode={mode}):\n{done.stdout}\n{done.stderr}"
    lines = [ln for ln in done.stdout.splitlines() if ln.startswith("PROBE_RESULT ")]
    assert len(lines) == 1, f"probe printed no result (mode={mode}):\n{done.stdout}\n{done.stderr}"
    result = json.loads(lines[0][len("PROBE_RESULT "):])
    # The mode the kernel actually resolved, so a bad SIM_OBS_MODE value cannot pass silently.
    assert result["mode"] == mode, f"probe ran in mode {result['mode']}, asked for {mode}"
    return result["loaded"]


def _scratch_copy_with_unguarded_import(dest: Path, module: str) -> Path:
    """Copy ``src/`` into ``dest`` and add an unguarded top-level import of ``module`` to kernel.py."""
    shutil.copytree(REPO_ROOT / "src", dest / "src", ignore=shutil.ignore_patterns("__pycache__"))
    for name in ("data", "content"):
        if (REPO_ROOT / name).exists():
            (dest / name).symlink_to(REPO_ROOT / name, target_is_directory=True)
    kernel_py = dest / "src" / "engine" / "kernel.py"
    lines = kernel_py.read_text(encoding="utf-8").splitlines(keepends=True)
    at = next(i for i, ln in enumerate(lines) if ln.startswith("from src."))
    lines.insert(at, f"import {module}  # injected by the phase19 parity proof\n")
    kernel_py.write_text("".join(lines), encoding="utf-8")
    return dest


def test_off_mode_kernel_imports_none_of_the_four():
    assert _loaded_after_tick("OFF", REPO_ROOT) == []


def test_on_mode_control_loads_all_four():
    # Without this the OFF assertion could pass because the probe cannot see the modules.
    assert sorted(_loaded_after_tick("LIGHT", REPO_ROOT)) == sorted(FOUR_MODULES)


@pytest.mark.parametrize("module", FOUR_MODULES)
def test_unguarded_import_in_scratch_kernel_is_caught(tmp_path, module):
    scratch = _scratch_copy_with_unguarded_import(tmp_path, module)
    assert module in _loaded_after_tick("OFF", scratch)


def test_the_four_modules_are_the_contract_ignore_edges():
    """The probe's list must stay equal to the phase19 contract's ignore_imports edges."""
    toml = (REPO_ROOT / "codebase" / "structure" / "importlinter.toml").read_text(encoding="utf-8")
    block = toml.split('id = "c06_hot_path_not_heavy"', 1)[1].split("[[tool.importlinter.contracts]]", 1)[0]
    edges = sorted(
        ln.strip().strip(",").strip('"').split(" -> ", 1)[1]
        for ln in block.splitlines()
        if ln.strip().startswith('"src.engine.kernel ->')
    )
    assert edges == sorted(FOUR_MODULES)
