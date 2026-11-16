"""World farm step one (T4, T5, T7): lab run ids are unique by default, an id in use is refused (never deleted), and the id is a name only."""

import re
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from src.lab.cli import default_lab_run_id
from src.observability.world_farm_io import RunDirectoryInUseError

_SHAPE = re.compile(r"^labrun_\d{8}_\d{6}_\d+_[0-9a-f]{8}$")


def test_two_default_ids_made_in_the_same_second_differ():
    frozen = datetime(2026, 11, 15, 10, 0, 0, tzinfo=timezone.utc)
    first, second = default_lab_run_id(now=frozen), default_lab_run_id(now=frozen)
    assert first != second
    assert _SHAPE.match(first) and _SHAPE.match(second)


def test_default_id_carries_the_process_id():
    with patch("src.lab.cli.os.getpid", return_value=4242):
        assert "_4242_" in default_lab_run_id()


def test_orchestrator_refuses_an_existing_data_runs_dir_and_deletes_nothing(tmp_path, monkeypatch):
    from src.lab.orchestrator import ensure_seed_run_dirs_free

    monkeypatch.chdir(tmp_path)
    existing = Path("data/runs/run_labrun_x_seed_7")
    existing.mkdir(parents=True)
    (existing / "keep.txt").write_text("first run", encoding="utf-8")
    with patch("shutil.rmtree") as rmtree:
        with pytest.raises(RunDirectoryInUseError) as err:
            ensure_seed_run_dirs_free("labrun_x", [3, 7])
        assert not rmtree.called
    assert "run_labrun_x_seed_7" in str(err.value)
    assert (existing / "keep.txt").read_text(encoding="utf-8") == "first run"


def test_orchestrator_accepts_ids_with_no_existing_dir(tmp_path, monkeypatch):
    from src.lab.orchestrator import ensure_seed_run_dirs_free

    monkeypatch.chdir(tmp_path)
    ensure_seed_run_dirs_free("labrun_new", [1, 2, 3])
