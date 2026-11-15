"""TCK-20261115-PROJECT-SYNC-HOST-TIMER (P3c): the systemd templates carry their caps and the right command. No network, nothing installed."""
import configparser
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2] / "tools" / "sessions" / "systemd"


def _read(name: str) -> configparser.ConfigParser:
    cp = configparser.ConfigParser(interpolation=None, strict=True)
    cp.optionxform = str  # systemd keys are case-sensitive
    cp.read_string((ROOT / name).read_text(encoding="utf-8"))
    return cp


def test_the_service_is_a_capped_oneshot_with_a_skip_condition():
    svc = _read("project-sync.service")["Service"]
    assert svc["Type"] == "oneshot" and svc["WorkingDirectory"] == "@REPO@"
    assert svc["Nice"] == "19" and svc["IOSchedulingClass"] == "idle"
    assert svc["CPUQuota"] == "25%" and svc["MemoryMax"] == "256M" and svc["TimeoutStartSec"] == "15min"
    cond = svc["ExecCondition"]  # exit 1 = skip (1-254), never 255; the limit is 1 GiB in kB
    assert "MemAvailable" in cond and "1048576" in cond and "? 1 : 0" in cond and "$$2" in cond


def test_exec_start_runs_apply_with_fetch_from_the_repo_venv():
    start = _read("project-sync.service")["Service"]["ExecStart"]
    assert start.split()[0] == "@REPO@/.venv/bin/python"
    assert "tools/sessions/project_sync.py" in start and "--apply" in start and "--fetch" in start


def test_the_timer_is_hourly_at_00_persistent_and_jittered():
    timer = _read("project-sync.timer")
    assert timer["Timer"]["OnCalendar"] == "*-*-* *:00:00"
    assert timer["Timer"]["Persistent"] == "true" and timer["Timer"]["RandomizedDelaySec"] == "60"
    assert timer["Install"]["WantedBy"] == "timers.target"


@pytest.mark.parametrize("name", ["project-sync.service", "project-sync.timer"])
def test_no_template_names_a_token_path_or_value(name):
    text = (ROOT / name).read_text(encoding="utf-8").lower()
    assert "token" not in text and "rpg-project-sync" not in text and "gh_token" not in text and "ghp_" not in text
