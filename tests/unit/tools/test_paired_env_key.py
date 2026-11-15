"""TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST AC8 (i): the paired cache key carries env8, ``<sha12>-<child8>-<ticks>-<env8>[-repeat]`` (rpg-planner's ruling,
2026-11-15). Fake files only; nothing runs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.rpg_measure import paired
from tools.test_architecture import paired_arms as pa

SHA = "a" * 40
LOCAL = {"GITHUB_ACTIONS": "false"}
CI = {"GITHUB_ACTIONS": "true", "ImageOS": "ubuntu24", "ImageVersion": "20260101.1.0"}


def _env(tmp_path, environ=LOCAL, host="u24desktop", lock=b"v1\n", arm_tree=None):
    root = tmp_path / ("tool" if lock is not None else "tool-without-lock")
    root.mkdir(exist_ok=True)
    if lock is not None:
        (root / "uv.lock").write_bytes(lock)
    return paired.run_env(environ, host, root, arm_tree)


def test_a_local_and_a_ci_environment_give_different_keys(tmp_path):
    local, ci = _env(tmp_path), _env(tmp_path, CI)
    assert local["runner"] == "local:u24desktop" and ci["runner"] == "ci:ubuntu24-20260101.1.0"
    assert paired.env_key(local) != paired.env_key(ci)
    assert paired.env_key(local) != paired.env_key(_env(tmp_path, host="other-host"))


def test_the_same_environment_gives_the_same_key(tmp_path):
    assert paired.env_key(_env(tmp_path)) == paired.env_key(_env(tmp_path))
    assert len(paired.env_key(_env(tmp_path))) == 8


def test_a_uv_lock_change_gives_a_new_key_and_the_source_is_recorded(tmp_path):
    first = _env(tmp_path, lock=b"v1\n")
    assert first["uv_lock_source"] == "tool"
    assert paired.env_key(first) != paired.env_key(_env(tmp_path, lock=b"v2\n"))
    arm = tmp_path / "arm"
    arm.mkdir()
    (arm / "uv.lock").write_bytes(b"arm\n")
    fallback = _env(tmp_path, lock=None, arm_tree=arm)  # the tool checkout has none: the arm tree's is used, and says so
    assert fallback["uv_lock_source"] == "arm_tree" and fallback["uv_lock"] != first["uv_lock"]
    assert _env(tmp_path, lock=None)["uv_lock_source"] == "none"


def test_the_key_is_the_ordered_components_with_env8_last_before_repeat(tmp_path):
    env = _env(tmp_path)
    comps = paired.key_components(SHA, 5000, env)
    assert comps == [SHA[:12], paired.child_hash(), "5000", paired.env_key(env)]
    assert paired.result_key(comps) == "-".join(comps) and paired.result_key(comps, repeat=True) == "-".join(comps) + "-repeat"
    assert paired.result_path(tmp_path, SHA, 5000, "w", 42, True, env).parent.name == "-".join(comps) + "-repeat"


def _stage(cache: Path, env, name_env=None, write_env=True, repeat=False):
    path = paired.result_path(cache, SHA, 10, "w", 42, repeat, name_env or env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"runner": "PINNED"}))
    if write_env:
        paired.write_env_json(path.parent, env)
    return path


def test_an_old_format_entry_is_a_miss_and_is_never_deleted(tmp_path):
    old = tmp_path / "results" / f"{SHA[:12]}-{paired.child_hash()}-10" / "w_42.json"
    old.parent.mkdir(parents=True)
    old.write_text(json.dumps({"runner": "PINNED"}))
    assert paired.missing_results(tmp_path, [("base", SHA, [("w", 42)], 10, False)]) == ["base:w:42"]
    assert not paired.result_path(tmp_path, SHA, 10, "w", 42).exists()
    paired.write_env_json(paired.result_path(tmp_path, SHA, 10, "w", 42).parent)  # writing the new entry leaves the old one alone
    assert old.is_file()


def test_a_collected_result_is_found_under_the_env8_of_the_machine_that_made_it(tmp_path):
    ci = _env(tmp_path, CI)
    made = _stage(tmp_path, ci)
    assert paired.collected_path(tmp_path, SHA, 10, "w", 42) == made  # the aggregate's own env is not needed
    entries = [("base", SHA, [("w", 42)], 10, False)]
    assert paired.missing_results(tmp_path, entries) == [] and paired.env_problems(tmp_path, entries) == []


def test_a_mismatched_env_json_is_refused(tmp_path, capsys):
    ci = _env(tmp_path, CI)
    _stage(tmp_path, {**ci, "uv_lock": "f" * 64}, name_env=ci)  # env.json says another uv.lock than the directory name's env8
    entries = [("base", SHA, [("w", 42)], 10, False)]
    problem = paired.env_problems(tmp_path, entries)
    assert problem and "not the env8" in problem[0]


def test_a_missing_env_json_and_a_set_built_under_two_environments_are_refused(tmp_path):
    ci, local = _env(tmp_path, CI), _env(tmp_path)
    _stage(tmp_path, ci, write_env=False)
    entries = [("base", SHA, [("w", 42)], 10, False)]
    assert "no readable env.json" in paired.env_problems(tmp_path, entries)[0]
    _stage(tmp_path, ci)
    _stage(tmp_path, local, repeat=True)  # the base repeat was built elsewhere
    both = entries + [("base", SHA, [("w", 42)], 10, True)]
    assert "different environments" in paired.env_problems(tmp_path, both)[-1]


def test_run_arm_writes_env_json_beside_the_result(tmp_path, monkeypatch):
    monkeypatch.setattr(paired, "prepare_tree", lambda repo, rev, cache: (SHA, tmp_path / "tree"))
    monkeypatch.setattr(paired, "run_one", lambda tree, w, s, t, out: out.write_text('{"runner": "PINNED"}'))
    pa.run_arm(tmp_path, SHA, "base", "w", 42, 10, tmp_path / "cache")
    out = paired.result_path(tmp_path / "cache", SHA, 10, "w", 42)
    assert json.loads((out.parent / paired.ENV_FILE).read_text()) == paired.current_env() and paired.env_json_problem(out.parent) is None
