#!/usr/bin/env python3
"""Reproduces the numbers of the J2 evaluation (TCK-20261108-STALE-DOC-DETECTION-PILOT): a docs audit, not an implementation audit.

Run read-only at a pinned SHA: `python3 tools/gate_checks/doc_drift_pilot.py --pin <sha>`. It prints
- the flagged counts by signal and by domain (`doc_drift.detect`), the wall time, and `git status --porcelain -- docs/` before and
  after (to show that no doc was edited);
- the hand-read sample: about 20 docs, taken by a fixed stride WITHIN each signal's ranked list (not over the merged list, which
  would sample only the top). The verdict and a one-line reason per doc are written by hand into the report, not here;
- recall on the labelled set at its own pin. Recall is reported as measured: nothing here is a threshold, and no test targets
  these docs.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_TOOLS = str(Path(__file__).resolve().parents[1])
if _TOOLS not in sys.path:
    sys.path.insert(0, _TOOLS)
_REPO = str(Path(__file__).resolve().parents[2])
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from gate_checks import doc_drift  # noqa: E402

#: Items 1, 2, 4 and 6 of the 2026-11-07 audit at 531010a9a. Items 2 and 4 are labelled undetectable by design.
LABELLED_PIN = "531010a9a"
LABELLED = {
    "docs/engine/contracts/simulation_kernel_contract.md": "item 1",
    "docs/architecture/kernel_concurrency_design_philosophy.md": "item 6",
    "docs/engine/deterministic_execution.md": "item 2 (undetectable by design)",
    "docs/observability/hard_law_monitor.md": "item 4 (undetectable by design)",
}
SAMPLE_SPLIT = {"evidence-newer": 7, "unresolved-name": 7, "plan-lifecycle": 6}


def stride_sample(rows: list, count: int) -> list:
    """`count` rows at the midpoints of `count` equal slices of the ranked list: deterministic, spread over the whole ranking."""
    if count <= 0 or not rows:
        return []
    if len(rows) <= count:
        return list(rows)
    return [rows[int((j + 0.5) * len(rows) / count)] for j in range(count)]


def sample(report: dict) -> dict:
    flat = [row for domain_rows in report["ranked"].values() for row in domain_rows]
    flat.sort(key=lambda r: tuple(-x for x in r["score"]) + (r["path"],))
    chosen: dict = {}
    taken: set = set()
    for signal, count in SAMPLE_SPLIT.items():
        pool = [r for r in flat if signal in r["signals"] and r["path"] not in taken]
        picks = stride_sample(pool, count)
        taken.update(r["path"] for r in picks)
        chosen[signal] = picks
    return chosen


def git_status_docs(root: Path) -> str:
    return subprocess.run(["git", "status", "--porcelain", "--", "docs/"], cwd=root, capture_output=True, text=True, check=False).stdout


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--pin", required=True)
    parser.add_argument("--sample-out", default=None, help="write the sample rows as JSONL here (scratch, not committed)")
    args = parser.parse_args(argv)
    root = Path(args.repo_root)
    before = git_status_docs(root)
    repo = doc_drift.Repo(root, args.pin)
    if not repo.resolve():
        print(f"cannot resolve {args.pin}")
        return 0
    report = doc_drift.detect(repo)
    print(f"pin: {report['pin']}")
    print(f"scanned {report['docs_scanned']} docs; excluded {report['excluded']}; quiet {report['quiet_with_clean_baseline']}")
    print(f"flagged {report['flagged']} docs; by signal {report['by_signal']}")
    print(f"by domain {report['by_domain']}")
    print(f"wall time {report['wall_seconds']} s")
    picks = sample(report)
    rows = [(signal, row) for signal, group in picks.items() for row in group]
    print(f"sample ({len(rows)} docs; stride within each signal's ranked list):")
    for signal, row in rows:
        print(f"  [{signal}] {row['path']} ({row['domain']}): {json.dumps(row['signals'][signal])[:300]}")
    if args.sample_out:
        Path(args.sample_out).write_text("".join(json.dumps({"sampled_for": s, **r}) + "\n" for s, r in rows), encoding="utf-8")
    labelled = doc_drift.Repo(root, LABELLED_PIN)
    if labelled.resolve():
        found = doc_drift.detect(labelled)
        flagged_paths = {r["path"]: r for rr in found["ranked"].values() for r in rr}
        print(f"recall at {labelled.pin} (labelled set, measured not tuned):")
        for path, label in LABELLED.items():
            hit = flagged_paths.get(path)
            print(f"  {label}: {path}: " + (f"flagged {sorted(hit['signals'])}" if hit else "not flagged"))
        print(f"  (that pin's run flagged {found['flagged']} of {found['docs_scanned']} docs)")
    after = git_status_docs(root)
    print(f"git status --porcelain -- docs/ before: {before!r}; after: {after!r}; unchanged: {before == after}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
