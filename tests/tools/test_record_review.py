"""Tests for TCK-20261101-RECORD-REVIEW-AFTER-THE-PR-REVIEW-EXISTS: record_review.py, the `supersedes` field, the read overlay."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

_MONITORING_DIR = Path(__file__).parent.parent.parent / "tools" / "agent-monitoring"
if str(_MONITORING_DIR) not in sys.path:
    sys.path.insert(0, str(_MONITORING_DIR))

import generate_retro  # noqa: E402
import path_report  # noqa: E402
import record_events  # noqa: E402
import record_review  # noqa: E402
from run_dedup import drop_superseded_events  # noqa: E402

TICKET = "TCK-FAKE-REVIEW"
REF = "812#6600000001"


def _run(tier="standard", execution_id="x-1", end_ts="2026-11-01T10:00:00Z", mode="hand"):
    return {"run_id": TICKET, "execution_id": execution_id, "provider": "claude", "ticket_id": TICKET,
            "workflow": "implement-ticket", "tier": tier, "execution_mode": mode, "end_ts": end_ts}


def _event(seq, phase, status, execution_id="x-1", **extra):
    e = {"run_id": TICKET, "execution_id": execution_id, "provider": "claude", "ticket_id": TICKET, "seq": seq,
         "phase": phase, "agent": "claude", "status": status, "summary": "s", "ts": "2026-11-01T10:00:00Z"}
    if status == "skipped":
        e["skip_reason"] = "no_hand_tool"
    e.update(extra)
    return e


def _write(root: Path, runs, events):
    week = root / "2026-W44"
    week.mkdir(parents=True)
    (week / "runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in runs))
    (week / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    return week / "events.jsonl"


def _standard_events():
    return [_event(1, "Scope", "ok"), _event(2, "Review", "skipped"), _event(3, "Implement", "ok"), _event(4, "Finalize", "ok")]


def _snapshot(root: Path):
    return {str(p): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def _gh(stdout="", returncode=0, stderr=""):
    return lambda *a, **k: subprocess.CompletedProcess(a, returncode, stdout, stderr)


def _ok_gh(pr="812"):
    return _gh(f"https://api.github.com/repos/o/r/issues/{pr}\n")


def _main(root, events_file, ref=REF, runner=None, ticket=TICKET):
    return record_review.main(["--ticket-id", ticket, "--review-ref", ref], data_root=root, events_file=events_file,
                              runner=runner or _ok_gh())


def test_append_adds_one_review_ok_event_superseding_the_skip_and_rewrites_nothing(tmp_path):
    events_file = _write(tmp_path, [_run()], _standard_events())
    before = events_file.read_bytes()
    assert _main(tmp_path, events_file) == 0
    after = events_file.read_bytes()
    assert after.startswith(before)
    (new,) = [json.loads(x) for x in after[len(before):].decode().splitlines()]
    assert (new["phase"], new["status"], new["seq"], new["supersedes"]) == ("Review", "ok", 5, 2)
    assert (new["run_id"], new["execution_id"]) == (TICKET, "x-1")
    assert "812" in new["summary"] and "6600000001" in new["summary"]
    assert record_events.validate_record(new) == []


def test_a_run_with_no_review_event_gets_the_row_without_supersedes(tmp_path):
    events_file = _write(tmp_path, [_run()], [_event(1, "Scope", "ok")])
    assert _main(tmp_path, events_file) == 0
    new = json.loads(events_file.read_text().splitlines()[-1])
    assert new["seq"] == 2 and "supersedes" not in new


@pytest.mark.parametrize("case", ["no_run", "hotfix", "bad_ref_1", "bad_ref_2", "bad_ref_3", "bad_ref_4", "already_ok",
                                  "second_run", "comment_missing", "comment_other_pr"])
def test_each_refusal_exits_1_and_leaves_the_shards_byte_identical(tmp_path, case):
    runs, events, ref, runner = [_run()], _standard_events(), REF, _ok_gh()
    if case == "no_run":
        runs = [_run(mode="workflow")]
    elif case == "hotfix":
        runs = [_run(tier="hotfix")]
    elif case.startswith("bad_ref"):
        ref = {"bad_ref_1": "12", "bad_ref_2": "12#", "bad_ref_3": "0#5", "bad_ref_4": "a#b"}[case]
    elif case == "already_ok":
        events = [_event(1, "Review", "ok")]
    elif case == "second_run":
        events = _standard_events()
    elif case == "comment_missing":
        runner = _gh(returncode=1, stderr="gh: Not Found (HTTP 404)")
    elif case == "comment_other_pr":
        runner = _ok_gh(pr="999")
    events_file = _write(tmp_path, runs, events)
    if case == "second_run":
        assert _main(tmp_path, events_file) == 0
    snap = _snapshot(tmp_path)
    assert _main(tmp_path, events_file, ref=ref, runner=runner) == 1
    assert _snapshot(tmp_path) == snap


def test_gh_unavailable_warns_and_still_writes(tmp_path, capsys):
    events_file = _write(tmp_path, [_run()], _standard_events())

    def boom(*a, **k):
        raise FileNotFoundError("gh")

    assert _main(tmp_path, events_file, runner=boom) == 0
    assert "WARNING" in capsys.readouterr().err
    assert json.loads(events_file.read_text().splitlines()[-1])["phase"] == "Review"


def test_gh_failing_for_another_reason_warns_and_still_writes(tmp_path, capsys):
    events_file = _write(tmp_path, [_run()], _standard_events())
    assert _main(tmp_path, events_file, runner=_gh(returncode=1, stderr="network down")) == 0
    assert "WARNING" in capsys.readouterr().err


def test_the_latest_hand_execution_wins(tmp_path):
    runs = [_run(execution_id="x-old", end_ts="2026-10-30T10:00:00Z"), _run(execution_id="x-new", end_ts="2026-11-01T10:00:00Z")]
    events = [_event(1, "Review", "skipped", execution_id="x-old"), _event(1, "Review", "skipped", execution_id="x-new")]
    events_file = _write(tmp_path, runs, events)
    assert _main(tmp_path, events_file) == 0
    assert json.loads(events_file.read_text().splitlines()[-1])["execution_id"] == "x-new"


@pytest.mark.parametrize("bad", [0, -1, "3", True, 1.5])
def test_validate_record_rejects_a_bad_supersedes(bad):
    assert any("supersedes" in e for e in record_events.validate_record(_event(5, "Review", "ok", supersedes=bad)))


def test_validate_record_accepts_a_positive_int_supersedes():
    assert record_events.validate_record(_event(5, "Review", "ok", supersedes=2)) == []


def test_drop_superseded_events_drops_only_the_matching_skip_and_keeps_order():
    events = _standard_events() + [_event(5, "Review", "ok", supersedes=2)]
    assert [e["seq"] for e in drop_superseded_events(events)] == [1, 3, 4, 5]


@pytest.mark.parametrize("new", [_event(5, "Review", "failed", supersedes=2), _event(5, "Review", "ok", supersedes=2, execution_id="x-2"),
                                 _event(5, "Verify", "ok", supersedes=2)])
def test_drop_superseded_events_keeps_a_skip_the_new_row_does_not_replace(new):
    assert [e["seq"] for e in drop_superseded_events(_standard_events() + [new])] == [1, 2, 3, 4, 5]


def test_drop_superseded_events_is_a_no_op_without_supersedes():
    events = _standard_events()
    assert drop_superseded_events(events) == events


def test_phase_status_counts_review_once_with_a_post_review_and_is_unchanged_without():
    base = _standard_events()
    with_review = base + [_event(5, "Review", "ok", supersedes=2)]
    runs = [_run()]
    after = generate_retro.compute_retro_metrics(runs, drop_superseded_events(with_review))["phase_status_distribution"]["Review"]
    before = generate_retro.compute_retro_metrics(runs, base)["phase_status_distribution"]["Review"]
    assert (after.get("ok", 0), after.get("skipped", 0)) == (1, 0)
    assert (before.get("ok", 0), before.get("skipped", 0)) == (0, 1)
    assert generate_retro.compute_retro_metrics(runs, drop_superseded_events(base)) == generate_retro.compute_retro_metrics(runs, base)


def test_loader_applies_the_overlay_on_the_direct_read_path(tmp_path, monkeypatch):
    _write(tmp_path, [_run()], _standard_events() + [_event(5, "Review", "ok", supersedes=2)])
    monkeypatch.setattr(generate_retro, "DEFAULT_DB_PATH", tmp_path / "missing" / "no.db")
    monkeypatch.setattr(generate_retro, "RUNS_FILE", tmp_path)
    monkeypatch.setattr(generate_retro, "EVENTS_FILE", tmp_path)
    monkeypatch.setattr(generate_retro, "_index_is_stale", lambda *_: False)
    _, events = generate_retro._load_runs_and_events()
    assert [(e["seq"], e["status"]) for e in events if e["phase"] == "Review"] == [(5, "ok")]


def test_path_report_counts_review_as_ran_once_with_both_rows():
    run = {**_run(), "path_reason": "small_change", "phases_omitted": []}
    both = _standard_events() + [_event(5, "Review", "ok", supersedes=2)]
    (group,) = path_report.analyze([run], both)
    assert (group["phases"]["Review"]["ran"], group["phases"]["Review"]["skipped"]) == (1, 0)
    (group,) = path_report.analyze([run], _standard_events())
    assert (group["phases"]["Review"]["ran"], group["phases"]["Review"]["skipped"]) == (0, 1)


def test_cross_week_append_still_joins_the_runs_week(tmp_path):
    (tmp_path / "2026-W43").mkdir()
    (tmp_path / "2026-W43" / "runs.jsonl").write_text(json.dumps(_run()) + "\n")
    (tmp_path / "2026-W43" / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in _standard_events()))
    late = tmp_path / "2026-W44"
    late.mkdir()
    events_file = late / "events.jsonl"
    assert _main(tmp_path, events_file) == 0
    from validate import load_data_glob
    events = drop_superseded_events(load_data_glob(tmp_path, "events"))
    run_ids = {r["run_id"] for r in load_data_glob(tmp_path, "runs")}
    mine = [e for e in events if e["run_id"] in run_ids and e["phase"] == "Review"]
    assert [(e["seq"], e["status"]) for e in mine] == [(5, "ok")]
