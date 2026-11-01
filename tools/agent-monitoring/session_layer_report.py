"""tools/agent-monitoring/session_layer_report.py: the session-layer measures added to the existing retro report
(TCK-20261004-SESSION-LAYER-M6A-MINIMUM-MEASUREMENT; no new report). Pure rendering over already-collected
records, so it is testable without a data tree.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from batch_latency import render_row
from manual_actions import CATEGORIES, count_by_category
from session_role import UNRESOLVED

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.append(str(_REPO_ROOT))
from tools.sessions.classify import is_governing_path  # noqa: E402

PREDATES = "predates field"

_LABELS = {
    "role_reminder": "role reminder", "routing_correction": "routing correction", "manual_wake": "manual wake",
    "worktree_correction": "worktree correction", "boundary_reminder": "boundary reminder",
    "handover_recovery": "handover recovery",
}


def load_family(data_dir: Path, filename: str) -> list[dict]:
    """Every record of one new file family (`manual_actions.jsonl`, `role_boundary.jsonl`) across the week folders."""
    out: list[dict] = []
    for path in sorted(Path(data_dir).glob(f"*/{filename}")):
        for line in path.read_text().splitlines():
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict):
                out.append(rec)
    return out


def in_period(records: list[dict], week_str: str | None = None, cutoff: str | None = None) -> list[dict]:
    from datetime import datetime

    def keep(rec: dict) -> bool:
        ts = rec.get("ts")
        if not isinstance(ts, str):
            return False
        if week_str is not None:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%G-W%V") == week_str
            except ValueError:
                return False
        return cutoff is None or ts >= cutoff

    return [r for r in records if keep(r)]


def _dark(family: str, total: int | None, in_period_n: int) -> str | None:
    """The line for a family that cannot be read as zeros, or None when its zeros are real.

    `total` is every record of the family in any week; None means the caller did not count (old behaviour).
    """
    if total is None or total > 0 and in_period_n:
        return None
    if total == 0:
        return (f"_Instrument not running: no {family} records exist in any week. "
                "Zeros below would be meaningless, so the table is omitted._")
    return f"_(instrument active; {total - in_period_n} records outside this period)_"


def _manual_lines(manual: list[dict], total: int | None) -> list[str]:
    lines = ["### Manual orchestration actions", ""]
    note = _dark("manual_actions", total, len(manual))
    if total == 0:
        return lines + [note, ""]
    counts = count_by_category(manual)
    lines += ["| category | sample | tally |", "|---|---|---|"]
    for cat in CATEGORIES:
        lines.append(f"| {_LABELS[cat]} | {counts[cat]['sample']} | {counts[cat]['tally']} |")
    count = sum(v["sample"] + v["tally"] for v in counts.values())
    lines += ["", f"Total: {count}. Per-batch: tally with `manual_actions.py tally <category> --batch <id>`."]
    return lines + ([note] if note else []) + [""]


def merged_governing_commits(week_str: str | None, cutoff: str | None, ref: str = "origin/main", run=subprocess.run) -> dict[str, int] | None:
    """{governing path: merged commits touching it in the period} from `git log <ref>`, or None when git cannot say.

    Same path definition as the guard rows and the PR list (`classify.is_governing_path`). Period = commit date, like the rows."""
    try:
        if week_str:
            year, week = week_str.split("-W")
            since = datetime.fromisocalendar(int(year), int(week), 1).replace(tzinfo=timezone.utc) - timedelta(days=1)
            since_arg = since.isoformat()
        else:
            since_arg = cutoff or "1970-01-01"
        out = run(["git", "log", ref, f"--since={since_arg}", "--name-only", "--format=@@%cI"], cwd=_REPO_ROOT, capture_output=True,
                  text=True, timeout=60)
        if out.returncode != 0:
            return None
    except Exception:  # noqa: BLE001 - the retro line must never fail the report
        return None
    counts: Counter = Counter()
    touched: set[str] = set()
    keep = False
    for line in out.stdout.splitlines():
        if line.startswith("@@"):
            counts.update(touched)
            touched = set()
            keep = bool(in_period([{"ts": line[2:]}], week_str, cutoff))
        elif keep and line.strip() and is_governing_path(line.strip()):
            touched.add(line.strip())
    counts.update(touched)
    return dict(counts)


def _governing_lines(attempts: list[dict], total: int | None, merged: dict[str, int] | None) -> list[str]:
    lines = ["### Governing-file edit attempts (report-only)", "",
             "_Rows are written by the guard at PreToolUse, so each is an ATTEMPT. `edit` rows (basis `path`, an edit tool) are "
             "exact; `mention` rows (basis `mention`, a Bash command naming the path) may not be edits and over-count. Edit-tool "
             "rows for files outside the repo are not written. Merged commits are counted by path and period from `origin/main`, "
             "with the same path list the PR body uses; an attempt cannot be tied to one PR body._", ""]
    note = _dark("governing_edits", total, len(attempts))
    if total == 0:
        return lines + [note, ""]
    by_path: dict[str, Counter] = {}
    for a in attempts:
        by_path.setdefault(str(a.get("path") or "unknown"), Counter())[str(a.get("basis") or "unknown")] += 1
    if not by_path:
        lines.append("None in this period.")
    else:
        lines += ["| path | edit attempts | Bash mentions | merged commits |", "|---|---|---|---|"]
        for path in sorted(by_path):
            c = by_path[path]
            lines.append(f"| {path} | {c['path']} | {c['mention']} | {merged.get(path, 0) if merged is not None else 'unknown'} |")
    if merged is None:
        lines += ["", "_Merged commits unavailable (git could not be read), so nothing is matched._"]
    else:
        edits = sum(c["path"] for c in by_path.values())
        mentions = sum(c["mention"] for c in by_path.values())
        lines += ["", f"Totals: {edits} edit attempts, {mentions} Bash mentions; {sum(merged.values())} merged commits touching a "
                  "governing path (counted per path)."]
        unmatched = sorted(p for p, c in by_path.items() if c["path"] and not merged.get(p))
        lines += ["Edit attempts with no merged commit on that path in the period: " + (", ".join(unmatched) if unmatched else "none") + "."]
        unattempted = sorted(p for p, n in merged.items() if n and not by_path.get(p, Counter())["path"])
        lines += ["Governing paths with merged commits and no edit attempt row in the period: "
                  + (", ".join(unattempted) if unattempted else "none") + "."]
        lines += ["_Unmatched means one of: the edit was reverted, the call was denied or failed, the work has not merged "
                  "yet (an attempt in one week can merge the next), or a real edit never went through review. A merged path "
                  "with no attempt row can mean the edit was made where no row is written (see the limits below), or its "
                  "rows sit on an unmerged branch or the other host. Rows reach main only when a branch carries them, so a "
                  "missing row can also mean its branch is unmerged. A prompt to look, not a violation count._"]
    lines += ["_Limits: a Bash edit that does not name the path from the repo root (e.g. `cd tools/sessions && sed -i ... guard.py`) "
              "or that sits inside an interpreter payload writes no row, so an empty count does not mean no edits. A mention can "
              "also name a same-suffix file outside the repo (e.g. a user-level settings file)._"]
    if note:
        lines.append(note)
    return lines + [""]


def render(manual: list[dict], runs: list[dict], boundary: list[dict], latency_rows: list[tuple[str, dict]] | None = None,
           manual_total: int | None = None, boundary_total: int | None = None, governing: list[dict] | None = None,
           governing_total: int | None = None, merged: dict[str, int] | None = None) -> str:
    lines = ["## Session-Layer Measures", "",
             "_Headline metric and batch latency from `docs/plans/agent_infrastructure/session_layer_working_process.md` "
             "section 11. Counts are repeated instructions, never decisions, design feedback or requirements. "
             "`sample` is the conservative prompt tagger (under-counts); `tally` is the owner's own line per batch._", ""]
    lines += _manual_lines(manual, manual_total)
    # TCK-20261006-SESSION-START-CLEAR-FALSE-LIVE-HOLDER-WARNING (Scope 3): a run with no `session_role` key predates the field, which
    # is not the same as a run stamped `unresolved` because no binding named its closing session.
    roles = Counter(PREDATES if "session_role" not in r else str(r.get("session_role") or UNRESOLVED) for r in runs)
    lines += ["### Runs by session role", ""]
    if roles:
        lines += ["| session_role | runs |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(roles.items())]
    else:
        lines.append("No runs in this period.")
    if set(roles) - {PREDATES} == {UNRESOLVED}:
        lines += ["", "_No run in this period had a resolved role, so role binding was not active._"]
    lines += ["", f"_`{PREDATES}` = recorded before `session_role` existed (no key); `{UNRESOLVED}` = stamped, but no binding named the closing "
              "session (a plain session, or one started outside a current worktree)._", ""]
    kinds = Counter(str(b.get("kind") or "unknown") for b in boundary)
    lines += ["### `role_boundary` warnings (advisory)", ""]
    note = _dark("role_boundary", boundary_total, len(boundary))
    if boundary_total == 0:
        lines.append(note)
    else:
        lines.append(", ".join(f"{k}: {v}" for k, v in sorted(kinds.items())) if kinds else "None in this period.")
        if note:
            lines.append(note)
    if governing is not None:
        lines += [""] + _governing_lines(governing, governing_total, merged)
    lines += ["", "### Batch latency", ""]
    if latency_rows:
        lines += ["| batch | implementation | finalization | cycle | dispatch from |", "|---|---|---|---|---|"]
        lines += [render_row(label, result) for label, result in latency_rows]
        lines.append("")
        lines.append("_Dispatch defaults to the batch's first commit (the dispatch message leaves no repo artifact); "
                     "`unknown` means a timestamp was unavailable, never zero._")
    else:
        lines.append("Not computed for this report. Pass `--latency-prs <N> ...` to derive implementation, finalization "
                     "and cycle time from merged PRs (`unknown` when a timestamp is unavailable, never zero).")
    lines.append("")
    return "\n".join(lines)
