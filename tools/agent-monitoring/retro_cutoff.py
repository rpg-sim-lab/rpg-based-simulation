"""The cutoff the retro nudge counts DONE runs from (TCK-20261111-RETRO-NUDGE-CUTOFF-FROM-RETRO-WEEK-NAME).

The cutoff comes from the newest `RETRO-YYYY-Www.md` file NAME, not from a file's mtime: git sets mtime whenever it writes a
file (checkout, merge, branch switch), so an mtime cutoff moves on every sync and differs between worktrees for one commit.
A retro named for week W covers activity up to the end of W (Sunday 24:00 UTC, the same line the week close uses), so a run
that started later counts toward the next nudge.
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from week_close import WeekCloseError, week_end  # noqa: E402

_RETRO_NAME = re.compile(r"^RETRO-(\d{4}-W\d{2})\.md$")


def latest_retro_week_end_ts(retro_dir: Path) -> float:
    """UTC timestamp of the end of the newest dated retro's ISO week; 0.0 when there is none.

    `RETRO-ALL.md` and names that do not parse as a real ISO week are ignored.
    """
    ends = []
    for path in Path(retro_dir).glob("RETRO-*.md"):
        match = _RETRO_NAME.match(path.name)
        if not match:
            continue
        try:
            ends.append(week_end(match.group(1)))
        except WeekCloseError:
            continue
    if not ends:
        return 0.0
    end_of_sunday = datetime.combine(max(ends) + timedelta(days=1), time.min, tzinfo=timezone.utc)
    return end_of_sunday.timestamp()
