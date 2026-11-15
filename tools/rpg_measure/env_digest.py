"""The sha256 of the installed distributions of the RUNNING interpreter. Stdlib only, so ``arm_child.py`` can load it by file path from the tool checkout (never through the
arm tree), the same function ``paired.py`` keys the cache with: ``paired`` then compares the two digests (TCK-20261115-PAIRED-ARMS-EVIDENCE-SETS-NEED-THEIR-REPEAT-AND-ONE-LOCKED-ENVIRONMENT)."""
from __future__ import annotations

import hashlib
import importlib.metadata
import re


def installed_dists_digest() -> str:
    """The sha256 of the sorted, newline-joined ``name==version`` of ``importlib.metadata.distributions()`` in the RUNNING interpreter (``sys.executable``'s environment,
    the one the arm children inherit): names lowercased and PEP 503 normalised, duplicates kept. ``"empty"`` or ``"unreadable"`` (never a sha256) when the list is empty
    or cannot be read, so ``paired.env_problem`` refuses it. Why it sits beside ``uv_lock``: one main-checkout .venv can serve many worktrees, so the tool checkout's uv.lock
    can claim a dependency set the run did not have."""
    try:
        rows = []
        for dist in importlib.metadata.distributions():
            name, version = dist.metadata["Name"], dist.version
            if not name or version is None:
                return "unreadable"
            rows.append(f"{re.sub(r'[-_.]+', '-', name).lower()}=={version}")
    except Exception:  # noqa: BLE001 - any failure to read the environment is a refusal, not a crash
        return "unreadable"
    if not rows:
        return "empty"
    return hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()
