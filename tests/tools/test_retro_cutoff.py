"""TCK-20261111-RETRO-NUDGE-CUTOFF-FROM-RETRO-WEEK-NAME: the retro nudge cutoff comes from the newest retro's week NAME."""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "agent-monitoring"))

import retro_cutoff as rc  # noqa: E402


def _utc(y, m, d):
    return datetime(y, m, d, tzinfo=timezone.utc).timestamp()


def _touch(directory, *names):
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_text("# r\n", encoding="utf-8")


def test_no_retros_gives_zero(tmp_path):
    assert rc.latest_retro_week_end_ts(tmp_path / "missing") == 0.0
    _touch(tmp_path, "RETRO-ALL.md", "notes.md")
    assert rc.latest_retro_week_end_ts(tmp_path) == 0.0


def test_cutoff_is_the_end_of_the_newest_named_week(tmp_path):
    _touch(tmp_path, "RETRO-2026-W38.md", "RETRO-2026-W40.md", "RETRO-2026-W39.md")
    # W40 of 2026 ends Sunday 2026-10-04; the cutoff is the start of Monday 10-05 UTC.
    assert rc.latest_retro_week_end_ts(tmp_path) == _utc(2026, 10, 5)


def test_cutoff_ignores_file_mtimes(tmp_path):
    _touch(tmp_path, "RETRO-2026-W38.md", "RETRO-2026-W40.md")
    before = rc.latest_retro_week_end_ts(tmp_path)
    for name, stamp in (("RETRO-2026-W38.md", 4_000_000_000), ("RETRO-2026-W40.md", 1_000_000)):
        os.utime(tmp_path / name, (stamp, stamp))
    assert rc.latest_retro_week_end_ts(tmp_path) == before


def test_newest_week_wins_over_a_newer_mtime(tmp_path):
    _touch(tmp_path, "RETRO-2026-W38.md", "RETRO-2026-W40.md")
    os.utime(tmp_path / "RETRO-2026-W38.md", (4_000_000_000, 4_000_000_000))
    assert rc.latest_retro_week_end_ts(tmp_path) == _utc(2026, 10, 5)


def test_unparsable_names_are_ignored(tmp_path):
    _touch(tmp_path, "RETRO-2026-W38.md", "RETRO-2026-W99.md", "RETRO-banana.md", "RETRO-2026-W40.md.bak")
    assert rc.latest_retro_week_end_ts(tmp_path) == _utc(2026, 9, 21)  # W38 ends Sun 09-20
