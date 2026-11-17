"""The pinned runner: one definition, and the classifier and refusal that read it (TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE).

Behaviour evidence (a paired table, a probe count, a trace row used in a verdict) comes from the pinned runner: ``tools/rpg_measure`` or
``tools.test_architecture.rpg_gate_run.build_kernel``. The kernel writes a typed ``run_conditions`` record into each run's manifest (governor, executor, tick
budget, audit mode, frame pacing; ``RunConditions`` in ``src/observability/reporting/artifact_repository.py``). This module is the only place that says what
the pinned values are. It classifies a run from that record alone, never from a label a runner wrote about itself and never from kernel private fields, so a
run on ``tools.calibrate_simq._run_engine`` (default governor and executor) classifies NOT_PINNED by what it was built with.

* ``classify(run_conditions)`` returns a ``Verdict``: ``PINNED`` only when every field equals ``PINNED``; a missing record (an older manifest, or a run that stopped
  before the executor was chosen) is NOT_PINNED, since nothing shows it was pinned.
* ``require_pinned(manifest)`` is the refusal an evidence helper applies; it raises ``NotPinnedError`` naming each field that differs.
* ``evidence_row(manifest, **facts)`` is the report helper: it returns the facts plus ``runner: PINNED``, or raises.

Command line: ``python -m tools.test_architecture.pinned_runner <run_manifest.json> [...]`` prints each verdict and exits 1 if any is NOT_PINNED.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


@dataclass(frozen=True)
class PinnedSpec:
    """What ``rpg_gate_run.build_kernel`` builds: the pinned governor and the sequential executor, a raised tick budget, audit mode, no frame pacing."""

    governor: str = "tests.helpers.kernel_pinning.PinnedNormalGovernor"
    executor: str = "src.engine.executor.LocalSequentialExecutor"
    min_tick_budget_ms: float = 1e9
    audit_mode: bool = True
    no_frame_pacing: bool = True


PINNED = PinnedSpec()


class NotPinnedError(ValueError):
    """A run that is not on the pinned runner was offered as behaviour evidence."""


@dataclass(frozen=True)
class Verdict:
    verdict: str  # PINNED | NOT_PINNED
    differences: List[str]

    @property
    def pinned(self) -> bool:
        return self.verdict == "PINNED"


def classify(run_conditions: Optional[Mapping[str, Any]], spec: PinnedSpec = PINNED) -> Verdict:
    """PINNED only if the record equals the spec on every field; each field that differs (or is missing) is named."""
    if not run_conditions:
        return Verdict("NOT_PINNED", ["no run_conditions record (an older manifest, or a run that stopped before its executor was chosen)"])
    diffs: List[str] = []
    for field_name in ("governor", "executor"):
        got = run_conditions.get(field_name)
        if got != getattr(spec, field_name):
            diffs.append(f"{field_name} is {got!r}, pinned is {getattr(spec, field_name)!r}")
    budget = run_conditions.get("max_tick_budget_ms")
    if not isinstance(budget, (int, float)) or isinstance(budget, bool) or budget < spec.min_tick_budget_ms:
        diffs.append(f"max_tick_budget_ms is {budget!r}, pinned is at least {spec.min_tick_budget_ms:g}")
    for field_name in ("audit_mode", "no_frame_pacing"):
        if run_conditions.get(field_name) is not getattr(spec, field_name):
            diffs.append(f"{field_name} is {run_conditions.get(field_name)!r}, pinned is {getattr(spec, field_name)!r}")
    return Verdict("NOT_PINNED" if diffs else "PINNED", diffs)


def classify_manifest(manifest: Mapping[str, Any], spec: PinnedSpec = PINNED) -> Verdict:
    return classify(manifest.get("run_conditions"), spec)


def require_pinned(manifest: Mapping[str, Any], *, what: str = "this run") -> Verdict:
    """The refusal: raise ``NotPinnedError`` unless the manifest's record classifies PINNED. Returns the verdict when it does."""
    verdict = classify_manifest(manifest)
    if not verdict.pinned:
        raise NotPinnedError(f"{what} is NOT_PINNED and cannot be reported as behaviour evidence: " + "; ".join(verdict.differences))
    return verdict


def evidence_row(manifest: Mapping[str, Any], **facts: Any) -> Dict[str, Any]:
    """The report helper: the facts a probe reports, plus the runner verdict. Refuses a run that is not pinned."""
    require_pinned(manifest, what=f"run {manifest.get('run_id', '?')}")
    return {**facts, "runner": "PINNED", "run_id": manifest.get("run_id")}


def read_manifest(path: Path) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("manifests", nargs="+", help="run_manifest.json paths (data/runs/<run_id>/run_manifest.json)")
    args = ap.parse_args(argv)
    worst = 0
    for path in args.manifests:
        verdict = classify_manifest(read_manifest(Path(path)))
        print(f"{path}: {verdict.verdict}" + ("" if verdict.pinned else " — " + "; ".join(verdict.differences)))
        worst |= 0 if verdict.pinned else 1
    return worst


if __name__ == "__main__":
    sys.exit(main())
