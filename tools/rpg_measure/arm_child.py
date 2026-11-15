"""One run of one arm: build the pinned kernel (audit_mode, no frame pacing), run it, and write a small JSON of typed facts (never a raw event dump).

Executed by ``paired.py`` with the ARM'S source tree as the working directory and on PYTHONPATH, so it must import only what every arm tree has
(``tools.test_architecture.rpg_gate_run.build_kernel``, the engine, ``keeps_coin``). Counters that an older arm tree does not record are written as null,
never as zero.

Usage: python arm_child.py <world> <seed> <ticks> <out.json>
"""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

LEDGER_TALLY = "rpg_gate_ledger_tally"


def _pinned_runner():
    """``tools/test_architecture/pinned_runner.py``, loaded by file path from THIS tool checkout, never through the arm tree.

    The arm tree is the working directory and on PYTHONPATH, so ``from tools.test_architecture.pinned_runner import ...`` would look in the arm tree, which has no such
    module before the pinned-runner change (ModuleNotFoundError on every older arm). The module is stdlib-only, so it loads without the arm's ``src`` or ``tools``.
    When ``tools.test_architecture.pinned_runner`` is already imported from this same file (a test, or a tool-checkout run) that module is reused, so its
    exception classes are the caller's own."""
    path = Path(__file__).resolve().parents[2] / "tools" / "test_architecture" / "pinned_runner.py"
    existing = sys.modules.get("tools.test_architecture.pinned_runner")
    if existing is not None and Path(getattr(existing, "__file__", "") or "").resolve() == path:
        return existing
    name = "_arm_child_pinned_runner"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses look the module up by name while the class body runs
    spec.loader.exec_module(module)
    return module


def _env_digest():
    """``tools/rpg_measure/env_digest.py``, loaded by file path from THIS tool checkout (stdlib only), never through the arm tree: the same function ``paired`` keys the
    cache with, so the arm document's ``dists`` and the key's can be compared."""
    path = Path(__file__).resolve().with_name("env_digest.py")
    name = "_arm_child_env_digest"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _qualname(obj) -> str:
    return f"{type(obj).__module__}.{type(obj).__qualname__}"


def _has_run_conditions_model() -> bool:
    """Does THIS arm tree define ``RunConditions``? A tree that does not predates the record, so its kernel writes none."""
    return hasattr(importlib.import_module("src.observability.reporting.artifact_repository"), "RunConditions")


def _derived_conditions(kernel) -> dict:
    """The run conditions of a pre-record tree, read from the live kernel the same way a newer kernel records them (governor and executor class names, the profile's
    tick budget, audit_mode and the no_frame_pacing flag)."""
    return {
        "governor": _qualname(kernel._governor), "executor": _qualname(kernel._executor),
        "max_tick_budget_ms": float(kernel._profile.max_tick_budget_ms),
        "audit_mode": bool(kernel._audit_mode), "no_frame_pacing": bool(kernel._no_frame_pacing),
    }


def _cause(entity) -> str | None:
    """The typed cause recorded at death (``death_record``), else the older passive cause or reason string (``legacy:``), else None while alive."""
    if entity.combat.alive:
        return None
    record = getattr(entity.lifecycle, "death_record", None)
    if record is not None:
        return str(getattr(record.cause, "value", record.cause))
    legacy = getattr(entity.lifecycle.passive_death_cause, "value", None) or entity.lifecycle.death_reason or "unknown"
    return f"legacy:{legacy}"


def _roster(state, keeps_coin) -> list:
    return [[e.id, e.kind, int(bool(keeps_coin(e))), int(e.combat.alive)] for e in sorted(state.entities.values(), key=lambda x: x.id)]


def _tally(run_dir: Path) -> dict | None:
    path = run_dir / "simulation_events.jsonl"
    if not path.exists():
        return None
    found = None
    for line in path.read_text(encoding="utf-8").splitlines():
        if LEDGER_TALLY in line:
            found = json.loads(line).get("payload")
    return found


def main(argv: list[str]) -> int:
    world, seed, ticks, out = argv[0], int(argv[1]), int(argv[2]), argv[3]
    from src.engine.checkpoint import CanonicalStateHasher
    from src.engine.serves import keeps_coin
    from tools.test_architecture.rpg_gate_run import build_kernel

    pinned_runner = _pinned_runner()

    run_id = f"rpgm_{world}_{seed}_{os.getpid()}"
    kernel = build_kernel(world, seed, run_id)
    forced = {"audit_mode": getattr(kernel, "_audit_mode", None), "no_frame_pacing": getattr(kernel, "_no_frame_pacing", None)}
    if forced["audit_mode"] is not True or forced["no_frame_pacing"] is not True:
        raise RuntimeError(f"this arm's build_kernel did not force audit_mode and no_frame_pacing: {forced}")
    # The governor, executor and budget too (one PINNED definition: tools/test_architecture/pinned_runner.py). A tree with the RunConditions model has its kernel write the
    # record into the manifest, and that record is what is classified; a tree without the model (older than the record) is classified from its live kernel. A tree WITH the
    # model whose manifest lacks the record, or whose record is not pinned, is refused.
    if _has_run_conditions_model():
        source = "manifest"
        manifest_path = Path("data") / "runs" / run_id / "run_manifest.json"
        evidence = pinned_runner.read_manifest(manifest_path) if manifest_path.exists() else {}
    else:
        source = "derived_from_kernel"
        evidence = {"run_conditions": _derived_conditions(kernel)}
    pinned = pinned_runner.require_pinned(evidence, what="this arm's build_kernel")
    start = _roster(kernel.state, keeps_coin)
    start_hash = CanonicalStateHasher.get_hash(kernel.state)
    for _ in range(ticks):
        kernel.tick_once()
    state = kernel.state
    kernel.shutdown()
    run_dir = Path("data") / "runs" / run_id
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8")) if (run_dir / "run_manifest.json").exists() else {}
    tally = _tally(run_dir)
    final = {str(e.id): [int(e.combat.alive), _cause(e), e.kind] for e in state.entities.values()}
    doc = {
        "world": world, "seed": seed, "ticks": ticks, "hashseed": os.environ.get("PYTHONHASHSEED"),
        "start_hash": start_hash, "final_hash": CanonicalStateHasher.get_hash(state),
        "forced_flags": forced, "dists": _env_digest().installed_dists_digest(), "runner": pinned.verdict, "run_conditions_source": source, "audit_mode": manifest.get("audit_mode"), "signals_zeroed": manifest.get("signals_zeroed"),
        "start": start, "final": final,
        "counters": (tally or {}).get("behaviour") if tally and "behaviour" in tally else None,
        "perception_samples": (tally or {}).get("perception_samples"),
        "adds": (tally or {}).get("adds"),
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(doc, sort_keys=True), encoding="utf-8")
    shutil.rmtree(run_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
