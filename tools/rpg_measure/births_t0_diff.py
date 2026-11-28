"""The births T0 check (designer ruling 9b06026c): compile each gate world at tick 0 (assembly only, no ticks) in the head tree and in the reference tree (c4e2dde60) and diff the two canonical states.
The ONLY allowed difference is one added ``identity.properties.archetype_id`` per archetype-backed body; the count is reported, and anything else is a STOP (exit 4).

Usage: python -m tools.rpg_measure.births_t0_diff --head-tree <tree> --ref-tree <tree> --out <dir> --go <ref> [--worlds ...] [--seed 42]
Children: ``python tools/rpg_measure/births_t0_diff.py dump <world> <seed> <out.json>`` run with cwd and PYTHONPATH = the tree (the same environment births_run gives its children)."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

T0_STOP_EXIT = 4
DEFAULT_WORLDS = ("frontier_living_world", "urban_political", "crowded_frontier")


def diff_canonical(ref: Any, head: Any, path: Tuple[Any, ...] = ()) -> List[Tuple[Tuple[Any, ...], str]]:
    """Every path where `head` differs from `ref`, as (path, "added" | "removed" | "changed"); lists are compared by index and a length difference is added or removed at the tail."""
    out: List[Tuple[Tuple[Any, ...], str]] = []
    if isinstance(ref, dict) and isinstance(head, dict):
        for key in sorted(set(ref) | set(head), key=str):
            if key not in ref:
                out.append((path + (key,), "added"))
            elif key not in head:
                out.append((path + (key,), "removed"))
            else:
                out.extend(diff_canonical(ref[key], head[key], path + (key,)))
    elif isinstance(ref, list) and isinstance(head, list):
        for index in range(max(len(ref), len(head))):
            if index >= len(ref):
                out.append((path + (index,), "added"))
            elif index >= len(head):
                out.append((path + (index,), "removed"))
            else:
                out.extend(diff_canonical(ref[index], head[index], path + (index,)))
    elif ref != head:
        out.append((path, "changed"))
    return out


def is_archetype_stamp(path: Tuple[Any, ...], kind: str) -> bool:
    """An ADDED ``entities/<id>/properties/archetype_id``: exactly four path parts. The shape is read from a real canonical dump (``out_t0_diff/*_t0_head.json``): the canonical writer
    ``EntityState.to_canonical_dict`` (src/core/state.py:947) writes ``identity.properties`` as the entity's own ``properties`` key, with no ``identity`` level."""
    return kind == "added" and len(path) == 4 and path[0] == "entities" and path[2] == "properties" and path[3] == "archetype_id"


def t0_verdict(diffs: List[Tuple[Tuple[Any, ...], str]]) -> Dict[str, Any]:
    """PASS only when every difference is an added archetype stamp; `other` lists any other path (a STOP)."""
    stamps = [d for d in diffs if is_archetype_stamp(*d)]
    other = [d for d in diffs if not is_archetype_stamp(*d)]
    return {"archetype_stamps_added": len(stamps), "other_differences": [["/".join(map(str, p)), k] for p, k in other][:50], "other_count": len(other), "verdict": "PASS" if not other and stamps else "STOP"}


def dump(world: str, seed: int, out: Path) -> int:
    """Child: compile the world with the real compile and write the canonical state JSON (assembly only)."""
    import os

    from src.engine.checkpoint import CanonicalStateHasher
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context(world)
    state, _report = WorldCompiler.compile(spec, seed, context=context)
    out.write_text(CanonicalStateHasher.to_canonical_json(state), encoding="utf-8")
    return 0


def run_child(tree: Path, out: Path, world: str, seed: int, tag: str) -> Path:
    from tools.rpg_measure.births_run import child_env

    path = out / f"{world}_{seed}_t0_{tag}.json"
    proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "dump", world, str(seed), str(path)], cwd=tree, env=child_env(tree, True), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"t0 dump child failed ({tag} {world} {seed}): {proc.stderr.strip()[-400:]}")
    return path


def main(argv: List[str]) -> int:
    if argv and argv[0] == "dump":
        return dump(argv[1], int(argv[2]), Path(argv[3]))
    ap = argparse.ArgumentParser()
    ap.add_argument("--head-tree", required=True, type=Path)
    ap.add_argument("--ref-tree", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--go", required=True, help="reference of the lead-planner go for THIS run")
    ap.add_argument("--worlds", nargs="*", default=list(DEFAULT_WORLDS))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    report: Dict[str, Any] = {"go": args.go, "seed": args.seed, "worlds": {}}
    for world in args.worlds:
        ref = json.loads(run_child(args.ref_tree, args.out, world, args.seed, "ref").read_text(encoding="utf-8"))
        head = json.loads(run_child(args.head_tree, args.out, world, args.seed, "head").read_text(encoding="utf-8"))
        report["worlds"][world] = t0_verdict(diff_canonical(ref, head))
    report["verdict"] = "PASS" if all(w["verdict"] == "PASS" for w in report["worlds"].values()) else "STOP"
    (args.out / "t0_diff_summary.json").write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["verdict"] == "STOP":
        print("T0 STOP: the head's t0 state differs from the reference's by more than the archetype_id stamp; report to rpg-designer")
        return T0_STOP_EXIT
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
