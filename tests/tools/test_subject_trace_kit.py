"""Planted controls for the subject trace kit (tools/rpg_measure/subject_trace_*): the pass-through legality wrapper, the window bounds, the subject derivation from a synthetic sealed cell, the cell checks
(0 rows, no legality call on NEW s42, a hash mismatch, a spy exception) and the launcher's record step from a cwd outside the kit. Each control was mutation-checked: disabling the check it guards makes it fail."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

import pytest

from tests.tools.test_person_attack_kit import row
from tools.rpg_measure import person_attack_summary as summary
from tools.rpg_measure import subject_trace_run as run
from tools.rpg_measure import subject_trace_spy as spy_module

ROOT = Path(__file__).resolve().parents[2]
LAUNCH = ROOT / "tools" / "rpg_measure" / "subject_trace_launch.sh"


# --------------------------------------------------------------------------------------------- fakes
def entity(eid: int, position: tuple = (0.0, 0.0), mode: str = "WANDER", target: Optional[tuple] = None, readiness: float = 100.0, hp: int = 50, alive: bool = True,
           payload: Optional[Dict[str, Any]] = None, failure: Optional[str] = None) -> Any:
    return SimpleNamespace(id=eid, navigation=SimpleNamespace(position=position, target=target, path=[], movement_mode=SimpleNamespace(value=mode), last_failure_reason=failure, lodged_in=None),
                           combat=SimpleNamespace(readiness=readiness, hp=hp, alive=alive), task=SimpleNamespace(work_kind="ENTITY_ACT", payload=payload or {}),
                           strategic=SimpleNamespace(current_project_id=None, current_objective_id=None, projects={}))


def state(tick: int, *entities: Any) -> Any:
    return SimpleNamespace(tick=tick, entities={e.id: e for e in entities})


def subject(eid: int, windows: List[List[int]], counterparts: Optional[List[int]] = None, roles: Optional[List[str]] = None) -> Dict[str, Any]:
    return {"id": eid, "roles": roles or ["victim"], "windows": windows, "counterparts": counterparts or []}


class FakeApply:
    @staticmethod
    def apply_generation(prior, update, *args, **kwargs):
        return update


class FakeLegality:
    result = (False, SimpleNamespace(name="OUT_OF_RANGE", value="target out of range"))

    @staticmethod
    def verify_attack_legality(attacker, target, state_or_context, is_opportunity_attack=False, *, night=None):
        return FakeLegality.result


# --------------------------------------------------------------------------------------------- the legality wrapper
def test_the_legality_wrapper_returns_the_original_result_object_and_records_only_a_subject_attacker_in_its_window() -> None:
    original = FakeLegality.verify_attack_legality
    spy = spy_module.SubjectSpy([subject(7, [[100, 200]])]).install(FakeApply, FakeLegality)
    try:
        in_window = FakeLegality.verify_attack_legality(entity(7), entity(8), state(150))
        assert in_window is FakeLegality.result                                             # the SAME object: pass-through
        FakeLegality.verify_attack_legality(entity(7), entity(8), state(150), True)         # an opportunity attack
        FakeLegality.verify_attack_legality(entity(8), entity(7), state(150))               # the subject is the TARGET: not recorded
        FakeLegality.verify_attack_legality(entity(9), entity(8), state(150))               # not a subject: not recorded
        FakeLegality.verify_attack_legality(entity(7), entity(8), state(300))               # outside the window: not recorded
    finally:
        spy.restore()
    assert [(r["attacker_id"], r["target_id"], r["tick"], r["tick_source"], r["opportunity"], r["legal"], r["reason"], r["failure_text"]) for r in spy.legality_rows] == [
        (7, 8, 150, "context", False, False, "OUT_OF_RANGE", "target out of range"), (7, 8, 150, "context", True, False, "OUT_OF_RANGE", "target out of range")]      # CHANGED (S1): no more in_window null row
    assert FakeLegality.verify_attack_legality.__func__ is original.__func__ if hasattr(FakeLegality.verify_attack_legality, "__func__") else FakeLegality.verify_attack_legality is original


def test_a_legal_result_is_recorded_without_a_failure_text() -> None:
    legal = (True, SimpleNamespace(name="OK", value="ok"))
    FakeLegality.result = legal
    spy = spy_module.SubjectSpy([subject(7, [[0, 10]])]).install(FakeApply, FakeLegality)
    try:
        assert FakeLegality.verify_attack_legality(entity(7), entity(8), state(5)) is legal
    finally:
        spy.restore()
        FakeLegality.result = (False, SimpleNamespace(name="OUT_OF_RANGE", value="target out of range"))
    assert spy.legality_rows[0]["legal"] is True and spy.legality_rows[0]["failure_text"] is None


# --------------------------------------------------------------------------------------------- S1: the legality tick
def clock_state(tick: int, world_time: int, *entities: Any) -> Any:
    return SimpleNamespace(tick=tick, world_time=world_time, entities={e.id: e for e in entities})


def test_a_context_without_a_tick_gets_world_time_plus_the_offset_and_an_out_of_window_call_is_dropped() -> None:     # NEW (S1)
    spy = spy_module.SubjectSpy([subject(7, [[100, 110]])]).install(FakeApply, FakeLegality)
    try:
        spy.observe(clock_state(99, 89), clock_state(100, 90))                              # offset = tick - world_time = 10
        FakeLegality.verify_attack_legality(entity(7), entity(8), SimpleNamespace(world_time=95))      # derived tick 105: in the window
        FakeLegality.verify_attack_legality(entity(7), entity(8), SimpleNamespace(world_time=120))     # derived tick 130: dropped
        FakeLegality.verify_attack_legality(entity(7), entity(8), SimpleNamespace(world_time=95, tick=108))      # the context's own tick wins
    finally:
        spy.restore()
    assert [(r["tick"], r["tick_source"], r["world_time"]) for r in spy.legality_rows] == [(105, "world_time+offset", 95), (108, "context", 95)]
    assert spy.report()["legality_calls_in_window"] == 2 and spy.report()["offset_drift"] is False


def test_a_call_with_neither_tick_nor_world_time_raises_in_the_original_and_passes_through_or_is_a_spy_exception() -> None:     # NEW (S1)
    class NeedsTheClock:
        @staticmethod
        def verify_attack_legality(attacker, target, state_or_context, is_opportunity_attack=False, *, night=None):
            raise TypeError("verify_attack_legality: the state or context has no world_time")      # what the real engine does (legality.py:39)

    spy = spy_module.SubjectSpy([subject(7, [[0, 10]])]).install(FakeApply, NeedsTheClock)
    try:
        with pytest.raises(TypeError, match="no world_time"):
            NeedsTheClock.verify_attack_legality(entity(7), entity(8), SimpleNamespace())
    finally:
        spy.restore()
    assert spy.spy_exceptions == [] and spy.legality_rows == []                       # the engine's own error passes through; it is not the spy's
    lenient = spy_module.SubjectSpy([subject(7, [[0, 10]])]).install(FakeApply, FakeLegality)
    try:
        with pytest.raises(RuntimeError, match="neither tick nor world_time"):         # an original that does NOT raise leaves a call the spy cannot place: fatal
            FakeLegality.verify_attack_legality(entity(7), entity(8), SimpleNamespace())
    finally:
        lenient.restore()
    assert len(lenient.spy_exceptions) == 1


def test_out_of_window_and_unplaced_calls_never_meet_reach() -> None:     # NEW (S1)
    spy = spy_module.SubjectSpy([subject(7, [[100, 110]])]).install(FakeApply, FakeLegality)
    try:
        FakeLegality.verify_attack_legality(entity(7), entity(8), SimpleNamespace(world_time=5))          # no apply seen yet: no offset, unplaced
        spy.observe(clock_state(99, 99), clock_state(100, 100))
        FakeLegality.verify_attack_legality(entity(7), entity(8), SimpleNamespace(tick=500))               # out of window
    finally:
        spy.restore()
    doc = spy.report()
    assert (doc["legality_calls_in_window"], doc["legality_calls_unplaced"], doc["legality_call_count"]) == (0, 1, 0)
    assert run.check_cell({**good_spy(), **doc, "row_count": 30}, PLAIN, "new", 42)["reasons"] == ["VOID: NEW s42 has no legality call by any subject in its window"]


def test_a_non_constant_offset_is_drift_and_voids_the_cell() -> None:     # NEW (S1)
    steady = spy_module.SubjectSpy([subject(7, [[0, 100]])])
    steady.observe(clock_state(4, 3), clock_state(5, 4))
    steady.observe(clock_state(5, 4), clock_state(6, 5))
    assert steady.report()["offset_drift"] is False and steady.report()["offsets_seen"] == [1]
    drifting = spy_module.SubjectSpy([subject(7, [[0, 100]])])
    drifting.observe(clock_state(4, 3), clock_state(5, 4))
    drifting.observe(clock_state(5, 4), clock_state(6, 4))             # world_time stalled: the offset moved
    doc = drifting.report()
    assert doc["offset_drift"] is True and doc["offsets_seen"] == [1, 2]
    assert run.check_cell({**good_spy(), "offset_drift": True}, PLAIN, "new", 45)["reasons"][0].startswith("OFFSET_DRIFT")
    assert run.check_cell({**good_spy(), "offset_drift": False}, PLAIN, "new", 45)["valid"] is True


# --------------------------------------------------------------------------------------------- the per-tick rows
def test_a_tick_row_has_before_and_after_fields_and_chebyshev_distances_to_counterparts_and_the_goal_tile() -> None:
    spy = spy_module.SubjectSpy([subject(7, [[10, 20]], counterparts=[8])])
    prior = state(10, entity(7, (0.0, 0.0), "WANDER", target=(5.0, 1.0), payload={"reason": "REGROUP", "target_position": (5.0, 1.0)}), entity(8, (3.0, 4.0)))
    after = state(11, entity(7, (1.0, 0.0), "REGROUP", target=(5.0, 1.0), readiness=40.0, hp=30, failure="blocked", payload={"reason": "REGROUP"}), entity(8, (3.0, -1.0)))
    spy.observe(prior, state(9, entity(7)))                      # tick 9: outside the window, no row
    spy.observe(prior, after)                                     # tick 11: inside
    assert len(spy.rows) == 1
    got = spy.rows[0]
    assert (got["tick"], got["before"]["mode"], got["after"]["mode"], got["after"]["reason"], got["after"]["failure_reason"], got["after"]["readiness"], got["after"]["hp"]) == (11, "WANDER", "REGROUP", "REGROUP", "blocked", 40.0, 30)
    assert got["before"]["goal_tile"] == [5.0, 1.0] and got["before"]["payload"]["target_position"] == [5.0, 1.0]
    assert (got["distance_before"], got["distance_after"]) == ({"8": 4.0}, {"8": 2.0})     # (0,0)-(3,4) = 4; (1,0)-(3,-1) = 2
    assert (got["goal_distance_before"], got["goal_distance_after"]) == (5.0, 4.0)


# --------------------------------------------------------------------------------------------- the spy's own exception is fatal
def test_an_exception_in_the_recording_code_is_stored_and_reraised_even_when_the_kernel_would_swallow_it() -> None:
    spy = spy_module.SubjectSpy([subject(7, [[0, 100]])]).install(FakeApply, FakeLegality)
    try:
        broken = SimpleNamespace(tick=5, entities={7: SimpleNamespace(id=7)})                 # a body without the fields: the snapshot raises
        with pytest.raises(AttributeError):
            FakeApply.apply_generation(broken, broken)
    finally:
        spy.restore()
    assert len(spy.spy_exceptions) == 1 and "AttributeError" in spy.spy_exceptions[0]
    assert spy.report()["spy_exceptions"] == spy.spy_exceptions


# --------------------------------------------------------------------------------------------- window bounds
def test_the_window_runs_from_the_first_hit_minus_100_to_end_plus_100_and_clamps_at_zero() -> None:     # CHANGED (combined scope): death now gets the +100 padding too
    assert run.padded_window(1901, 2610) == [1801, 2710]
    assert run.padded_window(40, 90) == [0, 190]
    assert run.merge_windows([[10, 20], [21, 30], [50, 60], [55, 70]]) == [[10, 30], [50, 70]]


# --------------------------------------------------------------------------------------------- subject derivation from a synthetic stage-1 cell
def hits(attacker: int, victim: int, start: int, n: int, step: int = 5, **kw: Any) -> List[Dict[str, Any]]:
    return [row(start + i * step, attacker=attacker, victim=victim, **kw) for i in range(n)]


def sealed_cell(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"rows": rows, "mode_rows": [], "final_tick": 5000, "attack_rows": []}


def derive(rows: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    return {s["id"]: s for s in run.derive_subjects({42: sealed_cell(rows)}, summary)["42"]}


DECIDING = {"victim_attacked_same_tick": True}      # a decision on every hit: no R7 chain, only the hit count decides


def test_derivation_a_nine_hit_engagement_is_out_and_a_ten_hit_one_is_in_with_its_attacker() -> None:
    ids = derive(hits(1, 100, 2000, 10, step=40, **DECIDING) + hits(2, 200, 4000, 9, step=40, **DECIDING))
    assert sorted(ids) == [1, 100] and ids[100]["roles"] == ["victim"] and ids[1]["roles"] == ["attacker"] and ids[100]["counterparts"] == [1] and ids[1]["counterparts"] == [100]


def test_derivation_takes_a_chain_victim_with_fewer_than_ten_hits_and_its_attackers() -> None:
    rows = hits(2, 200, 3000, 5, step=2) + hits(3, 300, 4000, 2)             # five hits in a row with no decision: an R7 chain; two hits: nobody
    got = derive(rows)
    assert sorted(got) == [2, 200] and got[200]["roles"] == ["chain_victim"] and got[2]["roles"] == ["attacker"]
    asleep = derive(hits(2, 200, 3000, 3, step=40, victim_asleep_before=True, **DECIDING))     # an asleep run of 3: a chain, whatever the decisions
    assert sorted(asleep) == [2, 200]


def test_derivation_window_ends_at_the_death_tick_plus_100_or_at_the_last_hit_plus_100() -> None:
    lived = hits(1, 100, 2000, 10, step=40, **DECIDING) + [row(2390, attacker=1, victim=100, hit=False, **DECIDING)]     # a trailing MISS 30 ticks after the last hit: the engagement ends there, the last HIT does not
    assert derive(lived)[100]["windows"] == [[1900, 2360 + 100]]                      # last hit at 2000 + 9 * 40 = 2360
    killed = hits(1, 100, 2000, 11, step=40, **DECIDING)
    killed[7] = {**killed[7], "victim_alive_after": False}                            # dies at 2280, later hits are rows of a dead body
    assert derive(killed)[100]["windows"] == [[1900, 2280 + 100]]                     # END = the death tick, not the last hit
    assert derive(killed)[1]["windows"] == [[1900, 2380]]                             # the attacker keeps the same padded window


def test_a_new_victim_inside_the_padding_is_not_a_subject() -> None:
    rows = hits(1, 100, 2000, 10, step=40, **DECIDING) + [row(2400, attacker=1, victim=400, **DECIDING)]       # attacker 1 hits another victim 40 ticks after the engagement: inside the padding
    assert sorted(derive(rows)) == [1, 100]


def test_derive_subjects_is_pure_and_reports_the_seeds_that_have_a_subject(tmp_path: Path) -> None:
    cells = {42: sealed_cell(hits(1, 100, 2000, 10, step=40, **DECIDING)), 45: sealed_cell(hits(3, 300, 4000, 2))}
    before = json.dumps(cells, sort_keys=True)
    out = run.derive_subjects(cells, summary)
    assert json.dumps(cells, sort_keys=True) == before and sorted(out) == ["42", "45"] and out["45"] == [] and [s["id"] for s in out["42"]] == [1, 100]


def test_the_plan_records_the_sha256_of_every_sealed_cell_it_read_lists_the_seeds_with_subjects_and_is_deterministic(tmp_path: Path) -> None:
    cells = tmp_path / "cells"
    cells.mkdir()
    (cells / "new__w__s42__spy.json").write_text(json.dumps(sealed_cell(hits(1, 100, 2000, 10, step=40, **DECIDING))), encoding="utf-8")
    (cells / "new__w__s45__spy.json").write_text(json.dumps(sealed_cell([])), encoding="utf-8")
    for arm in ("new", "base"):
        for seed in (42, 45):
            (cells / f"{arm}__w__s{seed}__plain.json").write_text(json.dumps({"final_hash": arm}), encoding="utf-8")
    first = run.derive_plan(cells, "w", [42, 45], summary)
    assert first == run.derive_plan(cells, "w", [42, 45], summary) and first["seeds_with_subjects"] == [42]
    assert len(first["derived_from"]) == 6 and all(len(v) == 64 for v in first["derived_from"].values())
    (cells / "new__w__s42__plain.json").write_text(json.dumps({"final_hash": "changed"}), encoding="utf-8")
    assert run.derive_plan(cells, "w", [42, 45], summary)["plan_sha256"] != first["plan_sha256"]       # the sealed inputs are part of the plan's identity


# --------------------------------------------------------------------------------------------- S2: every qualifying chain
def states_of(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return summary.hit_states(rows, [])


def test_two_chains_on_one_victim_give_both_windows_and_both_sets_of_wolves() -> None:     # NEW (S2)
    rows = hits(1, 100, 1000, 5, step=5) + hits(2, 100, 3000, 6, step=5)               # 5 hits at t1000-1020 by wolf 1, 6 hits at t3000-3025 by wolf 2, no decisions
    got = derive(rows)
    assert got[100]["windows"] == [[900, 1120], [2900, 3125]] and got[100]["counterparts"] == [1, 2] and got[100]["roles"] == ["chain_victim"]
    assert got[1]["windows"] == [[900, 1120]] and got[2]["windows"] == [[2900, 3125]]    # each wolf is a subject in ITS chain's window only


def test_a_four_hit_run_gives_nothing_and_five_gives_one_chain() -> None:     # NEW (S2)
    assert run.chain_runs(states_of(hits(1, 100, 1000, 4, step=5))) == {"no_decision_run": [], "asleep_or_lodged_run": []}
    assert derive(hits(1, 100, 1000, 4, step=5)) == {}
    five = run.chain_runs(states_of(hits(1, 100, 1000, 5, step=5)))["no_decision_run"]
    assert [(c["run"], c["start_tick"], c["end_tick"], c["attackers"]) for c in five] == [(5, 1000, 1020, [1])]


def test_a_gap_of_51_ticks_makes_two_chains_and_a_gap_of_50_makes_one() -> None:     # NEW (S2)
    split = hits(1, 100, 1000, 5, step=5) + hits(1, 100, 1071, 5, step=5)               # last hit 1020, next 1071: gap 51
    joined = hits(1, 100, 1000, 5, step=5) + hits(1, 100, 1070, 5, step=5)              # gap 50
    assert [c["run"] for c in run.chain_runs(states_of(split))["no_decision_run"]] == [5, 5]
    assert [c["run"] for c in run.chain_runs(states_of(joined))["no_decision_run"]] == [10]


def test_the_chain_helpers_longest_run_agrees_with_hit_chains() -> None:     # NEW (S2)
    fixtures = [
        hits(1, 100, 1000, 5, step=5),
        hits(1, 100, 1000, 5, step=5) + hits(2, 100, 3000, 7, step=5),
        hits(1, 100, 1000, 6, step=5) + hits(1, 100, 1071, 5, step=5),
        hits(1, 100, 1000, 3, step=5, victim_asleep_before=True) + hits(1, 100, 1100, 1, step=5) + hits(1, 100, 1130, 4, step=5, victim_asleep_before=True),
        hits(1, 100, 1000, 8, step=5, victim_attacked_same_tick=False)[:4] + [row(1030, attacker=1, victim=100, victim_mode_after="RETREAT")] + hits(1, 100, 1040, 6, step=5),
    ]
    for rows in fixtures:
        worst = summary.hit_chains(rows, [])
        found = run.chain_runs(states_of(rows))
        for key in ("no_decision_run", "asleep_or_lodged_run"):
            longest = max((c["run"] for c in found[key]), default=0)
            assert longest == (worst[key]["run"] if worst[key]["run"] >= (5 if key == "no_decision_run" else 3) else 0), (key, rows[0]["tick"], longest, worst[key])


# --------------------------------------------------------------------------------------------- rows after death, the legality wrap, the stage-1 seal
def test_a_subject_keeps_getting_rows_after_it_dies_and_after_it_is_removed() -> None:
    spy = spy_module.SubjectSpy([subject(7, [[0, 100]])])
    alive, dead = entity(7), entity(7, alive=False, hp=0)
    spy.observe(state(5, alive), state(6, dead))                 # dies on this apply
    spy.observe(state(6, dead), state(7, dead))                  # still in the world, dead
    spy.observe(state(7, dead), state(8))                        # removed: absent
    assert [(r["tick"], r["before"]["state"], r["after"]["state"]) for r in spy.rows] == [(6, "ALIVE", "DEAD"), (7, "DEAD", "DEAD"), (8, "DEAD", "ABSENT")]
    assert spy.rows[0]["after"]["alive"] is False and spy_module.snapshot(None) == {"present": False, "state": "ABSENT"}


@pytest.mark.parametrize("result", [(True, SimpleNamespace(name="OK", value="ok")), (False, SimpleNamespace(name="OUT_OF_RANGE", value="far"))], ids=["true", "false"])
def test_the_legality_wrap_passes_true_and_false_through_unchanged(result: Any) -> None:
    saved = FakeLegality.result
    FakeLegality.result = result
    spy = spy_module.SubjectSpy([subject(7, [[0, 10]])]).install(FakeApply, FakeLegality)
    try:
        assert FakeLegality.verify_attack_legality(entity(7), entity(8), state(5)) is result
    finally:
        spy.restore()
        FakeLegality.result = saved
    assert spy.legality_rows[0]["legal"] is result[0]


def test_the_legality_wrap_passes_an_exception_of_the_original_through_unchanged_and_it_is_not_a_spy_exception() -> None:
    class Exploding:
        @staticmethod
        def verify_attack_legality(attacker, target, state_or_context, is_opportunity_attack=False, *, night=None):
            raise KeyError("the engine's own error")

    spy = spy_module.SubjectSpy([subject(7, [[0, 10]])]).install(FakeApply, Exploding)
    try:
        with pytest.raises(KeyError, match="the engine's own error"):
            Exploding.verify_attack_legality(entity(7), entity(8), state(5))
    finally:
        spy.restore()
    assert spy.spy_exceptions == [] and spy.legality_rows == []


def test_stage_2_refuses_to_start_when_the_stage_1_seal_does_not_match(tmp_path: Path) -> None:
    stage1 = tmp_path / "stage1"
    (stage1 / "cells").mkdir(parents=True)
    (stage1 / "SHA256SUMS").write_text("abc  ./x\n", encoding="utf-8")
    good = hashlib.sha256((stage1 / "SHA256SUMS").read_bytes()).hexdigest()
    (stage1 / "SHA256SUMS.seal.log").write_text(f"SEAL {good} 10:00:00\n", encoding="utf-8")
    assert run.seal_matches(stage1)["ok"] is True
    (stage1 / "SHA256SUMS").write_text("abc  ./x\nextra  ./y\n", encoding="utf-8")      # a file added to the sealed set after the seal
    assert run.seal_matches(stage1)["ok"] is False
    env = launcher_env(tmp_path, SEALED=str(stage1 / "cells"))
    done = subprocess.run(["bash", str(LAUNCH), str(env), "GO-1", "cells"], capture_output=True, text=True, cwd=tmp_path)
    log = (tmp_path / "out" / "cells" / "launcher.log").read_text(encoding="utf-8")
    assert done.returncode == 3 and "the stage-1 seal does not match" in log and "TREE" not in log        # aborted BEFORE any tree or process check


# --------------------------------------------------------------------------------------------- the cell checks
def good_spy(**kw: Any) -> Dict[str, Any]:
    return {"final_hash": "H", "ticks": 5000, "row_count": 30, "legality_calls_in_window": 4, "spy_exceptions": [], "fatal": None, **kw}


PLAIN = {"final_hash": "H", "ticks": 5000}


def test_a_clean_cell_is_valid_and_a_hash_mismatch_is_a_perturbation_failure() -> None:
    assert run.check_cell(good_spy(), PLAIN, "new", 42)["valid"] is True
    bad = run.check_cell(good_spy(final_hash="X"), PLAIN, "new", 42)
    assert bad["valid"] is False and bad["reasons"] == ["PERTURBATION: the spy's final hash differs from the sealed plain twin's"]
    assert run.check_cell(good_spy(ticks=2000), PLAIN, "new", 42)["valid"] is False


def test_a_cell_with_no_subject_rows_is_void() -> None:
    voided = run.check_cell(good_spy(row_count=0), PLAIN, "base", 45)
    assert voided["valid"] is False and voided["reasons"] == ["VOID: 0 subject rows in the windows"]


def test_new_s42_with_no_legality_call_is_void_but_the_other_cells_do_not_need_one() -> None:
    assert run.check_cell(good_spy(legality_calls_in_window=0), PLAIN, "new", 42)["valid"] is False
    for arm, seed in (("new", 45), ("base", 42), ("base", 45)):
        assert run.check_cell(good_spy(legality_calls_in_window=0), PLAIN, arm, seed)["valid"] is True


def test_a_spy_exception_makes_the_cell_void() -> None:
    assert run.check_cell(good_spy(spy_exceptions=["Traceback ..."]), PLAIN, "new", 45)["reasons"] == ["SPY_EXCEPTION (fatal)"]
    assert run.check_cell(good_spy(fatal="Traceback ..."), PLAIN, "new", 45)["valid"] is False


def test_check_all_reads_the_sealed_plain_twins_and_marks_a_missing_file_void(tmp_path: Path) -> None:
    cells, sealed = tmp_path / "cells", tmp_path / "sealed"
    cells.mkdir()
    sealed.mkdir()
    items = run.items_for("cells", "w", [42, 45], 5000)
    for item in items[:3]:
        (cells / f"{item['name']}.json").write_text(json.dumps(good_spy()), encoding="utf-8")
        (sealed / f"{run.cell_name(item['arm'], 'w', item['seed'], 'plain')}.json").write_text(json.dumps(PLAIN), encoding="utf-8")
    verdict = run.check_all(cells, sealed, "w", items)
    assert [k for k, v in verdict["cells"].items() if not v["valid"]] == ["base/s45"] and verdict["all_valid"] is False


# --------------------------------------------------------------------------------------------- the launcher
def launcher_env(tmp_path: Path, **extra: str) -> Path:
    env = tmp_path / "record.env"
    values = {"KIT": str(ROOT), "OUT_BASE": str(tmp_path / "out"), "SEALED": str(tmp_path / "sealed"), "TREE_NEW": "/trees/new", "TREE_BASE": "/trees/base", "SHA_NEW": "n", "SHA_BASE": "b",
              "PY": sys.executable, "FREEZE_SHA": "f" * 64, "WORLD": "w", "SEEDS": '"42 45"', "TICKS": "5000", "SMOKE_TICKS": "2000", **extra}
    env.write_text("".join(f"{k}={v}\n" for k, v in values.items()), encoding="utf-8")
    return env


def test_the_dry_run_prints_the_four_cells_in_order_and_two_smoke_processes(tmp_path: Path) -> None:
    env = launcher_env(tmp_path)
    cells = subprocess.run(["bash", str(LAUNCH), str(env), "1", "cells"], capture_output=True, text=True, env={**os.environ, "LAUNCH_DRY_RUN": "1"}, cwd=tmp_path, check=True).stdout.splitlines()
    smoke = subprocess.run(["bash", str(LAUNCH), str(env), "1", "smoke"], capture_output=True, text=True, env={**os.environ, "LAUNCH_DRY_RUN": "1"}, cwd=tmp_path, check=True).stdout.splitlines()
    assert [(c.split("--arm ")[1].split()[0], c.split("--seed ")[1].split()[0], c.split("--mode ")[1].split()[0]) for c in cells] == [("new", "42", "spy"), ("new", "45", "spy"), ("base", "42", "spy"), ("base", "45", "spy")]
    assert all("MemoryMax=3G" in c and "taskset -c 4-5" in c and "--ticks 5000" in c for c in cells)
    assert [(c.split("--mode ")[1].split()[0], c.split("--ticks ")[1].split()[0]) for c in smoke] == [("plain", "2000"), ("spy", "2000")]


def test_the_runner_record_is_written_from_a_cwd_outside_the_kit(tmp_path: Path) -> None:
    env = launcher_env(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    done = subprocess.run(["bash", str(LAUNCH), str(env), "GO-1", "cells"], capture_output=True, text=True, env={**os.environ, "LAUNCH_RECORD_ONLY": "1"}, cwd=elsewhere)
    record = tmp_path / "out" / "cells" / "runner.json"
    log = (tmp_path / "out" / "cells" / "launcher.log").read_text(encoding="utf-8")
    assert done.returncode == 0 and record.exists(), (done.stdout, done.stderr, log)
    assert "DISK_CHECK rc=" in log and "ImportError" not in log and "ModuleNotFoundError" not in log, log      # a kit `python -c` call (the disk check) also works from a cwd outside the kit
    data = json.loads(record.read_text(encoding="utf-8"))
    assert (data["status"], data["go"], data["freeze"]["final"]) == ("COMPLETE", "GO-1", "f" * 64) and len(data["returncodes"]) == 4


def test_a_runner_record_that_cannot_be_written_exits_non_zero_and_says_so(tmp_path: Path) -> None:
    env = launcher_env(tmp_path)
    blocked = tmp_path / "out" / "cells"
    blocked.mkdir(parents=True)
    (blocked / "runner.json").mkdir()                                                    # writing the file now fails
    done = subprocess.run(["bash", str(LAUNCH), str(env), "GO-1", "cells"], capture_output=True, text=True, env={**os.environ, "LAUNCH_RECORD_ONLY": "1"}, cwd=tmp_path)
    log = (blocked / "launcher.log").read_text(encoding="utf-8")
    assert done.returncode == 6 and "RECORD NOT WRITTEN" in log and "STATUS=RECORD_NOT_WRITTEN RC=6" in log


def test_every_kit_python_call_in_the_launcher_goes_through_kitpy_and_a_failed_record_is_never_complete() -> None:
    text = LAUNCH.read_text(encoding="utf-8")
    stray = [line for line in text.splitlines() if '"$PY"' in line and not line.lstrip().startswith("#") and "kitpy()" not in line and "SCOPE_CMD=" not in line and '--python "$PY"' not in line]
    assert stray == [], stray                              # the only bare interpreter uses: kitpy's own definition, the scope command (run under cd $KIT and PYTHONPATH), and the --python arguments
    assert text.count("kitpy ") >= 6 and '(cd "$KIT" && PYTHONPATH="$KIT" "$PY" "$@"' in text
    assert text.index("\nfinish_record\n") < text.index("RUN EXIT") < text.index("> SHA256SUMS")


def stage1_dir(tmp_path: Path, after_run_line: Optional[str]) -> Path:
    stage1 = tmp_path / "stage1"
    (stage1 / "run" / "cells").mkdir(parents=True)
    sums = stage1 / "run" / "SHA256SUMS"
    sums.write_text("abc  ./x\n", encoding="utf-8")
    (stage1 / "run" / "SHA256SUMS.seal.log").write_text(f"SEAL {hashlib.sha256(sums.read_bytes()).hexdigest()} 10:00:00\n", encoding="utf-8")
    if after_run_line is not None:
        (stage1 / "kit_sha256_after_run.txt").write_text(after_run_line + "\n", encoding="utf-8")
    return stage1


def test_stage_2_aborts_unless_the_stage_1_after_run_file_names_the_approved_spy_but_a_smoke_does_not_need_it(tmp_path: Path) -> None:     # NEW (choice 4)
    spy_sha = "e920a5fe" + "0" * 56
    for line in (None, "deadbeef" + "0" * 56 + "  tools/rpg_measure/person_attack_spy.py"):
        base = tmp_path / ("a" if line is None else "b")
        base.mkdir()
        stage1 = stage1_dir(base, line)
        env = launcher_env(base, SEALED=str(stage1 / "run" / "cells"), KIT_SHA_person_attack_spy_py=spy_sha)
        done = subprocess.run(["bash", str(LAUNCH), str(env), "GO-1", "cells"], capture_output=True, text=True, cwd=base)
        log = (base / "out" / "cells" / "launcher.log").read_text(encoding="utf-8")
        assert done.returncode == 3 and "does not name the stage-1 spy e920a5fe" in log and "TREE" not in log
    good = tmp_path / "c"
    good.mkdir()
    stage1 = stage1_dir(good, f"{spy_sha}  tools/rpg_measure/person_attack_spy.py")
    env = launcher_env(good, SEALED=str(stage1 / "run" / "cells"), KIT_SHA_person_attack_spy_py=spy_sha)
    subprocess.run(["bash", str(LAUNCH), str(env), "GO-1", "cells"], capture_output=True, text=True, cwd=good)
    assert "does not name the stage-1 spy" not in (good / "out" / "cells" / "launcher.log").read_text(encoding="utf-8")        # past the assert: it stops later (the trees do not exist here)
    smoke = tmp_path / "d"
    smoke.mkdir()
    stage1 = stage1_dir(smoke, None)
    env = launcher_env(smoke, SEALED=str(stage1 / "run" / "cells"), KIT_SHA_person_attack_spy_py=spy_sha)
    subprocess.run(["bash", str(LAUNCH), str(env), "GO-1", "smoke"], capture_output=True, text=True, cwd=smoke)
    assert "does not name the stage-1 spy" not in (smoke / "out" / "smoke" / "launcher.log").read_text(encoding="utf-8")
