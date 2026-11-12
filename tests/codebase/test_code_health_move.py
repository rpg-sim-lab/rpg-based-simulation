"""Tests for the move-aware code-health ratchet (TCK-20261112-CODE-HEALTH-NAMES-AND-REKEYS-MOVED-ROWS).

`likely_moves` and `move_rows` are tested on hand-built findings and rows; the CLI tests run in the scratch repository
of `conftest.py` and move one complexipy function between two sample files. Nothing here touches the real registry.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from codebase.health import registry
from codebase.health.findings import TOOL_AST_GREP, TOOL_JSCPD
from codebase.health.ratchet import compare, format_report, format_summary, likely_moves
from codebase.health.registry import MoveRefusedError, move_rows
from tests.codebase.conftest import _f, _rows, _run, _scan_arg

SYMBOL = "risky"


def _cx(file: str, symbol: str | None, value: int, rule: str = "cognitive-complexity", tool: str = "complexipy"):
    return _f(file, rule, value, symbol=symbol, tool=tool)


def _moves(old: list, new: list, rows_of=None):
    return likely_moves(compare(new, _rows(rows_of if rows_of is not None else old)))


# ── likely_moves: the pairing rule ────────────────────────────────────────────


def test_a_gone_row_and_a_new_finding_with_the_same_symbol_tool_and_rule_are_one_pair():
    moves = _moves([_cx("a.py", "f", 20)], [_cx("b.py", "f", 20)])
    assert [(m.row.file, m.finding.file, m.ambiguous) for m in moves] == [("a.py", "b.py", False)]
    assert moves[0].command == "python3 -m codebase.health move a.py b.py --symbol f"


def test_a_value_over_the_ceiling_is_not_a_move():
    assert _moves([_cx("a.py", "f", 20)], [_cx("b.py", "f", 21)]) == ()


def test_a_value_under_the_ceiling_is_still_a_move():
    assert len(_moves([_cx("a.py", "f", 20)], [_cx("b.py", "f", 12)])) == 1


@pytest.mark.parametrize(
    ("symbol", "tool"),
    [(None, "ruff"), ("<module>", TOOL_AST_GREP), ("dup:other.py", TOOL_JSCPD)],
    ids=["file-level", "module", "jscpd-pair"],
)
def test_file_level_module_and_jscpd_rows_are_never_paired(symbol, tool):
    old = [_cx("a.py", symbol, 5, rule="R", tool=tool)]
    new = [_cx("b.py", symbol, 5, rule="R", tool=tool)]
    assert _moves(old, new) == ()


def test_the_same_file_is_not_a_move():
    assert likely_moves(compare([_cx("a.py", "f", 20, rule="other")], _rows([_cx("a.py", "f", 20)]))) == ()


def test_a_different_rule_or_tool_is_not_a_move():
    assert _moves([_cx("a.py", "f", 20)], [_cx("b.py", "f", 20, rule="function-length", tool="line_count")]) == ()


def test_two_candidate_files_for_one_row_list_both_as_ambiguous():
    moves = _moves([_cx("a.py", "f", 20)], [_cx("b.py", "f", 20), _cx("c.py", "f", 20)])
    assert [(m.finding.file, m.ambiguous) for m in moves] == [("b.py", True), ("c.py", True)]


def test_two_gone_rows_for_one_finding_list_both_as_ambiguous():
    moves = _moves([_cx("a.py", "run", 20), _cx("b.py", "run", 20)], [_cx("c.py", "run", 20)])
    assert [(m.row.file, m.ambiguous) for m in moves] == [("a.py", True), ("b.py", True)]


def test_the_order_is_old_file_then_symbol_then_new_file_whatever_the_input_order():
    old = [_cx("b.py", "g", 9), _cx("a.py", "h", 9), _cx("a.py", "f", 9)]
    new = [_cx("z.py", "g", 9), _cx("y.py", "h", 9), _cx("x.py", "f", 9)]
    first = [(m.row.file, m.row.symbol) for m in _moves(old, new)]
    assert first == [("a.py", "f"), ("a.py", "h"), ("b.py", "g")]
    assert [(m.row.file, m.row.symbol) for m in _moves(old[::-1], new[::-1])] == first


def test_pairing_never_changes_the_ratchet_result():
    result = compare([_cx("b.py", "f", 20)], _rows([_cx("a.py", "f", 20)]))
    likely_moves(result)
    assert result.blocking_failed and len(result.new) == 1 and len(result.gone) == 1 and not result.worse


def test_the_report_and_the_summary_name_the_pair_and_the_command():
    result = compare([_cx("b.py", "f", 20)], _rows([_cx("a.py", "f", 20)]))
    moves = likely_moves(result)
    command = "python3 -m codebase.health move a.py b.py --symbol f"
    report = format_report(result, moves=moves)
    assert "likely move" in report and command in report and report.count("FAIL") == 1
    summary = format_summary(result, moves=moves)
    assert "likely move" in summary and command in summary
    assert "likely move" not in format_report(result) and "likely move" not in format_summary(result)


def test_an_ambiguous_pair_is_tagged_in_the_report():
    result = compare([_cx("b.py", "f", 20), _cx("c.py", "f", 20)], _rows([_cx("a.py", "f", 20)]))
    assert format_report(result, moves=likely_moves(result)).count("ambiguous") == 2


# ── move_rows ─────────────────────────────────────────────────────────────────


def test_move_rows_changes_file_and_nothing_else():
    rows = _rows([_cx("a.py", "f", 20), _cx("a.py", "keep", 7), _cx("c.py", "g", 3)])
    findings = [_cx("b.py", "f", 18), _cx("a.py", "keep", 7), _cx("c.py", "g", 3)]
    moved, changes = move_rows(rows, findings, "a.py", "b.py")
    original = next(r for r in rows if r.symbol == "f")
    assert replace(next(r for r in moved if r.file == "b.py"), file="a.py") == original
    assert {(r.file, r.symbol) for r in moved} == {("b.py", "f"), ("a.py", "keep"), ("c.py", "g")}
    assert len(changes) == 1 and "ceiling 20 kept" in changes[0]


def test_move_rows_with_a_symbol_moves_only_that_symbol():
    rows = _rows([_cx("a.py", "f", 20), _cx("a.py", "g", 20)])
    findings = [_cx("b.py", "f", 20), _cx("b.py", "g", 20)]
    moved, _ = move_rows(rows, findings, "a.py", "b.py", symbol="f")
    assert {(r.file, r.symbol) for r in moved} == {("b.py", "f"), ("a.py", "g")}


def test_move_rows_leaves_rows_whose_code_did_not_move_where_they_are():
    rows = _rows([_cx("a.py", "f", 20), _cx("a.py", "stays", 20)])
    findings = [_cx("b.py", "f", 20), _cx("a.py", "stays", 20)]
    moved, _ = move_rows(rows, findings, "a.py", "b.py")
    assert {(r.file, r.symbol) for r in moved} == {("b.py", "f"), ("a.py", "stays")}


def _refused(rows, findings, symbol=None, new_file="b.py") -> str:
    before = list(rows)
    with pytest.raises(MoveRefusedError) as caught:
        move_rows(rows, findings, "a.py", new_file, symbol)
    assert rows == before
    return caught.value.reason


def test_move_rows_refuses_a_value_over_the_ceiling():
    assert "above its ceiling" in _refused(_rows([_cx("a.py", "f", 20)]), [_cx("b.py", "f", 21)])


def test_move_rows_refuses_when_the_target_already_has_the_row():
    rows = _rows([_cx("a.py", "f", 20), _cx("b.py", "f", 20)])
    assert "already has a row" in _refused(rows, [_cx("b.py", "f", 20)])


def test_move_rows_refuses_a_symbol_that_did_not_move():
    rows = _rows([_cx("a.py", "f", 20)])
    assert "cannot be moved" in _refused(rows, [_cx("a.py", "f", 20), _cx("b.py", "f", 20)], symbol="f")
    assert "cannot be moved" in _refused(rows, [], symbol="f")


def test_move_rows_with_a_symbol_refuses_if_one_of_its_rows_did_not_move():
    rows = _rows([_cx("a.py", "f", 20), _cx("a.py", "f", 30, rule="function-length", tool="line_count")])
    findings = [_cx("b.py", "f", 20)]
    assert "cannot be moved" in _refused(rows, findings, symbol="f")


def test_move_rows_refuses_when_nothing_would_move_or_the_files_are_the_same():
    rows = _rows([_cx("a.py", "f", 20)])
    assert "no row" in _refused(rows, [_cx("a.py", "f", 20)])
    assert "same file" in _refused(rows, [_cx("a.py", "f", 20)], new_file="a.py")


def test_move_rows_does_not_move_file_level_or_module_rows():
    rows = _rows([_f("a.py", "F401", 2), _cx("a.py", "<module>", 1, rule="e3", tool=TOOL_AST_GREP)])
    findings = [_f("b.py", "F401", 2), _cx("b.py", "<module>", 1, rule="e3", tool=TOOL_AST_GREP)]
    assert "no row" in _refused(rows, findings)


# ── The command, end to end in a scratch repository ───────────────────────────


def _move_risky(repo: Path, new_file: str = "sample_src/moved.py") -> None:
    """The sample's `risky` complexipy function (and its function-length row, if any) now lives in `new_file`."""
    for name, file_key in (("complexipy.json", "path"), ("line_count.json", "file")):
        path = repo / "scan" / name
        data = json.loads(path.read_text())
        entries = data if isinstance(data, list) else data.get("entries", data.get("results", []))
        for entry in entries:
            if isinstance(entry, dict) and SYMBOL in str(entry.get("function_name", entry.get("symbol", ""))):
                entry[file_key] = new_file
        path.write_text(json.dumps(data))


def _registry_bytes(repo: Path) -> bytes:
    return (repo / "reg.jsonl").read_bytes()


def test_check_fails_a_moved_function_and_names_the_pair_then_move_makes_it_pass(seeded, capsys):
    _move_risky(seeded)
    capsys.readouterr()
    assert _run(seeded, "check", *_scan_arg(seeded)) == 1
    out = capsys.readouterr().out
    assert "likely move" in out and f"move sample_src/bad.py sample_src/moved.py --symbol {SYMBOL}" in out

    before = _registry_bytes(seeded).splitlines()
    assert _run(seeded, "move", "sample_src/bad.py", "sample_src/moved.py", "--symbol", SYMBOL, *_scan_arg(seeded)) == 0
    after = _registry_bytes(seeded).splitlines()
    gone = [json.loads(x) for x in before if x not in after]
    added = [json.loads(x) for x in after if x not in before]
    assert gone and len(gone) == len(added)
    assert all({**g, "file": "sample_src/moved.py"} in added for g in gone)
    assert _run(seeded, "check", *_scan_arg(seeded)) == 0
    assert "likely move" not in capsys.readouterr().out


def test_the_summary_file_lists_the_pair(seeded):
    _move_risky(seeded)
    summary = seeded / "summary.md"
    assert _run(seeded, "check", *_scan_arg(seeded), "--summary-out", str(summary)) == 1
    assert "likely move" in summary.read_text() and "sample_src/moved.py" in summary.read_text()


def test_a_refused_move_exits_2_and_leaves_the_registry_byte_identical(seeded, capsys):
    _move_risky(seeded)
    before = _registry_bytes(seeded)
    assert _run(seeded, "move", "sample_src/bad.py", "sample_src/moved.py", "--symbol", "nosuch", *_scan_arg(seeded)) == 2
    assert _run(seeded, "move", "sample_src/dup_a.py", "sample_src/moved.py", *_scan_arg(seeded)) == 2
    assert _run(seeded, "move", "sample_src/bad.py", "sample_src/bad.py", *_scan_arg(seeded)) == 2
    assert "refusing" in capsys.readouterr().err
    assert _registry_bytes(seeded) == before


def test_move_refuses_a_value_over_the_ceiling_and_writes_nothing(seeded):
    _move_risky(seeded)
    path = seeded / "scan" / "complexipy.json"
    data = json.loads(path.read_text())
    for entry in data:
        if entry["function_name"] == SYMBOL:
            entry["complexity"] += 5
    path.write_text(json.dumps(data))
    before = _registry_bytes(seeded)
    assert _run(seeded, "move", "sample_src/bad.py", "sample_src/moved.py", "--symbol", SYMBOL, *_scan_arg(seeded)) == 2
    assert _registry_bytes(seeded) == before
    assert registry.load_rows(seeded / "reg.jsonl", seeded, check_files=False)
