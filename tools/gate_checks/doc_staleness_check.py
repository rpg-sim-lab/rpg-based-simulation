"""Flag a behavior-changing diff that touches no `docs/` path.

Built for TCK-20260711-DOC-STALENESS-GATE-CHECK: the 2026-W28 agent-monitoring retro
(`agent-working/agent-monitoring/retro/RETRO-2026-W28.md`) found done-checker's Verify phase failing its first
attempt on 22/61 calls (36%) in one week, every failure tagged `reason_code=dod_condition_failed`,
and traced (Notes items 1 and 3) to one recurring root cause: a behavior-changing Implement phase
touching `src/` or a `.claude/workflows/*.js` file without a corresponding `docs/` update, caught
only reactively by done-checker instead of before Verify. `TCK-20260711-EPIC-SCOPE-ORPHAN-FIX` and
`TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK` hit this exact shape in the same session.

Mirrors `workflow_meta_conformance.py`'s one-function, list-of-dicts shape (not
`parity_updater_static.py`'s two-call `expected_subsystems_for_files`/`cross_reference_touched`
split) — there is no agent-prompt injection point this check needs to feed, only a single
`files_changed`/`behavior_changed` -> PASS/FAIL verdict.

Wired into `.claude/workflows/implement-ticket.js` by `TCK-20260720-GATE-CHECK-WIRING-DECISIONS`
as a hard blocking gate (`DOC_STALENESS_BLOCKED`). Built to the same `MARKER:`-prefixed JSON CLI
contract every other `gate_checks` script uses.

`TCK-20260802-DOC-UPDATE-DISCIPLINE` added two extensions, both additive — no existing `PASS`/`FAIL`
verdict changes shape or meaning:
- `config/` (e.g. `config/simulation_quality/*.yaml` scoring weights/thresholds — behavior-driving
  settings that live outside `src/`) is now a flagged prefix alongside `src/` and
  `.claude/workflows/*.js`.
- An optional `docs_to_update` param (paths the Investigate phase identified up front as needing an
  update) adds a separate, non-blocking `ADVISORY` result entry when one of those specific paths
  isn't in `files_changed` — even if the blanket `docs/`-path-presence check already `PASS`es. This
  is intentionally advisory-only (confirmed with the user during scoping): promoting it to a hard
  block is deferred until there's evidence of how often Investigate over-lists docs that turn out
  not to need touching once Review/Implement refine the plan — same reasoning that kept this whole
  check unwired for one ticket cycle before TCK-20260720 promoted it to blocking.
"""

import json
import re
import sys
from typing import List, Optional

# Plan P5: docs on a critical invariant are listed first in the advisory and named in the close summary.
CRITICAL_INVARIANT = re.compile(
    r"\b(determinis\w*|conservation|persist\w*|restore\w*|checkpoint\w*|concurren\w*|acknowledg\w*|ack)\b",
    re.IGNORECASE,
)
MAX_ADVISORY_DOCS = 15


def check_doc_staleness(
    files_changed: List[str],
    behavior_changed: bool,
    docs_to_update: Optional[List[str]] = None,
    search_result: Optional[dict] = None,
) -> List[dict]:
    """Aggregate verdict: did a behavior-changing src/config/workflow diff skip its docs/ update.

    Single aggregate entry point (mirrors `check_workflow_meta_conformance`'s one-function,
    list-of-dicts shape). `FAIL` only when all three hold: `behavior_changed` is `True`, at least
    one path in `files_changed` starts with `src/`, starts with `config/`, or is a
    `.claude/workflows/*.js` path, and zero paths in `files_changed` start with `docs/`. Otherwise
    `PASS` — including when `behavior_changed` is `False` (e.g. a pure test-only change) or when a
    `docs/` path is present alongside the src/config/workflow change. `FAIL` returns early with a
    single-entry list — `docs_to_update` is not consulted in that case, since a blanket failure is
    already the strongest signal.

    When the `PASS` branch is taken and `docs_to_update` names paths not present in
    `files_changed`, a second, non-blocking `ADVISORY` entry is appended — the caller must never
    treat this as a `FAIL`.

    `search_result` (TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY, F3) is the output of
    `docs_search.search_docs_for_change` on the same diff. When it names live docs that cite a changed file or symbol and
    are not in `files_changed`, one more non-blocking `ADVISORY` entry lists them, critical-invariant docs first. Excluded
    (history) docs never appear. It is appended after the verdict, so the verdict and the exit behaviour are unchanged, and
    a missing or malformed `search_result` changes nothing.
    """
    flagged_paths = [
        path for path in files_changed
        if path.startswith("src/")
        or path.startswith("config/")
        or (path.startswith(".claude/workflows/") and path.endswith(".js"))
    ]
    docs_paths = [path for path in files_changed if path.startswith("docs/")]

    if behavior_changed and flagged_paths and not docs_paths:
        return [{
            "status": "FAIL",
            "evidence": f"behavior_changed=True touched {flagged_paths} with no docs/ path in "
                        f"files_changed",
        }]

    results = [{
        "status": "PASS",
        "evidence": f"behavior_changed={behavior_changed}, "
                    f"{len(flagged_paths)} src/config/workflow path(s) flagged, "
                    f"{len(docs_paths)} docs/ path(s) present",
    }]

    if docs_to_update:
        missing = [path for path in docs_to_update if path not in files_changed]
        if missing:
            results.append({
                "status": "ADVISORY",
                "evidence": f"investigation.md flagged {missing} as requiring an update, but "
                            f"none of these specific path(s) appear in files_changed — verify "
                            f"they don't need touching, or update them",
            })

    advisory = _search_advisory(search_result, files_changed)
    if advisory:
        results.append(advisory)

    return results


def _critical(item: dict) -> bool:
    text = item.get("path", "") + " " + " ".join(h.get("text", "") for h in item.get("hits", []))
    return bool(CRITICAL_INVARIANT.search(text))


def _search_advisory(search_result: Optional[dict], files_changed: List[str]) -> Optional[dict]:
    """One ADVISORY entry for live docs that cite a changed file and were not touched, or None."""
    if not isinstance(search_result, dict):
        return None
    try:
        touched = set(files_changed)
        items = [
            item for key in ("required", "candidate") for item in search_result.get(key, [])
            if item["path"] not in touched
        ]
        if not items:
            return None
        critical = [i for i in items if _critical(i)]
        rest = [i for i in items if not _critical(i)]
        ordered = critical + rest
        shown = [i["path"] for i in ordered[:MAX_ADVISORY_DOCS]]
        more = len(ordered) - len(shown)
        text = (
            f"{len(items)} live doc(s) cite a changed file or symbol and were not touched: " + ", ".join(shown)
            + (f" (+{more} more)" if more > 0 else "")
        )
        if critical:
            text += "; critical-invariant docs first: " + ", ".join(i["path"] for i in critical[:MAX_ADVISORY_DOCS])
        return {"status": "ADVISORY", "evidence": text, "docs": [i["path"] for i in ordered],
                "critical": [i["path"] for i in critical]}
    except (KeyError, TypeError, AttributeError):
        return None


def _record(results, behavior_changed, files_changed, enabled, execution_mode):
    """Write the verdict to the gate_verdicts shard (TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES)."""
    import sys  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415
    monitoring_dir = str(Path(__file__).resolve().parents[1] / "agent-monitoring")
    if monitoring_dir not in sys.path:
        sys.path.insert(0, monitoring_dir)
    import gate_verdicts  # noqa: PLC0415
    failed = any(r["status"] == "FAIL" for r in results)
    gate_verdicts.record_gate_verdict(
        enabled=enabled,
        gate_id=gate_verdicts.gate_id_for("doc_staleness_check", "check_doc_staleness"),
        gate_type="static_check",
        phase="Document-Update",
        verdict="FAIL" if failed else "PASS",
        blocking=failed,
        execution_mode=execution_mode,
        inputs_ref={"head_sha": gate_verdicts.head_sha(),
                    "files_sha": gate_verdicts.sha256_hex(f"{behavior_changed}|" + "\n".join(sorted(files_changed)))},
    )


def _pop_option(args, flag, takes_value):
    """Remove `flag` (and its value) from `args`; return the value (True for a bare flag), else None."""
    if flag not in args:
        return None
    idx = args.index(flag)
    if not takes_value:
        del args[idx]
        return True
    value = args[idx + 1] if idx + 1 < len(args) else None
    del args[idx:idx + 2]
    return value


if __name__ == "__main__":
    argv = sys.argv[1:]
    no_record = bool(_pop_option(argv, "--no-record", False))
    mode_arg = _pop_option(argv, "--execution-mode", True)
    search_json_arg = _pop_option(argv, "--search-json", True)
    behavior_changed_arg = argv[0].lower() == "true"
    rest_args = argv[1:]
    if "--docs-to-update" in rest_args:
        split_idx = rest_args.index("--docs-to-update")
        files_changed_arg = rest_args[:split_idx]
        docs_to_update_arg = rest_args[split_idx + 1:]
    else:
        files_changed_arg = rest_args
        docs_to_update_arg = []
    search_result_arg = None
    if search_json_arg:
        try:
            with open(search_json_arg, encoding="utf-8") as handle:
                search_result_arg = json.load(handle)
        except (OSError, ValueError):
            search_result_arg = None
    result = check_doc_staleness(files_changed_arg, behavior_changed_arg, docs_to_update_arg, search_result_arg)
    print("MARKER:" + json.dumps(result))
    _record(result, behavior_changed_arg, files_changed_arg, not no_record, mode_arg)
