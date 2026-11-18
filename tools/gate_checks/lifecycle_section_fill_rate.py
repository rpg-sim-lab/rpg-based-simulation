"""Fill-rate report for the required `## Durable state, lifecycle and clocks` ticket section.

TCK-20261118-REQUIRED-DURABLE-STATE-LIFECYCLE-CLOCKS-SECTION-IN-TICKETS-AND-PR-BODIES (scope item 6). Counts tickets dated on
or after `LIFECYCLE_SECTION_REQUIRED_FROM` (the landing date) by section state, so the owner can read the fill rate and the
`N/A` rate after about four weeks and set them against the defects first reported after 2026-11-18. Report-only: it never
exits non-zero for a low rate, and it judges presence, never answer quality.

    python3 tools/gate_checks/lifecycle_section_fill_rate.py [--root agent-working/tickets] [--json]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List

_TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from ticket_field_values import (  # noqa: E402
    LIFECYCLE_SECTION,
    LIFECYCLE_SECTION_REQUIRED_FROM,
    check_lifecycle_section,
    has_body_section,
)
from generate_registry import parse_body_section, _strip_frontmatter  # noqa: E402
from validate_frontmatter import extract_frontmatter  # noqa: E402

_DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "agent-working" / "tickets"
STATES = ("answers", "na_with_reason", "missing_or_invalid")


def classify(path: Path) -> str:
    """One of STATES for a ticket that is subject to the section (dated on or after the landing date)."""
    status, _ = check_lifecycle_section(path)
    if status == "FAIL":
        return "missing_or_invalid"
    content = parse_body_section(_strip_frontmatter(path.read_text(encoding="utf-8")), LIFECYCLE_SECTION)
    return "na_with_reason" if content.lstrip().lower().startswith("n/a") else "answers"


def collect(root: Path = _DEFAULT_ROOT) -> Dict[str, object]:
    counts: Counter = Counter()
    subject: List[str] = []
    for path in sorted(root.rglob("TCK-*.md")):
        text = path.read_text(encoding="utf-8")
        date = str((extract_frontmatter(text) or {}).get("date") or "")[:10]
        if not date or date < LIFECYCLE_SECTION_REQUIRED_FROM:
            continue
        subject.append(path.stem)
        counts[classify(path)] += 1
    total = len(subject)
    rate = lambda k: (counts[k] / total) if total else None  # noqa: E731
    return {
        "required_from": LIFECYCLE_SECTION_REQUIRED_FROM,
        "tickets_subject_to_section": total,
        "counts": {s: counts[s] for s in STATES},
        "fill_rate": rate("answers") + rate("na_with_reason") if total else None,
        "na_rate": rate("na_with_reason"),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=_DEFAULT_ROOT, help="tickets root (todos/, inprogress/, done/ under it)")
    parser.add_argument("--json", action="store_true", help="print the report as JSON")
    args = parser.parse_args(argv)
    report = collect(args.root)
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print(f"tickets dated on or after {report['required_from']}: {report['tickets_subject_to_section']}")
    for state, n in report["counts"].items():
        print(f"  {state}: {n}")
    fmt = lambda v: "n/a (no tickets yet)" if v is None else f"{v:.0%}"  # noqa: E731
    print(f"fill rate (section present and valid): {fmt(report['fill_rate'])}; N/A rate: {fmt(report['na_rate'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
