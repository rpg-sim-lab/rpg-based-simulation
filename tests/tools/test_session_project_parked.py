"""TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE: the Parked marker, its precedence and its guards. Pure functions and synthetic
fixtures; no GitHub, no git. The STALEMATE F1 shape is synthetic (an old lane branch whose ticket carries a valid marker naming an open ticket); the live check
on the real F1 ticket is the u24 planner writing the marker after the code lands, not claimed here."""
from dataclasses import replace
from datetime import date, datetime, timezone

from tests.tools.test_session_project_sync_all_lanes import copy, plan_for
from tests.tools.test_session_project_sync_second_host import B, NOW, OLD, STALE_BEFORE, TID
from tools.sessions import project_client as pc
from tools.sessions import project_sync as ps

TARGET = "TCK-20261119-THE-TARGET"
OPEN, DONE = "todos", "done"


def _extras(done=(), known=(TARGET,), today=None):
    ex = ps.Extras()
    ex.known, ex.done, ex.today = frozenset(known), frozenset(done), today
    return ex


def _origin(marker=None, bad=(), blocked=False, folder="inprogress"):
    c = copy(TID, folder)
    return replace(c, parked=marker, parked_bad=tuple(bad), blocked=blocked)


def _lane(activity=OLD):
    return ps.BranchFact(B, "rpg-lane", "/wt", "rpg-implementer-3", "rpg", (copy(TID, "inprogress"),), activity)


def _status(origin, ex=None, prs=(), branches=None, host=B):
    row, findings = ps.derive_item(TID, [origin], list(branches if branches is not None else [_lane()]), None if prs is None else list(prs), None, host, "s",
                                   STALE_BEFORE, ex or _extras())
    return row["Status"], findings


# ---- the parser: line-start, validated, never inferred
def test_a_valid_marker_is_read_in_its_three_forms():
    assert ps.parse_parked(f"x\nParked: waits on {TARGET} since 2026-11-01\n")[0] == ("ticket", TARGET, "2026-11-01")
    assert ps.parse_parked("Parked: waits on PR#12 since 2026-11-01")[0] == ("pr", "PR#12", "2026-11-01")
    assert ps.parse_parked("Parked: waits on decision owner_decision_memo.md row 7 since 2026-10-02")[0] == ("decision", "owner_decision_memo.md row 7", "2026-10-02")


def test_malformed_or_not_line_start_markers_are_not_read_and_a_parked_line_is_reported_as_a_finding():
    for text in (f"  Parked: waits on {TARGET} since 2026-11-01",        # indented: not line-start
                 f"see Parked: waits on {TARGET} since 2026-11-01",       # mid-line
                 "Parked: waits on PR#12 since 2026-13-45",               # not a date
                 "Parked: waits on decision  since 2026-10-02",           # empty reference
                 "Parked: waits on a thing since 2026-10-02",             # no ticket id, PR or decision
                 "this ticket is parked until the owner answers",         # prose is never read
                 "Parked by explicit user decision, not abandoned."):     # the existing prose lines in the corpus
        assert ps.parse_parked(text)[0] is None
    bad = ps.parse_parked("Parked: waits on PR#12 since 2026-13-45\nParked: waits on decision  since 2026-10-02")[1]
    assert len(bad) == 2 and ps.parse_parked("Parked by explicit user decision")[1] == ()  # only a line that STARTS with `Parked: ` counts as malformed


def test_parse_copy_carries_the_marker_and_the_malformed_lines():
    c = ps.parse_copy(f"{ps.TICKETS.as_posix()}/inprogress/{TID}.md", f"## Title\nT\n\nParked: waits on {TARGET} since 2026-11-01\nParked: oops\n")
    assert c.parked == ("ticket", TARGET, "2026-11-01") and c.parked_bad == ("Parked: oops",)


# ---- the F1 fixture and its must-nots (acceptance 1)
def test_the_f1_shape_an_old_lane_with_a_valid_marker_naming_an_open_ticket_reads_parked_not_stale():
    assert _status(_origin(None))[0] == "Stale"  # positive control: without the marker the same old lane reads Stale
    status, findings = _status(_origin(("ticket", TARGET, "2026-11-10")))
    assert status == "Parked" and not [f for f in findings if "Parked" in f]


def test_a_marker_naming_a_done_ticket_clears_itself_and_the_status_is_stale_again():
    assert _status(_origin(("ticket", TARGET, "2026-11-10")), _extras(done=(TARGET,)))[0] == "Stale"


def test_a_malformed_marker_leaves_the_status_unchanged_and_prints_a_finding():
    status, findings = _status(_origin(None, bad=("Parked: waits on a thing since 2026-10-02",)))
    assert status == "Stale" and any("malformed Parked marker ignored" in f for f in findings)


def test_precedence_done_in_review_blocked_then_parked_then_the_rest():
    marker = ("ticket", TARGET, "2026-11-10")
    assert _status(_origin(marker, folder="done"))[0] == "Done"
    review = ps.PrFact(5, "https://x/5", frozenset({f"{ps.TICKETS.as_posix()}/inprogress/{TID}.md"}))
    assert _status(_origin(marker), prs=[review])[0] == "In review"
    assert _status(_origin(marker, blocked=True), branches=[])[0] == "Blocked"  # a ticket Status of BLOCKED wins
    blocked_lane = ps.BranchFact(B, "rpg-lane", "/wt", "rpg-implementer-3", "rpg", (replace(copy(TID, "inprogress"), blocked=True),), OLD)
    assert _status(_origin(marker), branches=[blocked_lane])[0] == "Blocked"  # a lane copy whose Status is BLOCKED beats the marker too
    assert _status(_origin(marker, folder="todos"), branches=[])[0] == "Parked"  # a filed ticket that waits is Parked too (stated in the docs)


def test_a_pr_target_is_open_only_while_it_is_in_the_open_pr_list():
    marker = ("pr", "PR#12", "2026-11-10")
    open_pr = ps.PrFact(12, "https://x/12", frozenset())
    assert _status(_origin(marker), prs=[open_pr])[0] == "Parked"
    assert _status(_origin(marker), prs=[])[0] == "Stale"  # merged or closed: it is no longer in the open list
    status, findings = _status(_origin(marker), prs=None)
    assert status == "Stale" and any("open-PR list could not be read" in f for f in findings)  # unknown: no Parked, a finding


def test_a_decision_target_never_clears_itself_and_an_unknown_ticket_target_is_a_finding_not_parked():
    assert _status(_origin(("decision", "owner_decision_memo.md row 7", "2026-10-02")))[0] == "Parked"
    status, findings = _status(_origin(("ticket", "TCK-20261119-NOWHERE", "2026-11-10")))
    assert status == "Stale" and any("no ticket file on origin/main" in f for f in findings)


def test_a_marker_older_than_the_proposed_45_days_adds_a_finding_never_a_status_change():
    old = ("decision", "ref", "2026-10-01")
    s_old, f_old = _status(_origin(old), _extras(today=date(2026, 11, 20)))  # 50 days
    s_new, f_new = _status(_origin(("decision", "ref", "2026-10-10")), _extras(today=date(2026, 11, 20)))  # 41 days
    assert s_old == s_new == "Parked"
    assert any("over 45 days old" in f for f in f_old) and not any("days old" in f for f in f_new)


# ---- the plan: the note, the option and the colour
def test_the_plan_reports_ran_set_cleared_malformed_and_unknown():
    main = {"TCK-A": [replace(copy("TCK-A", "todos"), parked=("ticket", "TCK-B", "2026-11-10"))],
            "TCK-B": [copy("TCK-B", "todos")],
            "TCK-C": [replace(copy("TCK-C", "todos"), parked=("ticket", "TCK-D", "2026-11-10"))],
            "TCK-D": [copy("TCK-D", "done")],
            "TCK-E": [replace(copy("TCK-E", "todos"), parked_bad=("Parked: oops",))]}
    plan = plan_for(main)
    note = next(n for n in plan.notes if n.startswith("parked:"))
    assert "ran on 3 tickets" in note and "1 read Parked" in note and "1 cleared" in note and "1 malformed" in note
    assert {c["Ticket ID"]: c["Status"] for c in plan.creates}["TCK-A"] == "Parked"


def test_parked_is_the_last_status_has_a_colour_and_init_appends_it_keeping_every_existing_id():
    assert ps.STATUSES[-1] == "Parked" and pc.STATUS_COLORS["Parked"] == "YELLOW"
    from tests.tools.test_project_client import Fake, project
    existing = tuple(s for s in ps.STATUSES if s != "Parked")
    fake = Fake(project(status_options=existing), items=[{"_item_id": "I1", "Status": "Done"}])
    lines, code = pc.init_fields(fake, ps.STATUSES, layers=("combat",))
    (call,) = [c for c in fake.calls if c[0] == "options"]
    assert code == 0 and [n for n, i in call[2]] == list(ps.STATUSES)
    assert all(i == f"O_{n}" for n, i in call[2] if n != "Parked") and dict(call[2])["Parked"] is None  # every existing option keeps its id; only Parked is new


# ---- the timers run --apply, not --init: what happens when a host fast-forwards before `--init` has appended the Parked option
def _board_without_parked():
    from tests.tools.test_session_project_sync_all_lanes import WANTED, _project
    p = _project()
    p.fields["Domain"] = pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", tuple((n, f"O_{n}") for n in WANTED))  # the live Domain is already a select
    st = p.fields["Status"]
    p.fields["Status"] = pc.ProjectField(st.id, st.name, st.type, tuple(o for o in st.options if o[0] != "Parked"))
    return p


class _Client:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        return lambda *a, **k: self.calls.append(name) or ("I", "D")


def _plan_with(status_of):
    main = {"TCK-A": [replace(copy("TCK-A", "todos"), parked=("decision", "memo row 7", "2026-11-10"))] if status_of == "Parked" else [copy("TCK-A", "todos")]}
    return plan_for(main)


def test_apply_without_the_parked_option_carries_on_when_no_ticket_is_parked():
    plan = _plan_with("To do")
    assert plan.creates[0]["Status"] == "To do"
    client = _Client()
    done, not_done, error = pc.apply_plan(client, _board_without_parked(), plan)
    assert error is None and not not_done and client.calls  # the run is not refused: no planned Status needs the missing option


def test_apply_without_the_parked_option_refuses_the_whole_run_before_any_write_once_a_ticket_reads_parked():
    import pytest
    plan = _plan_with("Parked")
    assert plan.creates[0]["Status"] == "Parked"
    client = _Client()
    with pytest.raises(pc.ClientRefused) as err:
        pc.apply_plan(client, _board_without_parked(), plan)
    assert "not options of their field" in str(err.value) and "Parked" in str(err.value) and client.calls == []  # exit 2 in project_sync.main, nothing written
