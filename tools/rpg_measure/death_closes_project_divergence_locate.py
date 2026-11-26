"""Locate a D7 living-projection divergence: the first differing field path and body of two ``--dump-tick`` files of ``death_closes_project_spy`` (BASE and FIX, the same tick).

Usage: python death_closes_project_divergence_locate.py <base.tick<N>.living.json> <fix.tick<N>.living.json>   (exit 0 equal, 1 differs; prints the first 10 paths). Read only; it names the path and the body, it never attributes a cause.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, List, Tuple


def diff(a: Any, b: Any, path: Tuple[str, ...] = ()) -> List[Tuple[str, ...]]:
    if isinstance(a, dict) and isinstance(b, dict):
        out: List[Tuple[str, ...]] = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append(path + (str(k),))
            else:
                out += diff(a[k], b[k], path + (str(k),))
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, path + (str(i),))
        return out
    return [] if a == b else [path]


def main(argv: List[str]) -> int:
    base, fix = (json.loads(Path(p).read_text(encoding="utf-8")) for p in argv[:2])
    paths = diff(base, fix)
    for p in paths[:10]:
        body = p[1] if len(p) > 1 and p[0] == "entities" else None
        print(f"path={'.'.join(p)} body={body}")
    print(f"{'EQUAL' if not paths else f'DIFFERS ({len(paths)} paths)'}")
    return 0 if not paths else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
