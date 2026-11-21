"""TCK-20261120-SUBJECT-LINK-DOES-NOT-LIFT-A-TICKET-THE-BRANCH-ALSO-EDITS-IN-TODOS: a branch that edits a ticket's todos/ file (filing) AND works it by
commit subject (a leading id plus a code file) reads In progress with its seat. The births shape is built end to end in a throwaway git repo; nothing reads
the real RPG worktrees. No network (the merged-PR lookup is stubbed)."""
import os
import shutil
import subprocess
from pathlib import Path

from tests.tools.test_session_project_sync_all_lanes import copy
from tools.agent_working_paths import TICKETS
from tools.sessions import project_sync as ps

REPO = Path(__file__).resolve().parents[2]
ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t", "PATH": os.environ["PATH"], "HOME": os.environ.get("HOME", "/")}
A, B = "TCK-20261120-TICKET-A", "TCK-20261120-TICKET-B"
HOST = "ubuntu"


def _git(cwd, *a):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True, env=ENV).stdout


def _ticket_text(tid, extra=""):
    return f"---\nstatus: active\nlayer: ai\nticket_id: {tid}\nphase: open\ndate: 2026-11-20\ntags: []\n---\n\n# {tid}\n\n## Title\nT {tid}\n\n## Status\nOPEN\n\n## Tier\nhotfix\n{extra}"


def _repo(tmp_path):
    """A repo whose origin/main holds the registries and two todos tickets; HEAD stays on main until a test checks out a lane."""
    r = tmp_path / "repo"
    (r / TICKETS / "todos").mkdir(parents=True)
    shutil.copytree(REPO / "registries", r / "registries")
    (r / "src").mkdir()
    for tid in (A, B):
        (r / TICKETS / "todos" / f"{tid}.md").write_text(_ticket_text(tid))
    _git(r, "init", "-q", "-b", "main")
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    _git(r, "update-ref", "refs/remotes/origin/main", "HEAD")
    return r


def _commit(r, subject, files):
    for rel, text in files.items():
        p = r / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", subject)


def _run(args, cwd=None):
    if args[:2] == ["gh", "pr"]:
        return subprocess.CompletedProcess(args, 0, "[]", "")  # no merged PR
    return ps.run_command(args, cwd)


def _facts(r, tmp_path):
    state = tmp_path / "state"
    state.mkdir(exist_ok=True)
    notes: list[str] = []
    facts, _ = ps.read_branch_facts(r, HOST, notes, _run, state_root_override=state)
    return facts, notes


def _status(facts, tid):
    mine = [f for f in facts if any(c.id == tid for c in f.copies)]
    main = [copy(tid, "todos")]
    row, _ = ps.derive_item(tid, main, mine, None, None, HOST, "s", None)
    return row["Status"], row


def _edit_todos(r, tid):
    return {f"{TICKETS.as_posix()}/todos/{tid}.md": _ticket_text(tid, "\nmore notes\n")}


# ---- the births shape, end to end
def test_a_branch_editing_the_todos_file_and_working_the_ticket_by_subject_reads_in_progress_before_and_after_the_edit(tmp_path):
    r = _repo(tmp_path)
    _git(r, "checkout", "-q", "-b", "rpg-lane")
    _commit(r, f"{A}: the first code commit", {"src/a.py": "1"})
    facts, notes = _facts(r, tmp_path)
    assert _status(facts, A)[0] == "In progress"  # BEFORE the todos edit: the regression guard (this is what the births row read first)
    _commit(r, f"{A}: investigation notes", _edit_todos(r, A))  # the branch now ALSO carries a todos/ copy of the ticket
    facts, notes = _facts(r, tmp_path)
    status, row = _status(facts, A)
    assert status == "In progress" and "[filing]" not in row["Branch"]  # AFTER: it used to fall back to To do with the Branch flagged [filing]
    assert any("1 lifted from a todos copy" in n for n in notes if n.startswith("subject-link"))


def test_without_a_worked_commit_the_todos_edit_alone_stays_filing_and_to_do(tmp_path):  # must-not: positive control for the case above
    r = _repo(tmp_path)
    _git(r, "checkout", "-q", "-b", "rpg-lane")
    _commit(r, f"{A}: investigation notes", _edit_todos(r, A))
    facts, _ = _facts(r, tmp_path)
    status, row = _status(facts, A)
    assert status == "To do" and "[filing]" in row["Branch"]


def test_a_docs_only_or_mid_subject_citation_does_not_lift_a_todos_copy(tmp_path):
    r = _repo(tmp_path)
    _git(r, "checkout", "-q", "-b", "rpg-lane")
    _commit(r, f"{A}: notes", {**_edit_todos(r, A), "docs/x.md": "d"})  # a docs-only commit
    _commit(r, f"Refactor after {A}", {"src/a.py": "1"})  # a mid-subject citation with code
    facts, _ = _facts(r, tmp_path)
    assert _status(facts, A)[0] == "To do"


def test_a_todos_copy_of_one_ticket_never_excludes_a_worked_commit_for_another(tmp_path):
    r = _repo(tmp_path)
    _git(r, "checkout", "-q", "-b", "rpg-lane")
    _commit(r, f"{A}: notes only", _edit_todos(r, A))  # A: filing copy, no worked commit
    _commit(r, f"{B}: the code", {"src/b.py": "1"})  # B: worked, no copy on the branch (linked from origin/main)
    facts, _ = _facts(r, tmp_path)
    assert _status(facts, B)[0] == "In progress" and _status(facts, A)[0] == "To do"


def test_a_copy_already_in_inprogress_keeps_todays_behaviour_with_no_double_link(tmp_path):
    r = _repo(tmp_path)
    _git(r, "checkout", "-q", "-b", "rpg-lane")
    old = r / TICKETS / "todos" / f"{A}.md"
    (r / TICKETS / "inprogress").mkdir(parents=True)
    _git(r, "mv", str(old), str(r / TICKETS / "inprogress" / f"{A}.md"))
    _commit(r, f"{A}: the code", {"src/a.py": "1"})
    facts, notes = _facts(r, tmp_path)
    assert _status(facts, A)[0] == "In progress"
    f = next(x for x in facts if x.branch == "rpg-lane")
    assert [c.folder for c in f.copies if c.id == A] == ["inprogress"]  # one copy, not two
    assert any("0 lifted" in n and "linked 0 tickets" in n for n in notes if n.startswith("subject-link"))


def test_a_ticket_done_on_origin_main_stays_done_and_a_merged_pr_branch_is_not_counted(tmp_path):
    r = _repo(tmp_path)
    _git(r, "checkout", "-q", "-b", "rpg-lane")
    _commit(r, f"{A}: the code", {"src/a.py": "1", **_edit_todos(r, A)})

    def merged(args, cwd=None):
        return subprocess.CompletedProcess(args, 0, '[{"number": 9}]', "") if args[:2] == ["gh", "pr"] else ps.run_command(args, cwd)
    state = tmp_path / "state"
    state.mkdir()
    facts, _ = ps.read_branch_facts(r, HOST, [], merged, state_root_override=state)
    assert _status(facts, A)[0] == "To do"  # the branch's PR is merged: its subject links are skipped, so the todos copy stays filing
    row, _ = ps.derive_item(A, [copy(A, "done")], [x for x in facts if x.branch == "rpg-lane"], None, None, HOST, "s", None)
    assert row["Status"] == "Done"
