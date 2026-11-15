"""Close-time advisory: a ticket's evidence scripts that run the engine through ``_run_engine`` (TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE).

``tools.calibrate_simq._run_engine`` builds the default governor and executor under the profile's own tick budget; it is not the pinned runner, and its worlds differ from
``rpg_gate_run.build_kernel``'s. Behaviour evidence comes from the pinned runner (docs/guides/delivery_process.md, "Behaviour evidence comes from the pinned runner"), so a
Python script stored under a ticket's ``agent-working/stored_artifacts/<id>/`` (or ``staging_artifacts/<id>/``) that names ``_run_engine`` is flagged for a look.

Report-only, in the style of ``tools/gate_checks/cited_evidence_advisory.py``: ``check_evidence_runner(ticket_id, tier)`` returns ``(status, evidence)`` with status ``OK`` / ``WARN`` /
``NA``, never raises, never blocks. SIMQ grade anchors use ``_run_engine`` by design; a ticket that does so on purpose reads the warning and closes. A script kept outside the
repo (lane scratch) cannot be seen here: the run manifest's ``run_conditions`` record and ``pinned_runner.py`` are the guard for those.

Command line: ``python -m tools.test_architecture.evidence_runner_advisory <TCK-ID>``.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO = Path(__file__).resolve().parents[2]
ROOTS = ("agent-working/stored_artifacts", "agent-working/staging_artifacts")
_NAME = re.compile(r"\b_run_engine\b")


def evidence_scripts(ticket_id: str, root: Path = REPO) -> List[Path]:
    out: List[Path] = []
    for base in ROOTS:
        folder = root / base / ticket_id
        if folder.is_dir():
            out.extend(sorted(p for p in folder.rglob("*.py") if p.is_file()))
    return out


def flagged(ticket_id: str, root: Path = REPO) -> List[Tuple[str, int]]:
    """(repo-relative path, line) for each line of an evidence script that names ``_run_engine``."""
    hits: List[Tuple[str, int]] = []
    for path in evidence_scripts(ticket_id, root):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        hits.extend((path.relative_to(root).as_posix(), n) for n, line in enumerate(lines, 1) if _NAME.search(line))
    return hits


def check_evidence_runner(ticket_id: str, tier: str = "standard", root: Path = REPO) -> Tuple[str, str]:
    try:
        scripts = evidence_scripts(ticket_id, root)
        if not scripts:
            return "NA", f"no Python evidence scripts under the stored or staged artifacts of {ticket_id}"
        hits = flagged(ticket_id, root)
        if not hits:
            return "OK", f"{len(scripts)} evidence script(s) checked, none names _run_engine"
        shown = ", ".join(f"{path}:{line}" for path, line in hits[:5]) + (f" (+{len(hits) - 5} more)" if len(hits) > 5 else "")
        return "WARN", (f"{shown} names _run_engine, which is not the pinned runner; behaviour evidence comes from tools/rpg_measure or rpg_gate_run.build_kernel "
                        "(docs/guides/delivery_process.md). Fine for SIMQ calibration; otherwise re-run pinned or label the result as measured on another runner.")
    except Exception as exc:  # noqa: BLE001 - an advisory never blocks a close
        return "NA", f"advisory could not run: {type(exc).__name__}: {exc}"


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: python -m tools.test_architecture.evidence_runner_advisory <TCK-ID>")
        return 2
    status, evidence = check_evidence_runner(args[0])
    print(f"[advisory] evidence_runner_pinned: {status} — {evidence}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
