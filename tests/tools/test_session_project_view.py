"""TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED: link by commit subject, Involved, Blocked by, Hotspot,
hash v5. Synthetic fixtures only (the live coin / STALEMATE F1 / #965 checks are done by the u24 side at the before/after dry run). No network."""
import os
import subprocess

from tests.tools.test_session_project_sync_all_lanes import copy, plan_for
from tests.tools.test_session_project_sync_second_host import A, B, TID, fact
from tools.sessions import project_client as pc
from tools.sessions import project_sync as ps

ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
       "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}
T1, T2, T3 = "TCK-20261119-ONE", "TCK-20261119-TWO", "TCK-20261119-THREE"


def log(*commits):
    """The text `git log --no-merges --format=@@%s --name-only` prints for [(subject, [files])]."""
    return "\n".join(f"@@{s}\n\n" + "\n".join(files) + "\n" for s, files in commits)


# ---- (b) cited vs worked
def test_a_leading_id_with_a_src_file_is_worked_and_named():
    named, worked = ps.subject_links(log((f"{T1}: fix the coin sink", ["src/core/x.py", "agent-working/agent-monitoring/data/a.jsonl"])))
    assert worked == {T1} and named == {T1}


def test_a_leading_id_with_only_agent_working_or_docs_files_is_cited_not_worked():  # must-not
    named, worked = ps.subject_links(log((f"{T1}: file it", ["agent-working/tickets/todos/x.md"]), (f"{T2}: notes", ["docs/guides/x.md", "docs/REGISTRY.yaml"])))
    assert worked == set() and named == {T1, T2}


def test_an_id_in_the_middle_of_a_subject_is_cited_not_worked_even_with_code():  # must-not
    named, worked = ps.subject_links(log((f"Refactor after {T1} and {T2}", ["src/core/x.py"])))
    assert worked == set() and named == {T1, T2}


def test_the_weakest_case_a_tests_config_only_commit_is_worked_and_the_same_commit_in_docs_is_not():  # TCK-20261009-RPG-REGRESSION-METRICS shape, both directions
    _, worked = ps.subject_links(log((f"{T1}: gate config", ["tests/simulation_quality/rpg_gate/config.yaml"])))
    assert worked == {T1}
    _, worked = ps.subject_links(log((f"{T1}: gate config", ["docs/testing/rpg_gate.md"])))
    assert worked == set()


def test_a_commit_already_merged_to_main_never_counts(tmp_path):  # must-not: the exact git command read_branch_facts runs
    def git(*a):
        return subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True, text=True, env=ENV).stdout
    git("init", "-q", "-b", "main")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("1")
    git("add", "-A")
    git("commit", "-q", "-m", f"{T1}: merged work")
    git("update-ref", "refs/remotes/origin/main", "HEAD")
    git("checkout", "-q", "-b", "lane")
    (tmp_path / "src" / "b.py").write_text("2")
    git("add", "-A")
    git("commit", "-q", "-m", f"{T2}: lane work")
    out = git("log", "--no-merges", "--format=@@%s", "--name-only", "HEAD", "--not", "origin/main")
    named, worked = ps.subject_links(out)
    assert worked == {T2} and named == {T2}  # T1 is reachable from origin/main


def test_a_subject_linked_copy_moves_the_ticket_in_progress_with_the_seat_but_a_cited_one_only_names_the_seat():
    worked = ps.BranchFact(B, "rpg-lane", "/wt", "rpg-implementer-3", "rpg", (copy(TID, "inprogress"),), 0.0, frozenset({TID}))
    d, _ = ps.derive_item(TID, [copy(TID, "todos")], [worked], None, None, B, "s", None)
    assert d["Status"] == "In progress" and d["Seat"] == "rpg-implementer-3" and d["Involved"] == "rpg-implementer-3"
    cited = ps.BranchFact(B, "rpg-lane", "/wt", "rpg-implementer-3", "rpg", (), 0.0, frozenset({TID}))
    d, _ = ps.derive_item(TID, [copy(TID, "todos")], [cited], None, None, B, "s", None)
    assert d["Status"] == "To do" and d["Seat"] == "" and d["Involved"] == "rpg-implementer-3"


# ---- (c) Involved
def test_involved_is_the_recorded_seats_of_branches_naming_the_ticket_and_unrecorded_lanes_leave_it_empty():
    named = lambda seat: ps.BranchFact(B, f"b-{seat}", "/wt", seat, "rpg", (), 0.0, frozenset({TID}))  # noqa: E731
    d, _ = ps.derive_item(TID, [copy(TID, "todos")], [named("rpg-implementer-2"), named("rpg-planner")], None, None, B, "s", None)
    assert d["Involved"] == "rpg-implementer-2, rpg-planner"
    d, _ = ps.derive_item(TID, [copy(TID, "todos")], [named("rpg (seat not recorded)")], None, None, B, "s", None)
    assert d["Involved"] == ""  # no recorded seat: empty until the record_seat backfill runs


def test_involved_keeps_the_other_hosts_seats_from_their_host_facts_segment():
    other = {"Host facts": f"{A}: state=filing domain=rpg involved=rpg-planner-u24", "Ticket ID": TID}
    d, _ = ps.derive_item(TID, [copy(TID, "todos")], [fact(B, folder="inprogress")], None, other, B, "s", None)
    assert d["Involved"] == "rpg-implementer, rpg-planner-u24"


# ---- (d) Blocked by
def test_waits_on_ids_reads_line_start_lines_only_not_prose():
    text = f"## Assumptions\n- waits on {T1} and {T2}\nBlocked by: {T3}\nThe work depends on {T3} in prose here.\n"
    assert ps.waits_on_ids(text) == (T1, T2, T3)
    assert ps.waits_on_ids("This ticket depends on TCK-20261119-PROSE somewhere in a sentence.\n") == ()  # must-not


def test_blocked_by_lists_waits_on_ids_that_are_not_done_and_flags_an_id_with_no_file():
    waiting = ps.TicketCopy(T1, "todos", f"{ps.TICKETS.as_posix()}/todos/{T1}.md", "w", "hotfix", False, "2026-11-19", waits_on=(T2, T3, "TCK-20261119-GONE"))
    plan = plan_for({T1: [waiting], T2: [copy(T2, "todos")], T3: [copy(T3, "done")]})
    row = next(c for c in plan.creates if c["Ticket ID"] == T1)
    assert row["Blocked by"] == T2  # T3 is Done, GONE has no file
    assert any("GONE" in f and "Blocked by" in f for f in plan.findings)


def test_a_ticket_with_no_waits_on_line_has_an_empty_blocked_by():
    assert plan_for({T1: [copy(T1, "todos")]}).creates[0]["Blocked by"] == ""


# ---- (e) Hotspot
def _areas(*files):
    return tuple(files)


def test_hotspot_is_the_src_py_file_cited_by_the_most_open_tickets_and_empty_when_cited_once():
    main = {f"TCK-20261119-C{i}": [copy(f"TCK-20261119-C{i}", "todos", areas=("src/engine/tactical.py",))] for i in range(3)}
    main[T1] = [copy(T1, "todos", areas=("src/engine/tactical.py", "src/engine/only_me.py"))]  # a file cited 4 times, another cited once
    main[T2] = [copy(T2, "todos", areas=("src/engine/only_me2.py",))]  # positive control for "cited only by itself": empty
    plan = plan_for(main)
    rows = {c["Ticket ID"]: c["Hotspot"] for c in plan.creates}
    assert rows[T1] == "src/engine/tactical.py" and rows["TCK-20261119-C0"] == "src/engine/tactical.py"
    assert rows[T2] == ""  # must-not: a file cited only by itself
    assert any(n.startswith("hotspot: ran on") and "errored 0" in n for n in plan.notes)


def test_hotspot_ignores_directories_non_src_and_done_tickets_and_breaks_ties_by_path_order():
    main = {
        T1: [copy(T1, "todos", areas=("src/core", "tools/x.py", "src/b.py", "src/a.py"))],
        T2: [copy(T2, "todos", areas=("src/core", "src/b.py", "src/a.py"))],
        T3: [copy(T3, "done", areas=("src/a.py", "src/b.py"))],  # a Done ticket is not an open citation
    }
    rows = {c["Ticket ID"]: c["Hotspot"] for c in plan_for(main).creates}
    assert rows[T1] == "src/a.py"  # a and b are both cited by 2 open tickets; the earlier path wins; the directory never counts


# ---- hash v5 and --init
def test_hash_v5_adds_the_three_fields_and_keeps_v4_intact():
    assert ps.CURRENT_HASH_VERSION == "v5" and ps.HASH_VERSIONS["v5"][-3:] == ("Involved", "Blocked by", "Hotspot")
    assert ps.HASH_VERSIONS["v4"][-1] == "Filed" and "Involved" not in ps.HASH_VERSIONS["v4"]
    d = plan_for({T1: [copy(T1, "todos")]}).creates[0]
    assert d["Sync hash"].startswith("v5:") and d["Sync hash"] == ps.sync_hash(d)


def test_init_and_apply_know_the_three_text_fields():
    for name in ("Involved", "Blocked by", "Hotspot"):
        assert name in pc.TEXT_FIELDS and name in pc.VALUE_ORDER


# ---- (b) a squash-merged branch kept as a worktree must not read as live work
def _gh(stdout="", code=0):
    return lambda args, cwd=None: subprocess.CompletedProcess(args, code, stdout, "")


def test_branch_pr_merged_reads_the_merged_pr_list_and_fails_safe(tmp_path):
    assert ps.branch_pr_merged("lane", tmp_path, _gh('[{"number": 7}]')) is True
    assert ps.branch_pr_merged("lane", tmp_path, _gh("[]")) is False  # positive control: a branch with no merged PR still links
    assert ps.branch_pr_merged("lane", tmp_path, _gh("", 1)) is None  # a failed lookup is None, never "not merged"
    assert ps.branch_pr_merged("lane", tmp_path, _gh("not json")) is None


def test_the_merged_pr_lookup_is_a_read_the_guard_allows_and_asks_only_for_merged_prs(tmp_path):
    seen = []

    def run(args, cwd=None):
        ps._guard(args)  # the real read-only guard: `gh pr list` passes, a write would raise
        seen.append(args)
        return subprocess.CompletedProcess(args, 0, "[]", "")

    ps.branch_pr_merged("rpg-lane", tmp_path, run)
    assert seen[0][:6] == ["gh", "pr", "list", "--state", "merged", "--head"] and seen[0][6] == "rpg-lane"


# ---- --state-root for project_sync: read only, printed, never a silent fallback
def test_project_sync_state_root_flag_reads_the_given_directory_and_prints_it(tmp_path, monkeypatch):
    from pathlib import Path as P
    seen = []
    monkeypatch.setattr(ps, "worktree_entries", lambda root: [])  # no dependence on how the checkout running this test is laid out
    monkeypatch.setattr(ps, "_worktree_for", lambda role, infos, main, state_root: seen.append(state_root))
    notes: list[str] = []
    ps.read_branch_facts(P(__file__).resolve().parents[2], "ubuntu", notes, state_root_override=tmp_path)
    assert f"seat state root: {tmp_path} (--state-root)" in notes
    assert seen and all(s == tmp_path for s in seen)  # every seat lookup used the given root, never the repo's own
    assert list(tmp_path.iterdir()) == []  # read only: nothing was written under it


def test_project_sync_without_the_flag_uses_the_repos_own_state_root(monkeypatch):
    from pathlib import Path as P
    seen = []
    monkeypatch.setattr(ps, "worktree_entries", lambda root: [])
    monkeypatch.setattr(ps, "_worktree_for", lambda role, infos, main, state_root: seen.append(state_root))
    notes: list[str] = []
    ps.read_branch_facts(P(__file__).resolve().parents[2], "ubuntu", notes)
    assert any(n.startswith("seat state root: ") and "(--state-root)" not in n for n in notes) and seen


def test_project_sync_state_root_flag_that_is_not_a_directory_is_a_usage_error(tmp_path, capsys):
    assert ps.main(["--root", ".", "--items", str(tmp_path / "x.json"), "--state-root", str(tmp_path / "missing")]) == 2
    assert "no fallback" in capsys.readouterr().err


# ---- the hourly timer runs --apply, not --init: what happens when the three new fields do not exist yet
def _project_without_the_new_fields():
    from tests.tools.test_session_project_sync_all_lanes import _project
    from tests.tools.test_session_project_sync_all_lanes import WANTED
    p = _project()
    p.fields["Domain"] = pc.ProjectField("F_Domain", "Domain", "SINGLE_SELECT", tuple((n, f"O_{n}") for n in WANTED))  # the live Project's Domain is already a select
    p.fields["Layer"] = pc.ProjectField("F_Layer", "Layer", "SINGLE_SELECT", (("combat", "O_combat"),))
    for name in ("Involved", "Blocked by", "Hotspot"):
        del p.fields[name]
    return p


class _Client:
    def __init__(self):
        self.calls = []

    def __getattr__(self, name):
        return lambda *a, **k: self.calls.append((name, a)) or ("I", "D")


def test_apply_before_init_refuses_before_the_first_write_naming_the_fields():
    import pytest

    plan = plan_for({T1: [copy(T1, "todos")]})
    client = _Client()
    with pytest.raises(pc.ClientRefused) as err:
        pc.apply_plan(client, _project_without_the_new_fields(), plan)
    assert "Involved, Blocked by, Hotspot" in str(err.value) and "run --init first" in str(err.value)
    assert client.calls == []  # nothing written, so a timer tick that hits this leaves the board exactly as it was


def test_init_then_creates_exactly_the_three_fields_leaves_status_alone_and_a_second_init_changes_nothing():
    from tests.tools.test_session_project_sync_all_lanes import WANTED, FakeInit
    fake = FakeInit(_project_without_the_new_fields())
    lines, code = pc.init_fields(fake, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert code == 0
    created = [c for c in fake.calls if c[0] == "create_text"]
    assert sorted(c[1] for c in created) == ["Blocked by", "Hotspot", "Involved"]
    assert not any(c[0] in ("options", "rename", "create_select", "create_date") for c in fake.calls)  # no Status, Domain, select or date change
    again = FakeInit(_project_without_the_new_fields())
    for name in ("Involved", "Blocked by", "Hotspot"):
        again.proj.fields[name] = pc.ProjectField(f"F_{name}", name, "TEXT")
    lines, code = pc.init_fields(again, ps.STATUSES, layers=("combat",), domains=WANTED)
    assert code == 0 and again.calls == []  # a second --init reports nothing created or updated


def test_a_host_that_only_cites_a_ticket_reads_origins_copy_and_never_blanks_the_content():
    # the bug the four Done rows showed in the u24 dry run: a cited-only segment made this host the ONE holder with no copy of its own
    cited = ps.BranchFact(B, "rpg-lane", "/wt", "rpg-planner", "rpg", (), 0.0, frozenset({TID}))
    origin = ps.TicketCopy(TID, "done", f"{ps.TICKETS.as_posix()}/done/{TID}.md", "Origin title", "standard", False, "2026-11-15", layer="ai", priority="P2")
    current = {"Ticket ID": TID, "Title": f"{TID}: Origin title", "Tier": "standard", "Layer": "ai", "Priority": "P2", "Filed": "2026-11-15"}
    d, _ = ps.derive_item(TID, [origin], [cited], None, current, B, "s", None)
    assert d["Title"] == f"{TID}: Origin title" and d["Tier"] == "standard" and d["Layer"] == "ai" and d["Priority"] == "P2" and d["Filed"] == "2026-11-15"
    assert d["Status"] == "Done" and d["Involved"] == "rpg-planner"  # Status untouched; the only new fact is Involved
    assert "domain=" not in d["Host facts"]  # a citing branch does not decide the ticket's Domain


# ---- a ticket filed only on an unpushed branch and worked on a lane branch (the coin-fix shape)
COIN = "TCK-20261118-COIN-SHAPE"


def _filing_copy():
    return ps.TicketCopy(COIN, "todos", f"{ps.TICKETS.as_posix()}/todos/{COIN}.md", "Coin shape", "standard", False, "2026-11-18")


def test_link_worked_reads_the_hosts_filing_copy_when_origin_has_no_file_and_names_what_has_none():
    copies, counts = ps.link_worked({COIN, "TCK-20261118-NOWHERE"}, {}, {COIN: _filing_copy()}, lambda p: None)
    assert [c.id for c in copies] == [COIN] and copies[0].folder == "inprogress"
    assert counts["linked"] == 1 and counts["via_filing"] == 1 and counts["skipped"] == 1 and counts["no_file"] == {"TCK-20261118-NOWHERE"}  # must-not: no file anywhere stays skipped and named


def test_link_worked_a_done_ticket_stays_skipped_and_a_ticket_with_a_main_file_still_reads_main():
    done = {"TCK-D": [("done", "p/d.md")], "TCK-M": [("todos", "p/m.md")]}
    loaded = {"p/m.md": ps.TicketCopy("TCK-M", "todos", "p/m.md", "Main copy", "hotfix", False, "2026-11-18")}
    copies, counts = ps.link_worked({"TCK-D", "TCK-M"}, done, {"TCK-D": _filing_copy()}, lambda p: loaded[p])
    assert [c.id for c in copies] == ["TCK-M"] and counts["skipped"] == 1 and counts["via_filing"] == 0


def test_the_coin_shape_reads_in_progress_with_the_lane_seat_and_without_the_fix_it_reads_to_do():
    lane_copy = ps.link_worked({COIN}, {}, {COIN: _filing_copy()}, lambda p: None)[0]
    lane = ps.BranchFact(B, "rpg-coin-sink", "/wt", "rpg-implementer", "rpg", tuple(lane_copy), 0.0, frozenset({COIN}))
    filing = ps.BranchFact(B, "rpg-planner-tickets", "/wt2", "rpg-planner", "rpg", (_filing_copy(),), 0.0, frozenset({COIN}))
    after, _ = ps.derive_item(COIN, [], [filing, lane], None, None, B, "s", None)
    assert after["Status"] == "In progress" and "rpg-implementer" in after["Seat"] and after["Involved"] == "rpg-implementer, rpg-planner"
    unlinked = ps.BranchFact(B, "rpg-coin-sink", "/wt", "rpg-implementer", "rpg", (), 0.0, frozenset({COIN}))  # positive control: the old behaviour
    before, _ = ps.derive_item(COIN, [], [filing, unlinked], None, None, B, "s", None)
    assert before["Status"] == "To do"


def test_two_hosts_over_the_same_data_do_not_disagree_and_the_host_without_the_filing_copy_writes_nothing_for_it():
    lane_copy = ps.link_worked({COIN}, {}, {COIN: _filing_copy()}, lambda p: None)[0]
    host_a = ps.BranchFact(A, "rpg-coin-sink", "/wt", "rpg-implementer", "rpg", tuple(lane_copy), 0.0, frozenset({COIN}))
    a_row, _ = ps.derive_item(COIN, [], [host_a], None, None, A, "s", None)
    # host B has no filing copy: its subject link skipped the ticket, so it has no fact; it reads A's segment from the item and agrees
    b_row, _ = ps.derive_item(COIN, [], [], None, {**a_row, "Ticket ID": COIN}, B, "s", None)
    assert a_row["Status"] == b_row["Status"] == "In progress"
    assert b_row["Host facts"] == a_row["Host facts"] and B not in b_row["Host facts"]  # B wrote none of its own facts


# ---- one --apply per host at a time (a hand-run first apply and the hourly tick must not write the same items together)
def test_apply_lock_refuses_a_second_holder_and_frees_after_release(tmp_path):
    first = ps.acquire_apply_lock(tmp_path / "apply.lock")
    assert first is not None
    assert ps.acquire_apply_lock(tmp_path / "apply.lock") is None  # a second apply on the same host would skip
    first.close()
    again = ps.acquire_apply_lock(tmp_path / "apply.lock")
    assert again is not None  # positive control: it frees when the holder ends
    again.close()


def test_apply_exits_zero_without_writing_when_the_lock_is_held(tmp_path, monkeypatch, capsys):
    held = ps.acquire_apply_lock(tmp_path / "apply.lock")
    monkeypatch.setattr(ps, "APPLY_LOCK_PATH", tmp_path / "apply.lock")
    called = []
    monkeypatch.setattr(ps, "load_config", lambda *a, **k: called.append("config") or {})
    assert ps.main(["--root", ".", "--apply"]) == 0 and called == []  # returned before reading the config or touching the Project
    assert "another --apply is running" in capsys.readouterr().err
    held.close()
