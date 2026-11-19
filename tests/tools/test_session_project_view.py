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
