"""Autouse fixture for tests that run labs, sweeps or mining under fixed ids in the real ``data/runs``.

Since the world farm change a run directory that already exists is refused, never deleted (``src/observability/world_farm_io.py``),
so a test that leaves ``data/runs/run_<fixed id>_seed_<n>`` behind would fail on its next run. This removes only the ``*_seed_*``
directories the test itself created; default run ids contain no ``_seed_``, so a backend writing default runs is never touched.
"""

import os
import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def remove_seed_run_dirs_this_test_created():
    root = Path(os.path.abspath("data/runs"))
    before = set(os.listdir(root)) if root.is_dir() else set()
    yield
    if root.is_dir():
        for name in set(os.listdir(root)) - before:
            if "_seed_" in name:
                shutil.rmtree(root / name, ignore_errors=True)
