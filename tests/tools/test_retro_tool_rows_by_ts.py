"""Retro readers pick a period's tool rows by their own `ts`, not by run_id (null since W42).

TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "agent-monitoring"))
sys.path.insert(0, str(REPO_ROOT))

import generate_retro as gr  # noqa: E402

from tools.delivery import delivery_cost_measurement as dcm  # noqa: E402

W45_TS = "2026-11-03T10:00:00+00:00"  # ISO 2026-W45
W44_TS = "2026-10-28T10:00:00+00:00"  # ISO 2026-W44


def _row(tool="Bash", ts=W45_TS, run_id=None, summary="x"):
    return {"tool": tool, "ts": ts, "run_id": run_id, "input_summary": summary, "session_id": "s"}


def test_week_selects_null_run_id_rows_by_ts():
    rows = [_row(ts=W45_TS), _row(ts=W44_TS), _row(ts=W45_TS, summary="y")]
    picked, missing, dups = gr.tools_in_period(rows, week="2026-W45")
    assert len(picked) == 2 and (missing, dups) == (0, 0)


def test_cutoff_window_selects_by_ts():
    rows = [_row(ts=W45_TS), _row(ts=W44_TS)]
    picked, _, _ = gr.tools_in_period(rows, cutoff="2026-11-01T00:00:00+00:00")
    assert [r["ts"] for r in picked] == [W45_TS]


def test_rows_without_a_usable_ts_are_counted_not_guessed():
    rows = [_row(ts=None), {"tool": "Bash"}, _row(ts="garbage"), _row()]
    picked, missing, _ = gr.tools_in_period(rows, week="2026-W45")
    assert len(picked) == 1 and missing == 3
    assert "3 without a usable `ts`" in gr.tool_selection_note(missing, 0)


def test_the_same_row_in_two_shards_counts_once():
    rows = [_row(summary="same"), _row(summary="same"), _row(summary="other")]
    picked, _, dups = gr.tools_in_period(rows, week="2026-W45")
    assert len(picked) == 2 and dups == 1
    assert "1 exact-duplicate" in gr.tool_selection_note(0, dups)


def test_no_note_when_nothing_was_set_aside():
    assert gr.tool_selection_note(0, 0) is None


def test_period_with_only_null_run_id_rows_says_not_attributable():
    rows = [_row(tool="ToolSearch"), _row(tool="Read"), _row(tool="Skill", summary="{'skill': 'graphify'}")]
    assert gr.build_search_count_section(rows)["per_run_note"] == gr.NOT_ATTRIBUTABLE_NOTE
    assert gr.build_raw_investigation_count_section(rows)["per_run_note"] == gr.NOT_ATTRIBUTABLE_NOTE


def test_a_real_run_id_in_the_mix_keeps_per_run_table_without_the_note():
    rows = [_row(tool="ToolSearch"), _row(tool="ToolSearch", run_id="run-1")]
    assert gr.build_search_count_section(rows)["per_run_note"] is None


def test_report_renders_the_tool_totals_and_notes_for_null_run_id_rows():
    rows = [_row(tool="ToolSearch"), _row(tool="Read")]
    text = gr.generate([], [], "2026-W45", week_str="2026-W45", tools=rows, tool_note=gr.tool_selection_note(2, 1))
    assert "**Total:** 1" in text
    assert gr.NOT_ATTRIBUTABLE_NOTE in text
    assert "1 exact-duplicate" in text


def test_delivery_cost_counts_gh_calls_on_null_run_id_rows():
    rows = [_row(summary="gh pr list"), _row(summary="gh pr create --title t"), _row(summary="git status")]
    report = dcm.build_gh_call_report(rows)
    assert report["gh_calls_total"] == 2 and report["gh_pr_create_count"] == 1


def test_a_legacy_row_without_ts_but_with_a_period_run_id_is_kept():
    rows = [{"tool": "Read", "run_id": "TCK-1"}, {"tool": "Read", "run_id": "other"}]
    picked, missing, _ = gr.tools_in_period(rows, week="2026-W45", legacy_run_ids={"TCK-1"})
    assert [r["run_id"] for r in picked] == ["TCK-1"] and missing == 1
