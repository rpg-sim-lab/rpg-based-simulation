"""The sha256 of the installed distributions of the RUNNING interpreter. Stdlib only, so ``arm_child.py`` can load it by file path from the tool checkout (never through the
arm tree), the same function ``paired.py`` keys the cache with: ``paired`` then compares the two digests (TCK-20261115-PAIRED-ARMS-EVIDENCE-SETS-NEED-THEIR-REPEAT-AND-ONE-LOCKED-ENVIRONMENT)."""
from __future__ import annotations

import hashlib
import importlib.metadata
import re
import site
import sysconfig
from pathlib import Path
from typing import List

PROJECT_DIST = "rpg-based-simulation"  # this project's own distribution (an editable install in the main checkout): never counted


def _normalise(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def site_dirs() -> List[str]:
    """The interpreter's own site-packages directories (``sysconfig`` purelib and platlib, ``site.getsitepackages()``), resolved and de-duplicated. Never the working
    directory or a ``PYTHONPATH`` entry: those differ between ``paired`` (run from a checkout) and ``arm_child`` (cwd and PYTHONPATH set to the arm tree)."""
    raw = [sysconfig.get_paths().get("purelib"), sysconfig.get_paths().get("platlib"), *site.getsitepackages()]
    found: List[str] = []
    for entry in raw:
        if entry and Path(entry).is_dir() and str(Path(entry).resolve()) not in found:
            found.append(str(Path(entry).resolve()))
    return found


def installed_dists_digest() -> str:
    """The sha256 of the sorted, newline-joined ``name==version`` of ``importlib.metadata.distributions()`` in the RUNNING interpreter (``sys.executable``'s own site-packages only, see ``site_dirs``;
    the project's own distribution is excluded): names lowercased and PEP 503 normalised, duplicates kept. ``"empty"`` or ``"unreadable"`` (never a sha256) when the list is empty
    or cannot be read, so ``paired.env_problem`` refuses it. Why it sits beside ``uv_lock``: one main-checkout .venv can serve many worktrees, so the tool checkout's uv.lock
    can claim a dependency set the run did not have."""
    try:
        rows = []
        for dist in importlib.metadata.distributions(path=site_dirs()):
            name, version = dist.metadata["Name"], dist.version
            if not name or version is None:
                return "unreadable"
            if _normalise(name) != PROJECT_DIST:
                rows.append(f"{_normalise(name)}=={version}")
    except Exception:  # noqa: BLE001 - any failure to read the environment is a refusal, not a crash
        return "unreadable"
    if not rows:
        return "empty"
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()
