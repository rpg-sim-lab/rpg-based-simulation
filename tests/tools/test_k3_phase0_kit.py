"""Unit controls for the K3 Phase 0 trace kit (tools/rpg_measure/k3_phase0_*): planted positives and negatives for every class the designer fixed (D1, D2, D3, the HARD flag), the pass-through, the summary rules, the layout, the launcher and a JSON round trip of
the exact report. No simulation is run here (rpg-designer-k3-plan-rulings.md 972600b672863882...)."""
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
KIT_FILES = ("arm_child.py", "person_attack_spy.py", "person_attack_summary.py", "k3_phase0_spy.py", "k3_phase0_summary.py", "k3_phase0_launch.sh")


def load_from(path, key):
    sys.modules.pop("_arm_child_pinned_runner", None)
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


spy_mod = load_from(KIT / "k3_phase0_spy.py", "_t_k3p0_spy")
summary = load_from(KIT / "k3_phase0_summary.py", "_t_k3p0_summary")


def funcs(threat=False):
    return {"need_is_pressing": lambda h, s: h >= 57.0 or s >= 58.8, "present_threat_to": lambda e, s: threat, "acting_threat_to": lambda e, s: False,
            "same_kind": lambda p, k: str(getattr(p.kind, "value", p.kind)) == str(getattr(k, "value", k)), "live_statuses": ("ACTIVE", "SUSPENDED")}


def project(pid="p1", kind="hunger", status="ACTIVE", ended=None, score=70.0):
    return NS(id=pid, kind=NS(value=kind), status=NS(value=status), ended_by=None if ended is None else NS(value=ended), score=score)


def entity(eid=1, hunger=80.0, sleep=10.0, projects=(), current="p1", gold=10, results=()):
    return NS(id=eid, biological=NS(hunger=hunger, sleep_debt=sleep), inventory=NS(gold=gold), identity=NS(latest_intent_results=tuple(results)), combat=NS(alive=True),
              strategic=NS(projects={p.id: p for p in projects}, current_project_id=current))


def state(tick, entities):
    return NS(tick=tick, entities={e.id: e for e in entities}, buildings={})


def update(eid=1, current_set=None, entries=(), remove=()):
    return NS(entity_updates={eid: NS(strategic=NS(current_project_id_set=current_set, projects_add_or_update=list(entries), projects_remove=list(remove)))})


def scores(kind="hunger", utility=90.0):
    return [NS(kind=NS(value=kind), utility=utility, target_id=7, target_pos=None)]


def cycle(spy, d_entity, d1_entity, tick=10, kind="hunger", upd=None):
    """One decision at state tick d and its apply (d+1)."""
    spy.decision(d_entity, state(tick, [d_entity]), scores(kind))
    spy.observe(state(tick, [d_entity]), state(tick + 1, [d1_entity]), upd if upd is not None else update())


# ---------------------------------------------------------------- the classes
def test_d1_a_hunger_project_completed_with_the_need_met_is_a_lawful_end():
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=25.0, projects=[project(status="COMPLETED")], current=""), upd=update(current_set="", entries=[project(status="COMPLETED")]))
    row = spy.report()["rows"][0]
    assert row["class"] == "D1" and spy.report()["classes"] == {"D1": 1} and row["after"]["need_met"] is True and row["after"]["writer"] == "not readable"
    assert row["after"]["update_strategic"]["current_project_id_set"] == "" and row["after"]["update_strategic"]["project_entries"][0]["status"] == "COMPLETED"


def test_d1_a_service_delivered_counts_as_the_need_met_even_when_the_value_did_not_fall():
    spy = spy_mod.Phase0Spy(funcs())
    meal = NS(transaction_id="t1", accepted=True)
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=80.0, projects=[project(status="COMPLETED")], current="", results=[meal]))
    assert spy.report()["classes"] == {"D1": 1}


def test_a_stale_accepted_result_carried_over_is_not_a_delivery_so_the_row_is_d2_and_a_fresh_one_is_d1():
    """m3 control (designer review 1a065963): patches.py keeps the previous latest_intent_results when an update has none; that carry-over must NOT count as the need met."""
    stale = NS(transaction_id="t-old", accepted=True)
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=80.0, projects=[project()], results=[stale]), entity(hunger=80.0, projects=[project(status="COMPLETED")], current="", results=[stale]))
    row = spy.report()["rows"][0]
    assert row["class"] == "D2" and row["after"]["need_met"] is False and row["after"]["fresh_accepted_results"] == 0
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=80.0, projects=[project()], results=[stale]), entity(hunger=80.0, projects=[project(status="COMPLETED")], current="", results=[stale, NS(transaction_id="t-new", accepted=True)]))
    row = spy.report()["rows"][0]
    assert row["class"] == "D1" and row["after"]["fresh_accepted_results"] == 1
    spy = spy_mod.Phase0Spy(funcs())                                     # a fresh REJECTED result is no delivery either
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=80.0, projects=[project(status="COMPLETED")], current="", results=[NS(transaction_id="t-r", accepted=False)]))
    assert spy.report()["rows"][0]["class"] == "D2"


def test_a_paid_transfer_is_d1_with_its_raw_fields_recorded():
    spy = spy_mod.Phase0Spy(funcs())
    before, after = entity(hunger=80.0, projects=[project()], gold=10), entity(hunger=80.0, projects=[project(status="COMPLETED")], current="", gold=5)
    spy.decision(before, state(10, [before]), scores())
    prior = NS(tick=10, entities={1: before}, buildings={7: NS(inventory=NS(gold=100))})
    spy.observe(prior, NS(tick=11, entities={1: after}, buildings={7: NS(inventory=NS(gold=105))}), update())
    row = spy.report()["rows"][0]
    assert row["class"] == "D1" and row["after"]["gold_delta"] == -5 and row["after"]["purse_rises"] == {7: 5}


def test_d2_a_typed_end_while_the_need_rises_is_listed_by_reason_and_a_completed_without_the_need_met_is_d2_too():
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=81.0, projects=[project(status="ABANDONED", ended="WAY_CLOSED")], current=""), tick=10)
    cycle(spy, entity(2, hunger=80.0, projects=[project("p2")], current="p2"), entity(2, hunger=81.0, projects=[project("p2", status="COMPLETED")], current=""), tick=20)
    cycle(spy, entity(3, hunger=80.0, projects=[project("p3")], current="p3"), entity(3, hunger=81.0, projects=[project("p3", status="ABANDONED", ended="DESTINATION_GIVEN_UP")], current=""), tick=30)
    rep = spy.report()
    assert rep["classes"] == {"D2": 3} and rep["d2_by_reason"] == {"WAY_CLOSED": 1, "COMPLETED_NOT_MET": 1, "DESTINATION_GIVEN_UP": 1}


def test_d3_current_cleared_while_the_project_stays_active():
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=81.0, projects=[project()], current=""), upd=update(current_set=""))
    row = spy.report()["rows"][0]
    assert row["class"] == "D3" and row["after"]["project"]["status"] == "ACTIVE" and row["after"]["update_strategic"]["current_project_id_set"] == ""


def test_continues_switched_away_and_other_are_told_apart_and_continues_is_not_a_row():
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=81.0, projects=[project()], current="p1"), tick=10)                                                     # still current
    cycle(spy, entity(2, hunger=80.0, projects=[project("p2")], current="p2"), entity(2, hunger=81.0, projects=[project("p2", status="SUSPENDED"), project("q", kind="town_return")], current="q"), tick=20)
    cycle(spy, entity(3, hunger=80.0, projects=[project("p3")], current="p3"), entity(3, hunger=81.0, projects=[], current=""), tick=30)                                         # the record is gone
    rep = spy.report()
    assert rep["classes"] == {"switched_away": 1, "other": 1} and all(r["class"] != "continues" for r in rep["rows"])


def test_only_an_escalated_need_winner_with_its_own_kind_current_is_in_the_family():
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=40.0, projects=[project()]), entity(hunger=41.0, projects=[], current=""))                                                                            # not escalated
    cycle(spy, entity(2, hunger=80.0, projects=[project("p2", kind="town_return")], current="p2"), entity(2, hunger=81.0, projects=[], current=""), tick=20)                         # another kind current
    cycle(spy, entity(3, hunger=80.0, projects=[project("p3")], current="p3"), entity(3, hunger=81.0, projects=[], current=""), tick=30, kind="combat")                               # the winner is not a need
    cycle(spy, entity(4, hunger=80.0, sleep=90.0, projects=[project("p4", kind="fatigue")], current="p4"), entity(4, hunger=80.0, sleep=91.0, projects=[], current=""), tick=40, kind="fatigue")   # a fatigue winner counts
    rep = spy.report()
    assert rep["reach"]["d_family_decisions"] == 1 and [r["need"] for r in rep["rows"]] == ["fatigue"] and rep["reach"]["escalated_need_decisions"] == 2


def test_the_threat_flags_are_recorded_at_the_decision():
    spy = spy_mod.Phase0Spy(funcs(threat=True))
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=81.0, projects=[project()], current=""))
    assert spy.report()["rows"][0]["before"]["threat"] is True and spy.report()["threat_at_decision"] == 1


# ---------------------------------------------------------------- the HARD flag
def _d3_run(spy, eid, hungers, start=100):
    for i, hunger in enumerate(hungers):
        t = start + 10 * i
        cycle(spy, entity(eid, hunger=hunger, projects=[project("p%d" % eid)], current="p%d" % eid), entity(eid, hunger=hunger + 0.1, projects=[project("p%d" % eid)], current=""), tick=t)


def test_three_consecutive_d3_decisions_at_hunger_95_are_hard_two_are_not_and_hunger_below_95_is_not():
    hard = spy_mod.Phase0Spy(funcs())
    _d3_run(hard, 1, [96.0, 96.5, 97.0])
    assert hard.report()["hard_d3_cycles"] == [{"subject": 1, "ticks": [100, 110, 120], "hunger": [96.0, 96.5, 97.0]}]
    assert spy_mod.Phase0Spy(funcs()).report()["hard_d3_cycles"] == []
    two = spy_mod.Phase0Spy(funcs())
    _d3_run(two, 1, [96.0, 96.5])
    assert two.report()["hard_d3_cycles"] == []
    low = spy_mod.Phase0Spy(funcs())
    _d3_run(low, 1, [96.0, 90.0, 97.0, 96.0])
    assert low.report()["hard_d3_cycles"] == []                                                         # a decision below 95 breaks the run
    broken = spy_mod.Phase0Spy(funcs())
    _d3_run(broken, 1, [96.0, 96.5])
    cycle(broken, entity(1, hunger=97.0, projects=[project("p1")], current="p1"), entity(1, hunger=97.1, projects=[project("p1")], current="p1"), tick=130)               # continues in between
    _d3_run(broken, 1, [96.0, 96.5], start=140)
    assert broken.report()["hard_d3_cycles"] == []


# ---------------------------------------------------------------- the report round trip, the pass-through
def test_the_exact_report_serializes_with_sort_keys_whatever_the_classes_and_reasons():              # the v3 own-job kit died on a None key here; the report must serialize with the real call
    spy = spy_mod.Phase0Spy(funcs())
    cycle(spy, entity(hunger=80.0, projects=[project()]), entity(hunger=81.0, projects=[project(status="ABANDONED", ended="WAY_CLOSED")], current=""), tick=10)
    cycle(spy, entity(2, hunger=80.0, projects=[project("p2")], current="p2"), entity(2, hunger=81.0, projects=[project("p2")], current=""), tick=20)
    cycle(spy, entity(3, hunger=80.0, projects=[project("p3")], current="p3"), entity(3, hunger=81.0, projects=[], current=""), tick=30)
    text = json.dumps(spy.report(), sort_keys=True, default=str)
    assert json.loads(text)["classes"] == {"D2": 1, "D3": 1, "other": 1}


def test_the_wrappers_are_pass_through_and_restore():
    class Apply:
        @staticmethod
        def apply_generation(prior, upd, *a, **k):
            return NS(tick=prior.tick + 1, entities={}, buildings={})

    class Score:
        marker = []

        @staticmethod
        def apply_modifiers(entity, state, scores):
            return Score.marker

    oa, os_ = Apply.__dict__["apply_generation"], Score.__dict__["apply_modifiers"]
    spy = spy_mod.Phase0Spy(funcs()).install(Apply, Score)
    assert Score.apply_modifiers(entity(), state(1, []), []) is Score.marker and Apply.apply_generation(state(3, []), update()).tick == 4
    spy.restore()
    assert Apply.__dict__["apply_generation"].__func__ is oa.__func__ and Score.__dict__["apply_modifiers"].__func__ is os_.__func__


# ---------------------------------------------------------------- the summary rules
def _cell(out, plain_hash, spy_hash, classes=None, hard=None, **extra):
    base = {"fatal": None, "logging_errors": []}
    (out / "urban_political_s42_t2400_plain.json").write_text(json.dumps(dict(base, final_hash=plain_hash)))
    (out / "urban_political_s42_t2400_spy.json").write_text(json.dumps(dict(base, final_hash=spy_hash, spy_exceptions=[], findings=[], classes=classes or {}, d2_by_reason={}, hard_d3_cycles=hard or [], rows=[], reach={}, **extra)))


def test_the_summary_passes_a_matching_baseline_and_computes_the_baseline_after_d1(tmp_path):
    _cell(tmp_path, summary.BASELINE_HASH, summary.BASELINE_HASH, classes={"D1": 4, "D3": 2})
    doc = summary.summarize(tmp_path)
    assert doc["valid"] and doc["baseline_ok"] and doc["flags"] == [] and doc["baseline_after_d1"] == 26 and summary.main([str(tmp_path)]) == 0


def test_a_baseline_hash_difference_flags_that_the_30_does_not_carry_over_and_a_void_cell_is_invalid(tmp_path):
    _cell(tmp_path, "other", "other")
    doc = summary.summarize(tmp_path)
    assert doc["valid"] and not doc["baseline_ok"] and doc["flags"][0].startswith("BASELINE") and "re-count K3 with kit v6" in doc["flags"][0] and summary.main([str(tmp_path)]) == 2
    _cell(tmp_path, summary.BASELINE_HASH, "different")
    assert summary.summarize(tmp_path)["valid"] is False


def test_a_hard_cycle_is_flagged_and_exits_2(tmp_path):
    _cell(tmp_path, summary.BASELINE_HASH, summary.BASELINE_HASH, hard=[{"subject": 1, "ticks": [1, 2, 3], "hunger": [96.0, 96.0, 96.0]}])
    assert summary.summarize(tmp_path)["flags"][0].startswith("HARD") and summary.main([str(tmp_path)]) == 2


# ---------------------------------------------------------------- the layout and the launcher
def build_kit_layout(root, with_pinned_runner=True):
    (root / "tools" / "rpg_measure").mkdir(parents=True)
    for name in KIT_FILES:
        shutil.copy(KIT / name, root / "tools" / "rpg_measure" / name)
    if with_pinned_runner:
        (root / "tools" / "test_architecture").mkdir(parents=True)
        shutil.copy(REPO / "tools" / "test_architecture" / "pinned_runner.py", root / "tools" / "test_architecture" / "pinned_runner.py")
    return root


def test_the_spy_resolves_the_pinned_runner_from_the_tool_checkout_layout(tmp_path):
    kit = build_kit_layout(tmp_path / "kit")
    spy = load_from(kit / "tools" / "rpg_measure" / "k3_phase0_spy.py", "_layout_k3p0_spy")
    assert hasattr(spy, "main") and hasattr(spy.load_sibling("arm_child")._pinned_runner(), "require_pinned")


def _launch(kit, tmp_path, **env):
    full = {**os.environ, "KIT": str(kit), "OUT": str(tmp_path / "out"), "TREE": str(tmp_path / "tree"), "LAUNCH_DRY_RUN": "1", **env}
    return subprocess.run(["bash", str(kit / "tools" / "rpg_measure" / "k3_phase0_launch.sh")], env=full, capture_output=True, text=True, timeout=60)


def test_the_launcher_prechecks_the_pinned_runner_refuses_a_used_tree_and_dry_runs_the_one_cell(tmp_path):
    missing = build_kit_layout(tmp_path / "kit", with_pinned_runner=False)
    done = _launch(missing, tmp_path)
    assert done.returncode == 1 and "pinned_runner.py is missing" in done.stdout
    kit = build_kit_layout(tmp_path / "kit2")
    done = _launch(kit, tmp_path)
    lines = [l for l in done.stdout.splitlines() if l.startswith("CELL ")]
    assert done.returncode == 0 and len(lines) == 1 and "urban_political s42 2400t" in lines[0] and "2a6e74f04cd735a1" in lines[0] and f"{kit}/tools/rpg_measure/k3_phase0_spy.py" in lines[0]
    assert _launch(kit, tmp_path, TREE=str(tmp_path / "k2fix_tree_e39")).returncode == 18
