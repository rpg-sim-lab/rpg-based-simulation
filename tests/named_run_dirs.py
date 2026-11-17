"""Opt-in fixture: remove exactly the ``data/runs`` directories a test's fixed run ids name, by name.

A run directory that already exists is refused, never deleted (``src/observability/world_farm_io.py``), so a test that runs a lab,
sweep or mining experiment under a fixed id would fail on its next run if it left ``data/runs/run_<id>_seed_<n>`` behind. This
deletes only the ids the test itself names (``RUN_ID_PREFIXES[test name]``), before the test as well as after it (a crashed earlier run would otherwise refuse the next one), never by time window, so a parallel worker's run or
another session's run in the same checkout is never touched. Two tests that share an id would already refuse each other.

Use it as ``pytestmark = pytest.mark.usefixtures("remove_named_run_dirs")`` after importing the fixture, and give the module a
``RUN_ID_PREFIXES = {"test_function_name": ("prefix", ...)}`` (``run_<prefix>_seed_<n>`` is the directory name).
"""

import os
import shutil
from pathlib import Path

import pytest


def _remove(wanted):
    root = Path(os.path.abspath("data/runs"))
    for prefix in wanted:
        for path in root.glob(f"run_{prefix}_seed_*"):
            shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def remove_named_run_dirs(request):
    wanted = getattr(request.module, "RUN_ID_PREFIXES", {}).get(request.node.originalname or request.node.name, ())
    _remove(wanted)  # before: a crashed or killed earlier run leaves a dir that would refuse this run
    yield
    _remove(wanted)  # after


def remove_run_dir(run_id):
    """Remove exactly ``data/runs/<run_id>`` (one id, never a glob or a time window); a name that is not a single path component is refused."""
    if not run_id or os.path.basename(run_id) != run_id or run_id in (".", ".."):
        raise ValueError(f"not a single run id: {run_id!r}")
    shutil.rmtree(Path(os.path.abspath("data/runs")) / run_id, ignore_errors=True)


@pytest.fixture
def remove_restored_run_dirs(monkeypatch):
    """Opt-in: every ``ScenarioCheckpointer.restore`` the test makes records its kernel's run id, and exactly those run directories are removed after the test.

    A restore builds a real kernel, which creates ``data/runs/restored_<spec id>_<pid>_<uuid>``. Use it as
    ``pytestmark = pytest.mark.usefixtures("remove_restored_run_dirs")`` after importing the fixture. It wraps ``restore`` and returns its real result unchanged.
    """
    from src.engine.scenario_checkpoint import ScenarioCheckpointer

    real = ScenarioCheckpointer.restore
    made = []

    def restore(*args, **kwargs):
        svc = real(*args, **kwargs)
        made.append(svc._kernel._run_id)
        return svc

    monkeypatch.setattr(ScenarioCheckpointer, "restore", staticmethod(restore))
    yield made
    for run_id in made:
        remove_run_dir(run_id)
