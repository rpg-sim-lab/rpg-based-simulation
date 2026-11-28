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

def _cell(hash_plain="h", hash_spy="h", wall=0.01, **spy_over):
    spy = {"final_hash": hash_spy, "wall_per_tick": wall, "fatal": None, "logging_errors": [], "spy_exceptions": [], "findings": [], "replay_dirs_redirected": 1, "perceived": 10,
           "hunts_started": 3, "engagements_started": 2, "hits_landed": 5, "vision_still_small_day": 4, "vision_still_medium_night": 2, "by_channel": {"visibility": 10},
           "sampled": {"hostile_pairs": 6, "prey_pairs": 4}}
    spy.update(spy_over)
    plain = {"final_hash": hash_plain, "wall_per_tick": wall, "fatal": None, "logging_errors": [], "findings": [], "replay_dirs_redirected": 1}
    return {"plain": plain, "spy": spy}


def test_a_clean_pair_of_arms_passes_with_exit_0():
    lines, code = summary.render({"c": _cell()}, {"c": _cell()})
    assert code == 0 and not [l for l in lines if l.startswith(("HARD", "STOP", "PERF", "NOT"))]


def test_a_spy_hash_that_differs_from_its_plain_twin_is_a_hard_failure_h1():
    _, code = summary.render({"c": _cell()}, {"c": _cell(hash_spy="x")})
    assert code == 2


def test_a_collapse_to_zero_on_the_fix_arm_is_a_stop():
    lines, code = summary.render({"c": _cell()}, {"c": _cell(hunts_started=0)})
    assert code == 4 and any(l.startswith("STOP (collapse to 0)") and "hunts_started" in l for l in lines)


def test_a_zero_that_is_also_zero_on_the_base_is_not_a_collapse():
    _, code = summary.render({"c": _cell(engagements_started=0)}, {"c": _cell(engagements_started=0)})
    assert code == 0


def test_an_empty_non_vacuity_row_is_not_measured_not_a_pass():
    lines, code = summary.render({"c": _cell()}, {"c": _cell(vision_still_small_day=0, vision_still_medium_night=0)})
    assert code == 0 and any(l.startswith("NOT MEASURED") for l in lines)


def test_a_wall_per_tick_ratio_over_1_10_is_a_perf_flag_not_a_failure():
    lines, code = summary.render({"c": _cell(wall=0.010)}, {"c": _cell(wall=0.0125)})
    assert code == 0 and any(l.startswith("PERF FLAG") and "1.250" in l for l in lines)


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
    assert report["vision_still_small_day"] >= 1 and report["vision_still_medium_night"] >= 1 and report["spy_exceptions"] == []
    assert PerceptionGate.can_perceive.__name__ == "can_perceive"  # restored to the original
