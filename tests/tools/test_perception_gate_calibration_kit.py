"""The perception-gate calibration kit (tools/rpg_measure/perception_gate_calibration_*): the pure logic, the summarizer's verdicts, and the spy's gate wrapper on a REAL compiled catalog and bodies
(not hand-built dicts: the README lesson). Nothing here runs a kernel tick."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "tools" / "rpg_measure"


def _load(name):
    spec = importlib.util.spec_from_file_location(f"_pgc_test_{name}", TOOLS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


logic = _load("perception_gate_calibration_logic")
summary = _load("perception_gate_calibration_summary")
LEVELS_FIX = {"small": "medium_high", "medium": "high"}
LEVELS_BASE = {"small": "low", "medium": "medium"}


def test_size_levels_read_the_arms_own_record_else_the_old_map():
    assert logic.size_levels({"small": "medium_high", "medium": "high", "large": "very_high"}) == LEVELS_FIX
    assert logic.size_levels(None) == LEVELS_BASE


def test_a_vision_only_perception_of_a_still_small_body_by_day_is_the_first_non_vacuity_row():
    row = logic.classify_perception(True, ["visibility"], {"visibility": "medium_high", "noise": "low"}, False, LEVELS_FIX)
    assert row["vision_still_small_day"] and not row["vision_still_medium_night"] and row["channels"] == "visibility"


def test_a_vision_only_perception_of_a_still_medium_body_at_night_is_the_second():
    row = logic.classify_perception(True, ["visibility"], {"visibility": "high", "noise": "low"}, True, LEVELS_FIX)
    assert row["vision_still_medium_night"] and not row["vision_still_small_day"]


def test_a_moving_body_a_touch_or_an_unperceived_result_is_not_a_non_vacuity_row():
    assert not logic.classify_perception(True, ["visibility"], {"visibility": "medium_high", "noise": "medium"}, False, LEVELS_FIX)["vision_still_small_day"]
    assert not logic.classify_perception(True, ["visibility", "touch"], {"visibility": "medium_high", "noise": "low"}, False, LEVELS_FIX)["vision_still_small_day"]
    assert not logic.classify_perception(False, [], {"visibility": "medium_high", "noise": "low"}, False, LEVELS_FIX)["vision_still_small_day"]


def test_objective_starts_are_a_changed_objective_naming_a_body():
    hunt = {"id": "o1", "kind": "REACH_LOCATION", "project_kind": "hunger", "target_entity_id": 7}
    fight = {"id": "o2", "kind": "defeat_enemy", "project_kind": "combat_engage", "target_entity_id": 7}
    assert logic.objective_started(None, hunt) == "hunt" and logic.objective_started("o0", fight) == "engagement"
    assert logic.objective_started("o1", hunt) is None  # not a change
    assert logic.objective_started(None, {**hunt, "target_entity_id": None}) is None  # names no body
    assert logic.objective_started(None, None) is None


def test_the_counters_report_what_was_fed():
    c = logic.Counters()
    c.gate(logic.classify_perception(True, ["visibility"], {"visibility": "medium_high", "noise": "low"}, False, LEVELS_FIX))
    c.gate(logic.classify_perception(False, [], {}, True, LEVELS_FIX))
    c.started("hunt"); c.started("engagement"); c.started(None)
    r = c.report()
    assert (r["gate_calls"], r["perceived"], r["vision_still_small_day"], r["hunts_started"], r["engagements_started"]) == (2, 1, 1, 1, 1)
    assert r["by_channel"] == {"visibility": 1}


# --- the summarizer's verdicts -------------------------------------------------------------------------------------------------------------

def _cell(hash_plain="h", hash_spy="h", wall=0.01, levels=None, **spy_over):
    spy = {"final_hash": hash_spy, "wall_per_tick": wall, "fatal": None, "logging_errors": [], "spy_exceptions": [], "findings": [], "replay_dirs_redirected": 1, "perceived": 10,
           "hunts_started": 3, "engagements_started": 2, "bodies_hit": 5, "vision_still_small_day": 4, "vision_still_medium_night": 2, "by_channel": {"visibility": 10},
           "sampled": {"hostile_pairs": 6, "prey_pairs": 4}, "size_levels": dict(levels or LEVELS_FIX)}
    spy.update(spy_over)
    plain = {"final_hash": hash_plain, "wall_per_tick": wall, "fatal": None, "logging_errors": [], "findings": [], "replay_dirs_redirected": 1}
    return {"plain": plain, "spy": spy}


def _base(**kw):
    return _cell(levels=LEVELS_BASE, **kw)


def test_a_clean_pair_of_arms_passes_with_exit_0():
    lines, code = summary.render({"c": _base()}, {"c": _cell()})
    assert code == 0 and not [l for l in lines if l.startswith(("HARD", "STOP", "PERF", "NOT"))]


def test_a_spy_hash_that_differs_from_its_plain_twin_is_a_hard_failure_h1():
    _, code = summary.render({"c": _base()}, {"c": _cell(hash_spy="x")})
    assert code == 2
    _, code = summary.render({"c": _base(hash_spy="x")}, {"c": _cell()})
    assert code == 2  # the base arm's twin too


def test_a_collapse_to_zero_on_the_fix_arm_is_a_stop():
    lines, code = summary.render({"c": _base()}, {"c": _cell(hunts_started=0)})
    assert code == 4 and any(l.startswith("STOP (collapse to 0)") and "hunts_started" in l for l in lines)


def test_a_zero_that_is_also_zero_on_the_base_is_not_a_collapse():
    _, code = summary.render({"c": _base(engagements_started=0)}, {"c": _cell(engagements_started=0)})
    assert code == 0


def test_the_non_vacuity_total_is_printed_and_a_zero_cell_is_fine_while_another_is_above_zero():
    lines, code = summary.render({"a": _base(), "b": _base()}, {"a": _cell(vision_still_small_day=0, vision_still_medium_night=0), "b": _cell()})
    assert code == 0 and any(l.startswith("NON-VACUITY total") and "small_day 4" in l for l in lines)
    assert not any(l.startswith("NOT MEASURED") for l in lines)


def test_zero_non_vacuity_rows_in_every_cell_is_not_measured_not_a_pass():
    lines, code = summary.render({"c": _base()}, {"c": _cell(vision_still_small_day=0, vision_still_medium_night=0)})
    assert code == 0 and any(l.startswith("NOT MEASURED") for l in lines)


def test_a_wall_per_tick_ratio_over_1_10_is_a_perf_flag_not_a_failure():
    lines, code = summary.render({"c": _base(wall=0.010)}, {"c": _cell(wall=0.0125)})
    assert code == 0 and any(l.startswith("PERF FLAG") and "1.250" in l for l in lines)


def test_b3_the_arms_size_levels_must_be_their_own_records():
    """The fix arm must read the calibration record, the base arm the 02a map: a fix arm that fell back to the 02a map is a HARD failure, not a silent NOT MEASURED."""
    _, code = summary.render({"c": _base()}, {"c": _cell(levels=LEVELS_BASE)})
    assert code == 2
    _, code = summary.render({"c": _cell(levels=LEVELS_FIX)}, {"c": _cell()})
    assert code == 2


def test_b3_a_fix_arm_that_never_saw_a_settings_record_is_a_finding_a_base_arm_is_not():
    assert logic.settings_finding("fix", 100, 0) is not None
    assert logic.settings_finding("fix", 100, 100) is None
    assert logic.settings_finding("base", 100, 0) is None
    assert logic.settings_finding("fix", 0, 0) is None  # no gate call at all is a different failure (the run is void for other reasons)


def test_b2_a_hunger_hunt_is_a_hunt_whatever_its_objective_kind_and_an_engagement_is_a_defeat_enemy():
    """A hunger project's hunt objective names its prey with the kind REACH_LOCATION (ac759e0ba intelligence.py:1500 / scorers.py:118-120); the project kind decides, so even a DEFEAT_ENEMY objective
    inside a hunger project is a hunt and the hunt STOP cannot be starved. Real enums, real project shape."""
    from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus

    def started(project_kind, objective_kind):
        obj = ObjectiveState(id="o", kind=objective_kind, target="7", target_entity_id=7, status=ObjectiveStatus.ACTIVE)
        proj = ProjectState(id="p", kind=project_kind, status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id="o")
        entity = SimpleNamespace(strategic=SimpleNamespace(current_objective_id="o", current_project_id="p", projects={"p": proj}))
        return logic.objective_started(None, _spy_mod().current_objective(entity))

    assert started(GoalKind.HUNGER, ObjectiveKind.REACH_LOCATION) == "hunt"  # the real shape of a hunt
    assert started(GoalKind.HUNGER, ObjectiveKind.DEFEAT_ENEMY) == "hunt"  # the project kind first
    assert started(GoalKind.COMBAT_ENGAGE, ObjectiveKind.DEFEAT_ENEMY) == "engagement"  # the combat scorer's shape
    assert started(GoalKind.COMBAT_ENGAGE, ObjectiveKind.REACH_LOCATION) is None


def _spy_mod():
    return _load("perception_gate_calibration_spy")


# --- the spy's gate wrapper on a REAL compiled catalog and bodies ----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def real():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def _body(species_id):
    return SimpleNamespace(kind=species_id, identity=SimpleNamespace(properties={"species_id": species_id}), navigation=SimpleNamespace(lodged_in=None, last_moved_tick=None),
                           task=SimpleNamespace(work_kind="", payload={}), combat=SimpleNamespace(alive=True))


def test_the_spy_counts_the_ticket_rows_through_the_real_gate(real):
    """On the shipped catalog a still goblin (small) seen by day, and a still human (medium) seen at night, move the non-vacuity rows; on an arm without the calibration record the base levels are used."""
    spy_mod = _load("perception_gate_calibration_spy")
    from src.engine.perception_signals import emitted_signals
    from src.world.perception.gate import PerceptionGate

    class Apply:  # the spy patches apply_generation as well; a stand-in suffices for this unit
        @staticmethod
        def apply_generation(prior, update, *a, **k):
            return prior

    spy = spy_mod.CalibrationSpy(logic, PerceptionGate, Apply).install()
    try:
        gate = PerceptionGate(real)
        sizes = gate.settings.size_visibility
        goblin = emitted_signals(_body("goblin"), real.get_body_model(real.get_species("goblin").body_model), None, sizes)
        human = emitted_signals(_body("human"), real.get_body_model(real.get_species("human").body_model), None, sizes)
        gate.can_perceive(_body("human"), goblin, {"distance": 3.0, "night": False})
        gate.can_perceive(_body("human"), human, {"distance": 2.0, "night": True})
    finally:
        spy.restore()
    report = spy.report()
    assert report["vision_still_small_day"] >= 1 and report["vision_still_medium_night"] >= 1 and report["spy_exceptions"] == [] and report["settings_seen"] >= 2
    assert report["size_levels"] == LEVELS_FIX
    assert PerceptionGate.can_perceive.__name__ == "can_perceive"  # restored to the original


def test_b1_a_sample_only_run_leaves_the_gate_counters_at_zero(real):
    """The spy's own sampling queries reach the wrapped gate through appraisal.perceives; they must not be counted as the run's perceptions (nor feed the non-vacuity rows)."""
    from tests.helpers.scenario import compile_world
    from src.engine.perception_signals import emitted_signals  # noqa: F401  (the compiled world builds the bodies)
    from src.world.perception.gate import PerceptionGate

    spy_mod = _spy_mod()
    state = compile_world("frontier_living_world", 42)

    class Apply:
        @staticmethod
        def apply_generation(prior, update, *a, **k):
            return prior

    spy = spy_mod.CalibrationSpy(logic, PerceptionGate, Apply).install()
    try:
        spy.sample(state)  # real compiled bodies; every pair goes through the real gate
    finally:
        spy.restore()
    report = spy.report()
    assert report["sampled"]["samples"] == 1
    assert report["gate_calls"] == 0 and report["perceived"] == 0 and report["vision_still_small_day"] == 0 and report["vision_still_medium_night"] == 0 and report["spy_exceptions"] == []
