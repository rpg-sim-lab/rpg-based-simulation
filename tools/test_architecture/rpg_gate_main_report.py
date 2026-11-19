"""Fetch main's latest completed rpg gate report, the baseline the rerun skip and the "new vs main" diff are judged against.

TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN. Selection rule (decision a), in words:

1. Events: both ``schedule`` and ``workflow_dispatch`` runs count. The run's conclusion does not matter (main's own run is red on an inherited row and is
   exactly the baseline wanted); only "completed" does.
2. "Main" means the branch name ``main`` (``gh run list --branch main``) AND sha equality: the report's ``sha`` must equal the run's head sha, so the report was
   made from the commit the run is on. A dispatch whose ``ref`` input points elsewhere is passed over (the sha differs). "Main" is deliberately NOT decided by
   ancestry in main's history: the report job has a depth-1 checkout. That is a known limit, not an oversight.
3. So a dispatch on main whose ``ref`` input equals main's head at dispatch time DOES count (for example run 44452967207: head a30847030, ref input
   a30847030). The workflow's "evidence only, not a baseline source" label belongs to ``rebaseline`` (the baseline candidate) and has nothing to do with this
   rule; do not read it as an exclusion.
4. Branch runs (a dispatch on a PR branch) never count: ``--branch main`` excludes them. A completed run without a usable report artifact (the gate skipped it,
   it never reached the report, retention ran out) is passed over, at most ``MAX_RUNS`` deep. The NEWEST run that has an artifact decides: if that one is
   unreadable the answer is a fallback, never an older report.
5. Staleness: if that newest run's ``createdAt`` is older than ``main_report_max_age_days`` (``rpg_gate_main_report.yaml``, default file value 3) the answer is a
   fallback ("main's newest gate report is N days old, bound B"), never an older report. Staleness only ever gives a fuller rerun. A missing file, missing key
   or a value that is not a positive integer is also a fallback.


Output: one JSON file, either ``{"run_id", "head_sha", "report"}`` or ``{"fallback": "<why>"}``. Every failure (no ``gh``, an API error, a download error,
bad JSON, a run older than the bound, an invalid settings file) is a fallback record and exit 0, so the caller runs the full rerun. ``rpg_gate_report.load_main_baseline`` judges comparability.

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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, List, Mapping, Optional

import yaml

MAX_RUNS = 10
SETTINGS_PATH = Path(__file__).with_name("rpg_gate_main_report.yaml")
REPORT_NAME = "rpg-gate-report.json"

Gh = Callable[[List[str]], str]


def _gh(args: List[str]) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True, timeout=300).stdout


def load_max_age_days(path: Path = SETTINGS_PATH) -> int:
    """The staleness bound in days from the settings file; raises ``ValueError`` for an absent file, a missing key or a value that is not a positive integer."""
    try:
        value = (yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}).get("main_report_max_age_days")
    except (OSError, yaml.YAMLError, AttributeError) as exc:
        raise ValueError(f"settings file unusable ({type(exc).__name__})") from exc
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"main_report_max_age_days must be a positive integer, got {value!r}")
    return value


def _age_days(created: Any, now: datetime) -> Optional[int]:
    try:
        return max(0, (now - datetime.fromisoformat(str(created).replace("Z", "+00:00"))).days)
    except ValueError:
        return None


def fetch(gh: Gh = _gh, *, workflow: str = "rpg-gate-report.yml", branch: str = "main", exclude_run_id: Optional[str] = None, max_runs: int = MAX_RUNS,
          now: Optional[datetime] = None, settings: Path = SETTINGS_PATH) -> dict:
    """Return ``{"run_id", "head_sha", "report"}`` for main's newest usable completed run, or ``{"fallback": reason}``."""
    try:
        max_age_days = load_max_age_days(settings)
    except ValueError as exc:
        return {"fallback": f"the main-report settings are invalid: {exc}"}
    now = now or datetime.now(timezone.utc)
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
            continue  # a dispatch with a ref input that is not this run's head: the report is about another checkout
        age = _age_days(run.get("createdAt"), now)
        if age is None or age > max_age_days:
            return {"fallback": f"main's newest gate report is {'of unknown age' if age is None else f'{age} days old'}, bound {max_age_days}"}
        return {"run_id": run_id, "head_sha": sha, "event": run.get("event", ""), "age_days": age, "max_age_days": max_age_days, "report": report}
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
    src = f"run {result['run_id']} ({result['event']}, {str(result['head_sha'])[:8]}, {result['age_days']}d old, bound {result['max_age_days']}d)" if "report" in result else f"FALLBACK to the full rerun: {result['fallback']}"
    print(f"main report: {src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
