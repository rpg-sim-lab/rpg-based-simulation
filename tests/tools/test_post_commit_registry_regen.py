"""TCK-20261111-REGISTRY-REGEN-MISSES-A-MERGE-FINISHED-BY-COMMIT: the post-commit hook regenerates docs/REGISTRY.yaml
after a merge that stopped on a conflict and was finished with `git commit` (post-merge never ran for it).

Real `tools/hooks/post-commit-reindex.sh`, installed as .git/hooks/post-commit of a temp repo with a stub
`tools/generate_registry.py` whose --check exits 2 until a regeneration has run once. No knowledge.db, so the reindex
half of the hook is a no-op. Everything lives in tmp_path."""
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
_REGEN_SUBJECT = "auto-regenerate docs/REGISTRY.yaml after merge"
_STUB = '''import sys
from pathlib import Path
marker = Path("docs/.regenerated")
if "--check" in sys.argv:
    sys.exit(0 if marker.exists() else 2)
marker.parent.mkdir(exist_ok=True)
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
    (root / "tools" / "generate_registry.py").write_text(_STUB)
    (root / "docs" / "REGISTRY.yaml").write_text("old\n")
    (root / "f.txt").write_text("base\n")
    _git(root.parent, "init", "-q", "-b", "main", str(root))
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "init")
    hook = root / ".git" / "hooks" / "post-commit"
    shutil.copy(_REPO / "tools" / "hooks" / "post-commit-reindex.sh", hook)
    hook.chmod(0o755)
    return root


def _regen_commits(repo):
    return _git(repo, "log", "--format=%s").stdout.splitlines().count(_REGEN_SUBJECT)


def _conflicted_merge_finished_by_commit(repo):
    _git(repo, "switch", "-q", "-c", "side")
    (repo / "f.txt").write_text("side\n")
    _git(repo, "commit", "-qam", "side change")
    _git(repo, "switch", "-q", "main")
    (repo / "f.txt").write_text("main\n")
    _git(repo, "commit", "-qam", "main change")
    assert _git(repo, "merge", "side", check=False).returncode != 0  # stops on the conflict: post-merge never runs
    (repo / "f.txt").write_text("resolved\n")
    _git(repo, "add", "f.txt")
    return _git(repo, "commit", "--no-edit")


def test_a_merge_finished_with_git_commit_gets_exactly_one_regen_commit(repo):
    done = _conflicted_merge_finished_by_commit(repo)
    assert "[registry-post-commit]" in done.stdout + done.stderr  # git routes hook stdout to stderr
    assert _regen_commits(repo) == 1
    assert (repo / "docs" / "REGISTRY.yaml").read_text() == "regenerated\n"
    assert _git(repo, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split().__len__() == 2  # one parent: no loop
    assert _git(repo, "status", "--porcelain", "--", "docs/REGISTRY.yaml").stdout == ""  # the regenerated file was committed


def test_a_non_merge_commit_does_nothing(repo):
    (repo / "f.txt").write_text("changed\n")
    _git(repo, "commit", "-qam", "plain commit")
    assert _regen_commits(repo) == 0
    assert (repo / "docs" / "REGISTRY.yaml").read_text() == "old\n"


def test_a_merge_whose_check_exits_zero_does_nothing(repo):
    (repo / "docs" / ".regenerated").write_text("x")  # the stub's --check now exits 0
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "registry already current")
    _conflicted_merge_finished_by_commit(repo)
    assert _regen_commits(repo) == 0
    assert (repo / "docs" / "REGISTRY.yaml").read_text() == "old\n"
