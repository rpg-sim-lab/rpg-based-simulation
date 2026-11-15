"""TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST AC8 (i): the paired cache key carries env8, ``<sha12>-<child8>-<ticks>-<env8>[-repeat]`` (rpg-planner's ruling,
2026-11-15). Fake files only; nothing runs."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.rpg_measure import env_digest, paired
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


# ---- fail closed on a missing lock (testing-planner review of AC7/AC8): "missing" is never a dependency set

@pytest.mark.parametrize("value", ["missing", "", None, "abc", "G" * 64, "A" * 64])
def test_lock_problem_accepts_only_a_lowercase_sha256(value):
    assert paired.lock_problem(value)
    assert paired.lock_problem("0" * 64) is None


def test_assembly_refuses_a_set_whose_jobs_all_record_a_missing_lock(tmp_path):
    from tests.unit.tools import test_paired_arms as tpa
    root = tmp_path / "arms"
    unlocked = {**tpa.RUNNER, "uv_lock": "missing"}
    tpa._pair_job(root, seed=42, runner=unlocked)
    tpa._pair_job(root, seed=43, runner=unlocked)  # all jobs agree, which used to assemble as matching
    with pytest.raises(pa.ArmsRefused, match="not a sha256"):
        pa.assemble(root, tmp_path / "out", base=tpa.BASE, new=tpa.NEW)


def test_collected_refuses_an_env_json_that_records_a_missing_lock(tmp_path):
    ci = _env(tmp_path, CI, lock=None)
    assert ci["uv_lock"] == "missing"
    _stage(tmp_path, ci)  # the name and env.json agree; the lock is what is wrong
    problem = paired.env_problems(tmp_path, [("base", SHA, [("w", 42)], 10, False)])
    assert problem and "not a sha256" in problem[0]


def test_local_paired_refuses_to_cache_under_a_missing_lock(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(paired, "_CURRENT_ENV", _env(tmp_path, lock=None))
    rc = paired.main(["--base", "HEAD", "--new", "HEAD", "--cache", str(tmp_path / "cache")])
    assert rc == 2 and "not a sha256" in capsys.readouterr().err
    assert not (tmp_path / "cache" / "results").exists()
    with pytest.raises(pa.ArmsRefused, match="not a sha256"):  # paired_arms run-arm too
        pa.run_arm(tmp_path, SHA, "base", "w", 42, 10, tmp_path / "cache2")


# ---- the CI runner label (rpg-planner review): image on a hosted runner, RUNNER_NAME on a self-hosted one, else refused

def test_a_hosted_runner_is_keyed_by_its_image_not_its_runner_name(tmp_path):
    env = _env(tmp_path, {**CI, "RUNNER_NAME": "GitHub Actions 7"})
    assert env["runner"] == "ci:ubuntu24-20260101.1.0"
    assert paired.env_key(env) == paired.env_key(_env(tmp_path, {**CI, "RUNNER_NAME": "GitHub Actions 9"}))


def test_a_self_hosted_runner_without_imageos_is_keyed_by_its_runner_name(tmp_path):
    env = _env(tmp_path, {"GITHUB_ACTIONS": "true", "RUNNER_NAME": "farm-3"})
    assert env["runner"] == "ci:self-hosted:farm-3" and paired.env_problem(env) is None
    assert paired.env_key(env) != paired.env_key(_env(tmp_path, {"GITHUB_ACTIONS": "true", "RUNNER_NAME": "farm-4"}))


def test_a_ci_runner_with_neither_imageos_nor_runner_name_is_refused_everywhere(tmp_path, monkeypatch, capsys):
    env = _env(tmp_path, {"GITHUB_ACTIONS": "true"})
    assert env["runner"] == paired.UNIDENTIFIED_RUNNER and "unidentified" in paired.env_problem(env)
    monkeypatch.setattr(paired, "_CURRENT_ENV", env)
    assert paired.main(["--base", "HEAD", "--new", "HEAD", "--cache", str(tmp_path / "cache")]) == 2
    assert "unidentified" in capsys.readouterr().err and not (tmp_path / "cache" / "results").exists()
    with pytest.raises(pa.ArmsRefused, match="unidentified"):
        pa.run_arm(tmp_path, SHA, "base", "w", 42, 10, tmp_path / "cache2")
    _stage(tmp_path, env)  # and a collected dir that records it
    assert "unidentified" in paired.env_problems(tmp_path, [("base", SHA, [("w", 42)], 10, False)])[0]


# ---- dists: the interpreter's installed distributions (testing-planner ruling, rpg-planner-ubuntu review)

class _Dist:
    def __init__(self, name, version):
        self.metadata, self.version = {"Name": name}, version


def _installed(monkeypatch, *pairs):
    monkeypatch.setattr(env_digest.importlib.metadata, "distributions", lambda **kw: [_Dist(n, v) for n, v in pairs])


def test_the_same_installed_set_gives_the_same_digest_whatever_its_order_and_spelling(monkeypatch):
    _installed(monkeypatch, ("Foo_Bar", "1.0"), ("baz", "2.0"))
    first = paired.installed_dists_digest()
    _installed(monkeypatch, ("baz", "2.0"), ("foo.bar", "1.0"))  # PEP 503: Foo_Bar == foo.bar
    assert paired.installed_dists_digest() == first and len(first) == 64


def test_adding_or_changing_a_distribution_gives_a_new_key_and_duplicates_count(tmp_path, monkeypatch):
    _installed(monkeypatch, ("a", "1"))
    base = paired.env_key(_env(tmp_path))
    _installed(monkeypatch, ("a", "1"), ("b", "1"))
    assert paired.env_key(_env(tmp_path)) != base
    _installed(monkeypatch, ("a", "2"))
    assert paired.env_key(_env(tmp_path)) != base
    _installed(monkeypatch, ("a", "1"), ("a", "1"))  # duplicates are kept
    _installed(monkeypatch, ("a", "1"))
    one = paired.installed_dists_digest()
    _installed(monkeypatch, ("a", "1"), ("a", "1"))
    assert paired.installed_dists_digest() != one


def test_an_empty_or_unreadable_distribution_list_is_refused(tmp_path, monkeypatch):
    _installed(monkeypatch)
    env = _env(tmp_path)
    assert env["dists"] == "empty" and "dists" in paired.env_problem(env)
    monkeypatch.setattr(env_digest.importlib.metadata, "distributions", lambda **kw: (_ for _ in ()).throw(OSError("no")))
    assert paired.installed_dists_digest() == "unreadable"
    _installed(monkeypatch, ("a", None))
    assert paired.installed_dists_digest() == "unreadable"


def test_collected_refuses_an_env_json_whose_dists_differ_from_its_name_or_are_unreadable(tmp_path, monkeypatch):
    _installed(monkeypatch, ("a", "1"))
    env = _env(tmp_path, CI)
    _stage(tmp_path, {**env, "dists": "e" * 64}, name_env=env)  # env.json says other dists than the directory name's env8
    entries = [("base", SHA, [("w", 42)], 10, False)]
    assert "not the env8" in paired.env_problems(tmp_path, entries)[0]
    other = tmp_path / "second"
    _stage(other, {**env, "dists": "unreadable"})
    assert "dists" in paired.env_problems(other, entries)[0]


# ---- the arm child reports its own dists; paired refuses an arm whose dists is not the key's

def test_a_local_arm_whose_child_reports_other_dists_is_refused_naming_both_digests(tmp_path, monkeypatch):
    key = paired.current_env()["dists"]
    def stub(doc):
        def run_one(tree, w, s, t, out):
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(doc))
        return run_one

    monkeypatch.setattr(paired, "run_one", stub({"runner": "PINNED", "dists": "c" * 64}))
    with pytest.raises(paired.DistsMismatchError) as err:
        paired.run_arm(tmp_path / "tree", tmp_path / "cache", SHA, [("w", 42)], 10, 1)
    assert "c" * 64 in str(err.value) and key in str(err.value)
    monkeypatch.setattr(paired, "run_one", stub({"runner": "PINNED"}))  # no dists at all
    with pytest.raises(paired.DistsMismatchError):
        paired.run_arm(tmp_path / "tree", tmp_path / "cache2", SHA, [("w", 42)], 10, 1)


def test_a_collected_arm_with_other_dists_is_refused_and_no_table_is_printed(tmp_path, capsys):
    from tests.unit.tools.test_rpg_measure_collected import BASE, NEW, TICKS, _put, _run, collected
    for w in paired.WORLDS:
        for s in (42, 43):
            _put(tmp_path, BASE, w, s, _run(w, s), runner=None)
            _put(tmp_path, NEW, w, s, {**_run(w, s), "dists": "c" * 64}, runner=None)  # the new arm's child had other dependencies
        _put(tmp_path, BASE, w, 42, _run(w, 42), repeat=True)
    with pytest.raises(paired.DistsMismatchError, match="c" * 64):
        collected(tmp_path)
    out = capsys.readouterr().out
    assert "| Step |" not in out and "People deaths" not in out


def test_the_arm_child_writes_dists_from_the_tool_checkouts_own_module():
    source = (Path(paired.__file__).with_name("arm_child.py")).read_text(encoding="utf-8")
    assert '"dists": _env_digest().installed_dists_digest()' in source and 'with_name("env_digest.py")' in source


# ---- the digest sees only the interpreter's own site-packages (rpg-planner review at c84269c33)

def _fake_dist(directory: Path, name: str, version: str, kind: str = "dist-info") -> None:
    info = directory / f"{name.replace('-', '_')}-{version}.{kind}"
    info.mkdir(parents=True, exist_ok=True)
    (info / ("METADATA" if kind == "dist-info" else "PKG-INFO")).write_text(f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")


def test_a_dist_in_the_cwd_or_on_sys_path_or_the_project_itself_never_moves_the_digest(tmp_path, monkeypatch):
    import sys
    before = env_digest.installed_dists_digest()
    cwd, extra = tmp_path / "cwd", tmp_path / "extra"
    cwd.mkdir()
    for name, kind in (("not-in-site", "egg-info"), ("rpg-based-simulation", "egg-info"), ("also-not", "dist-info")):
        _fake_dist(cwd, name, "9", kind)
        _fake_dist(extra, name, "9", kind)
    monkeypatch.chdir(cwd)
    monkeypatch.setattr(sys, "path", [str(cwd), str(extra), *sys.path])  # what PYTHONPATH / cwd do to sys.path in an arm child
    assert env_digest.installed_dists_digest() == before
    assert str(cwd.resolve()) not in env_digest.site_dirs() and str(extra.resolve()) not in env_digest.site_dirs()


def test_the_projects_own_distribution_is_never_counted_even_inside_site_packages(tmp_path, monkeypatch):
    site = tmp_path / "site"
    _fake_dist(site, "a", "1")
    monkeypatch.setattr(env_digest, "site_dirs", lambda: [str(site)])
    first = env_digest.installed_dists_digest()
    _fake_dist(site, "Rpg_Based.Simulation", "0.1", "dist-info")  # PEP 503: the same project, spelled differently
    assert env_digest.installed_dists_digest() == first


def test_changing_a_distribution_in_site_packages_still_moves_the_digest(tmp_path, monkeypatch):
    site = tmp_path / "site"
    _fake_dist(site, "a", "1")
    monkeypatch.setattr(env_digest, "site_dirs", lambda: [str(site)])
    first = env_digest.installed_dists_digest()
    _fake_dist(site, "b", "1")
    second = env_digest.installed_dists_digest()
    assert second != first and len(second) == 64
    _fake_dist(site, "a", "2")
    assert env_digest.installed_dists_digest() not in (first, second)


def test_site_dirs_are_the_interpreters_own_and_exist():
    import sysconfig
    dirs = env_digest.site_dirs()
    assert dirs and str(Path(sysconfig.get_paths()["purelib"]).resolve()) in dirs and all(Path(d).is_dir() for d in dirs)
