"""The changed-file list of a run, derived from git (shared by gate_cli.py and docs_search.py).

Moved out of gate_cli.py so the docs search can derive exactly the list the doc-staleness gate uses, from the same
function, without importing gate_cli (which imports the docs search).
"""
from __future__ import annotations

import subprocess

# Paths a run writes as bookkeeping, never as the ticket's own change. A path is excluded when it starts with one of
# these, or contains one of the fragments.
EXCLUDED_PREFIXES = (
    "agent-working/agent-monitoring/",  # run, event, tool and gate-verdict shards
    "data/runs/",                       # simulation run output
    "reports/release_proof/",           # release-proof output
    "graphify-out/",                    # the knowledge graph
    ".claude/current_run",              # the per-session run sidecar
)
EXCLUDED_FRAGMENTS = ("/__pycache__/", "/.pytest_cache/")


def is_excluded(path: str) -> bool:
    return path.startswith(EXCLUDED_PREFIXES) or any(fragment in "/" + path for fragment in EXCLUDED_FRAGMENTS)


def _git(*args: str) -> list[str]:
    done = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return [line for line in done.stdout.splitlines() if line.strip()]


def derive_changed_files(start_sha: str) -> list[str]:
    """Tracked changes since ``start_sha`` (working tree included) plus untracked files, bookkeeping removed, sorted."""
    paths = set(_git("diff", "--name-only", start_sha, "--")) | set(_git("ls-files", "--others", "--exclude-standard"))
    return sorted(p for p in paths if not is_excluded(p))


def code_paths(files: list[str]) -> list[str]:
    """The code paths among changed files: not `docs/` and not `agent-working/` records."""
    return [f for f in files if not f.startswith(("docs/", "agent-working/"))]
