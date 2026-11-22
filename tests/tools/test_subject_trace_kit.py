"""Planted controls for the subject trace kit (tools/rpg_measure/subject_trace_*): the pass-through legality wrapper, the window bounds, the subject derivation from a synthetic sealed cell, the cell checks
(0 rows, no legality call on NEW s42, a hash mismatch, a spy exception) and the launcher's record step from a cwd outside the kit. Each control was mutation-checked: disabling the check it guards makes it fail."""
from __future__ import annotations

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
        FakeLegality.verify_attack_legality(entity(7), entity(8), SimpleNamespace())        # no tick on the context: recorded with in_window null
    finally:
        spy.restore()
    assert [(r["attacker_id"], r["target_id"], r["tick"], r["in_window"], r["opportunity"], r["legal"], r["reason"], r["failure_text"]) for r in spy.legality_rows] == [
        (7, 8, 150, True, False, False, "OUT_OF_RANGE", "target out of range"), (7, 8, 150, True, True, False, "OUT_OF_RANGE", "target out of range"), (7, 8, None, None, False, False, "OUT_OF_RANGE", "target out of range")]
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
    assert spy_module.snapshot(None) == {"present": False}


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
def test_the_window_runs_from_the_first_hit_minus_100_to_the_death_or_the_end_plus_100() -> None:
    killed = {"start_tick": 1901, "end_tick": 2610, "outcome": "victim_killed"}
    lived = {"start_tick": 3000, "end_tick": 3400, "outcome": "disengaged"}
    early = {"start_tick": 40, "end_tick": 90, "outcome": "disengaged"}
    assert run.engagement_window(killed) == [1801, 2610]          # death: no padding after it
    assert run.engagement_window(lived) == [2900, 3500]           # the victim lived: end plus 100
    assert run.engagement_window(early) == [0, 190]               # never below tick 0
    assert run.merge_windows([[10, 20], [21, 30], [50, 60], [55, 70]]) == [[10, 30], [50, 70]]


# --------------------------------------------------------------------------------------------- subject derivation from a synthetic sealed cell
def hits(attacker: int, victim: int, start: int, n: int, step: int = 5, **kw: Any) -> List[Dict[str, Any]]:
    return [row(start + i * step, attacker=attacker, victim=victim, **kw) for i in range(n)]


def sealed_cell(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"rows": rows, "mode_rows": [], "final_tick": 5000, "attack_rows": []}


def test_derivation_takes_the_victims_of_10_plus_hit_engagements_the_chain_victims_their_attackers_and_the_extra_input() -> None:
    rows = hits(1, 100, 2000, 12)                                # attacker 1 -> victim 100, 12 hits: a >= 10 engagement
    rows += hits(2, 200, 3000, 5, step=2)                        # attacker 2 -> victim 200, 5 hits in a row, no decision: an R7 chain (but < 10 hits)
    rows += hits(3, 300, 4000, 2)                                # attacker 3 -> victim 300, 2 hits: nobody
    plan = run.derive_seed(sealed_cell(rows), summary, [{"seed": 42, "id": 999, "windows": [[10, 20]]}])
    by_id = {s["id"]: s for s in plan}
    assert sorted(by_id) == [1, 2, 100, 200, 999]
    assert by_id[100]["roles"] == ["chain_victim", "victim"] and by_id[100]["counterparts"] == [1] and by_id[100]["windows"] == [[1900, 2155]]
    assert by_id[200]["roles"] == ["chain_victim"] and by_id[2]["roles"] == ["attacker"] and by_id[2]["counterparts"] == [200]
    assert by_id[1]["roles"] == ["attacker"] and by_id[999]["roles"] == ["extra"] and by_id[999]["windows"] == [[10, 20]]
    assert 3 not in by_id and 300 not in by_id


def test_the_hit_threshold_is_exactly_ten_hits() -> None:
    ten = hits(1, 100, 2000, 10, step=40, victim_attacked_same_tick=True)                  # a decision on every hit: no chain, only the hit count decides
    nine = hits(2, 200, 4000, 9, step=40, victim_attacked_same_tick=True)
    ids = {s["id"] for s in run.derive_seed(sealed_cell(ten + nine), summary, [])}
    assert ids == {1, 100}                                                                  # 10 hits in, 9 hits out


def test_a_killed_victims_window_ends_at_its_death_in_the_derivation() -> None:
    rows = hits(1, 100, 2000, 11)
    rows[-1] = {**rows[-1], "victim_alive_after": False}
    plan = run.derive_seed(sealed_cell(rows), summary, [])
    assert [s["windows"] for s in plan if s["id"] == 100] == [[[1900, 2050]]]


def test_the_plan_records_the_sha256_of_every_sealed_cell_it_read_and_is_deterministic(tmp_path: Path) -> None:
    cells = tmp_path / "cells"
    cells.mkdir()
    (cells / "new__w__s42__spy.json").write_text(json.dumps(sealed_cell(hits(1, 100, 2000, 12))), encoding="utf-8")
    for arm in ("new", "base"):
        (cells / f"{arm}__w__s42__plain.json").write_text(json.dumps({"final_hash": arm}), encoding="utf-8")
    first = run.derive_plan(cells, "w", [42], [], summary)
    assert first == run.derive_plan(cells, "w", [42], [], summary)
    assert set(first["derived_from"]) == {"new__w__s42__spy.json", "new__w__s42__plain.json", "base__w__s42__plain.json"} and all(len(v) == 64 for v in first["derived_from"].values())
    (cells / "new__w__s42__plain.json").write_text(json.dumps({"final_hash": "changed"}), encoding="utf-8")
    assert run.derive_plan(cells, "w", [42], [], summary)["plan_sha256"] != first["plan_sha256"]       # the sealed inputs are part of the plan's identity


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
