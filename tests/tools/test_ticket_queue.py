"""Tests for TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS: tools/delivery/ticket_queue.py."""
import hashlib
import json
import sys
from pathlib import Path

import pytest

_DELIVERY = Path(__file__).parent.parent.parent / "tools" / "delivery"
if str(_DELIVERY) not in sys.path:
    sys.path.insert(0, str(_DELIVERY))

import ticket_queue  # noqa: E402
from pr_status import CommandResult  # noqa: E402

REPO_ROOT = Path(__file__).parent.parent.parent
# Verbatim copy of roadmap.md line 1264 (section 12.5) as of 2026-11-02: two order sentences, the last one current.
ROADMAP_ORDER_LINE = "- **Order:** HUNGER step B → step A → the decision-73 step (free meal removed) → the §12.3 milestone 1 items. Amended by the owner on 2026-10-31 (#715 6541804604, memo row 93): after F4, four repairs land before the decision-73 step, in this order: F3 (a sleeper holds a door or service tile), the N14 re-measure on F3, A' (sleep wins over hunger with no bed) and the stalemate/wander navigation family; D80C (SimQ reads the lossless event file) also stays ahead of decision 73. The order is then HUNGER B → A → F4 → F3 → N14 → A' → nav → decision 73 → the items. Amended again on 2026-10-31 (#715 6543553366, memo row 95): the SURV-07 precedence fix lands between F3 and the N14 re-measure, so the order is HUNGER B → A → F4 → F3 → precedence → N14 → A' → nav → D80C → decision 73 → the items. F4 lands as soon as it is ready, independent of this order, provided the gate worlds form no faction squad on seeds 42-46 (probe A0 extended to the gate's 3 worlds × seeds 42-46 × 5000 ticks; memo row 90, owner 2026-10-26). Otherwise it keeps its slot after step A with its own paired step."
ROADMAP = "## 12. x\n\n### 12.4 before\ntext\n\n### 12.5 Milestone 1: done criteria\n\n- **Order:** " + ROADMAP_ORDER_LINE + "\n- next bullet\n\n### 12.6 after\nThe order is X \u2192 Y \u2192 Z.\n"
STEPS = ["HUNGER B", "A", "F4", "F3", "precedence", "N14", "A'", "nav", "D80C", "decision 73", "the items"]


def _ticket(ticket_id, status="OPEN", tier="standard", priority="P2", layer="ai", extra="", order_ref=None):
    ref = f"\n## Order Ref\n{order_ref}\n" if order_ref else ""
    return (f"---\nstatus: active\nlayer: {layer}\nauthority: P1\naudience: agent\nticket_id: {ticket_id}\nphase: open\n"
            f"date: 2026-11-01\ntags: []\n---\n\n# {ticket_id}\n\n## Title\nT\n\n## Status\n{status}\n\n## Tier\n{tier}\n\n"
            f"## Priority\n{priority}\n{ref}\n## Request Summary\nS\n{extra}\n")


class Runner:
    """Answers git/gh from a dict of tickets {path: text}; records every command."""
    def __init__(self, tickets, roadmap=ROADMAP, prs=None, comments="", gh_ok=True):
        self.tickets, self.roadmap, self.prs, self.comments, self.gh_ok, self.calls = tickets, roadmap, prs or [], comments, gh_ok, []

    def __call__(self, cmd, timeout=30):
        self.calls.append(cmd)
        if cmd[0] == "gh":
            if not self.gh_ok:
                return CommandResult(1, "", "gh: command not found")
            if cmd[1] == "pr":
                return CommandResult(0, json.dumps(self.prs), "")
            return CommandResult(0, self.comments, "")
        if cmd[1] == "rev-parse":
            return CommandResult(0, "abcdef1234567890\n", "")
        if cmd[1] == "show" and cmd[2] == "-s":
            return CommandResult(0, "2026-11-02T10:00:00+07:00\n", "")
        if cmd[1] == "ls-tree":
            return CommandResult(0, "\n".join(sorted(self.tickets) + ["agent-working/tickets/todos/.gitkeep", "agent-working/tickets/todos/SEQUENCE.md"]) + "\n", "")
        if cmd[1] == "show":
            key = cmd[2].split(":", 1)[1]
            if key == ticket_queue.ROADMAP:
                return CommandResult(0, self.roadmap, "")
            return CommandResult(0, self.tickets[key], "")
        raise AssertionError(cmd)


def _path(ticket_id, folder="todos"):
    return f"agent-working/tickets/{folder}/{ticket_id}.md"


def _view(tickets, **kw):
    return ticket_queue.build_view(Runner(tickets, **kw), "origin/main")


def _row(view, ticket_id):
    return next(r for r in view["rows"] if r["id"] == ticket_id)


def test_every_ticket_path_once_header_names_ref_sha_and_date_and_skips_non_tickets():
    tickets = {_path("TCK-20261101-A"): _ticket("TCK-20261101-A"), _path("TCK-20261101-B", "inprogress"): _ticket("TCK-20261101-B")}
    view = _view(tickets)
    assert sorted(r["id"] for r in view["rows"]) == ["TCK-20261101-A", "TCK-20261101-B"]
    assert view["header"]["source"] == "origin/main" and view["header"]["sha"].startswith("abcdef")
    assert view["header"]["commit_date"] == "2026-11-02T10:00:00+07:00"
    assert "abcdef123456" in ticket_queue.render_text(view)


def test_a_ticket_in_two_status_folders_is_flagged_not_resolved():
    tickets = {_path("TCK-20261101-A"): _ticket("TCK-20261101-A"), _path("TCK-20261101-A", "inprogress"): _ticket("TCK-20261101-A")}
    view = _view(tickets)
    assert len(view["rows"]) == 2 and all("two-folders" in r["flags"] for r in view["rows"]) and view["summary"]["two_folders"] == 2


def test_status_reads_the_first_token_only():
    tickets = {
        _path("TCK-20261101-PROSE"): _ticket("TCK-20261101-PROSE", status="OPEN (counts first; was previously BLOCKED)"),
        _path("TCK-20261101-BLK"): _ticket("TCK-20261101-BLK", status="BLOCKED"),
    }
    view = _view(tickets)
    assert _row(view, "TCK-20261101-PROSE")["status"] == "OPEN" and _row(view, "TCK-20261101-PROSE")["blocked"] is None
    assert _row(view, "TCK-20261101-BLK")["status"] == "BLOCKED"


def test_blocked_names_ticket_ids_from_the_status_line_else_unknown():
    tickets = {
        _path("TCK-20261101-WITH"): _ticket("TCK-20261101-WITH", status="BLOCKED (on TCK-20260914-OTHER-THING; more)"),
        _path("TCK-20261101-WITHOUT"): _ticket("TCK-20261101-WITHOUT", status="BLOCKED"),
    }
    view = _view(tickets)
    assert _row(view, "TCK-20261101-WITH")["blocked"] == {"on": ["TCK-20260914-OTHER-THING"]}
    assert _row(view, "TCK-20261101-WITHOUT")["blocked"] == {"on": "unknown"}
    assert view["summary"]["blocked_on_unknown"] == 1


def test_parked_yes_only_on_the_narrow_lines_with_path_and_line_and_mention_is_not_parked():
    env06 = "\n**ENV-06 is parked, not this ticket.**\n"
    paused = "\nPre.\n**Paused (owner, #715 issuecomment-1, recorded 2026-11-01).**\n"
    mention = "\nParked time: 3 days.\n"
    heading = "\n## Parked (owner ruling)\ntext\n"
    decision = "\n**Parked by explicit user decision, not abandoned.**\n"
    bold = "\n**Parked**, per the user's direction to fix only hard bugs.\n"
    fenced = "\n```\n## Parked\n**Paused (owner,\n```\n"
    tickets = {_path(f"TCK-20261101-{n}"): _ticket(f"TCK-20261101-{n}", extra=x) for n, x in
               {"ENV": env06, "PAUSED": paused, "MENTION": mention, "HEAD": heading, "DEC": decision, "BOLD": bold, "FENCE": fenced}.items()}
    view = _view(tickets)
    assert _row(view, "TCK-20261101-ENV")["parked"] == "mention"
    assert _row(view, "TCK-20261101-MENTION")["parked"] == "mention"
    assert _row(view, "TCK-20261101-FENCE")["parked"] is None
    for n in ("PAUSED", "HEAD", "DEC", "BOLD"):
        row = _row(view, f"TCK-20261101-{n}")
        assert row["parked"] == "yes" and row["parked_at"].startswith(_path(f"TCK-20261101-{n}") + ":")
    assert view["summary"]["parked"] == {"yes": 4, "mention": 2}


def test_the_parsed_order_matches_the_amended_line_on_a_verbatim_fixture_and_ignores_the_superseded_sentence():
    steps, at, warnings = ticket_queue.parse_order(ROADMAP)
    assert steps == STEPS and at.endswith(":" + str(ROADMAP.splitlines().index("- **Order:** " + ROADMAP_ORDER_LINE) + 1))
    assert warnings == []  # nothing with an arrow or 'Amended' follows on the same line, and 12.6 is outside the section


def test_order_refs_in_line_stale_and_none():
    tickets = {
        _path("TCK-20261101-IN"): _ticket("TCK-20261101-IN", order_ref="f3"),
        _path("TCK-20261101-STALE"): _ticket("TCK-20261101-STALE", order_ref="Z9"),
        _path("TCK-20261101-NONE"): _ticket("TCK-20261101-NONE"),
    }
    view = _view(tickets)
    assert _row(view, "TCK-20261101-IN")["order"] == "4"
    assert _row(view, "TCK-20261101-STALE")["order"] == "stale-ref"
    assert _row(view, "TCK-20261101-NONE")["order"] == "unknown"
    assert view["rows"][0]["id"] == "TCK-20261101-IN"  # a positioned row sorts first


def test_an_unparseable_roadmap_makes_every_order_unknown_with_one_warning_and_no_guess():
    bad = "### 12.5 x\n\nNo order sentence here, only F3 and HUNGER B.\n"
    view = _view({_path("TCK-20261101-IN"): _ticket("TCK-20261101-IN", order_ref="F3")}, roadmap=bad)
    assert _row(view, "TCK-20261101-IN")["order"] == "unknown"
    assert sum("no parseable order line" in w for w in view["warnings"]) == 1
    assert ticket_queue.parse_order(None)[0] == []


def test_a_superseding_arrow_after_the_order_line_warns_but_positions_still_print():
    text = ROADMAP.replace("- next bullet", "- next bullet")
    text = text.replace(ROADMAP_ORDER_LINE, ROADMAP_ORDER_LINE + " Amended again: A \u2192 B.")
    steps, _, warnings = ticket_queue.parse_order(text)
    assert steps == STEPS and any("may be superseded" in w for w in warnings)


def test_the_real_roadmap_still_parses_at_least_three_steps():
    steps, at, _ = ticket_queue.parse_order((REPO_ROOT / ticket_queue.ROADMAP).read_text(encoding="utf-8"))
    assert len(steps) >= 3, ("ticket_queue.py can no longer parse roadmap section 12.5 into an order line; the queue view "
                             "degrades to order 'unknown' for every ticket until the parser or the roadmap wording is fixed")


def test_flight_closes_touches_and_the_634_comment_are_counted_separately():
    ids = ["TCK-20261101-A", "TCK-20261101-B", "TCK-20261101-C", "TCK-20261101-D"]
    tickets = {_path(i): _ticket(i) for i in ids}
    prs = [{"number": 7, "title": "x", "files": [{"path": "agent-working/tickets/done/TCK-20261101-A.md"}]},
           {"number": 8, "title": "names TCK-20261101-B only", "files": [{"path": "agent-working/tickets/todos/TCK-20261101-C.md"}]}]
    comments = json.dumps([501, "claim TCK-20261101-D here"]) + "\n" + json.dumps([502, "later TCK-20261101-D"])
    view = _view(tickets, prs=prs, comments=comments)
    assert _row(view, "TCK-20261101-A")["flight"] == ["pr #7 closes"]
    assert _row(view, "TCK-20261101-B")["flight"] == ["pr #8 touches"]
    assert _row(view, "TCK-20261101-C")["flight"] == ["pr #8 touches"]
    assert _row(view, "TCK-20261101-D")["flight"] == ["#634 comment 502"]
    assert "running" not in ticket_queue.render_text(view)
    assert view["summary"]["flight"]["closes"] == 1 and view["summary"]["flight"]["touches"] == 2


def test_gh_limits_warn_for_a_pr_at_the_files_cap_and_a_full_list(monkeypatch):
    big = {"number": 9, "title": "t", "files": [{"path": f"f{i}"} for i in range(100)]}
    view = _view({_path("TCK-20261101-A"): _ticket("TCK-20261101-A")}, prs=[big])
    assert any("PR #9" in w and "100" in w for w in view["warnings"])
    monkeypatch.setattr(ticket_queue, "PR_LIMIT", 1)
    view = _view({_path("TCK-20261101-A"): _ticket("TCK-20261101-A")}, prs=[big])
    assert any("reached its limit" in w for w in view["warnings"])


def test_with_gh_unavailable_the_view_still_prints_and_flight_reads_unknown(capsys):
    runner = Runner({_path("TCK-20261101-A"): _ticket("TCK-20261101-A")}, gh_ok=False)
    assert ticket_queue.main(["--ref", "origin/main"], run_command=runner) == 0
    out = capsys.readouterr().out
    assert "TCK-20261101-A" in out and "flight reads unknown" in out and "| unknown" in out


def test_epic_rows_are_marked_and_left_out_of_the_work_counts():
    tickets = {_path("TCK-20261101-EP"): _ticket("TCK-20261101-EP", status="EPIC_SCOPED", tier="epic", priority="P1"),
               _path("TCK-20261101-W"): _ticket("TCK-20261101-W", priority="P1")}
    view = _view(tickets)
    assert _row(view, "TCK-20261101-EP")["epic"] is True
    assert view["summary"]["work_rows"] == 1 and view["summary"]["epic_tracking_rows"] == 1 and view["summary"]["p1"]["total"] == 1


def test_summary_has_unknown_counts_and_p1_by_status_tier_layer_and_json_equals_the_view(capsys):
    tickets = {_path("TCK-20261101-A"): _ticket("TCK-20261101-A", priority="P1", layer="ai"),
               _path("TCK-20261101-B"): _ticket("TCK-20261101-B", priority="P1", status="BLOCKED", tier="hotfix", layer="world")}
    runner = Runner(tickets)
    view = ticket_queue.build_view(runner, "origin/main")
    s = view["summary"]
    assert s["order"]["unknown"] == 2 and s["p1"]["by_status"] == {"OPEN": 1, "BLOCKED": 1}
    assert s["p1"]["by_tier"] == {"standard": 1, "hotfix": 1} and s["p1"]["by_layer"] == {"ai": 1, "world": 1}
    assert ticket_queue.main(["--json"], run_command=runner) == 0
    assert json.loads(capsys.readouterr().out) == json.loads(json.dumps(view))


def test_the_default_run_reads_no_working_tree_ticket_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # an empty directory: any working-tree read would find no tickets
    before = hashlib.sha256(repr(sorted(p.name for p in tmp_path.rglob("*"))).encode()).hexdigest()
    runner = Runner({_path("TCK-20261101-A"): _ticket("TCK-20261101-A")})
    view = ticket_queue.build_view(runner, "origin/main")
    assert [r["id"] for r in view["rows"]] == ["TCK-20261101-A"]
    assert all(c[0] in ("git", "gh") and c[1] in ("rev-parse", "show", "ls-tree", "pr", "api") for c in runner.calls)
    assert before == hashlib.sha256(repr(sorted(p.name for p in tmp_path.rglob("*"))).encode()).hexdigest()


def test_worktree_mode_reads_the_files_and_leaves_the_tree_byte_identical(tmp_path):
    todos = tmp_path / "agent-working" / "tickets" / "todos"
    todos.mkdir(parents=True)
    (todos / "TCK-20261101-A.md").write_text(_ticket("TCK-20261101-A"), encoding="utf-8")
    (tmp_path / "docs" / "plans" / "systemic_world").mkdir(parents=True)
    (tmp_path / ticket_queue.ROADMAP).write_text(ROADMAP, encoding="utf-8")

    def digest():
        return {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}

    before = digest()
    view = ticket_queue.build_view(Runner({}), worktree_root=tmp_path, use_gh=False)
    assert [r["id"] for r in view["rows"]] == ["TCK-20261101-A"] and view["header"]["source"] == "worktree"
    assert view["header"]["order_line"]["steps"] == STEPS
    assert digest() == before
