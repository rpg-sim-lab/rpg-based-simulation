"""The GitHub repo (`owner/name`) the delivery tools talk to, derived from `gh` instead of a hard-coded owner, so a repo
transfer (to the rpg-sim-lab org) needs no code change. Falls back to FALLBACK_REPO when gh fails or answers oddly."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
from typing import Any

FALLBACK_REPO = "rpg-sim-lab/rpg-based-simulation"
_SHAPE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_cache: dict[str, str] = {}


def _default_run(cmd: list[str]) -> Any:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)


def current_repo(run: Callable[[list[str]], Any] = _default_run) -> str:
    """`nameWithOwner` from `gh repo view`, else FALLBACK_REPO. A real answer is cached for the process; a fallback is not."""
    if "repo" in _cache:
        return _cache["repo"]
    try:
        done = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
        out = (done.stdout or "").strip() if done.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return FALLBACK_REPO
    if not _SHAPE.match(out):
        return FALLBACK_REPO
    _cache["repo"] = out
    return out
