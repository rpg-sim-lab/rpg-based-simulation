"""TCK-20261119-PROJECT-SYNC-APPLY-SKIPS-ITEMS-WITH-A-MISSING-STATUS-OPTION-AND-FLAGS-DOUBTFUL-PARKED-MARKERS: --apply leaves only the item whose planned select
value has no option on the Project, exits with the distinct code 3, records the skipped count and an honest `error` text; a missing FIELD still refuses the whole run;
two Parked-marker findings. Fixtures in memory (no `Parked: ` line at a line start is written to disk). No network."""
from dataclasses import replace

import pytest

from tests.tools.test_session_project_sync_all_lanes import WANTED, FakeClient, copy, plan_for
from tests.tools.test_session_project_sync_second_host import B, OLD, STALE_BEFORE, TID, fact
from tools.sessions import project_client as pc
from tools.sessions import project_sync as ps


@pytest.fixture(autouse=True)
def _last_run_in_tmp(tmp_path_factory, monkeypatch):  # main() writes last-run.json for any --apply run: never the host's real one
    monkeypatch.setattr(ps, "LAST_RUN_PATH", tmp_path_factory.mktemp("state") / "last-run.json")


class _Client:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        return lambda *a, **k: self.calls.append((name, a)) or ("I", "D")


def _board(without=()):
    from tests.tools.test_session_project_sync_all_lanes import _project
    p = _project()
    p.fields["Domain"] = pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", tuple((n, f"O_{n}") for n in WANTED))
    st = p.fields["Status"]
    p.fields["Status"] = pc.ProjectField(st.id, st.name, st.type, tuple(o for o in st.options if o[0] not in without))
    return p


def _parked(tid):
    return replace(copy(tid, "todos"), parked=("decision", "memo row 7", "2026-11-10"))


# ---- acceptance 1: one item planned for a missing option is skipped, every other item is written
def test_an_update_planned_for_a_missing_status_option_is_skipped_whole_and_the_other_items_are_written():
    main = {"TCK-P": [_parked("TCK-P")], "TCK-OK": [copy("TCK-OK", "todos")]}
    old = {"TCK-P": {"Ticket ID": "TCK-P", "Title": "TCK-P: A title", "Status": "To do", "Sync hash": "v5:old", "_item_id": "IP", "_draft_id": "DP"},
           "TCK-OK": {"Ticket ID": "TCK-OK", "Title": "TCK-OK: A title", "Status": "In progress", "Sync hash": "v5:old", "_item_id": "IOK", "_draft_id": "DOK"}}
    plan = plan_for(main, items=list(old.values()))
    assert {u[0]["Ticket ID"]: u[0]["Status"] for u in plan.updates} == {"TCK-P": "Parked", "TCK-OK": "To do"}
    assert pc.check_plan_options(_board(without=("Parked",)), plan) == ["TCK-P Status 'Parked'"]  # positive control: this input used to refuse the whole run
    client = _Client()
    done, not_done, error = pc.apply_plan(client, _board(without=("Parked",)), plan)
    assert error is None and not not_done and plan.skipped == {"TCK-P": ["Status 'Parked'"]}
    assert any(d.startswith("update TCK-OK:") for d in done)  # the other item is written
    assert not any("TCK-P" in d for d in done) and not any(c[1] and "IP" in c[1] for c in client.calls)  # nothing of the skipped item: no field and no Sync hash, so the next run retries it


def test_a_create_planned_for_a_missing_option_is_not_created():
    plan = plan_for({"TCK-P": [_parked("TCK-P")], "TCK-OK": [copy("TCK-OK", "todos")]})
    client = _Client()
    done, _, error = pc.apply_plan(client, _board(without=("Parked",)), plan)
    assert error is None and plan.skipped == {"TCK-P": ["Status 'Parked'"]}
    assert any(d == "create TCK-OK: draft item" for d in done) and not any("TCK-P" in d for d in done)


def test_every_select_field_is_covered_not_only_status():
    plan = plan_for({"TCK-T": [copy("TCK-T", "todos", tier="standard")]})
    plan.creates[0]["Tier"] = "weird"  # a Tier value the Project has no option for
    done, _, error = pc.apply_plan(_Client(), _board(), plan)
    assert error is None and done == [] and plan.skipped == {"TCK-T": ["Tier 'weird'"]}


# ---- acceptance 2: a missing FIELD still refuses the whole run
def test_a_missing_field_still_refuses_the_whole_run_before_any_write():
    plan = plan_for({"TCK-OK": [copy("TCK-OK", "todos")]})
    board = _board()
    del board.fields["Involved"]
    client = _Client()
    with pytest.raises(pc.ClientRefused, match="no field.*Involved.*run --init first"):
        pc.apply_plan(client, board, plan)
    assert client.calls == []


# ---- acceptance 3: the distinct exit code, the notes and the last-run record
def _apply_main(monkeypatch, tmp_path, skipped, error=None):
    (tmp_path / "registries").mkdir(exist_ok=True)
    (tmp_path / "registries" / "session_project.yaml").write_text("project: {owner: o, number: 1}\n")
    client = FakeClient()
    client.list_items = lambda: []
    client.load_project = lambda: client.proj
    monkeypatch.setattr(ps, "_client", lambda cfg, notes=None: client)
    monkeypatch.setattr(ps, "origin_info", lambda root: ("abc", None))
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: ([], 0))
    monkeypatch.setattr(ps, "read_open_prs", lambda root, notes, run=None: ps.PrList())

    def fake_apply(c, project, plan, **k):
        plan.skipped = skipped
        return (["update TCK-1: set Status"], [], error)
    monkeypatch.setattr(pc, "apply_plan", fake_apply)
    return ps.main(["--root", str(tmp_path), "--apply"])


def test_apply_with_a_skipped_item_exits_3_and_records_the_count_and_an_honest_error_text(monkeypatch, tmp_path, capsys):
    rc = _apply_main(monkeypatch, tmp_path, {"TCK-B": ["Status 'Parked'"], "TCK-A": ["Tier 'weird'"], "TCK-C": ["Layer 'x'"], "TCK-D": ["Domain 'y'"]})
    assert rc == ps.EXIT_SKIPPED == 3 and rc not in (0, 1, 2)  # distinct from a pass, a stop and a refusal
    err = capsys.readouterr()
    assert "finding: skipped TCK-A: Tier 'weird' has no option on the Project" in err.err and "skipped 4 item(s)" in err.out
    data = ps.read_last_run()
    assert data["rc"] == 3 and data["skipped"] == 4 and data["error"] == "skipped 4 item(s): TCK-A, TCK-B, TCK-C ...; run --init" and data["failed_streak"] == 1


def test_apply_with_nothing_skipped_still_exits_0_and_a_stop_still_exits_1(monkeypatch, tmp_path):
    assert _apply_main(monkeypatch, tmp_path, {}) == 0 and ps.read_last_run()["skipped"] == 0
    assert _apply_main(monkeypatch, tmp_path, {"TCK-A": ["Status 'Parked'"]}, error="update TCK-1: set Source: boom") == 1  # a stop wins over a skip
    assert ps.read_last_run()["error"].endswith("boom")


def test_the_sessionstart_line_reads_truthfully_with_no_hook_edit(monkeypatch, tmp_path):
    from tools.sessions import session_start_hook as hook
    _apply_main(monkeypatch, tmp_path, {"TCK-A": ["Status 'Parked'"]})
    _apply_main(monkeypatch, tmp_path, {"TCK-A": ["Status 'Parked'"]})  # the second tick in a row: failed_streak 2 raises the SessionStart line
    line = hook._sync_line()
    assert "the last 2 --apply runs" in line and "skipped 1 item(s): TCK-A; run --init" in line


# ---- acceptance 4: the two Parked findings
def _lane(activity):
    return ps.BranchFact(B, "rpg-lane", "/wt", "rpg-implementer-3", "rpg", (copy(TID, "inprogress"),), activity)


def _status(origin, branches, today=None):
    ex = ps.Extras()
    ex.known, ex.done, ex.today = frozenset({"TCK-TARGET", TID}), frozenset(), today
    row, findings = ps.derive_item(TID, [origin], branches, None, None, B, "s", STALE_BEFORE, ex)
    return row["Status"], findings


def test_a_marker_on_a_ticket_with_a_live_non_stale_branch_is_still_parked_with_a_finding():
    origin = replace(copy(TID, "inprogress"), parked=("ticket", "TCK-TARGET", "2026-11-10"))
    status, findings = _status(origin, [_lane(STALE_BEFORE + 86400)])  # fresh activity: a live branch
    assert status == "Parked" and any("a live branch is working it: still waiting?" in f for f in findings)


def test_a_marker_on_a_ticket_with_only_a_stale_branch_prints_no_such_finding():
    origin = replace(copy(TID, "inprogress"), parked=("ticket", "TCK-TARGET", "2026-11-10"))
    status, findings = _status(origin, [_lane(OLD)])
    assert status == "Parked" and not any("live branch" in f for f in findings)


def test_a_marker_naming_the_tickets_own_id_is_malformed_and_never_parked():
    origin = replace(copy(TID, "inprogress"), parked=("ticket", TID, "2026-11-10"))
    status, findings = _status(origin, [_lane(OLD)])
    assert status == "Stale" and any("names the ticket's own id" in f and "malformed" in f for f in findings)
