"""Replay `docs_search` against the real git history and print the measured noise.

Run by hand (needs the full history; the committed fixtures in tests/tools/fixtures/docs_search/ are the
repeatable CI form). Nothing here tunes the search: it prints what the search returns for each pinned merge.

    python3 tools/gate_checks/docs_search_replay.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List

from tools.gate_checks import docs_search

ROOT = Path(__file__).resolve().parents[2]

# (name, merge SHA, old terms the ticket removes, the audit items the replay must find or exclude)
CASES = [
    ("837", "531010a9a", [], {"found": ["simulation_kernel_contract.md", "deterministic_execution.md",
                                        "kernel_concurrency_design_philosophy.md"], "excluded": []}),
    ("786", "6d3f6235c", ["promtail"], {"found": ["README.md"], "excluded": []}),
    ("819", "61e9842121024030c0afe0ba353ec90305987236", [], {"found": [],
                                                              "excluded": ["import_linter_soak_review.md"]}),
]
_NOISE_PREFIXES = ("agent-working/", "docs/")  # the PR's own docs and records are not code paths


def changed_files(sha: str) -> List[str]:
    out = subprocess.run(["git", "show", "--name-only", "--format=", sha], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout.splitlines()
    return [p for p in out if p and not p.startswith(_NOISE_PREFIXES)]


def main() -> int:
    for name, sha, terms, expect in CASES:
        base = f"{sha}^"
        files = changed_files(sha)
        result = docs_search.search_docs_for_change(
            files, docs_search.GitRefSource(ROOT, base), docs_search.GitRefSource(ROOT, sha),
            docs_search.GitRefSource(ROOT, base), terms,
        )
        n = len(files)
        paths = {k: [i["path"] for i in result[k]] for k in ("required", "candidate", "excluded")}
        print(f"#{name} {sha[:9]}: {n} changed file(s); required {len(paths['required'])}, "
              f"candidate {len(paths['candidate'])} ({len(paths['candidate']) / max(n, 1):.1f} per changed path), "
              f"excluded {len(paths['excluded'])}")
        for want in expect["found"]:
            where = [k for k in ("required", "candidate") if any(p.endswith(want) for p in paths[k])]
            print(f"   found {want}: {where or 'MISSING'}")
        for want in expect["excluded"]:
            hit = any(p.endswith(want) for p in paths["excluded"])
            print(f"   excluded {want}: {'yes' if hit else 'NO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
