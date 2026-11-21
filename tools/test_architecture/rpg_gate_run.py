"""The child process of the rpg gate harness: one (world, seed) run, or one world's pooling. See ``rpg_gate_harness`` for the contract."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import resource
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SCHEMA = "rpg-gate-metrics/v1"


def _resolve(spec: str, attr_default: str) -> Callable[..., Any]:
    """``module`` -> ``module.<attr_default>``; ``module:attr`` names the function itself."""
    module_name, _, attr = spec.partition(":")
    return getattr(importlib.import_module(module_name), attr or attr_default)


def _write(path: Path, doc: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _peak_rss_mb() -> float:
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1)  # Linux reports KiB


@dataclass(frozen=True)
class RunArtifacts:
    """What the harness hands rpg's ``compute``: the run's identity, its final state and its recorded run directory (typed events and death records)."""

    world: str
    seed: int
    ticks: int
    sha: str
    state: Any
    run_dir: Path
    seeds: Tuple[int, ...] = ()  # the gate config's seed set (the run set a pooled floor is computed over); handed in, never read from a file by the metric module

    @property
    def events_path(self) -> Path:
        return self.run_dir / "simulation_events.jsonl"


def build_kernel(world: str, seed: int, run_id: str):
    """The pinned kernel: pinned governor, sequential executor, audit mode (no wall-clock throttle), no frame pacing."""
    from src.config.profiles import PROD_SMALL
    from src.engine.executor import LocalSequentialExecutor
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from tests.helpers.kernel_pinning import PinnedNormalGovernor
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context(world)
    state, _report = WorldCompiler.compile(spec, seed, context=context)
    return Kernel(
        PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), state, DeterministicRNG(seed),
        governor=PinnedNormalGovernor(), executor=LocalSequentialExecutor(),
        flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id,
    )


def runner_header(run_dir: Path) -> Dict[str, Any]:
    """The pinned-runner verdict for one run, read from the manifest the kernel wrote (``pinned_runner.classify_manifest``): ``{verdict, differences}``.
    A run with no readable manifest classifies NOT_PINNED, like any run with no ``run_conditions`` record (TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE)."""
    from tools.test_architecture import pinned_runner

    try:
        manifest = pinned_runner.read_manifest(run_dir / "run_manifest.json")
    except (OSError, ValueError):
        manifest = {}
    verdict = pinned_runner.classify_manifest(manifest if isinstance(manifest, dict) else {})
    return {"verdict": verdict.verdict, "differences": list(verdict.differences)}


def pooled_runner(docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """A pooled document's runner header: PINNED only when every document it pools is PINNED; otherwise NOT_PINNED, naming each document that is not."""
    differences = [
        f"pooled document {i} is not PINNED" for i, d in enumerate(docs)
        if not isinstance(d.get("runner"), dict) or d["runner"].get("verdict") != "PINNED"
    ]
    if not docs:
        differences.append("no documents were pooled")
    return {"verdict": "NOT_PINNED" if differences else "PINNED", "differences": differences}


def _no_data(args: argparse.Namespace, reason: str, exc: BaseException, seed: Optional[int]) -> Dict[str, Any]:
    doc = {"schema": SCHEMA, "status": "no-data", "reason": reason, "error": f"{type(exc).__name__}: {exc}", "exception_type": type(exc).__name__,
           "world": args.world, "ticks": args.ticks, "sha": args.sha, "harness_hash": args.harness_hash, "metrics": []}
    if seed is not None:
        doc["seed"] = seed
    return doc


def run(args: argparse.Namespace) -> int:
    """``run_error``: an exception in the simulation (world compile or ticks). ``metric_error``: an exception in rpg's ``compute``. Either way a
    ``no-data`` document carrying the reason and the exception type is written and the child exits 0; anything else is the harness's ``harness_error``."""
    out = Path(args.out)
    try:
        compute = _resolve(args.metrics_module, "compute")
    except Exception as exc:  # noqa: BLE001 - the module cannot be loaded: rpg's side
        _write(out, _no_data(args, "metric_error", exc, args.seed))
        return 0
    kernel = None
    try:
        kernel = build_kernel(args.world, args.seed, args.run_id)
        for _ in range(args.ticks):
            kernel.tick_once()
    except Exception as exc:  # noqa: BLE001
        _write(out, _no_data(args, "run_error", exc, args.seed))
        return 0
    finally:
        if kernel is not None:
            kernel.shutdown()  # flushes the recorded event stream before the metrics read it
    run_dir = Path("data") / "runs" / args.run_id
    try:
        artifacts = RunArtifacts(args.world, args.seed, args.ticks, args.sha, kernel.state, run_dir, tuple(args.seeds))
        result = compute(artifacts, non_eating=args.non_eating) if args.non_eating else compute(artifacts)
    except Exception as exc:  # noqa: BLE001
        _write(out, _no_data(args, "metric_error", exc, args.seed))
        return 0
    metrics = result["metrics"] if isinstance(result, dict) else result  # rpg returns a whole document; the harness writes the header itself
    doc = {"schema": SCHEMA, "status": "ok", "world": args.world, "seed": args.seed, "ticks": args.ticks, "sha": args.sha, "harness_hash": args.harness_hash, "floor_seeds": list(args.seeds), "runner": runner_header(run_dir), "metrics": list(metrics)}
    if isinstance(result, dict) and result.get("not_applicable"):
        doc["not_applicable"] = result["not_applicable"]  # data from the config declaration, printed per cell by the report
    _write(out, doc)
    _write(out.with_name(out.name + ".cost.json"), {"peak_rss_mb": _peak_rss_mb()})
    return 0


def pool(args: argparse.Namespace) -> int:
    try:
        pool_fn = _resolve(args.metrics_module, "pool")
        docs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in args.docs]
        metrics = pool_fn(docs, non_eating=args.non_eating) if args.non_eating else pool_fn(docs)
    except Exception as exc:  # noqa: BLE001
        _write(Path(args.out), _no_data(args, "metric_error", exc, None))
        return 0
    _write(Path(args.out), {"schema": SCHEMA, "status": "ok", "world": args.world, "ticks": args.ticks, "sha": args.sha, "harness_hash": args.harness_hash, "floor_seeds": list(args.seeds), "runner": pooled_runner(docs), "metrics": list(metrics)})
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    common = argparse.ArgumentParser(add_help=False)
    for name in ("--world", "--metrics-module", "--sha", "--harness-hash", "--out"):
        common.add_argument(name, required=True)
    common.add_argument("--ticks", type=int, required=True)
    common.add_argument("--non-eating", type=json.loads, default={})  # the config's non_eating_kind_groups as JSON; empty when none is declared
    r = sub.add_parser("run", parents=[common])
    r.add_argument("--seed", type=int, required=True)
    r.add_argument("--run-id", required=True)
    r.add_argument("--seeds", type=int, nargs="+", default=[])
    p = sub.add_parser("pool", parents=[common])
    p.add_argument("--docs", nargs="+", required=True)
    p.add_argument("--seeds", type=int, nargs="+", default=[])
    args = parser.parse_args(argv)
    return run(args) if args.cmd == "run" else pool(args)


if __name__ == "__main__":
    sys.exit(main())
