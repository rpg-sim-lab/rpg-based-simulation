"""tools/delivery/repo_name.py: the repo comes from gh, else the org fallback (no network: injected runner)."""

from __future__ import annotations

import subprocess

import pytest

from tools.delivery import repo_name


@pytest.fixture(autouse=True)
def _fresh_cache():
    repo_name._cache.clear()
    yield
    repo_name._cache.clear()


def _done(stdout="", returncode=0):
    return lambda cmd: subprocess.CompletedProcess(cmd, returncode, stdout, "")


def test_the_repo_is_derived_from_gh_when_gh_works():
    seen = []

    def run(cmd):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, "some-org/some-repo\n", "")

    assert repo_name.current_repo(run) == "some-org/some-repo"
    assert seen[0][:3] == ["gh", "repo", "view"]
    assert repo_name.current_repo(_done(returncode=1)) == "some-org/some-repo"  # a real answer is cached


@pytest.mark.parametrize("run", [
    _done(returncode=1), _done(""), _done("https://api.github.com/repos/o/r/issues/1"),
    lambda cmd: (_ for _ in ()).throw(OSError("no gh")),
])
def test_the_fallback_is_used_when_gh_fails_or_answers_oddly(run):
    assert repo_name.current_repo(run) == repo_name.FALLBACK_REPO == "rpg-sim-lab/rpg-based-simulation"
    assert "repo" not in repo_name._cache
