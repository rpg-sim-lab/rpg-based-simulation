#!/usr/bin/env python3
"""Advisory drift report for docs that carry evidence fields, plus the J1 stale-doc detection mode.

TCK-20261108-DOC-EVIDENCE-FIELDS-AND-DRIFT-REPORT and TCK-20261108-STALE-DOC-DETECTION-PILOT. Spec: the plan
`agent-working/lead/docs_as_review_source_plan.md` (rev 3.2), P1 "Drift report" and "Batch J". The pattern it follows is
`tools/mechanism_registry/mechanism_registry_changed_code_check.py` (a report of changed code a record cites); the
location is beside `docs_search.py`, whose exclusion classes it reuses.

Fields (optional frontmatter, shapes checked by `tools/validate_frontmatter.py`): `evidence_paths` (a list of files),
`verified_by` (a TCK-ID or `#<PR>`), `verified_at` (a commit SHA), `reviewed_by` (as `verified_by`, but weaker:
"triaged, no staleness found", never shown as verified).

Rules, stated once:
- Pin. Every read is `git show <sha>:path` or a git command against the resolved full SHA, which the report prints
  first. The working tree is never read, and nothing is written.
- Baseline. The last commit reachable from the pin that changed the doc's `verified_by:` line (`reviewed_by:` when
  only that is set), found with `git log -G`. It depends only on commits on the pin, so it survives a squash merge,
  and it includes the verifying PR's own edits. A commit that removes the line is the last such commit, and the doc
  then reads as unverified (no field at the pin, so no baseline is needed).
- Needs re-verify. True when, after the baseline, (a) an evidence path changed, was deleted, or was renamed (the new
  name is shown), or (b) the doc's text changed. Text changed means any diff to the doc after the baseline except the
  `verified_by:`, `verified_at:` and `reviewed_by:` lines; an edit to `evidence_paths:` counts, because it was not
  verified. Renames are found with `git diff -M --name-status <baseline> <pin>` run WITHOUT a pathspec (a pathspec
  limited to the old names would show a rename to a new directory as a delete) and filtered by old path in Python.
- States, strongest to weakest: needs-re-verify, verified_by, reviewed_by, unverified. A doc with no field is
  unverified. A doc whose baseline cannot be found (a shallow clone) is `baseline-unavailable`, never an error.
- Detection mode (J1). Every signal means "possibly stale", never "wrong". Docs that carry `verified_by` or
  `reviewed_by` are judged by the baseline rule above and stay quiet while it is clean; the J signals apply to all
  other live docs. Excluded classes (archive, audits, registry, historical status, review records, brainstorm) are
  skipped. Signals: `evidence-newer` (a cited code path whose last commit is later than the doc's last commit),
  `unresolved-name` (a cited path, or an identifier-shaped backticked name, that the pinned tree does not resolve; a
  renamed path shows its new name), and `plan-lifecycle` (a `docs/plans/` file whose `status` is not one of the
  finished values below, whose cited tickets are all under `tickets/done/`).
- Advisory. The exit status is always 0. A failure prints `MARKER:{"error": ...}`. Nothing blocks.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

_TOOLS = str(Path(__file__).resolve().parents[1])
_REPO = str(Path(__file__).resolve().parents[2])
for _p in (_TOOLS, _REPO):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import validate_frontmatter  # noqa: E402 - needs the sys.path entries above
from gate_checks import docs_search  # noqa: E402
from gate_checks.changed_files import derive_changed_files  # noqa: E402
from tools.sessions.route import route as route_path  # noqa: E402

P1_FIELDS = ("evidence_paths", "verified_by", "verified_at", "reviewed_by")
#: Lines the doc-text rule ignores. `evidence_paths:` is deliberately not here.
IGNORED_TEXT_FIELDS = ("verified_by", "verified_at", "reviewed_by")
#: `status` values that mean a plan is finished, from `validate_frontmatter.STATUS_VALUES` (docs/guidelines/frontmatter_schema.md).
FINISHED_STATUSES = {"historical", "archive"} & validate_frontmatter.STATUS_VALUES

DOCS_ROOT = "docs/"
SKIPPED_PREFIXES = ("docs/brainstorm/",)
TIME_PATHSPECS = ("docs", "src", "tests", "tools", "registries", "codebase", "frontend")
CODE_PREFIXES = ("src/", "tests/", "tools/", "registries/", "codebase/", "frontend/")
SYMBOL_CORPUS_SUFFIXES = (".py", ".yaml", ".yml", ".json", ".toml", ".js", ".ts", ".tsx")
SYMBOL_CORPUS_PREFIXES = ("src/", "tools/", "tests/", "registries/", "codebase/", "frontend/")

STATES = ("needs-re-verify", "baseline-unavailable", "verified_by", "reviewed_by", "unverified")
SIGNAL_WEIGHT = {"evidence-newer": 3, "plan-lifecycle": 2, "unresolved-name": 1}

_CITED_PATH = re.compile(
    r"(?<![\w/.-])((?:src|tests|tools|registries|codebase|frontend)/[\w./-]*[\w-]\.(?:py|yaml|yml|json|jsonl|toml|js|jsx|ts|tsx|sh|csv|html|css|txt))"
)
_BACKTICK_NAME = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)(?:\(\))?`")
_TICKET_ID = re.compile(r"TCK-\d{8}-[A-Z0-9]+(?:-[A-Z0-9]+)*")
_TOKEN = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


# --- git ------------------------------------------------------------------------------------------------------------


class Repo:
    """Read-only git access at one resolved pin."""

    def __init__(self, root: Path, ref: str = "HEAD"):
        self.root = Path(root)
        self.ref = ref
        self.pin: Optional[str] = None
        self._name_status: Dict[str, Dict[str, Tuple[str, Optional[str]]]] = {}
        self._tree: Optional[Set[str]] = None
        self._shallow: Optional[Set[str]] = None

    def git(self, *args: str) -> Optional[str]:
        proc = subprocess.run(
            ["git", "-c", "core.quotepath=false", *args], cwd=self.root, capture_output=True, check=False,
        )
        return proc.stdout.decode("utf-8", errors="replace") if proc.returncode == 0 else None

    def resolve(self) -> Optional[str]:
        out = self.git("rev-parse", "--verify", f"{self.ref}^{{commit}}")
        self.pin = out.strip() if out else None
        return self.pin

    def tree(self) -> Set[str]:
        if self._tree is None:
            out = self.git("ls-tree", "-r", "--name-only", self.pin or self.ref)
            self._tree = set(out.splitlines()) if out else set()
        return self._tree

    def source(self) -> "docs_search.GitRefSource":
        return docs_search.GitRefSource(self.root, self.pin or self.ref)

    def last_commit_times(self, pathspecs: Sequence[str] = TIME_PATHSPECS) -> Dict[str, int]:
        """Last commit time per path in ONE pass: `git log` is newest first, so the first time a path is seen wins."""
        out = self.git("log", "--format=%x01%ct", "--name-only", self.pin or self.ref, "--", *pathspecs)
        times: Dict[str, int] = {}
        current = 0
        for line in (out or "").splitlines():
            if line.startswith("\x01"):
                current = int(line[1:] or 0)
            elif line and line not in times:
                times[line] = current
        return times

    def rename_map(self, pathspecs: Sequence[str] = TIME_PATHSPECS) -> Dict[str, str]:
        """old path -> newest known new path, from one rename-detecting pass (newest rename seen first wins)."""
        out = self.git("log", "-M", "--diff-filter=R", "--name-status", "--format=", self.pin or self.ref, "--", *pathspecs)
        renames: Dict[str, str] = {}
        for line in (out or "").splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and parts[0].startswith("R") and parts[1] not in renames:
                renames[parts[1]] = parts[2]
        return renames

    def shallow_boundary(self) -> Set[str]:
        """Commits at a shallow clone's cut: their history is missing, so a baseline found there is not a real one."""
        if self._shallow is None:
            git_dir = self.git("rev-parse", "--git-dir")
            self._shallow = set()
            if git_dir:
                shallow_file = (self.root / git_dir.strip() / "shallow")
                if shallow_file.is_file():
                    self._shallow = set(shallow_file.read_text(encoding="utf-8").split())
        return self._shallow

    def baseline(self, doc: str, field: str) -> Optional[str]:
        out = self.git("log", "-1", "--follow", "--format=%H", f"-G^{field}:", self.pin or self.ref, "--", doc)
        found = out.strip() if out else ""
        return found if found and found not in self.shallow_boundary() else None

    def name_status(self, base: str) -> Dict[str, Tuple[str, Optional[str]]]:
        """path -> (code, new_name) for `git diff -M --name-status <base> <pin>` with NO pathspec, keyed by old path."""
        if base not in self._name_status:
            out = self.git("diff", "-M", "--name-status", base, self.pin or self.ref) or ""
            table: Dict[str, Tuple[str, Optional[str]]] = {}
            for line in out.splitlines():
                parts = line.split("\t")
                if parts[0].startswith("R") and len(parts) == 3:
                    table[parts[1]] = ("R", parts[2])
                elif len(parts) == 2:
                    table[parts[1]] = (parts[0][:1], None)
            self._name_status[base] = table
        return self._name_status[base]

    def doc_text_changed(self, base: str, doc: str) -> bool:
        """True if the doc has any diff after `base` other than the lines in IGNORED_TEXT_FIELDS."""
        moved_from = [old for old, (code, new) in self.name_status(base).items() if code == "R" and new == doc]
        specs = [doc, *moved_from]
        out = self.git("diff", "-M", "-U0", base, self.pin or self.ref, "--", *specs) or ""
        ignored = tuple(f"{field}:" for field in IGNORED_TEXT_FIELDS)
        for line in out.splitlines():
            if line.startswith(("+++", "---")) or not line.startswith(("+", "-")):
                continue
            if line[1:].lstrip().startswith(ignored):
                continue
            return True
        return False


# --- parsing --------------------------------------------------------------------------------------------------------


def p1_fields(text: str) -> Dict[str, object]:
    try:
        fm = validate_frontmatter.extract_frontmatter(text) or {}
    except ValueError:
        return {}
    return {k: fm[k] for k in P1_FIELDS if k in fm and fm[k] not in ("", [], None)}


def frontmatter_status(text: str) -> Optional[str]:
    try:
        fm = validate_frontmatter.extract_frontmatter(text) or {}
    except ValueError:
        return None
    value = fm.get("status")
    return str(value).lower() if value else None


def cited_paths(text: str) -> List[str]:
    seen: List[str] = []
    for match in _CITED_PATH.finditer(text):
        path = match.group(1)
        if path not in seen:
            seen.append(path)
    return seen


def evidence_for(fields: Dict[str, object], text: str) -> List[str]:
    listed = fields.get("evidence_paths")
    if isinstance(listed, list) and listed:
        return [str(p) for p in listed]
    return cited_paths(text)


# --- the drift report (drift mode) -----------------------------------------------------------------------------------


def classify(repo: Repo, doc: str, text: str, extra_changed: Iterable[str] = ()) -> dict:
    """The P1 state of one doc at the pin. `extra_changed` are uncommitted working-diff paths treated as changed."""
    fields = p1_fields(text)
    row: dict = {"path": doc, "state": "unverified", "reasons": [], "fields": sorted(fields)}
    field = "verified_by" if "verified_by" in fields else "reviewed_by" if "reviewed_by" in fields else None
    if field is None:
        return row
    base = repo.baseline(doc, field)
    if base is None:
        row["state"] = "baseline-unavailable"
        return row
    row["baseline"] = base
    extra = set(extra_changed)
    table = repo.name_status(base)
    tree = repo.tree()
    reasons: List[str] = []
    for path in evidence_for(fields, text):
        code, new = table.get(path, ("", None))
        if code == "R":
            reasons.append(f"evidence renamed: {path} -> {new}")
        elif code == "D":
            reasons.append(f"evidence deleted: {path}")
        elif code and code != "A":
            reasons.append(f"evidence changed: {path}")
        elif path in extra:
            reasons.append(f"evidence changed (uncommitted): {path}")
        elif path not in tree:
            reasons.append(f"evidence missing at the pin: {path}")
    if repo.doc_text_changed(base, doc):
        reasons.append("doc text changed after the baseline")
    row["reasons"] = reasons
    row["state"] = "needs-re-verify" if reasons else field
    return row


def drift_report(repo: Repo, docs: Optional[Sequence[str]] = None, extra_changed: Iterable[str] = ()) -> dict:
    corpus = repo.source().read_many(
        docs if docs is not None else [p for p in sorted(repo.tree()) if p.startswith(DOCS_ROOT) and p.endswith(".md")]
    )
    rows = []
    without_fields = 0
    for path in sorted(corpus):
        if docs is None and not p1_fields(corpus[path]):
            without_fields += 1
            continue
        rows.append(classify(repo, path, corpus[path], extra_changed))
    rows.sort(key=lambda r: (STATES.index(r["state"]), r["path"]))
    counts = {state: sum(1 for r in rows if r["state"] == state) for state in STATES}
    return {"mode": "drift", "pin": repo.pin, "docs": rows, "counts": counts, "docs_without_fields": without_fields}


# --- detection mode (J1) ----------------------------------------------------------------------------------------------


def _symbol_tokens(repo: Repo) -> Set[str]:
    paths = [p for p in repo.tree() if p.startswith(SYMBOL_CORPUS_PREFIXES) and p.endswith(SYMBOL_CORPUS_SUFFIXES)]
    source = repo.source()
    tokens: Set[str] = set()
    for start in range(0, len(paths), 400):
        for text in source.read_many(paths[start:start + 400]).values():
            tokens.update(_TOKEN.findall(text))
    return tokens


def _domain(path: str) -> str:
    try:
        result = route_path(path)
    except Exception:  # noqa: BLE001 - an unreadable roster only loses the domain label
        return "unowned"
    return result.domains[0] if result.domains else "unowned"


def detect(repo: Repo, extra_changed: Iterable[str] = ()) -> dict:
    started = time.monotonic()
    tree = repo.tree()
    times = repo.last_commit_times()
    renames = repo.rename_map()
    done_ids = {
        Path(p).stem for p in tree if p.startswith("agent-working/tickets/done/") and p.endswith(".md")
    }
    doc_paths = [p for p in sorted(tree) if p.startswith(DOCS_ROOT) and p.endswith(".md") and not p.startswith(SKIPPED_PREFIXES)]
    corpus = repo.source().read_many(doc_paths)
    tokens = _symbol_tokens(repo)
    skipped: Dict[str, int] = {}
    quiet = 0
    flagged: List[dict] = []
    for path in doc_paths:
        text = corpus.get(path)
        if text is None:
            continue
        reason = docs_search.exclusion_reason(path, text)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
            continue
        fields = p1_fields(text)
        if "verified_by" in fields or "reviewed_by" in fields:
            row = classify(repo, path, text, extra_changed)
            if row["state"] == "needs-re-verify":
                flagged.append({"path": path, "domain": _domain(path), "signals": {"needs-re-verify": row["reasons"]},
                                "score": (9, 0, 0)})
            else:
                quiet += 1
            continue
        signals: Dict[str, object] = {}
        doc_time = times.get(path, 0)
        cited = cited_paths(text)
        newer = [(p, times[p] - doc_time) for p in cited if p in tree and p.startswith(CODE_PREFIXES) and times.get(p, 0) > doc_time]
        if newer:
            signals["evidence-newer"] = {
                "newer": len(newer), "cited": sum(1 for p in cited if p in tree),
                "max_lag_days": round(max(lag for _, lag in newer) / 86400, 1), "paths": [p for p, _ in sorted(newer)][:8],
            }
        unresolved = []
        for p in cited:
            if p not in tree:
                unresolved.append({"name": p, "renamed_to": renames.get(p)})
        for name in dict.fromkeys(_BACKTICK_NAME.findall(text)):
            if docs_search.identifier_shaped(name) and name not in tokens:
                unresolved.append({"name": name, "renamed_to": None})
        if unresolved:
            signals["unresolved-name"] = {"count": len(unresolved), "names": unresolved[:8]}
        if path.startswith("docs/plans/") and frontmatter_status(text) not in FINISHED_STATUSES:
            ids = set(_TICKET_ID.findall(text))
            if ids and ids <= done_ids:
                signals["plan-lifecycle"] = {"cited_tickets": len(ids), "all_done": True}
        if signals:
            score = (
                sum(SIGNAL_WEIGHT[s] for s in signals),
                signals.get("evidence-newer", {}).get("max_lag_days", 0) if isinstance(signals.get("evidence-newer"), dict) else 0,
                signals.get("evidence-newer", {}).get("newer", 0) if isinstance(signals.get("evidence-newer"), dict) else 0,
            )
            flagged.append({"path": path, "domain": _domain(path), "signals": signals, "score": score})
    flagged.sort(key=lambda r: tuple(-x for x in r["score"]) + (r["path"],))
    by_domain: Dict[str, List[dict]] = {}
    for row in flagged:
        by_domain.setdefault(row["domain"], []).append(row)
    by_signal: Dict[str, int] = {}
    for row in flagged:
        for signal in row["signals"]:
            by_signal[signal] = by_signal.get(signal, 0) + 1
    return {
        "mode": "detect", "pin": repo.pin, "docs_scanned": len(doc_paths), "excluded": skipped,
        "live_docs": len(doc_paths) - sum(skipped.values()),
        "quiet_with_clean_baseline": quiet, "flagged": len(flagged), "by_signal": by_signal,
        "by_domain": {d: len(v) for d, v in sorted(by_domain.items())}, "ranked": by_domain,
        "wall_seconds": round(time.monotonic() - started, 1),
    }


# --- output -----------------------------------------------------------------------------------------------------------


def render_text(report: dict, limit: int = 10) -> str:
    lines = [f"doc drift report ({report['mode']}) at pin {report['pin']} (read-only; advisory, never blocks)"]
    if report["mode"] == "drift":
        lines.append("counts: " + ", ".join(f"{k}={v}" for k, v in report["counts"].items()) +
                     f"; docs without any P1 field: {report['docs_without_fields']}")
        for row in report["docs"]:
            lines.append(f"- {row['state']}: {row['path']}")
            lines.extend(f"    {reason}" for reason in row["reasons"])
        return "\n".join(lines)
    lines.append(f"scanned {report['docs_scanned']} docs, {report['live_docs']} live after exclusions {report['excluded']}; quiet (clean baseline) "
                 f"{report['quiet_with_clean_baseline']}; flagged {report['flagged']} {report['by_signal']}; "
                 f"wall {report['wall_seconds']} s")
    for domain, rows in report["ranked"].items():
        lines.append(f"## {domain} ({len(rows)})")
        for row in rows[:limit]:
            lines.append(f"- {row['path']}: " + "; ".join(sorted(row["signals"])))
        if len(rows) > limit:
            lines.append(f"  ... {len(rows) - limit} more (use --format jsonl)")
    return "\n".join(lines)


def advisory_lines(report: dict) -> List[str]:
    """Short lines for the close-time advisory (needs-re-verify docs only)."""
    return [
        f"{row['path']}: needs re-verify ({'; '.join(row['reasons'][:3])})"
        for row in report.get("docs", []) if row["state"] == "needs-re-verify"
    ]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--ref", default="HEAD", help="the tree to read; resolved and printed as a full SHA")
    parser.add_argument("--mode", choices=("drift", "detect"), default="drift")
    parser.add_argument("--doc", action="append", default=None, help="limit drift mode to these docs (listed even with no field)")
    parser.add_argument("--changed-file", action="append", default=[], help="uncommitted working-diff path treated as changed")
    parser.add_argument("--start-sha", default=None,
                        help="close-time use: treat the files changed since this SHA (committed or not) as changed evidence")
    parser.add_argument("--format", choices=("text", "jsonl", "advisory"), default="text",
                        help="advisory prints only the needs-re-verify lines, nothing when there are none")
    parser.add_argument("--limit", type=int, default=10, help="rows per domain in text detect output")
    args = parser.parse_args(argv)
    try:
        repo = Repo(Path(args.repo_root), args.ref)
        if not repo.resolve():
            print(f'MARKER:{json.dumps({"error": f"cannot resolve {args.ref}"})}')
            return 0
        changed = list(args.changed_file)
        if args.start_sha:
            changed += derive_changed_files(args.start_sha, cwd=str(args.repo_root))
        report = detect(repo, changed) if args.mode == "detect" else drift_report(repo, args.doc, changed)
        if args.format == "advisory":
            print("\n".join(advisory_lines(report)))
        elif args.format == "jsonl":
            print(json.dumps({k: v for k, v in report.items() if k not in ("docs", "ranked")}))
            rows = report["docs"] if report["mode"] == "drift" else [r for v in report["ranked"].values() for r in v]
            for row in rows:
                print(json.dumps({k: (list(v) if k == "score" else v) for k, v in row.items()}))
        else:
            print(render_text(report, args.limit))
    except Exception as exc:  # noqa: BLE001 - advisory: never block
        print(f'MARKER:{json.dumps({"error": f"{type(exc).__name__}: {exc}"})}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
