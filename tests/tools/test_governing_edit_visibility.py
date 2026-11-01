"""TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER: the reported governing-path list and the guard's attempt rows.

Report-only. The list is a SECOND list beside `GOVERNING_FILE_EDIT` (whose classify tests stay as they are). The guard
still allows a governing edit with no output and writes one row (seat, repo-relative path, basis, time); a failed write
changes nothing. Rows go to the `governing_sink` fixture, never to a live shard.
"""
import io
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tools.agent_working_paths import AGENT_MONITORING
from tools.sessions import boundary as bd
from tools.sessions import classify as cl
from tools.sessions import guard

FAMILY = "governing_edits.jsonl"


def _rows(sink: Path) -> list[dict]:
    return [json.loads(line) for f in sorted(sink.glob(f"*/{FAMILY}")) for line in f.read_text().splitlines()]


def _repo(tmp_path: Path) -> Path:
    """A real (empty) repo: an authority-class call resolves the git common dir, and a fake `.git` makes the guard fail closed."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "feature-x", str(repo)], check=True)
    return repo


def _run(payload):
    out, err = io.StringIO(), io.StringIO()
    code = guard.main(io.StringIO(json.dumps(payload)), out, err)
    return code, out.getvalue(), err.getvalue()


# ---- the list ---------------------------------------------------------------------------------

@pytest.mark.parametrize("rel", [
    "CLAUDE.md", ".claude/settings.json", ".claude/settings.local.json", "tools/sessions/guard.py", "tools/sessions/classify.py",
    "registries/session_authority.yaml", ".github/workflows/test.yml", ".claude/hooks/a.py", "tools/hooks/a.py", "codebase/hooks/a.py",
])
def test_reported_governing_paths(rel):
    assert cl.is_governing_path(rel)


@pytest.mark.parametrize("rel", [
    "frontend/src/hooks/useThing.ts", "tools/sessions/guard_x.py", "tools/sessions/roster.py", "docs/guides/x.md",
    ".github/CODEOWNERS", "src/a/hooks/b.py",
])
def test_not_governing_paths(rel):
    assert not cl.is_governing_path(rel)


def test_the_action_list_is_a_subset_of_the_reported_list_and_the_old_marker_is_not_reused():
    assert set(cl.GOVERNING_FILES) <= set(cl.GOVERNING_PATHS_EXACT)
    assert "/hooks/" not in (*cl.GOVERNING_PATHS_EXACT, *cl.GOVERNING_PATH_PREFIXES)
    # the action keeps its loose marker; the new list never changes what it classifies
    assert cl.classify("Edit", {"file_path": "frontend/src/hooks/a.ts"}).actions == frozenset({cl.GOVERNING_FILE_EDIT})
    assert cl.classify("Edit", {"file_path": "tools/sessions/guard.py"}).actions == frozenset()


def test_mentions_return_only_the_matched_token():
    got = cl.governing_mentions("python3 tools/sessions/guard.py --secret-flag abc && git add /x/.github/workflows/a.yml")
    assert got == ("tools/sessions/guard.py", ".github/workflows/a.yml")
    assert cl.governing_mentions("ls frontend/src/hooks tools/sessions/guard_x.py") == ()


def test_a_bash_mention_is_collected_only_from_non_read_only_segments():
    assert cl.classify("Bash", {"command": "cat tools/sessions/guard.py"}).governing_mentions == ()
    assert cl.classify("Bash", {"command": "python3 tools/sessions/guard.py"}).governing_mentions == ("tools/sessions/guard.py",)


# ---- the guard's rows -------------------------------------------------------------------------

def test_an_edit_tool_on_a_governing_path_writes_one_exact_repo_relative_row_and_still_allows(tmp_path, governing_sink):
    repo = _repo(tmp_path)
    for tool in ("Edit", "Write", "MultiEdit"):
        code, out, err = _run({"tool_name": tool, "cwd": str(repo), "session_id": "s", "tool_input": {"file_path": str(repo / "CLAUDE.md")}})
        assert (code, out, err) == (0, "", "")
    rows = _rows(governing_sink)
    assert [r["path"] for r in rows] == ["CLAUDE.md"] * 3
    row = rows[0]
    assert set(row) == {"ts", "event", "seat", "path", "basis", "attempt"}
    assert (row["basis"], row["attempt"], row["seat"]) == ("path", True, "unresolved")
    assert str(tmp_path) not in json.dumps(rows)


def test_a_linked_worktree_path_resolves_to_the_same_relative_path(tmp_path, governing_sink):
    wt = tmp_path / "wt"
    wt.mkdir()
    (wt / ".git").write_text("gitdir: /elsewhere/.git/worktrees/wt\n")
    _run({"tool_name": "Edit", "cwd": str(wt / "tools"), "tool_input": {"file_path": str(wt / ".github" / "workflows" / "test.yml")}})
    assert [r["path"] for r in _rows(governing_sink)] == [".github/workflows/test.yml"]


def test_a_file_outside_the_repo_writes_no_row(tmp_path, governing_sink):
    repo = _repo(tmp_path)
    outside = tmp_path / "home" / ".claude" / "settings.json"
    code, out, _ = _run({"tool_name": "Edit", "cwd": str(repo), "tool_input": {"file_path": str(outside)}})
    assert (code, out) == (0, "") and _rows(governing_sink) == []


def test_a_non_governing_edit_and_a_react_hooks_edit_write_nothing(tmp_path, governing_sink):
    repo = _repo(tmp_path)
    for rel in ("src/a.py", "frontend/src/hooks/useThing.ts"):
        _run({"tool_name": "Edit", "cwd": str(repo), "tool_input": {"file_path": str(repo / rel)}})
    assert _rows(governing_sink) == []


def test_bash_writes_a_mention_row_holding_only_the_token(tmp_path, governing_sink):
    repo = _repo(tmp_path)
    code, out, _ = _run({"tool_name": "Bash", "cwd": str(repo), "tool_input": {"command": "sed -i s/a/b/ CLAUDE.md"}})
    assert (code, out) == (0, "")
    rows = _rows(governing_sink)
    assert [(r["path"], r["basis"]) for r in rows] == [("CLAUDE.md", "mention")]
    assert "sed" not in json.dumps(rows)


def test_a_bash_mention_of_guard_py_alone_gives_the_same_output_as_before(tmp_path, governing_sink):
    """Adding the names to the fast-path regex sends these commands on to classify; the result must stay silent."""
    repo = _repo(tmp_path)
    for command in ("python3 tools/sessions/guard.py", "vim tools/sessions/classify.py", "touch .github/workflows/x.yml"):
        assert _run({"tool_name": "Bash", "cwd": str(repo), "session_id": "none", "tool_input": {"command": command}}) == (0, "", "")


def test_a_failed_write_does_not_fail_or_change_the_call(tmp_path, monkeypatch):
    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(bd, "write_event", boom)
    repo = _repo(tmp_path)
    assert _run({"tool_name": "Edit", "cwd": str(repo), "tool_input": {"file_path": str(repo / "CLAUDE.md")}}) == (0, "", "")
    monkeypatch.setattr(guard, "_governing_rows", boom)
    assert _run({"tool_name": "Edit", "cwd": str(repo), "tool_input": {"file_path": str(repo / "CLAUDE.md")}}) == (0, "", "")


def test_other_actions_are_decided_exactly_as_before(tmp_path, governing_sink):
    repo = _repo(tmp_path)
    code, out, _ = _run({"tool_name": "Bash", "cwd": str(repo), "session_id": "none", "tool_input": {"command": "git push origin main"}})
    assert code == 0 and json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert _rows(governing_sink) == []


def test_a_guard_row_made_in_a_test_never_reaches_the_live_week_shard(tmp_path):
    week = datetime.now(timezone.utc).strftime("%G-W%V")
    live = Path(AGENT_MONITORING) / "data" / week / FAMILY
    before = live.read_bytes() if live.exists() else None
    repo = _repo(tmp_path)
    _run({"tool_name": "Edit", "cwd": str(repo), "tool_input": {"file_path": str(repo / "CLAUDE.md")}})
    assert (live.read_bytes() if live.exists() else None) == before


def test_known_limits_of_bash_rows_are_pinned_not_fixed():
    """A Bash edit not naming the path from the repo root, or inside an interpreter payload, writes no row; a mention can name
    a same-suffix file outside the repo. Documented in schema.md and the retro note; these assertions fail loudly if that changes."""
    assert cl.classify("Bash", {"command": "cd tools/sessions && sed -i s/a/b/ guard.py"}).governing_mentions == ()
    assert cl.classify("Bash", {"command": "python3 -c \"open('CLAUDE.md','w')\""}).governing_mentions == ()
    assert cl.classify("Bash", {"command": "sed -i x $HOME/.claude/settings.json"}).governing_mentions == (".claude/settings.json",)
