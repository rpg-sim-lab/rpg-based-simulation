"""Fetch main's latest completed rpg gate report, the baseline the rerun skip and the "new vs main" diff are judged against.

TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN. Selection (decision a): the newest COMPLETED run of ``rpg-gate-report.yml`` on
main, newest first, that has an ``rpg-gate-report-<head sha>`` artifact. The run's conclusion does not matter (main's own run is red on an inherited row and is
exactly the baseline wanted). A completed run with no such artifact (the gate skipped it, it never reached the report, retention ran out) and a run whose
report was made from another checkout (a dispatch with a ``ref`` input: the report's sha differs from the run's head sha) are passed over, at most
``MAX_RUNS`` deep. The NEWEST run that has an artifact decides: if that one is unreadable the answer is a fallback, never an older report.

Output: one JSON file, either ``{"run_id", "head_sha", "report"}`` or ``{"fallback": "<why>"}``. Every failure (no ``gh``, an API error, a download error,
bad JSON) is a fallback record and exit 0, so the caller runs the full rerun. ``rpg_gate_report.load_main_baseline`` judges comparability.

Access: the lookups use ``gh run list`` and ``gh run download``, which need ``GH_TOKEN`` and, for the same-repo workflow token, ``actions: read`` on the job.

CLI::

    python -m tools.test_architecture.rpg_gate_main_report fetch --out FILE [--workflow rpg-gate-report.yml] [--branch main] [--exclude-run-id ID]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Mapping, Optional

MAX_RUNS = 10
REPORT_NAME = "rpg-gate-report.json"

Gh = Callable[[List[str]], str]


def _gh(args: List[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True, timeout=300).stdout


def fetch(gh: Gh = _gh, *, workflow: str = "rpg-gate-report.yml", branch: str = "main", exclude_run_id: Optional[str] = None, max_runs: int = MAX_RUNS) -> dict:
    """Return ``{"run_id", "head_sha", "report"}`` for main's newest usable completed run, or ``{"fallback": reason}``."""
    try:
        runs = json.loads(gh(["run", "list", "--workflow", workflow, "--branch", branch, "--status", "completed", "--limit", str(max_runs),
                              "--json", "databaseId,headSha,event,createdAt"]))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {"fallback": f"listing main's gate runs failed ({type(exc).__name__})"}
    runs = [r for r in runs if str(r.get("databaseId")) != str(exclude_run_id)]
    if not runs:
        return {"fallback": f"no completed {workflow} run on {branch}"}
    for run in runs:
        run_id, sha = run["databaseId"], run["headSha"]
        with tempfile.TemporaryDirectory() as tmp:
            try:
                gh(["run", "download", str(run_id), "-n", f"rpg-gate-report-{sha}", "-D", tmp])
            except (OSError, subprocess.SubprocessError):
                continue  # no such artifact: the run was gate-skipped, never reached the report, or the artifact expired
            path = Path(tmp) / "report" / REPORT_NAME
            try:
                report = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                return {"fallback": f"main's report in run {run_id} is unreadable ({type(exc).__name__})"}
        if not isinstance(report, Mapping):
            return {"fallback": f"main's report in run {run_id} is unreadable (not an object)"}
        if report.get("sha") != sha:
            continue  # a dispatch with a ref input: the report is about another checkout
        return {"run_id": run_id, "head_sha": sha, "report": report}
    return {"fallback": f"none of main's last {len(runs)} completed runs has a usable report artifact"}


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--out", type=Path, required=True)
    f.add_argument("--workflow", default="rpg-gate-report.yml")
    f.add_argument("--branch", default="main")
    f.add_argument("--exclude-run-id", default=None)
    args = parser.parse_args(argv)
    try:
        result: Any = fetch(workflow=args.workflow, branch=args.branch, exclude_run_id=args.exclude_run_id)
    except Exception as exc:  # noqa: BLE001 - any failure is a fallback, never a failed job
        result = {"fallback": f"fetching main's report failed ({type(exc).__name__})"}
    args.out.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    src = f"run {result['run_id']} head {str(result['head_sha'])[:9]}" if "report" in result else f"FALLBACK to the full rerun: {result['fallback']}"
    print(f"main report: {src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
