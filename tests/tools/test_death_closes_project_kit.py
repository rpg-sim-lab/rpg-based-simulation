"""Unit controls for the death-closes-project own-job kit (tools/rpg_measure/death_closes_project_*): the tracker (D1-D5 and the reported rows), the exact frozen event categories, the living projection digest, the summarizer bars and
exit codes, the divergence locator and the launcher layout. No simulation is run here (rpg-designer-death-closes-ownjob-definition.md sha256 df2ba4b5...)."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "tools" / "rpg_measure"
KIT_FILES = ("arm_child.py", "person_attack_spy.py", "person_attack_tree_check.py", "death_closes_project_logic.py", "death_closes_project_spy.py", "death_closes_project_summary.py", "death_closes_project_controls.py",
             "death_closes_project_divergence_locate.py", "death_closes_project_launch.sh", "death_closes_project_tree_check.sh")


def load_from(path, key):
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


logic = load_from(KIT / "death_closes_project_logic.py", "_t_dcp_logic")
summary = load_from(KIT / "death_closes_project_summary.py", "_t_dcp_summary")
locate = load_from(KIT / "death_closes_project_divergence_locate.py", "_t_dcp_locate")


def project(pid, status="ACTIVE", ended_by=None, ended_tick=None, quest_status=None):
    return NS(id=pid, status=status, ended_by=ended_by, ended_tick=ended_tick, quest_status=quest_status)


def body(eid, projects=(), current="", alive=True, dead_tick=None):
    return NS(id=eid, combat=NS(alive=alive), lifecycle=NS(death_record=None if dead_tick is None else NS(tick=dead_tick)), strategic=NS(projects={p.id: p for p in projects}, current_project_id=current))


def observe(tracker, prior, new, tick=10):
    tracker.observe(tick, {e.id: e for e in prior}, {e.id: e for e in new})
    return tracker.report()


def test_a_dead_body_with_a_live_project_or_only_a_current_project_is_dead_with_live():
    rep = observe(logic.DeathTracker(), [body(1, [project("a")], "a"), body(2, [project("b")], "b"), body(3)], [body(1, [project("a")], "a", alive=False, dead_tick=10), body(2, [], "ghost", alive=False, dead_tick=10), body(3, [], "", alive=False, dead_tick=10)])
    assert rep["dwl_total_rows"] == 2 and rep["dwl_sum"] == 2
    assert rep["dwl_rows"][0] == {"tick": 10, "id": 1, "live_ids": ["a"], "current_project_id": "a"} and rep["dwl_rows"][1]["live_ids"] == [] and rep["dwl_rows"][1]["current_project_id"] == "ghost"   # the current clause alone
    assert rep["dead_at_death_with_live"] == 2 and rep["dead_bodies"] == 3


def test_an_old_age_body_is_dead_by_its_death_record_and_the_alive_keyed_mutant_misses_it():
    old_age = body(1, [project("a")], "a", alive=True, dead_tick=10)
    assert observe(logic.DeathTracker(), [body(1)], [old_age])["dwl_total_rows"] == 1
    assert observe(logic.DeathTracker("alive"), [body(1)], [old_age])["dwl_total_rows"] == 0           # m7: the spy keyed on combat.alive sees nothing


def test_a_suspended_project_is_live_and_a_completed_one_is_not():
    rep = observe(logic.DeathTracker(), [body(1)], [body(1, [project("s", "SUSPENDED"), project("c", "COMPLETED")], "", alive=False, dead_tick=10)])
    assert rep["dwl_rows"][0]["live_ids"] == ["s"]


def test_a_death_end_must_be_abandoned_at_the_death_tick_on_a_dead_body():
    live = [project("a"), project("s", "SUSPENDED")]
    good = [project("a", "ABANDONED", "DEATH", 10), project("s", "ABANDONED", "DEATH", 10)]
    rep = observe(logic.DeathTracker(), [body(1, live, "a")], [body(1, good, "", alive=False, dead_tick=10)])
    assert (rep["d2_violations"], rep["dwl_total_rows"], rep["ends_by"], rep["death_split"], rep["abandoned_by"]) == (0, 0, {"DEATH": 2}, {"ACTIVE": 1, "SUSPENDED": 1}, {"DEATH": 2})
    late = [project("a", "ABANDONED", "DEATH", 11)]
    assert observe(logic.DeathTracker(), [body(1, [project("a")], "a")], [body(1, late, "", alive=False, dead_tick=10)])["d2_violations"] == 1          # m5: ended_tick = tick + 1
    wrong_status = [project("a", "COMPLETED", "DEATH", 10)]
    assert observe(logic.DeathTracker(), [body(1, [project("a")], "a")], [body(1, wrong_status, "", alive=False, dead_tick=10)])["d2_violations"] == 1
    not_dead = [project("a", "ABANDONED", "DEATH", 10)]
    assert observe(logic.DeathTracker(), [body(1, [project("a")], "a")], [body(1, not_dead, "", alive=True)])["d2_violations"] == 1                 # a DEATH end on a body with no death record


def test_other_ends_are_counted_but_never_a_death_violation():
    rep = observe(logic.DeathTracker(), [body(1, [project("a")], "a")], [body(1, [project("a", "COMPLETED", "THREAT_CLEARED", 10)], "")])
    assert rep["ends_total"] == 1 and rep["d2_violations"] == 0 and "DEATH" not in rep["ends_by"] and rep["abandoned_by"] == {}


def test_records_kept_d3_catches_a_removed_record_and_survives_a_removed_body():
    before = [project("a"), project("b", "COMPLETED")]
    assert observe(logic.DeathTracker(), [body(1, before, "a")], [body(1, [project("a", "ABANDONED", "DEATH", 10), project("b", "COMPLETED")], "", alive=False, dead_tick=10)])["d3_violations"] == 0
    rep = observe(logic.DeathTracker(), [body(1, before, "a")], [body(1, [project("b", "COMPLETED")], "", alive=False, dead_tick=10)])        # m4: the live record was removed
    assert rep["d3_violations"] == 1 and rep["d3_rows"][0]["missing"] == ["a"]


def test_a_lag_row_must_be_resolved_by_the_next_tick():
    tracker = logic.DeathTracker()
    tracker.observe(10, {}, {1: body(1, [project("a")], "a", alive=False)})                       # alive False, no death record: a lag row
    tracker.observe(11, {1: body(1, [project("a")], "a", alive=False)}, {1: body(1, [project("a", "ABANDONED", "DEATH", 11)], "", alive=False, dead_tick=11)})
    ok = tracker.report()
    assert (ok["lag_total"], ok["lag_resolved"], ok["lag_over_one_tick"]) == (1, 1, 0)
    slow = logic.DeathTracker()
    stuck = body(1, [project("a")], "a", alive=False)
    slow.observe(10, {}, {1: stuck})
    slow.observe(11, {1: stuck}, {1: stuck})
    assert slow.report()["lag_over_one_tick"] == 1 and slow.report()["lag_over_one_tick_rows"][0]["first_tick"] == 10
    last = logic.DeathTracker()
    last.observe(10, {}, {1: stuck})
    assert last.report()["lag_over_one_tick"] == 0 and last.report()["lag_unjudged_at_run_end"] == 1


def test_a_quest_project_ended_by_death_with_the_quest_status_still_open_is_reported():
    rep = observe(logic.DeathTracker(), [body(1, [project("q", quest_status="ACTIVE")], "q")], [body(1, [project("q", "ABANDONED", "DEATH", 10, quest_status="ACTIVE")], "", alive=False, dead_tick=10)])
    assert rep["quest_open_after_death_count"] == 1


def test_the_event_categories_are_the_exact_frozen_set():
    assert logic.PROJECT_LIFECYCLE_EVENT_CATEGORIES == frozenset({"QUEST_COMPLETED", "QUEST_FAILED"})


def ev(category, subject):
    return NS(category=NS(value=category), subject=subject, region_id=None, severity=1.0, payload={"q": 1.0}, tick=5)


def test_event_controls_living_kept_non_project_kept_dead_project_dropped_no_substring_match():
    nothing = logic.living_event_digest([], [1])
    assert logic.living_event_digest([ev("QUEST_COMPLETED", "2")], [1]) == logic.living_event_digest([ev("QUEST_COMPLETED", "2")], [], categories=()) != nothing     # e1
    assert logic.living_event_digest([ev("FEEDING_KILL", "1")], [1]) != nothing                                                                                       # e2
    assert logic.living_event_digest([ev("QUEST_FAILED", "1")], [1]) == nothing                                                                                       # e3
    assert logic.living_event_digest([ev("QUEST_COMPLETED_EXTRA", "1")], [1]) != nothing                                                                              # no substring match
    assert logic.living_event_digest([ev("QUEST_COMPLETED", "1"), ev("FEEDING_KILL", "9")], [1]) == logic.living_event_digest([ev("FEEDING_KILL", "9")], [1])


def test_the_living_projection_drops_only_a_dead_body_strategic_component():
    base = {"tick": 5, "entities": {"1": {"strategic": {"p": 1}, "x": 1}, "2": {"strategic": {"p": 2}, "x": 2}}}
    only_dead_differs = {"tick": 5, "entities": {"1": {"strategic": {"p": 99}, "x": 1}, "2": {"strategic": {"p": 2}, "x": 2}}}
    living_differs = {"tick": 5, "entities": {"1": {"strategic": {"p": 1}, "x": 1}, "2": {"strategic": {"p": 3}, "x": 2}}}
    dead_other_field = {"tick": 5, "entities": {"1": {"strategic": {"p": 1}, "x": 7}, "2": {"strategic": {"p": 2}, "x": 2}}}
    assert logic.living_projection_digest(base, [1]) == logic.living_projection_digest(only_dead_differs, ["1"])
    assert logic.living_projection_digest(base, [1]) != logic.living_projection_digest(living_differs, [1])
    assert logic.living_projection_digest(base, [1]) != logic.living_projection_digest(dead_other_field, [1])     # only `strategic` is dropped
    assert base["entities"]["1"]["strategic"] == {"p": 1}                                                          # the input is not modified


def cell_doc(**over):
    doc = {"final_hash": "h", "distinct_ticks": 5000, "dead_bodies": 30, "apply_calls": 5000, "dwl_sum": 400, "dwl_total_rows": 400, "dead_at_death_with_live": 20, "dwl_rows": [], "d2_violations": 0, "d2_rows": [], "d3_violations": 0, "d3_rows": [],
           "lag_total": 2, "lag_over_one_tick": 0, "lag_unjudged_at_run_end": 0, "ends_by": {"X": 3}, "ends_total": 3, "death_split": {}, "abandoned_by": {}, "quest_open_after_death_count": 0,
           "living_by_tick": {"1": "a", "2": "b"}, "events_by_tick": {"1": "e", "2": "f"}, "phase_rows": {}}
    doc.update(over)
    return doc


def write_cells(tmp_path, base_over=None, fix_over=None, twin_over=None, world="crowded_frontier"):
    base_dir, fix_dir = tmp_path / "base", tmp_path / "fix"
    base_dir.mkdir(parents=True)
    fix_dir.mkdir(parents=True)
    base = cell_doc(**{"dwl_total_rows": 0, "dwl_sum": 400, **(base_over or {})})
    fix = cell_doc(**{"dwl_total_rows": 0, "dwl_sum": 0, "ends_by": {"X": 3, "DEATH": 20}, "ends_total": 23, "death_split": {"ACTIVE": 20}, **(fix_over or {})})
    twin = cell_doc(**{"final_hash": fix["final_hash"], **(twin_over or {})})
    stem = f"{world}_s42_t5000"
    for d, mode, doc in ((base_dir, "spy", base), (fix_dir, "spy", fix), (fix_dir, "plain", twin)):
        (d / f"{stem}_{mode}.json").write_text(json.dumps(doc), encoding="utf-8")
    return base_dir, fix_dir


def test_a_clean_cell_passes_every_bar_and_reports_death_ends_against_the_extra_transitions(tmp_path):
    base_dir, fix_dir = write_cells(tmp_path, base_over={"final_hash": "hb"}, fix_over={"final_hash": "hf"}, twin_over={})
    (fix_dir / "crowded_frontier_s42_t5000_plain.json").write_text(json.dumps(cell_doc(final_hash="hf")), encoding="utf-8")
    cell = summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 5000)
    assert {k: b["status"] for k, b in cell["bars"].items()} == {"D1": "PASS", "D2": "PASS", "D3": "PASS", "D4": "PASS", "D5": "PASS", "D6": "PASS", "D7": "PASS"}
    assert cell["reported"]["death_ends"] == 20 and cell["reported"]["extra_ended_transitions_fix_minus_base"] == 20 and cell["reported"]["death_ends_equal_extra"] is True
    assert cell["reported"]["suspended_branch_unit_only"] is True and "NOT MEASURED" in cell["reported"]["simq_project_abandoned"]
    assert summary.main([str(base_dir), str(fix_dir)]) == 0


def test_a_thin_base_cell_makes_d1_not_measured_and_asks_to_widen(tmp_path):
    base_dir, fix_dir = write_cells(tmp_path, base_over={"dead_at_death_with_live": 4, "final_hash": "same"}, fix_over={"final_hash": "same"})
    (fix_dir / "crowded_frontier_s42_t5000_plain.json").write_text(json.dumps(cell_doc(final_hash="same")), encoding="utf-8")
    cell = summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 5000)
    assert cell["bars"]["D4"]["status"] == "FAIL" and cell["bars"]["D1"]["status"] == "NOT MEASURED" and cell["widen"] is True


def test_a_zero_base_cell_is_vacuous_and_must_be_full_hash_equal(tmp_path):
    base_dir, fix_dir = write_cells(tmp_path, base_over={"dwl_sum": 0, "dead_at_death_with_live": 0, "final_hash": "hb"}, fix_over={"final_hash": "hf"})
    (fix_dir / "crowded_frontier_s42_t5000_plain.json").write_text(json.dumps(cell_doc(final_hash="hf")), encoding="utf-8")
    cell = summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 5000)
    assert cell["bars"]["D7"]["status"] == "FAIL" and "FULL-hash" in cell["bars"]["D7"]["note"]


def test_a_remaining_dead_with_live_row_fails_d1_even_on_a_thin_cell(tmp_path):
    base_dir, fix_dir = write_cells(tmp_path, base_over={"dead_at_death_with_live": 1}, fix_over={"dwl_total_rows": 3, "dwl_rows": [{"tick": 9, "id": 4, "live_ids": ["x"]}]})
    assert summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 5000)["bars"]["D1"]["status"] == "FAIL"


def test_a_living_projection_divergence_is_a_stop_with_its_first_tick(tmp_path):
    base_dir, fix_dir = write_cells(tmp_path, fix_over={"living_by_tick": {"1": "a", "2": "CHANGED"}})
    cell = summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 5000)
    assert cell["bars"]["D7"]["status"] == "STOP" and cell["bars"]["D7"]["living_projection_first_divergence"][0] == "2"
    assert summary.main([str(base_dir), str(fix_dir)]) == 4
    base_dir2, fix_dir2 = write_cells(tmp_path / "second", fix_over={"events_by_tick": {"1": "e", "2": "X"}})
    assert summary.cell_summary(base_dir2, fix_dir2, "crowded_frontier", 42, 5000)["bars"]["D7"]["status"] == "STOP"


def test_the_twin_hash_and_a_void_cell_are_bars(tmp_path):
    base_dir, fix_dir = write_cells(tmp_path, fix_over={"final_hash": "spy"}, twin_over={"final_hash": "plain"})
    assert summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 5000)["bars"]["D6"]["status"] == "FAIL"
    base_dir2, fix_dir2 = write_cells(tmp_path / "void", fix_over={"logging_errors": [{"message": "boom"}]})
    cell = summary.cell_summary(base_dir2, fix_dir2, "crowded_frontier", 42, 5000)
    assert cell["problems"] and not cell["bars"] and summary.verdict([cell]) == 2
    assert summary.verdict([]) == 2


def test_the_smoke_mode_checks_only_the_pipeline(tmp_path):
    base_dir, fix_dir = write_cells(tmp_path, base_over={"distinct_ticks": 300}, fix_over={"distinct_ticks": 300})
    (fix_dir / "crowded_frontier_s42_t5000_plain.json").write_text(json.dumps(cell_doc(final_hash="h")), encoding="utf-8")
    cell = summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 300, smoke=True)
    assert cell["problems"] == ["BASE spy: cell missing", "FIX spy: cell missing", "FIX plain twin: cell missing"]     # the cell key carries the ticks: a 300 t smoke cell has its own files
    for d in (base_dir, fix_dir):
        for mode in ("spy", "plain"):
            src = d / f"crowded_frontier_s42_t5000_{mode}.json"
            if src.exists():
                src.rename(d / f"crowded_frontier_s42_t300_{mode}.json")
    cell = summary.cell_summary(base_dir, fix_dir, "crowded_frontier", 42, 300, smoke=True)
    assert set(cell["bars"]) == {"D6", "SMOKE"} and cell["bars"]["SMOKE"]["status"] == "PASS"


def test_first_divergence_and_the_locator(tmp_path):
    assert summary.first_divergence({"1": "a", "10": "b"}, {"1": "a", "10": "c"}) == ("10", "b", "c")
    assert summary.first_divergence({"1": "a"}, {"1": "a"}) is None
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    a.write_text(json.dumps({"entities": {"7": {"hp": 1, "x": [1, 2]}}}), encoding="utf-8")
    b.write_text(json.dumps({"entities": {"7": {"hp": 2, "x": [1, 2]}}}), encoding="utf-8")
    assert locate.diff(json.loads(a.read_text()), json.loads(b.read_text())) == [("entities", "7", "hp")]
    assert locate.main([str(a), str(b)]) == 1 and locate.main([str(a), str(a)]) == 0


def test_the_kit_files_exist_and_the_launcher_refuses_a_kit_that_is_not_a_tool_checkout(tmp_path):
    for name in KIT_FILES:
        assert (KIT / name).exists(), name
    env = {**os.environ, "ARM": "fix", "OUT": "/nonexistent/out", "TREE": "/nonexistent/tree", "KIT": str(tmp_path), "LAUNCH_DRY_RUN": "1"}
    probe = subprocess.run(["bash", str(KIT / "death_closes_project_launch.sh")], env=env, capture_output=True, text=True)
    assert probe.returncode == 1 and "pinned_runner.py is missing" in probe.stdout


@pytest.mark.parametrize("arm,stage,extra,cells,plain", [("fix", "1", {}, 3, True), ("base", "1", {}, 3, False), ("fix", "smoke", {}, 1, True), ("fix", "widen", {"WIDEN": "urban_political"}, 4, True)])
def test_the_launcher_dry_run_lists_the_cells(arm, stage, extra, cells, plain):
    env = {**os.environ, "ARM": arm, "OUT": "/nonexistent/out", "TREE": "/nonexistent/tree", "KIT": str(REPO), "STAGE": stage, "LAUNCH_DRY_RUN": "1", **extra}
    out = subprocess.run(["bash", str(KIT / "death_closes_project_launch.sh")], env=env, capture_output=True, text=True)
    lines = [line for line in out.stdout.splitlines() if line.startswith("CELL ")]
    assert out.returncode == 0 and len(lines) == cells, out.stdout + out.stderr
    assert all(("plain then spy" in line) == plain for line in lines)
    if stage == "1":
        assert {line.split()[2] for line in lines} == {"crowded_frontier", "frontier_living_world", "urban_political"} and all(" s42 5000t" in line for line in lines)
    if stage == "widen":
        assert [line.split()[3] for line in lines] == ["s43", "s44", "s45", "s46"]


def test_a_used_tree_is_refused_and_the_widen_stage_needs_its_worlds():
    base = {**os.environ, "ARM": "base", "OUT": "/nonexistent/out", "KIT": str(REPO), "LAUNCH_DRY_RUN": "1"}
    used = subprocess.run(["bash", str(KIT / "death_closes_project_launch.sh")], env={**base, "TREE": "/mnt/data2/x/tree_995b"}, capture_output=True, text=True)
    assert used.returncode == 18
    widen = subprocess.run(["bash", str(KIT / "death_closes_project_launch.sh")], env={**base, "TREE": "/nonexistent/tree", "STAGE": "widen"}, capture_output=True, text=True)
    assert widen.returncode != 0
