"""Proof that a frozen tree is EXACTLY ``git ls-tree -r <sha>``: the same paths, the same blob hashes (computed here with git's own blob algorithm, so no ``.git`` is needed in the tree), and no ``data/runs``.

Usage: python person_attack_tree_check.py --repo <checkout with the sha> --sha <sha> --tree <frozen tree>   (exit 0 equal, 1 differs; prints the first differences)
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List


def blob_hash(path: Path) -> str:
    data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def tree_listing(repo: str, sha: str) -> Dict[str, str]:
    out = subprocess.run(["git", "-C", repo, "ls-tree", "-r", "-z", sha], capture_output=True, check=True).stdout.decode("utf-8", "surrogateescape")
    listing: Dict[str, str] = {}
    for entry in filter(None, out.split("\0")):
        meta, _, name = entry.partition("\t")
        mode, kind, blob = meta.split()
        listing[name] = f"{kind}:{blob}" if kind != "commit" else f"commit:{blob}"
    return listing


def tree_files(tree: Path) -> Dict[str, str]:
    found: Dict[str, str] = {}
    for root, dirs, files in os.walk(tree):
        for name in files + [d for d in dirs if (Path(root) / d).is_symlink()]:
            path = Path(root) / name
            found[str(path.relative_to(tree))] = f"blob:{blob_hash(path)}"
    return found


def differences(expected: Dict[str, str], found: Dict[str, str]) -> List[str]:
    out = [f"missing in tree: {p}" for p in sorted(set(expected) - set(found))]
    out += [f"extra in tree: {p}" for p in sorted(set(found) - set(expected))]
    out += [f"blob differs: {p}" for p in sorted(set(expected) & set(found)) if expected[p] != found[p]]
    return out


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--tree", required=True, type=Path)
    args = ap.parse_args(argv)
    diffs = differences(tree_listing(args.repo, args.sha), tree_files(args.tree))
    if (args.tree / "data" / "runs").exists():
        diffs.append("data/runs exists in the tree")
    for line in diffs[:20]:
        print(line, file=sys.stderr)
    print(f"{args.sha}: {'EQUAL' if not diffs else 'DIFFERS (' + str(len(diffs)) + ')'}")
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
