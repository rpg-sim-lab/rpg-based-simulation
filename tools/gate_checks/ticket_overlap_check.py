#!/usr/bin/env python3
"""Advisory check: does a newly filed ticket overlap an open one it does not cite?
(TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS)

    python3 tools/gate_checks/ticket_overlap_check.py <ticket.md> [<ticket.md> ...]
    python3 tools/gate_checks/ticket_overlap_check.py --report --since 2026-11-21

Run it by hand before committing a new `todos/` or `inprogress/` ticket; the pre-push advisory hook (check H) runs it on every
ticket file a push adds or changes. It uses `tools/open_ticket_overlap.py`'s term weighting and does NOT change that tool.

The rule (measured on origin/main 5bedb5ff0, 151 tickets filed in 21 days; labels by agent-working-planner and
rpg-planner-ubuntu on a 20-pair stratified sample):

* the draft's title and Request Summary are scored with every `TCK-...` id removed (an id typed in the text would otherwise add
  its words to the query);
* a hit is an open ticket whose weighted overlap is at least `Q_THRESHOLD` (0.25) of the draft's own total term weight
  (`q`; code areas add 10 per shared path to the matched weight, as in the tool). The raw score is not used: it grows with the
  length of the draft, so one absolute cutoff does not work;
* a hit the draft already names in `## Related Tickets` is silent; so is a draft whose `## Related Tickets` carries the line
  `overlap scan: <n> hits, none duplicate (<why>)` (checked for presence only; the reason is never judged);
* at most the top `TOP_N` (2) uncited hits are shown, ranked by q, in ONE line:
  `overlap scan: N candidate(s): <id> (<title>, q=<value>), ...`;
* only tickets dated on or after `OVERLAP_CHECK_REQUIRED_FROM` are checked; older ones are never warned.

Read this as a LOCATOR, not a duplicate verdict. On the 20 labelled pairs about half of the hits were useful (duplicate or
related; Wilson 95% interval roughly 28-72% on n=20), the other half were cited-and-fine or unrelated, and rank 1 is not a
precision signal (three of the ten unrelated pairs were rank 1). About 47% of new tickets will see a line: that is the price of
keeping the owner-named inn-meal miss (q 0.259). A person or an agent decides whether a hit is a duplicate.

Advisory only: exit 0 on every input. A file that cannot be scanned is a named warning (`overlap scan: ERROR <path>: ...`),
never a silent pass; every run prints `ran / skipped / errored` counts per file class on stderr.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import NamedTuple, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
_TOOLS_DIR = _REPO_ROOT / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import open_ticket_overlap as ov  # noqa: E402
from generate_registry import _strip_frontmatter, parse_body_section, parse_related_code_areas  # noqa: E402
from validate_frontmatter import extract_frontmatter  # noqa: E402

Q_THRESHOLD = 0.25
TOP_N = 2
#: The day after the check landed: a ticket dated before it is grandfathered (as the lifecycle-section check did).
OVERLAP_CHECK_REQUIRED_FROM = "2026-11-21"
LINE_PREFIX = "overlap scan:"

_ID_RE = re.compile(r"TCK-\d{8}-[A-Z0-9-]*[A-Z0-9]")
_ANY_ID_RE = re.compile(r"TCK-[A-Z0-9][A-Z0-9-]*")
_WAIVER_RE = re.compile(r"overlap scan:\s*\d+\s+hits?,\s*none duplicate\s*\(.+\)", re.IGNORECASE)
_TITLE_MAX = 80
_OPEN_FOLDERS = ("todos", "inprogress")


class Hit(NamedTuple):
    ticket_id: str
    title: str
    q: float


class Result(NamedTuple):
    path: str
    status: str  # ran | skipped | errored
    reason: str  # why it was skipped or what failed; "" for ran
    hits: tuple  # the uncited hits shown (at most TOP_N), best first
    waived: bool
    cited_all: bool  # every candidate at or above the threshold was already cited (or there were none)


def _open_folder(path: Path) -> Optional[str]:
    parts = path.as_posix().split("/")
    for folder in _OPEN_FOLDERS:
        if folder in parts and "tickets" in parts:
            return folder
    return None


def _load_candidates(todos_root: Path, inprogress_root: Path, own_id: str) -> list:
    paths = []
    for root in (todos_root, inprogress_root):
        if root.exists():
            paths.extend(sorted(root.rglob("TCK-*.md")))
    out = []
    for p in paths:
        loaded = ov._load_ticket(p)
        if loaded is None or loaded["ticket_id"] == own_id:
            continue
        loaded["terms"] = ov._distinctive_terms(f"{loaded['title']} {loaded['summary']}")
        out.append(loaded)
    return out


def score_hits(title: str, summary: str, areas: list, own_id: str, todos_root: Path, inprogress_root: Path) -> list:
    """Every open ticket (other than the draft) with q >= Q_THRESHOLD, best first, as `Hit`s. The draft's text is scored with
    ids removed. q = (sum of IDF weights of the shared distinctive terms + 10 per shared code area) / (sum of IDF weights of all
    the draft's distinctive terms), the IDF taken over the candidate corpus exactly as `open_ticket_overlap` does."""
    cands = _load_candidates(todos_root, inprogress_root, own_id)
    if not cands:
        return []
    q_terms = ov._distinctive_terms(f"{_ID_RE.sub(' ', title)} {_ID_RE.sub(' ', summary)}")
    n_docs = len(cands)
    doc_freq = ov._build_doc_freq([c["terms"] for c in cands])
    total = sum(ov._idf(t, doc_freq, n_docs) for t in q_terms)
    if total <= 0:
        return []
    area_set = set(areas)
    hits = []
    for c in cands:
        shared = q_terms & c["terms"]
        raw = sum(ov._idf(t, doc_freq, n_docs) for t in shared) + ov._CODE_AREA_WEIGHT * len(area_set & set(c["code_areas"]))
        q = raw / total
        if q >= Q_THRESHOLD:
            hits.append(Hit(c["ticket_id"], " ".join((c["title"] or "").split())[:_TITLE_MAX], round(q, 3)))
    hits.sort(key=lambda h: h.q, reverse=True)
    return hits


def check_file(path: Path, required_from: str = OVERLAP_CHECK_REQUIRED_FROM, todos_root: Optional[Path] = None,
               inprogress_root: Optional[Path] = None) -> Result:
    """Scan one ticket file. Never raises: any failure is an `errored` Result that names the error."""
    todos_root = todos_root if todos_root is not None else ov._DEFAULT_TODOS_ROOT
    inprogress_root = inprogress_root if inprogress_root is not None else ov._DEFAULT_INPROGRESS_ROOT
    shown = str(path)
    try:
        if not path.is_file():
            return Result(shown, "errored", "not a readable file", (), False, False)
        if _open_folder(path) is None and not _under(path, todos_root, inprogress_root):
            return Result(shown, "skipped", "not under todos/ or inprogress/", (), False, False)
        text = path.read_text(encoding="utf-8")
        fm = extract_frontmatter(text) or {}
        ticket_id = fm.get("ticket_id")
        if not ticket_id:
            return Result(shown, "skipped", "no ticket_id in the frontmatter", (), False, False)
        date = str(fm.get("date") or "")
        if not date or date < required_from:
            return Result(shown, "skipped", f"dated {date or 'nothing'}, before {required_from} (grandfathered)", (), False, False)
        body = _strip_frontmatter(text)
        related = parse_body_section(body, "Related Tickets") or ""
        if _WAIVER_RE.search(related):
            return Result(shown, "ran", "", (), True, True)
        cited = set(_ANY_ID_RE.findall(related))
        areas = parse_related_code_areas(parse_body_section(body, "Related Code Areas"))
        title = parse_body_section(body, "Title") or ""
        summary = parse_body_section(body, "Request Summary") or ""
        hits = score_hits(title, summary, list(areas), ticket_id, todos_root, inprogress_root)
        uncited = [h for h in hits if h.ticket_id not in cited]
        return Result(shown, "ran", "", tuple(uncited[:TOP_N]), False, not uncited)
    except Exception as exc:  # a scanner failure is a named warning, never a silent pass
        return Result(shown, "errored", f"{type(exc).__name__}: {exc}", (), False, False)


def _under(path: Path, *roots: Path) -> bool:
    try:
        resolved = path.resolve()
        return any(resolved.is_relative_to(r.resolve()) for r in roots)
    except OSError:
        return False


def render_line(result: Result) -> Optional[str]:
    """The one advisory line for a file, or None when it is silent (cited, waived, clean or grandfathered)."""
    if result.status == "errored":
        return f"{LINE_PREFIX} ERROR {result.path}: {result.reason}"
    if result.status != "ran" or not result.hits:
        return None
    parts = ", ".join(f"{h.ticket_id} ({h.title}, q={h.q:.2f})" for h in result.hits)
    n = len(result.hits)
    return (f"{LINE_PREFIX} {result.path}: {n} candidate{'s' if n != 1 else ''}: {parts}. Cite the ones that matter in `## Related Tickets`, or add "
            f"`{LINE_PREFIX} <n> hits, none duplicate (<why>)` there. A locator, not a verdict.")


def check_files(paths: list, **kwargs) -> tuple:
    """(lines, counts): the advisory lines for the files that need one, and {'ran': n, 'skipped': n, 'errored': n}."""
    counts = {"ran": 0, "skipped": 0, "errored": 0}
    lines = []
    for p in paths:
        result = check_file(Path(p), **kwargs)
        counts[result.status] += 1
        line = render_line(result)
        if line:
            lines.append(line)
    return lines, counts


def report(since: str, todos_root: Optional[Path] = None, inprogress_root: Optional[Path] = None) -> tuple:
    """(rows, summary) over every open ticket dated on or after `since`: how many still carry an uncited candidate, how many carry
    a waiver line, how many are clean or errored. Report-only; the efficacy measure for the check."""
    todos_root = todos_root if todos_root is not None else ov._DEFAULT_TODOS_ROOT
    inprogress_root = inprogress_root if inprogress_root is not None else ov._DEFAULT_INPROGRESS_ROOT
    paths = []
    for root in (todos_root, inprogress_root):
        if root.exists():
            paths.extend(sorted(root.rglob("TCK-*.md")))
    rows = []
    tally = {"checked": 0, "uncited": 0, "waived": 0, "clean": 0, "errored": 0, "skipped": 0}
    for p in paths:
        r = check_file(p, since, todos_root, inprogress_root)
        if r.status == "skipped":
            tally["skipped"] += 1
            continue
        tally["checked"] += 1
        if r.status == "errored":
            tally["errored"] += 1
            rows.append((r.path, "errored", r.reason))
        elif r.waived:
            tally["waived"] += 1
            rows.append((r.path, "waived", ""))
        elif r.hits:
            tally["uncited"] += 1
            rows.append((r.path, "uncited", "; ".join(f"{h.ticket_id} q={h.q:.2f}" for h in r.hits)))
        else:
            tally["clean"] += 1
    return rows, tally


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Advisory overlap check for newly filed tickets (always exits 0).")
    parser.add_argument("paths", nargs="*", help="ticket files to scan")
    parser.add_argument("--report", action="store_true", help="list open tickets dated since --since with their overlap state")
    parser.add_argument("--since", default=OVERLAP_CHECK_REQUIRED_FROM, help="with --report: the first filing date to include (YYYY-MM-DD)")
    parser.add_argument("--todos-root", type=Path, default=None)
    parser.add_argument("--inprogress-root", type=Path, default=None)
    args = parser.parse_args(argv)
    try:
        if args.report:
            rows, tally = report(args.since, args.todos_root, args.inprogress_root)
            for path, state, detail in rows:
                print(f"{state:8} {path}" + (f"  {detail}" if detail else ""))
            print(f"overlap scan report since {args.since}: {tally['checked']} ticket(s) checked, {tally['uncited']} with an uncited candidate, "
                  f"{tally['waived']} waived, {tally['clean']} clean, {tally['errored']} errored, {tally['skipped']} older/skipped", file=sys.stderr)
            return 0
        lines, counts = check_files(args.paths, todos_root=args.todos_root, inprogress_root=args.inprogress_root)
        for line in lines:
            print(line)
        print(f"overlap scan: ran {counts['ran']}, skipped {counts['skipped']}, errored {counts['errored']}", file=sys.stderr)
    except Exception as exc:  # advisory: never a traceback, never a nonzero exit
        print(f"{LINE_PREFIX} ERROR the checker itself failed: {type(exc).__name__}: {exc}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
