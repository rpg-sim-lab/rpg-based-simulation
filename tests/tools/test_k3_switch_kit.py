"""Unit controls for the K3 own-job kit (tools/rpg_measure/k3_switch_*): FIRES = rule True AND ordinary False, TAKEN = rule True, the pass-through, the guard list, the summary bars, the layout and the launcher.
No simulation is run here (rpg-designer-k3-plan-rulings.md 972600b6...)."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "tools" / "rpg_measure"
KIT_FILES = ("arm_child.py", "person_attack_spy.py", "person_attack_summary.py", "k3_switch_spy.py", "k3_switch_summary.py", "k3_switch_launch.sh")


def load_from(path, key):
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


spy_mod = load_from(KIT / "k3_switch_spy.py", "_t_k3sw_spy")
summary = load_from(KIT / "k3_switch_summary.py", "_t_k3sw_summary")


def project(pid="p", kind="town_return", score=50.0, lock=0, status="ACTIVE"):
    return NS(id=pid, kind=NS(value=kind), score=score, lock_until_tick=lock, status=NS(value=status), ended_by=None)


def entity(eid=1, hp=100, projects=(), current=""):
    return NS(id=eid, biological=NS(hunger=80.0, sleep_debt=0.0), combat=NS(hp=hp), strategic=NS(projects={p.id: p for p in projects}, current_project_id=current))


def state(tick, entities=()):
    return NS(tick=tick, entities={e.id: e for e in entities})


class Sis:
    @staticmethod
    def evaluate_project_switch(entity, candidate, current_tick, state=None):
        return intel._escalated_need_takes_switch(entity, candidate, entity.strategic.projects[entity.strategic.current_project_id], state) and "update"


class Apply:
    @staticmethod
    def apply_generation(prior, update, *a, **k):
        return prior


intel = NS()


@pytest.fixture
def rig(monkeypatch):
    holder = NS(rule=True, ordinary=False, threat=False, acting=False, ordinary_calls=[])
    intel._escalated_need_takes_switch = lambda e, c, cur, s: holder.rule
    intel._ordinary_switch_allows = lambda e, c, cur, t, s: (holder.ordinary_calls.append((e.id, t)) or holder.ordinary)
    import src.ai.goals.present_threat as pt
    monkeypatch.setattr(pt, "present_threat_to", lambda e, s: holder.threat)
    monkeypatch.setattr(pt, "acting_threat_to", lambda e, s: holder.acting)
    holder.spy = spy_mod.SwitchSpy(intel, Sis, Apply).install()
    yield holder
    holder.spy.restore()


def decide(rig, hp=100, current_kind="town_return", tick=50, eid=1):
    cur = project("cur", current_kind, lock=60)
    ent = entity(eid, hp, [cur], "cur")
    return ent, Sis.evaluate_project_switch(ent, project("h", "hunger", 70.0), tick, state(tick, [ent]))


def test_a_fire_is_rule_true_and_ordinary_false_and_a_taken_the_ordinary_allows_is_not_a_fire(rig):
    decide(rig)
    rig.ordinary = True
    decide(rig, eid=2)
    rep = rig.spy.report()
    assert rep["taken"] == 2 and rep["fires"] == 1 and rep["fires_by_need_and_current_kind"] == {"hunger|town_return": 1} and rep["taken_by_need_and_current_kind"] == {"hunger|town_return": 2}
    assert [r["fire"] for r in rep["rows"]] == [True, False] and rig.ordinary_calls == [(1, 50), (2, 50)]       # the ordinary helper is read with the evaluate call's current_tick


def test_a_rule_false_decision_records_nothing_and_never_calls_the_ordinary_helper(rig):
    rig.rule = False
    _, out = decide(rig)
    assert out is False and rig.spy.report()["taken"] == 0 and rig.ordinary_calls == []


def test_the_wrappers_are_pass_through_and_restore(rig):
    _, out = decide(rig)
    assert out == "update"                                                                      # the original result
    rig.spy.restore()
    taken_before = rig.spy.report()["taken"]
    decide(rig, eid=2)
    assert rig.spy.report()["taken"] == taken_before                                           # restored: the originals no longer record
    rig.spy.install()


def test_a_taken_under_a_present_threat_is_counted_and_the_acting_threat_too(rig):
    rig.threat = True
    decide(rig)
    rep = rig.spy.report()
    assert rep["taken_under_present_threat"] == 1 and rep["taken_under_acting_threat"] == 0
    rig.threat, rig.acting = False, True
    decide(rig, eid=2)
    assert rig.spy.report()["taken_under_present_threat"] == 1 and rig.spy.report()["taken_under_acting_threat"] == 1


def test_the_guard_lists_a_combat_current_with_whether_hp_fell_within_50_ticks(rig):
    ent, _ = decide(rig, current_kind="combat_retreat")
    decide(rig, current_kind="combat_engage", eid=2)
    decide(rig, current_kind="town_return", eid=3)
    rig.spy.observe(state(60, [entity(1, hp=70), entity(2, hp=100)]))
    rig.spy.observe(state(120, [entity(1, hp=10)]))                                              # outside the 50 tick window: ignored
    rig.spy.finish(state(130, [entity(1, hp=10, projects=[project("cur", "combat_retreat", status="SUSPENDED")]), entity(2, hp=100)]))
    rep = rig.spy.report()
    assert [(g["subject"], g["current_kind"], g["damage_within_50"]) for g in rep["guard_rows"]] == [(1, "combat_retreat", True), (2, "combat_engage", False)]
    assert rep["rows"][0]["suspended_fate"]["status"] == "SUSPENDED"


def test_ticks_current_and_the_reach_counters_follow_a_fire(rig):
    decide(rig)
    rig.spy.observe(state(51, [entity(1, current="h")]))
    rig.spy.observe(state(52, [entity(1, current="other")]))
    ent = entity(2)
    ent.biological.hunger, ent.biological.sleep_debt = 96.0, 99.0
    rig.spy.observe(state(53, [ent]))
    rep = rig.spy.report()
    assert rep["rows"][0]["ticks_current"] == 1 and rep["reached"] == {"hunger_95": [2], "sleep_98": [2]}
    json.dumps(rep, sort_keys=True, default=str)


def _cell(out, world, seed, ticks, plain_hash, spy_hash=None, taken=0, threat=0, **extra):
    base = {"fatal": None, "logging_errors": []}
    (out / f"{world}_s{seed}_t{ticks}_plain.json").write_text(json.dumps(dict(base, final_hash=plain_hash)))
    if spy_hash is not None:
        (out / f"{world}_s{seed}_t{ticks}_spy.json").write_text(json.dumps(dict(base, final_hash=spy_hash, spy_exceptions=[], findings=[], taken=taken, fires=taken, taken_under_present_threat=threat, rows=[], reached={}, guard_rows=[], **extra)))


def test_the_summary_neutrality_bar_needs_the_base_hash_when_taken_is_zero(tmp_path):
    fix, base = tmp_path / "fix", tmp_path / "base"
    fix.mkdir(), base.mkdir()
    _cell(fix, "urban_political", 42, 2400, "aa", "aa", taken=0)
    _cell(base, "urban_political", 42, 2400, "aa")
    assert summary.main([str(fix), str(base)]) == 0
    _cell(base, "urban_political", 42, 2400, "bb")
    assert summary.main([str(fix), str(base)]) == 2                                              # TAKEN = 0 but the hash moved: STOP
    _cell(fix, "urban_political", 42, 2400, "cc", "cc", taken=3)                                  # TAKEN > 0: neutrality is not asserted
    assert summary.main([str(fix), str(base)]) == 0


def test_a_taken_under_a_present_threat_fails_and_a_hash_mismatch_is_void(tmp_path):
    fix, base = tmp_path / "fix", tmp_path / "base"
    fix.mkdir(), base.mkdir()
    _cell(fix, "urban_political", 42, 2400, "aa", "aa", taken=2, threat=1)
    assert summary.main([str(fix), str(base)]) == 2
    _cell(fix, "urban_political", 42, 2400, "aa", "zz", taken=2)
    cell = summary.cell_summary(fix, base, "urban_political", 42, 2400)
    assert cell["valid"] is False and "spy final_hash != plain final_hash" in cell["problems"]


def build_kit_layout(root, with_runner=True):
    (root / "tools" / "rpg_measure").mkdir(parents=True)
    for name in KIT_FILES:
        shutil.copy(KIT / name, root / "tools" / "rpg_measure" / name)
    if with_runner:
        (root / "tools" / "test_architecture").mkdir(parents=True)
        shutil.copy(REPO / "tools" / "test_architecture" / "pinned_runner.py", root / "tools" / "test_architecture" / "pinned_runner.py")
    return root


def test_the_spy_resolves_the_pinned_runner_from_the_tool_checkout_layout(tmp_path):
    kit = build_kit_layout(tmp_path / "kit")
    spy = load_from(kit / "tools" / "rpg_measure" / "k3_switch_spy.py", "_layout_k3sw_spy")
    assert hasattr(spy.load_sibling("arm_child")._pinned_runner(), "require_pinned")


def _launch(kit, tmp_path, **env):
    full = {**os.environ, "ARM": "fix", "KIT": str(kit), "OUT": str(tmp_path / "out"), "TREE": str(tmp_path / "tree"), "LAUNCH_DRY_RUN": "1", **env}
    return subprocess.run(["bash", str(kit / "tools" / "rpg_measure" / "k3_switch_launch.sh")], env=full, capture_output=True, text=True, timeout=60)


def test_the_launcher_prechecks_dry_runs_four_cells_per_arm_and_refuses_a_used_or_bad_arm(tmp_path):
    assert _launch(build_kit_layout(tmp_path / "k1", with_runner=False), tmp_path).returncode == 1
    kit = build_kit_layout(tmp_path / "k2")
    cells = [line for line in _launch(kit, tmp_path).stdout.splitlines() if line.startswith("CELL ")]
    assert len(cells) == 4 and all("plain then spy" in c for c in cells) and "urban_political s42 2400t" in cells[3]
    base = [line for line in _launch(kit, tmp_path, ARM="base").stdout.splitlines() if line.startswith("CELL ")]
    assert len(base) == 4 and all("then spy" not in c for c in base)
    assert _launch(kit, tmp_path, TREE=str(tmp_path / "k3_phase0_tree_e39")).returncode == 18
    assert _launch(kit, tmp_path, ARM="x").returncode == 9
