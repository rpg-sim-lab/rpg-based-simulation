"""TCK-20261111-POST-COMMIT-REINDEX-OPT-IN: the post-commit hook reindexes knowledge search only when the clone opts in
(`git config --bool knowledge.reindexOnCommit true`); the registry regen for a merge commit is unconditional.

Real `tools/hooks/post-commit-reindex.sh` installed as .git/hooks/post-commit of a temp repo, with a stub
`tools/knowledge_search.py` that writes a marker file when it is run, a fake knowledge.db, and a stub generate_registry.
Everything lives in tmp_path."""
import shutil
import subprocess
from pathlib import Path

import pytest

from tools.agent_working_paths import KNOWLEDGE_INDEX

_REPO = Path(__file__).resolve().parents[2]
_REGEN_SUBJECT = "auto-regenerate docs/REGISTRY.yaml after merge"
_SKIP = "reindex skipped (opt-in)"
_RUN = "running incremental reindex"
_KS_STUB = 'from pathlib import Path\nPath("reindex.ran").write_text("x")\n'
_REG_STUB = '''import sys
from pathlib import Path
marker = Path("docs/.regenerated")
if "--check" in sys.argv:
    sys.exit(0 if marker.exists() else 2)
marker.write_text("x")
Path("docs/REGISTRY.yaml").write_text("regenerated\\n")
'''


def _git(repo, *args, check=True):
    return subprocess.run(["git", "-c", "user.email=a@b", "-c", "user.name=t", *args], cwd=repo, check=check,
                          capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    (root / "tools").mkdir(parents=True)
    (root / "docs").mkdir()
    (root / KNOWLEDGE_INDEX).mkdir(parents=True)
    (root / KNOWLEDGE_INDEX / "knowledge.db").write_text("db")
    (root / "tools" / "knowledge_search.py").write_text(_KS_STUB)
    (root / "tools" / "generate_registry.py").write_text(_REG_STUB)
    (root / "docs" / "REGISTRY.yaml").write_text("old\n")
    (root / "docs" / "a.md").write_text("a\n")
    (root / "f.txt").write_text("base\n")
    (root / ".gitignore").write_text("reindex.ran\nagent-working/.index/\n")
    _git(root.parent, "init", "-q", "-b", "main", str(root))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    hook = root / ".git" / "hooks" / "post-commit"
    shutil.copy(_REPO / "tools" / "hooks" / "post-commit-reindex.sh", hook)
    hook.chmod(0o755)
    return root


def _docs_commit(repo):
    (repo / "docs" / "a.md").write_text("changed\n")
    done = _git(repo, "commit", "-qam", "docs change")
    return done.stdout + done.stderr  # git routes hook stdout to stderr


def _merge_commit(repo):
    _git(repo, "switch", "-q", "-c", "side")
    (repo / "f.txt").write_text("side\n")
    _git(repo, "commit", "-qam", "side change")
    _git(repo, "switch", "-q", "main")
    (repo / "f.txt").write_text("main\n")
    _git(repo, "commit", "-qam", "main change")
    assert _git(repo, "merge", "side", check=False).returncode != 0
    (repo / "f.txt").write_text("resolved\n")
    _git(repo, "add", "f.txt")
    return _git(repo, "commit", "--no-edit")


def _regen_commits(repo):
    return _git(repo, "log", "--format=%s").stdout.splitlines().count(_REGEN_SUBJECT)


def test_unset_opt_in_skips_the_reindex_and_says_so(repo):
    out = _docs_commit(repo)
    assert not (repo / "reindex.ran").exists()
    assert _SKIP in out and "knowledge.reindexOnCommit" in out and "make knowledge-index-update" in out


def test_opt_in_true_runs_the_incremental_reindex(repo):
    _git(repo, "config", "--bool", "knowledge.reindexOnCommit", "true")
    out = _docs_commit(repo)
    assert (repo / "reindex.ran").exists()
    assert _RUN in out and _SKIP not in out


@pytest.mark.parametrize("value", ["false", "0", "no"])
def test_opt_in_false_values_skip(repo, value):
    _git(repo, "config", "knowledge.reindexOnCommit", value)
    out = _docs_commit(repo)
    assert not (repo / "reindex.ran").exists() and _SKIP in out


def test_a_commit_that_does_not_trigger_a_reindex_prints_no_skip_line(repo):
    (repo / "f.txt").write_text("changed\n")
    done = _git(repo, "commit", "-qam", "not docs")
    assert _SKIP not in done.stdout + done.stderr and not (repo / "reindex.ran").exists()


def test_no_index_means_no_skip_line_and_no_reindex(repo):
    (repo / KNOWLEDGE_INDEX / "knowledge.db").unlink()
    assert _SKIP not in _docs_commit(repo)
    assert not (repo / "reindex.ran").exists()


@pytest.mark.parametrize("opt_in", [None, "true"])
def test_merge_commit_regenerates_the_registry_whatever_the_opt_in(repo, opt_in):
    if opt_in:
        _git(repo, "config", "--bool", "knowledge.reindexOnCommit", opt_in)
    done = _merge_commit(repo)
    assert "[registry-post-commit]" in done.stdout + done.stderr
    assert _regen_commits(repo) == 1
