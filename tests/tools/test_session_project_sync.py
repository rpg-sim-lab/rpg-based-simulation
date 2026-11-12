"""TCK-20261112-PROJECT-SYNC-DRY-RUN: the ticket-state Project plan is derived by pure functions from fixtures. No network, no real
repository: git and gh answers are canned."""
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from tools.agent_working_paths import TICKETS
from tools.sessions import project_sync as ps

T = TICKETS.as_posix()
NOW = datetime(2026, 11, 20, 12, 0, tzinfo=timezone.utc)
CFG = {"pilot_lanes": ["rpg"], "pilot_start": "2026-11-12", "done_window_days": 14, "stale_host_hours": 24}
HOST = "u24desktop"


def copy(tid="TCK-20261112-X", folder="inprogress", title="A title", tier="hotfix", blocked=False, date="2026-11-12"):
    return ps.TicketCopy(tid, folder, f"{T}/{folder}/{tid}.md", title, tier, blocked, date)


def branch(copies, name="rpg-batch", host=HOST, seat="rpg-implementer", domain="rpg"):
    return ps.BranchFact(host, name, f"/wt/{name}", seat, domain, tuple(copies))


def pr(copies, number=7):
    return ps.PrFact(number, f"https://github.com/o/r/pull/{number}", frozenset(c.path for c in copies))


def derive(tid="TCK-20261112-X", main=(), branches=(), prs=(), current=None, host=HOST):
    return ps.derive_item(tid, list(main), list(branches), None if prs is None else list(prs), current, host, "abc123 @ now")


def test_rule1_a_ticket_in_done_on_main_is_done():
    item, _ = derive(main=[copy(folder="done")], branches=[branch([copy()])], prs=[pr([copy()])])
    assert item["Status"] == "Done"


def test_rule2_an_open_pr_that_adds_the_ticket_is_in_review_with_its_url():
    c = copy()
    item, _ = derive(branches=[branch([c])], prs=[pr([c], 12)])
    assert item["Status"] == "In review" and item["PR"] == "https://github.com/o/r/pull/12"


def test_rule3_blocked_in_a_copy_that_exists_only_on_a_branch():
    item, _ = derive(branches=[branch([copy(blocked=True, title="Branch only")])])
    assert item["Status"] == "Blocked" and item["Title"] == "TCK-20261112-X: Branch only" and item["Tier"] == "hotfix"


def test_rule3_blocked_on_main_with_no_branch_copy():
    item, _ = derive(main=[copy(folder="todos", blocked=True)])
    assert item["Status"] == "Blocked"


def test_rule4_a_branch_copy_in_inprogress_is_in_progress_with_seat_and_branch():
    item, _ = derive(branches=[branch([copy()])])
    assert item["Status"] == "In progress" and item["Seat"] == "rpg-implementer" and item["Branch"] == f"{HOST}:rpg-batch"
    assert item["Host"] == HOST and item["Domain"] == "rpg"


def test_rule5_todos_only_is_to_do_and_an_orphaned_inprogress_ticket_is_a_finding():
    item, findings = derive(main=[copy(folder="todos")])
    assert item["Status"] == "To do" and findings == []
    item, findings = derive(main=[copy(folder="inprogress")])
    assert item["Status"] == "To do" and any("orphaned in-progress" in f for f in findings)


def test_a_ticket_in_two_folders_on_main_is_reported_and_takes_the_higher_status():
    item, findings = derive(main=[copy(folder="todos"), copy(folder="done")])
    assert item["Status"] == "Done" and any("two folders" in f for f in findings)


def test_a_squash_merged_branch_never_shows_in_progress():
    item, _ = derive(main=[copy(folder="done")], branches=[branch([copy()])])
    assert item["Status"] == "Done"


def test_filing_a_ticket_in_todos_on_a_branch_is_to_do_not_in_progress():
    item, _ = derive(branches=[branch([copy(folder="todos")])])
    assert item["Status"] == "To do" and item["Branch"] == f"{HOST}:rpg-batch {ps.FILING_SUFFIX}"


def test_an_open_pr_that_adds_a_todos_ticket_is_to_do_not_in_review():
    c = copy(folder="todos")
    item, _ = derive(branches=[branch([c])], prs=[pr([c])])
    assert item["Status"] == "To do" and item["PR"] == ""


def test_unmapped_seat_comes_from_the_branch_prefix_else_unknown():
    assert ps.attribute("rpg-hit-wake", []) == ("rpg (unmapped)", "rpg")
    assert ps.attribute("freemeal", []) == ("unknown", "")
    assert ps.attribute("x-y", [("rpg-implementer", "rpg"), ("rpg-planner", "rpg")]) == ("rpg-implementer/rpg-planner", "rpg")


def test_sync_hash_is_stable_ignores_source_and_a_hand_edit_is_reported_then_overwritten():
    item, _ = derive(branches=[branch([copy()])])
    assert item["Sync hash"] == ps.sync_hash({**item, "Source": "other run"})
    assert ps.hand_edits(item, item) == []
    edited = {**item, "Status": "Done"}  # someone moved it by hand; the stored hash no longer matches
    lines = ps.hand_edits(edited, item)
    assert lines == [f"hand edit: TCK-20261112-X Status 'Done' -> 'In progress'"]
    plan = _plan({"TCK-20261112-X": [copy()]}, [branch([copy()])], [edited])
    assert plan.hand_edits == lines and plan.updates and plan.updates[0][1] == ["Status"]
    assert plan.updates[0][0]["Status"] == "In progress"


def _plan(main, branches, items=(), prs=(), done_at=lambda p: None):
    index = {tid: [(c.folder, c.path) for c in cs] for tid, cs in main.items()}
    loaded = {c.path: c for cs in main.values() for c in cs}
    return ps.build_plan(index, lambda p: loaded[p], list(branches), None if prs is None else list(prs), list(items), HOST,
                         "abc @ now", CFG, done_at, NOW)


def test_items_without_an_id_or_without_a_ticket_file_are_archived_and_old_done_items_age_out():
    stray = {"Title": "hand made", "Ticket ID": ""}
    ghost = {"Title": "x", "Ticket ID": "TCK-20260101-GONE"}
    done_item, _ = derive("TCK-20261101-OLD", main=[copy("TCK-20261101-OLD", "done")])
    plan = _plan({"TCK-20261101-OLD": [copy("TCK-20261101-OLD", "done")]}, [], [stray, ghost, done_item],
                 done_at=lambda p: datetime(2026, 11, 1, tzinfo=timezone.utc))
    reasons = dict(plan.archives)
    assert "no Ticket ID" in reasons["hand made"] and "no ticket file" in reasons["TCK-20260101-GONE"]
    assert "Done more than 14 days ago" in reasons["TCK-20261101-OLD"]


def test_a_done_ticket_from_before_the_pilot_gets_no_item_but_one_after_it_does():
    old, new = copy("TCK-OLD-1", "done"), copy("TCK-NEW-1", "done")
    branches = [branch([copy("TCK-OLD-1"), copy("TCK-NEW-1")])]
    dates = {old.path: datetime(2026, 11, 5, tzinfo=timezone.utc), new.path: datetime(2026, 11, 15, tzinfo=timezone.utc)}
    plan = _plan({"TCK-OLD-1": [old], "TCK-NEW-1": [new]}, branches, done_at=dates.get)
    assert [i["Ticket ID"] for i in plan.creates] == ["TCK-NEW-1"]


def test_only_pilot_lane_branches_make_candidates():
    plan = _plan({"TCK-A-1": [copy("TCK-A-1", "todos")]}, [branch([copy("TCK-A-1")], name="eng-x", seat="eng", domain="eng")])
    assert plan.creates == []


def test_a_ticket_in_progress_on_ubuntu_and_in_review_through_a_pr_from_u24_is_in_review_keeping_both_hosts():
    c = copy()
    current, _ = derive(branches=[branch([c], name="rpg-ub", host="ubuntu", seat="rpg-implementer-ubuntu")], host="ubuntu")
    item, _ = derive(main=[], branches=[branch([c])], prs=[pr([c])], current=current)
    assert item["Status"] == "In review"
    assert item["Branch"] == f"{HOST}:rpg-batch, ubuntu:rpg-ub" and item["Host"] == f"{HOST}, ubuntu"
    # the same item with no PR keeps ubuntu's branch as rule-4 evidence even when this host has no branch
    item2, _ = derive(branches=[], prs=[], current=current)
    assert item2["Status"] == "In progress" and item2["Branch"] == "ubuntu:rpg-ub" and item2["Host"] == "ubuntu"


def test_a_filing_entry_from_another_host_is_not_progress_evidence():
    current = {"Branch": f"ubuntu:rpg-x {ps.FILING_SUFFIX}", "Host": "ubuntu"}
    item, _ = derive(main=[copy(folder="todos")], current=current)
    assert item["Status"] == "To do"


def test_apply_and_init_are_refused_and_nothing_runs(monkeypatch, capsys):
    monkeypatch.setattr(ps, "read_branch_facts", lambda *a, **k: pytest.fail("a reader ran"))
    for flag in ("--apply", "--init"):
        assert ps.main([flag]) == 2
    assert "P1" in capsys.readouterr().err


@pytest.mark.parametrize("cmd", [
    ["git", "push", "origin", "x"], ["git", "worktree", "remove", "/wt"], ["git", "fetch"], ["git", "checkout", "main"],
    ["gh", "pr", "create"], ["gh", "pr", "merge", "1"], ["gh", "api", "-X", "POST", "repos/o/r/issues"], ["gh", "api", "x", "-f", "a=b"],
    ["rm", "-rf", "/"],
])
def test_the_guard_refuses_every_write_verb(cmd):
    with pytest.raises(ps.WriteRefused):
        ps._guard(cmd)


@pytest.mark.parametrize("cmd", [
    ["git", "--no-optional-locks", "status", "--porcelain"], ["git", "ls-tree", "-r", "origin/main"], ["git", "worktree", "list"],
    ["gh", "pr", "list", "--state", "open"], ["gh", "api", "--paginate", "repos/{owner}/{repo}/pulls/1/files"],
])
def test_the_guard_lets_read_verbs_through(cmd):
    ps._guard(cmd)


def fake_runner(answers):
    calls = []

    def run(args, cwd=None):
        calls.append(args)
        key = next((k for k in answers if k in " ".join(args)), None)
        out = answers[key] if key else ""
        return SimpleNamespace(returncode=0, stdout=out, stderr="")

    run.calls = calls
    return run


def test_an_uncommitted_ticket_file_in_a_worktree_is_read_from_disk_and_a_committed_one_with_git_show(tmp_path):
    new = f"{T}/inprogress/TCK-20261112-NEW.md"
    committed = f"{T}/inprogress/TCK-20261112-OLD.md"
    (tmp_path / T / "inprogress").mkdir(parents=True)
    (tmp_path / new).write_text("---\ndate: 2026-11-12\n---\n# T\n\n## Title\nNew one\n\n## Tier\nStandard\n\n## Status\nBLOCKED\n")
    run = fake_runner({
        "merge-base": "base123\n",
        "diff --name-status": f"D\t{T}/done/TCK-20260101-GONE.md\nA\tdocs/not_a_ticket.md\n",
        "status --porcelain": f" M {committed}\0?? {new}\0 D {T}/todos/TCK-20260102-DELETED.md\0",
        "show HEAD:": "## Title\nCommitted one\n\n## Tier\nhotfix\n",
    })
    copies = {c.id: c for c in ps._worktree_ticket_copies(tmp_path, run)}
    assert set(copies) == {"TCK-20261112-NEW", "TCK-20261112-OLD"}
    assert copies["TCK-20261112-NEW"].title == "New one" and copies["TCK-20261112-NEW"].blocked and copies["TCK-20261112-NEW"].tier == "standard"
    assert copies["TCK-20261112-OLD"].title == "Committed one" and copies["TCK-20261112-OLD"].folder == "inprogress"
    assert any("--no-optional-locks" in c for c in run.calls)


def test_detached_worktrees_are_skipped_counted_and_reported_when_they_change_a_ticket(tmp_path, monkeypatch):
    entries = [{"worktree": str(tmp_path / "a")}, {"worktree": str(tmp_path / "b"), "branch": "refs/heads/rpg-hit-wake"}]
    infos = {str(tmp_path / "a"): SimpleNamespace(path=tmp_path / "a", branch=None, prunable=False, is_main=False),
             str(tmp_path / "b"): SimpleNamespace(path=tmp_path / "b", branch="rpg-hit-wake", prunable=False, is_main=False)}
    monkeypatch.setattr(ps, "load_roster", lambda root: SimpleNamespace(roles=[]))
    monkeypatch.setattr(ps, "main_checkout", lambda root: tmp_path / "main")
    monkeypatch.setattr(ps.st, "state_root", lambda root: tmp_path / "state")
    monkeypatch.setattr(ps, "worktree_entries", lambda root: entries)
    monkeypatch.setattr(ps, "inspect_worktree", lambda e, main, prr, szr: infos[e["worktree"]])
    monkeypatch.setattr(ps, "_worktree_ticket_copies", lambda wt, run: [copy()])
    notes: list[str] = []
    facts, detached = ps.read_branch_facts(tmp_path, HOST, notes)
    assert detached == 1 and [f.branch for f in facts] == ["rpg-hit-wake"] and facts[0].seat == "rpg (unmapped)"
    assert any(n.startswith("unattributed: detached worktree") and "TCK-20261112-X" in n for n in notes)


def test_a_pr_list_that_hits_the_limit_says_some_prs_may_be_missing():
    listing = json.dumps([{"number": i, "url": f"u{i}"} for i in range(ps.PR_LIMIT)])
    notes: list[str] = []
    prs = ps.read_open_prs(Path("."), notes, fake_runner({"pr list": listing, "pulls": f"{T}/inprogress/TCK-A-1.md\nsrc/x.py\n"}))
    assert len(prs) == ps.PR_LIMIT and prs[0].paths == frozenset({f"{T}/inprogress/TCK-A-1.md"})
    assert any("some PRs may be missing" in n for n in notes)


def test_a_failing_gh_skips_rule_2_with_a_note():
    notes: list[str] = []
    run = lambda args, cwd=None: SimpleNamespace(returncode=1, stdout="", stderr="no")  # noqa: E731
    assert ps.read_open_prs(Path("."), notes, run) is None and any("rule 2" in n for n in notes)


def test_the_registry_file_has_the_pilot_settings_and_no_field_ids():
    cfg = yaml.safe_load((Path(__file__).resolve().parents[2] / ps.CONFIG_REL).read_text(encoding="utf-8"))
    assert cfg["pilot_lanes"] == ["rpg"] and cfg["done_window_days"] == 14 and cfg["stale_host_hours"] == 24
    assert "PVTF" not in json.dumps(cfg, default=str) and "field" not in json.dumps(list(cfg)).lower()


def test_an_unstaged_only_change_with_a_leading_space_is_the_first_porcelain_entry_and_is_kept(tmp_path):
    ticket = f"{T}/done/TCK-20261110-A-NON-FLIGHT-MOVE.md"
    (tmp_path / T / "done").mkdir(parents=True)
    (tmp_path / ticket).write_text("## Title\nNon flight\n")
    run = fake_runner({"merge-base": "b\n", "diff --name-status": "", "status --porcelain": f" M {ticket}\0"})
    assert [c.id for c in ps._worktree_ticket_copies(tmp_path, run)] == ["TCK-20261110-A-NON-FLIGHT-MOVE"]


def test_a_renamed_porcelain_entry_skips_its_source_and_a_real_repo_agrees(tmp_path):
    import subprocess

    def git(*a):
        subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t", *a], cwd=tmp_path, check=True, capture_output=True)

    (tmp_path / T / "todos").mkdir(parents=True)
    (tmp_path / T / "done").mkdir(parents=True)
    old = tmp_path / T / "todos" / "TCK-20261111-MOVED.md"
    old.write_text("## Title\nMoved\n")
    done = tmp_path / T / "done" / "TCK-20261110-DONE-ONE.md"
    done.write_text("## Title\nDone one\n")
    git("init", "-q", "-b", "main")
    git("add", "-A")
    git("commit", "-q", "-m", "i")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    done.write_text("## Title\nDone one changed\n")  # unstaged only: ` M` is the first porcelain entry
    git("mv", str(old), str(tmp_path / T / "done" / "TCK-20261111-MOVED.md"))
    copies = {c.id: c.folder for c in ps._worktree_ticket_copies(tmp_path, ps.run_command)}
    assert copies == {"TCK-20261110-DONE-ONE": "done", "TCK-20261111-MOVED": "done"}


def test_seat_names_only_a_branch_that_works_the_ticket_never_one_that_only_filed_it():
    worker = branch([copy()], name="rpg-work", seat="rpg (unmapped)")
    filer = branch([copy(folder="todos")], name="rpg-planner-seat", seat="rpg-planner")
    item, _ = derive(branches=[worker, filer])
    assert item["Seat"] == "rpg (unmapped)" and item["Status"] == "In progress"
    assert f"{HOST}:rpg-planner-seat {ps.FILING_SUFFIX}" in item["Branch"] and f"{HOST}:rpg-work" in item["Branch"]
    todo, _ = derive(branches=[filer])
    assert todo["Status"] == "To do" and todo["Seat"] == ""
