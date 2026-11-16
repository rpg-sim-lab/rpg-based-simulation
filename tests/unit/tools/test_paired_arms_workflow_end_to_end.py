"""The paired-arms workflow's own commands, run in sequence (TCK-20261116-AN-ARM-RUNS-WHEN-THE-CACHE-PATH-IS-RELATIVE, B2).

The workflow path had shown two bugs that no test executed (a relative ``--cache``, a ``KeyError`` after the arm). This runs, in relative-cwd temp dirs like the
runner's checkout, the commands PARSED from ``.github/workflows/paired-arms.yml`` (their ``${VAR}`` expanded from the job env, never retyped): every planned job's
arm steps with ``--cache arm-cache``, the "Collect the results" shell step (real bash), ``assemble``, and the compare step's ``paired --collected`` command.
Retyped, because they are bash scripts with arrays: the ``plan`` call (its arguments) and the artifact-name template (read from the upload step, expressions filled in).
Only the arm child is a stub (it writes a fixed valid document); prepare_tree is stubbed (no git); ``run_one`` is the real one, in a real subprocess."""
from __future__ import annotations

import importlib
import os
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from tools.rpg_measure import paired
from tools.test_architecture import paired_arms as pa

WORKFLOW = Path(__file__).resolve().parents[3] / ".github" / "workflows" / "paired-arms.yml"
BASE, NEW = "a" * 40, "b" * 40
TICKS, SEEDS, STEP = "10", "42,43", "nonflight-move-off-engagement"
CHILD = (
    "import json, sys\n"
    "from pathlib import Path\n"
    "world, seed, ticks, out = sys.argv[1:5]\n"
    "doc = json.loads((Path(__file__).with_name('doc.json')).read_text())\n"
    "doc.update(world=world, seed=int(seed))\n"
    "Path(out).parent.mkdir(parents=True, exist_ok=True)\n"
    "Path(out).write_text(json.dumps(doc, sort_keys=True))\n"
)


def _workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _step(job: str, name: str) -> dict:
    return next(s for s in _workflow()["jobs"][job]["steps"] if s.get("name") == name)


def _expand(text: str, env: dict) -> str:
    return re.sub(r"\$\{(\w+)\}", lambda m: env[m.group(1)], text)


def _run_cli(run: str, env: dict) -> int:
    """Run one ``python -m <module> args...`` workflow command in-process (so the stubs apply), its ``${VAR}`` filled from ``env``."""
    tokens = shlex.split(_expand(" ".join(run.replace("\\\n", " ").split()), env))
    assert tokens[:2] == ["python", "-m"], tokens
    return importlib.import_module(tokens[2]).main(tokens[3:])


def _artifact_name(slug: str, world: str, seed: int, kind: str) -> str:
    upload = next(s for s in _workflow()["jobs"]["arms"]["steps"] if str(s.get("uses", "")).startswith("actions/upload-artifact@"))
    name = upload["with"]["name"].replace("${{ needs.plan.outputs.slug }}", slug).replace("${{ matrix.world }}", world).replace("${{ matrix.seed }}", str(seed))
    return name.replace("${{ matrix.kind == 'self' && '-self' || '' }}", "-self" if kind == "self" else "")


def _runs(step: dict, kind: str) -> bool:
    condition = step.get("if")
    return True if condition is None else re.search(r"matrix\.kind == '(\w+)'", condition).group(1) == kind


def _compare_command(env: dict, seeds: list[str]) -> str:
    run = _step("aggregate", "Compare with paired.py --collected")["run"].replace("\\\n", " ")
    command = run[run.index("python -m tools.rpg_measure.paired --collected"):]
    return command.replace('"${seeds[@]}"', " ".join(seeds)).replace('"${flags[@]}"', "")  # TERRAIN and LEGACY_BASE are false: no flags


def _fake_prepare_tree(repo, rev, cache):
    tree = cache / "trees" / rev[:12]  # relative whenever the cache is, as the real prepare_tree returns it
    tree.mkdir(parents=True, exist_ok=True)
    return rev, tree


@pytest.fixture
def workflow_run(tmp_path, monkeypatch, capsys):
    """Plan, every arm job and the Collect step, in relative cwds; leaves ``tmp_path/agg`` holding ``arms/<artifact>/results/...``."""
    child = tmp_path / "child" / "stub_child.py"
    child.parent.mkdir()
    child.write_text(CHILD, encoding="utf-8")
    (child.parent / "doc.json").write_text(json.dumps({
        "world": "", "seed": 0, "start": [[1, "merchant", 1, 1], [2, "guard", 1, 1]], "final": {"1": [1, None, "merchant"], "2": [1, None, "guard"]}, "counters": None,
        "perception_samples": 5, "final_hash": "h", "start_hash": "s", "audit_mode": True, "signals_zeroed": True, "adds": {}, "runner": "PINNED",
        "dists": paired.current_env()["dists"]}), encoding="utf-8")
    monkeypatch.setattr(paired, "CHILD", child)
    monkeypatch.setattr(paired, "prepare_tree", _fake_prepare_tree)
    monkeypatch.setattr(pa, "runner_identity", lambda env=None, **kw: {
        "name": "gh-1", "image": "ubuntu24-" + os.environ.get("ImageVersion", "?"), "image_os": "ubuntu24", "image_version": os.environ.get("ImageVersion", "?"), "libc": "glibc-2.39",
        "python_build": "3.13.1 (main) [GCC 13]", "cpu_model": "x", "nproc": 4, "mem_total_mb": 16000, "python": "3.13.1", "os": "Ubuntu", "uv_lock": paired.current_env()["uv_lock"]})
    # plan (retyped: the workflow step is a bash script with an array)
    assert pa.main(["plan", "--worlds", ",".join(paired.WORLDS), "--seeds", SEEDS, "--self-check", "seed42", "--evidence", "--step", STEP]) == 0
    plan = dict(line.split("=", 1) for line in capsys.readouterr().out.splitlines() if "=" in line)
    include, slug = json.loads(plan["matrix"])["include"], plan["slug"]
    assert {j["kind"] for j in include} == {"pair", "self"}
    agg = tmp_path / "agg"
    for n, job in enumerate(include):
        workdir = tmp_path / "jobs" / str(n)  # each job a fresh checkout-like cwd; --cache arm-cache is RELATIVE to it
        workdir.mkdir(parents=True)
        monkeypatch.chdir(workdir)
        monkeypatch.setenv("ImageVersion", "20261111.82.6" if n == 1 else "20261111.196.1")  # run 43805965260: one job was served the older image patch
        env = {"BASE_SHA": BASE, "NEW_SHA": NEW, "TICKS": TICKS, "WORLD": job["world"], "SEED": str(job["seed"])}
        for step in (s for s in _workflow()["jobs"]["arms"]["steps"] if s.get("name") in ("Base arm", "New arm", "Base-vs-base repeat arm")):
            if _runs(step, job["kind"]):
                assert "--cache arm-cache" in step["run"]
                assert _run_cli(step["run"], env) == 0, step["name"]
        collect = _step("arms", "Collect the results")["run"]
        subprocess.run(["bash", "-euc", collect], check=True, cwd=workdir)  # the workflow's own shell step, as written
        shutil.copytree(workdir / "upload", agg / "arms" / _artifact_name(slug, job["world"], job["seed"], job["kind"]))
    capsys.readouterr()
    return agg, include


def _compare(agg: Path, monkeypatch, capsys, div: str | None) -> tuple[int, str, bytes]:
    monkeypatch.chdir(agg)
    env = {"BASE_SHA": BASE, "NEW_SHA": NEW, "STEP_LABEL": STEP, "TICKS": TICKS, "SELF_CHECK": "seed42", "DIV": "-" if div is None else div}  # the input's default is "-"
    assert _run_cli(_step("aggregate", "Assemble one paired cache root")["run"], env) == 0
    command = _compare_command(env, SEEDS.split(","))
    for stale in ("table.md", "verdict.json"):
        Path(stale).unlink(missing_ok=True)
    assert _run_cli(command, env) == 0, capsys.readouterr().err
    return 0, Path("table.md").read_text(encoding="utf-8"), Path("verdict.json").read_bytes()


def test_the_workflows_own_commands_run_end_to_end_with_a_relative_cache_and_pass(workflow_run, monkeypatch, capsys):
    agg, include = workflow_run
    assert len(list((agg / "arms").iterdir())) == len(include)
    _rc, table, verdict = _compare(agg, monkeypatch, capsys, None)
    assert "## Paired measurement: nonflight-move-off-engagement (div -)" in table and "self-check (seed42, 3 runs): spread 0" in table
    assert json.loads(verdict) == {"outcome": "PASS", "mode": "step", "detail": None}
    assert (agg / "collected").is_dir()
    assert json.loads((agg / "collected" / "identities.json").read_text())["image_versions"] == ["20261111.196.1", "20261111.82.6"]  # two patch versions, one environment


def test_div_is_a_label_only_the_same_verdict_bytes_and_a_table_that_differs_only_in_the_label(workflow_run, monkeypatch, capsys):
    agg, _ = workflow_run
    _, plain_table, plain_verdict = _compare(agg, monkeypatch, capsys, None)
    shutil.rmtree(agg / "collected")
    _, div_table, div_verdict = _compare(agg, monkeypatch, capsys, "2.204")
    assert "(div -)" in plain_table and "| - |" in plain_table and "(div 2.204)" in div_table and "| 2.204 |" in div_table
    assert div_verdict == plain_verdict
    assert div_table.replace("(div 2.204)", "(div -)").replace("| 2.204 |", "| - |") == plain_table
