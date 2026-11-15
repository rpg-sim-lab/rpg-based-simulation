"""Every field reachable from the authoritative state is in the canonical digest, or is a reasoned row (TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ, item 1).

A ratchet like ``test_no_name_switches_in_decision_paths.py``. ``state_digest_probe.py`` changes each field path (a type-correct value, caches cleared) and sees whether
``CanonicalStateHasher.get_hash`` moves. A path that does not move is a row of ``state_digest_allowlist.yaml``: ``GAP`` (something outside observability reads it across a
tick, so the digest may hide a decision-read difference) or ``EXCLUDE`` (rebuilt from hashed state, run setup, or write-only). A new unhashed field fails; a row whose field is
now hashed or gone fails; a path whose type-correct change could not be built is ``unexercised``: pinned, and it can only shrink. No hash or scheme change is made here: widening
the digest is the owner's call (the v4 question in the ticket).

Samples are fixed: ``state_digest_probe.SAMPLES`` names the worlds, seeds and ticks. Synthesized records exist only inside a probe and are never given to a simulation.
"""
from __future__ import annotations

import collections
import re
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest
import yaml

from tests.architecture import state_digest_probe as probe

ALLOWLIST = Path(__file__).with_name("state_digest_allowlist.yaml")
STATUSES = {"GAP", "EXCLUDE"}
BASES = {"i", "ii", "iii"}
SITE = re.compile(r"src/[\w/]+\.py:\d+")


def load_allowlist(path: Path = ALLOWLIST) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def unhashed_rows(merged: Dict[str, probe.Result]) -> Dict[str, probe.Result]:
    """Unhashed paths, minus those under another unhashed path (one row covers a container)."""
    un = {p: r for p, r in merged.items() if r.status == "unhashed"}

    def under(p: str) -> bool:
        return any(p != u and (p.startswith(u + ".") or p.startswith(u + "[]")) for u in un)

    return {p: r for p, r in un.items() if not under(p)}


def expected_paths(doc: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for row in doc.get("rows", []):
        out[row["path"]] = row
    for pat in doc.get("patterns", []):
        for item in pat.get("matched", []):
            out[item["path"]] = {**pat, "path": item["path"], "reason": item["site"]}
    return out


def pattern_leaks(doc: Dict[str, Any], unhashed: Dict[str, Any]) -> List[str]:
    """A leaf a pattern matches that was not recorded: a new cache is seen at review, the pattern does not absorb it."""
    problems = []
    for pat in doc.get("patterns", []):
        recorded = {m["path"] for m in pat.get("matched", [])}
        regex = re.compile(pat["regex"]) if pat.get("regex") else None
        names = set(pat.get("names", []))
        for path in sorted(unhashed):
            if path not in recorded and ((regex and regex.match(path)) or path in names):
                problems.append(f"{path}: matches pattern {pat['name']!r} but is not in its recorded leaves; record it with its rebuild site or give it its own row")
    return problems


def check(doc: Dict[str, Any], merged: Dict[str, probe.Result]) -> List[str]:
    problems: List[str] = []
    unhashed = unhashed_rows(merged)
    expected = expected_paths(doc)
    problems += pattern_leaks(doc, unhashed)
    leaked = {p.split(":")[0] for p in problems}
    for path in sorted(unhashed):
        if path not in expected and path not in leaked:
            problems.append(f"{path}: not in the digest and not in state_digest_allowlist.yaml; hash it, or add a row (GAP if anything reads it across a tick) with its reason")
    for path in sorted(expected):
        if path in unhashed:
            continue
        now = merged.get(path)
        why = f"now {now.status}" if now else "no longer a field path"
        if now is not None and now.status == "unhashed":
            continue  # under another unhashed container: covered by that row, so this row is redundant
        problems.append(f"{path}: stale row ({why}); delete it" + (" (the field is in the digest now)" if now and now.status == "covered" else ""))
    exercised_now = {p for p, r in merged.items() if r.status == "unexercised"}
    pinned = {u["path"] for u in doc.get("unexercised", [])}
    for path in sorted(exercised_now - pinned):
        problems.append(f"{path}: unexercised (no type-correct change could be built: {merged[path].reason}) and not pinned; fix the synthesis or pin it with a reason")
    for path in sorted(pinned - exercised_now):
        problems.append(f"{path}: pinned as unexercised but is exercised now ({merged[path].status if path in merged else 'gone'}); remove it from `unexercised`")
    return problems


def check_rows(doc: Dict[str, Any]) -> List[str]:
    problems = []
    seen: Set[str] = set()
    for row in doc.get("rows", []):
        where = row.get("path", "?")
        if where in seen:
            problems.append(f"{where}: listed twice")
        seen.add(where)
        if row.get("status") not in STATUSES:
            problems.append(f"{where}: status must be GAP or EXCLUDE")
        if not str(row.get("reason", "")).strip():
            problems.append(f"{where}: no reason")
        if row.get("status") == "EXCLUDE":
            if row.get("basis") not in BASES:
                problems.append(f"{where}: an EXCLUDE needs basis i, ii or iii")
            if row.get("basis") == "i" and not SITE.search(str(row.get("reason", ""))):
                problems.append(f"{where}: basis i must cite the rebuild or clear site (file:line)")
            if row.get("basis") == "iii" and row.get("tag") != "no_reader":
                problems.append(f"{where}: basis iii must carry tag no_reader")
        if row.get("status") == "GAP" and row.get("group") in {"E", "F"} and not str(row.get("reader", "")).strip():
            problems.append(f"{where}: a GAP in group E or F names one reader (file:line)")
    for pat in doc.get("patterns", []):
        for item in pat.get("matched", []):
            if not SITE.search(item["site"]):
                problems.append(f"{item['path']}: a pattern leaf must cite its rebuild or clear site (file:line)")
    for u in doc.get("unexercised", []):
        if not str(u.get("reason", "")).strip():
            problems.append(f"{u['path']}: unexercised needs its reason")
    return problems


def report(doc: Dict[str, Any]) -> str:
    """The GAP rows, the unexercised list grouped by component, and the no_reader rows (rpg-planner's lists for the v4 question and the unwired triage)."""
    rows = list(expected_paths(doc).values())
    gaps = sorted((r for r in rows if r["status"] == "GAP"), key=lambda r: r["path"])
    no_reader = sorted(r["path"] for r in rows if r.get("tag") == "no_reader")

    def component(path: str) -> str:
        parts = path.split(".")
        return ".".join(parts[:3]) if parts[:2] == ["state", "entities[]"] else ".".join(parts[:2])

    groups: Dict[str, List[str]] = collections.defaultdict(list)
    for u in doc.get("unexercised", []):
        groups[component(u["path"])].append(u["path"])
    lines = [f"# {len(gaps)} GAP rows, {len([r for r in rows if r['status'] == 'EXCLUDE'])} EXCLUDE rows, {len(doc.get('unexercised', []))} unexercised", "## GAP"]
    lines += [f"{r['path']} [{r.get('group', '')}] {r.get('reader', '')}" for r in gaps]
    lines += ["## unexercised (not proven), by component"]
    for comp in sorted(groups):
        lines.append(f"{comp}: " + ", ".join(p[len(comp) + 1:] or p for p in groups[comp]))
    lines += ["## no_reader (for the unwired triage)"] + no_reader
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------------------------- the real state
@pytest.fixture(scope="module")
def merged() -> Dict[str, probe.Result]:
    return probe.merge([probe.probe_state(state) for _name, state in probe.build_samples()])


def test_the_allowlist_rows_are_well_formed():
    assert check_rows(load_allowlist()) == []


def test_every_unhashed_field_is_a_reasoned_row_and_every_row_is_still_unhashed(merged):
    assert check(load_allowlist(), merged) == []


def test_the_report_lists_the_gaps_the_unexercised_and_the_no_reader_rows(merged):
    text = report(load_allowlist())
    assert "## GAP" in text and "## unexercised (not proven), by component" in text and "## no_reader (for the unwired triage)" in text
    assert "state.entities[].identity.cooldowns" in text  # the ticket's first named suspect


def test_the_ticket_named_suspects_are_gaps_in_the_allowlist():
    rows = expected_paths(load_allowlist())
    for field in ("identity.cooldowns", "identity.traits", "identity.latest_intent_results", "stamina.current", "timeline"):
        path = f"state.entities[].{field}"
        assert path in rows and rows[path]["status"] == "GAP", path


# ---------------------------------------------------------------------------------------------------------------- the ratchet's own behaviour (synthetic)
def _r(path: str, status: str, reason: str = "") -> probe.Result:
    return probe.Result(path, "Owner", path.split(".")[-1], status, reason)


DOC = {
    "rows": [{"path": "state.gap", "status": "GAP", "group": "D", "reason": "read"}],
    "patterns": [{"name": "caches", "regex": r"^state\._[a-z_]*cache$", "status": "EXCLUDE", "group": "A", "basis": "i", "reason": "x",
                  "matched": [{"path": "state._a_cache", "site": "src/core/state.py:1"}]}],
    "unexercised": [{"path": "state.u", "reason": "synthesis failed: x"}],
}


def _merged(*results: probe.Result) -> Dict[str, probe.Result]:
    return {r.path: r for r in results}


def test_a_clean_synthetic_state_passes():
    assert check(DOC, _merged(_r("state.gap", "unhashed"), _r("state._a_cache", "unhashed"), _r("state.u", "unexercised", "x"), _r("state.ok", "covered"))) == []


def test_a_new_unhashed_field_fails():
    problems = check(DOC, _merged(_r("state.gap", "unhashed"), _r("state._a_cache", "unhashed"), _r("state.u", "unexercised", "x"), _r("state.new", "unhashed")))
    assert len(problems) == 1 and problems[0].startswith("state.new: not in the digest")


def test_a_row_whose_field_is_now_hashed_or_gone_fails():
    problems = check(DOC, _merged(_r("state.gap", "covered"), _r("state.u", "unexercised", "x")))
    assert any("state.gap: stale row (now covered)" in p for p in problems) and any("state._a_cache: stale row (no longer a field path)" in p for p in problems)


def test_a_new_cache_the_pattern_matches_but_did_not_record_fails():
    problems = check(DOC, _merged(_r("state.gap", "unhashed"), _r("state._a_cache", "unhashed"), _r("state._b_cache", "unhashed"), _r("state.u", "unexercised", "x")))
    assert len(problems) == 1 and "state._b_cache: matches pattern 'caches'" in problems[0]


def test_unexercised_is_pinned_and_can_only_shrink():
    base = [_r("state.gap", "unhashed"), _r("state._a_cache", "unhashed")]
    grew = check(DOC, _merged(*base, _r("state.u", "unexercised", "x"), _r("state.v", "unexercised", "y")))
    assert len(grew) == 1 and grew[0].startswith("state.v: unexercised")
    shrunk = check(DOC, _merged(*base, _r("state.u", "covered")))
    assert len(shrunk) == 1 and shrunk[0].startswith("state.u: pinned as unexercised but is exercised now")


def test_a_path_under_an_unhashed_container_needs_no_row_of_its_own():
    merged = _merged(_r("state.gap", "unhashed"), _r("state.gap[].leaf", "unhashed"), _r("state._a_cache", "unhashed"), _r("state.u", "unexercised", "x"))
    assert check(DOC, merged) == []


def test_row_validation_catches_a_missing_reason_a_bare_exclude_and_a_gap_without_a_reader():
    bad = {"rows": [{"path": "p1", "status": "EXCLUDE", "reason": "r"}, {"path": "p2", "status": "GAP", "group": "F", "reason": "r"},
                    {"path": "p3", "status": "EXCLUDE", "basis": "i", "reason": "no site here"}, {"path": "p4", "status": "EXCLUDE", "basis": "iii", "reason": "r"},
                    {"path": "p5", "status": "GAP", "group": "D", "reason": ""}]}
    problems = check_rows(bad)
    assert len(problems) == 5 and all(p.split(":")[0] in {"p1", "p2", "p3", "p4", "p5"} for p in problems)
