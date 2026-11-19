# Compliance IDs: WORLD-122
"""The coin/boss counter's summarizer and runner (tools/rpg_measure/coin_boss_summary.py, coin_boss_run.py): hand-built out json files, no child process, no world build."""
import json

import pytest

from tools.rpg_measure import coin_boss_run as run
from tools.rpg_measure import coin_boss_summary as summ

HASH = "a" * 64
LAST = 6
PLAIN = {"world": "w", "seed": 1, "ticks": 5, "final_hash": HASH}  # the births re-check's plain twin json (the fields the summarizer reads)


def _doc(**overrides):
    doc = {
        "world": "w", "seed": 1, "ticks": 5, "final_hash": HASH, "logging_errors": [], "v6": 0, "wiring": "OK", "unexplained_total_count": 0, "unexplained_rows": [], "apply_calls": 5, "distinct_ticks": 5,
        "boss_max": {c: 0 for c in summ.BOSS_COLUMNS}, "boss_disagreements": [], "coin_moving_ticks": 3, "control_applied_count": 0, "control": None, "counts_for_recheck": True,
    }
    doc.update(overrides)
    return doc


def _write(directory, name, doc, returncode=0):
    (directory / f"{name}.json").write_text(doc if isinstance(doc, str) else json.dumps(doc), encoding="utf-8")
    if returncode is not None:
        (directory / f"{name}.exit.json").write_text(json.dumps({"returncode": returncode, "stderr_tail": ""}), encoding="utf-8")


def _load(directory, name):
    doc, reason = summ.load_doc(directory / f"{name}.json")
    return doc, reason, summ.load_exit(directory / f"{name}.exit.json")


# ---- real cells ----------------------------------------------------------------------------------------------------------------------------------

def _real(tmp_path, plain=PLAIN, returncode=0, **overrides):
    _write(tmp_path, "real_w_1_5", _doc(**overrides), returncode)
    doc, reason, code = _load(tmp_path, "real_w_1_5")
    return summ.real_verdict(doc, reason, code, plain)


def test_a_clean_real_cell_passes_every_hard_check_and_reports_the_facts(tmp_path):
    verdict = _real(tmp_path)
    assert verdict["verdict"] == "PASS" and verdict["failed"] == [] and verdict["findings"] == []
    assert verdict["reported"]["apply_calls"] == 5 and verdict["reported"]["distinct_ticks"] == 5 and verdict["reported"]["unexplained_total_count"] == 0


@pytest.mark.parametrize("kwargs,failed", [
    ({"plain": {**PLAIN, "final_hash": "b" * 64}}, "hash_equals_plain"),
    ({"logging_errors": [{"logger": "x", "level": "ERROR", "message": "boom"}]}, "logging_errors_empty"),
    ({"returncode": 5}, "exit_zero"),
    ({"returncode": 4}, "exit_zero"),
    ({"returncode": 6}, "exit_zero"),
    ({"v6": 2.0}, "v6_zero"),
])
def test_each_hard_real_check_fails_on_its_own(tmp_path, kwargs, failed):
    verdict = _real(tmp_path, **kwargs)
    assert verdict["verdict"] == "FAIL" and verdict["failed"] == [failed]


def test_a_missing_plain_file_or_one_without_a_hash_fails_with_the_reason_stated(tmp_path):
    missing = _real(tmp_path, plain=None)
    assert "plain_twin_present" in missing["failed"] and missing["reasons"]["plain_twin_present"] == "the plain twin file is missing"
    no_hash = _real(tmp_path, plain={"world": "w", "seed": 1, "ticks": 5})
    assert "plain_twin_present" in no_hash["failed"] and no_hash["reasons"]["plain_twin_present"] == "the plain twin file has no final_hash"
    assert missing["verdict"] == no_hash["verdict"] == "FAIL"


@pytest.mark.parametrize("plain_change", [{"world": "other"}, {"seed": 2}, {"ticks": 6}])
def test_a_plain_twin_of_another_cell_fails_same_cell_even_when_the_hashes_match(tmp_path, plain_change):
    verdict = _real(tmp_path, plain={**PLAIN, **plain_change})
    assert verdict["hard"]["hash_equals_plain"] is True  # the hashes happen to match: the meaningless pass this check exists to stop
    assert verdict["verdict"] == "FAIL" and verdict["failed"] == ["same_cell"] and "!= plain cell" in verdict["reasons"]["same_cell"]


def test_a_plain_twin_without_the_cell_fields_fails_same_cell(tmp_path):
    verdict = _real(tmp_path, plain={"final_hash": HASH})
    assert verdict["failed"] == ["same_cell"]


@pytest.mark.parametrize("overrides", [
    {"control": {"kind": "coin", "amount": 5.0, "applied_at_tick": 5}},  # a control output renamed or copied into real_*.json
    {"counts_for_recheck": False},
    {"control": {"kind": "boss", "amount": 2, "applied_at_tick": 5}, "counts_for_recheck": False},
])
def test_a_control_output_cannot_count_as_a_real_cell(tmp_path, overrides):
    verdict = _real(tmp_path, **overrides)
    assert verdict["verdict"] == "FAIL" and verdict["failed"] == ["not_a_control"] and "cannot count as a real cell" in verdict["reasons"]["not_a_control"]


def test_an_out_json_without_counts_for_recheck_is_partial(tmp_path):
    doc = _doc()
    del doc["counts_for_recheck"]
    _write(tmp_path, "nocount", doc, 0)
    loaded, reason = summ.load_doc(tmp_path / "nocount.json")
    assert loaded is None and "counts_for_recheck" in reason


def test_a_missing_exit_record_fails_the_exit_check(tmp_path):
    _write(tmp_path, "real_w_1_5", _doc(), None)
    doc, reason, code = _load(tmp_path, "real_w_1_5")
    assert code is None and summ.real_verdict(doc, reason, code, PLAIN)["failed"] == ["exit_zero"]


def test_a_missing_bad_or_partial_out_json_is_a_fail(tmp_path):
    missing = summ.real_verdict(*summ.load_doc(tmp_path / "nope.json"), 0, PLAIN)
    assert missing["verdict"] == "FAIL" and "missing" in missing["reasons"]["out_json_complete"]
    _write(tmp_path, "bad", "{not json", 0)
    bad = summ.real_verdict(*summ.load_doc(tmp_path / "bad.json"), 0, PLAIN)
    assert bad["verdict"] == "FAIL" and "not valid JSON" in bad["reasons"]["out_json_complete"]
    partial = _doc()
    del partial["boss_max"]
    _write(tmp_path, "partial", partial, 0)
    result = summ.real_verdict(*summ.load_doc(tmp_path / "partial.json"), 0, PLAIN)
    assert result["verdict"] == "FAIL" and result["failed"] == ["out_json_complete"] and "partial" in result["reasons"]["out_json_complete"] and "boss_max" in result["reasons"]["out_json_complete"]


def test_unexplained_rows_and_boss_counts_are_findings_not_failures(tmp_path):
    verdict = _real(tmp_path, unexplained_total_count=1, unexplained_rows=[{"tick": 3, "delta": 2, "declared": 0, "unexplained": 2}],
                    boss_max={"predicate_post_964": 1, "raw_kind_alive": 1, "occupation_alive": 0}, boss_disagreements=[{"tick": 4, "counts": {}, "ids": {}}])
    assert verdict["verdict"] == "PASS" and len(verdict["findings"]) == 2


def test_the_real_summary_reads_a_directory_and_seals_it(tmp_path):
    _write(tmp_path, "real_w_1_5", _doc(), 0)
    plain = tmp_path / "w_1_plain.json"
    plain.write_text(json.dumps(PLAIN), encoding="utf-8")
    summary = summ.summarize_real(tmp_path, plain)
    assert summary["verdict"] == "PASS" and summary["plain_final_hash"] == HASH and (tmp_path / "summary_real.json").exists()
    sums = (tmp_path / "SHA256SUMS").read_text(encoding="utf-8")
    assert "real_w_1_5.json" in sums and "summary_real.json" in sums
    empty = tmp_path / "nothing_here"
    empty.mkdir()
    assert summ.summarize_real(empty, plain)["verdict"] == "FAIL"  # a directory with no real cell is not a pass


# ---- controls ------------------------------------------------------------------------------------------------------------------------------------

def _coin(real_overrides=None, **overrides):
    real = _doc(**(real_overrides or {}))
    row = {"tick": LAST, "delta": 5.0, "declared": 0.0, "unexplained": 5.0}
    control = _doc(v6=5.0, unexplained_total_count=1, unexplained_rows=[row], control_applied_count=1, control={"kind": "coin", "amount": 5.0, "applied_at_tick": LAST}, counts_for_recheck=False)
    control.update(overrides)
    return real, control


def test_a_good_coin_control_passes():
    real, control = _coin()
    assert summ.coin_control_verdict(real, control, 0, 5.0)["verdict"] == "PASS"


@pytest.mark.parametrize("overrides,failed", [
    ({"v6": 4.0}, "v6_delta_equals_n"),
    ({"unexplained_rows": []}, "exactly_one_unexplained_row_at_last_tick_equal_n"),
    ({"unexplained_rows": [{"tick": 3, "delta": 5.0, "declared": 0.0, "unexplained": 5.0}]}, "exactly_one_unexplained_row_at_last_tick_equal_n"),
    ({"unexplained_rows": [{"tick": LAST, "delta": 5.0, "declared": 0.0, "unexplained": 4.0}]}, "exactly_one_unexplained_row_at_last_tick_equal_n"),
    ({"control_applied_count": 0}, "control_applied_count_at_least_1"),
    ({"final_hash": "c" * 64}, "final_hash_equals_real"),
])
def test_each_coin_control_criterion_fails_on_its_own(overrides, failed):
    real, control = _coin(**overrides)
    verdict = summ.coin_control_verdict(real, control, 0, 5.0)
    assert verdict["verdict"] == "FAIL" and failed in verdict["failed"]


def test_a_coin_control_with_a_non_zero_exit_or_two_unexplained_rows_fails():
    real, control = _coin()
    assert summ.coin_control_verdict(real, control, 5, 5.0)["failed"] == ["exit_zero"]
    row = control["unexplained_rows"][0]
    real, control = _coin(unexplained_rows=[row, {**row, "tick": 2}])
    assert "exactly_one_unexplained_row_at_last_tick_equal_n" in summ.coin_control_verdict(real, control, 0, 5.0)["failed"]
    assert summ.coin_control_verdict(None, control, 0, 5.0)["verdict"] == "FAIL"


def _boss(**overrides):
    real = _doc()
    control = _doc(boss_max={c: 2 for c in summ.BOSS_COLUMNS}, control_applied_count=1, control={"kind": "boss", "amount": 2, "applied_at_tick": LAST}, counts_for_recheck=False)
    control.update(overrides)
    return real, control


def test_a_good_boss_control_passes_and_each_boss_criterion_fails_on_its_own():
    real, control = _boss()
    assert summ.boss_control_verdict(real, control, 0, 2)["verdict"] == "PASS"
    for overrides, failed in [
        ({"boss_max": {"predicate_post_964": 2, "raw_kind_alive": 2, "occupation_alive": 1}}, "boss_max_equals_k_in_all_columns"),
        ({"boss_disagreements": [{"tick": LAST, "counts": {}, "ids": {}}]}, "no_disagreement_row_at_last_tick"),
        ({"control_applied_count": 0}, "control_applied_count_at_least_1"),
        ({"final_hash": "c" * 64}, "final_hash_equals_real"),
    ]:
        real, control = _boss(**overrides)
        verdict = summ.boss_control_verdict(real, control, 0, 2)
        assert verdict["verdict"] == "FAIL" and failed in verdict["failed"], (overrides, verdict)
    real, control = _boss()
    assert summ.boss_control_verdict(real, control, 6, 2)["failed"] == ["exit_zero"]
    # a disagreement row on an EARLIER tick is not the last-tick criterion
    real, control = _boss(boss_disagreements=[{"tick": 2, "counts": {}, "ids": {}}])
    assert summ.boss_control_verdict(real, control, 0, 2)["verdict"] == "PASS"


def test_the_never_fire_control_passes_only_on_exit_6_with_nothing_applied():
    fired_nothing = _doc(control_applied_count=0, control={"kind": "coin", "amount": 5.0, "applied_at_tick": 999})
    assert summ.never_fire_verdict(fired_nothing, 6)["verdict"] == "PASS"
    assert summ.never_fire_verdict(fired_nothing, 0)["failed"] == ["exit_6"]
    assert summ.never_fire_verdict({**fired_nothing, "control_applied_count": 1}, 6)["failed"] == ["control_applied_count_zero"]
    assert summ.never_fire_verdict(None, 6)["failed"] == ["control_applied_count_zero"]


def test_the_controls_summary_reads_the_runner_layout_and_a_failing_control_fails_the_set(tmp_path):
    real, coin = _coin()
    _, boss = _boss()
    never = _doc(control_applied_count=0, control={"kind": "coin", "amount": 5.0, "applied_at_tick": 99})
    _write(tmp_path, "real", real, 0)
    _write(tmp_path, "control_coin_5", coin, 0)
    _write(tmp_path, "control_boss_2", boss, 0)
    _write(tmp_path, "control_never_fire", never, 6)
    summary = summ.summarize_controls(tmp_path)
    assert summary["verdict"] == "PASS" and set(summary["controls"]) == {"control_coin_5.json", "control_boss_2.json", "control_never_fire.json"}
    assert (tmp_path / "summary_controls.json").exists() and "control_coin_5.json" in (tmp_path / "SHA256SUMS").read_text(encoding="utf-8")
    _write(tmp_path, "control_never_fire", never, 0)  # the never-fire control exited 0: it did not behave like a control that cannot fire
    assert summ.summarize_controls(tmp_path)["verdict"] == "FAIL"


# ---- runner ----------------------------------------------------------------------------------------------------------------------------------

def test_the_plan_names_every_child_and_the_real_run_of_a_control_set_is_called_real():
    assert run.plan("real", "w", 3, 100, 5, 2) == [("real_w_3_100", None, None)]
    controls = run.plan("controls", "w", 3, 100, 5, 2)
    assert [c[0] for c in controls] == ["real", "control_coin_5", "control_boss_2", "control_never_fire"]
    assert controls[1][1] == "coin:5" and controls[2][1] == "boss:2" and controls[3][2] == 100 + run.NEVER_FIRE_TICK_OFFSET


def test_the_child_command_carries_the_cell_the_control_and_the_control_tick(tmp_path):
    cmd = run.child_command("w", 3, 100, tmp_path / "o.json", "coin:5", 77)
    assert cmd[1].endswith("coin_boss_spy.py") and cmd[2:6] == ["w", "3", "100", str(tmp_path / "o.json")] and cmd[6:] == ["--control", "coin:5", "--control-tick", "77"]
    assert run.child_command("w", 3, 100, tmp_path / "o.json")[6:] == []


def test_the_runner_gives_its_children_the_births_run_environment_with_recording_off(tmp_path):
    env = run.child_env(tmp_path, True)
    assert env["SIM_OBS_MODE"] == "OFF" and env["RPG_OBS_MODE"] == "OFF" and env["PYTHONPATH"] == str(tmp_path) and env["PYTHONHASHSEED"] == "0"


def test_the_runner_refuses_to_start_without_a_go():
    with pytest.raises(SystemExit):
        run.main(["--tree", "t", "--out", "o", "--mode", "real", "--world", "w", "--seed", "1", "--ticks", "5"])


def test_the_runner_aborts_when_the_tree_is_already_dirty_and_moves_new_runs_out_without_deleting(tmp_path):
    tree, out = tmp_path / "tree", tmp_path / "out"
    (tree / "data" / "runs" / "r1").mkdir(parents=True)
    assert run.main(["--tree", str(tree), "--out", str(out), "--go", "x", "--mode", "real", "--world", "w", "--seed", "1", "--ticks", "5"]) == 3
    out.mkdir()
    (tree / "data" / "runs" / "r1" / "manifest.json").write_text("{}", encoding="utf-8")
    moved = run.move_tree_runs(tree, out)
    assert moved == out / "tree-data-runs" and (moved / "r1" / "manifest.json").exists() and not (tree / "data" / "runs").exists()
    assert run.move_tree_runs(tree, out) is None
    (tree / "data" / "runs").mkdir()
    with pytest.raises(RuntimeError):
        run.move_tree_runs(tree, out)


def test_the_real_summary_fails_every_cell_when_the_plain_file_is_missing_or_unreadable(tmp_path):
    _write(tmp_path, "real_w_1_5", _doc(), 0)
    missing = summ.summarize_real(tmp_path, tmp_path / "no_plain.json")
    assert missing["verdict"] == "FAIL" and missing["cells"]["real_w_1_5.json"]["reasons"]["plain_twin_present"] == "the plain twin file is missing"
    garbled = tmp_path / "garbled_plain.json"
    garbled.write_text("{nope", encoding="utf-8")
    bad = summ.summarize_real(tmp_path, garbled)
    assert bad["verdict"] == "FAIL" and bad["cells"]["real_w_1_5.json"]["reasons"]["plain_twin_present"] == "the plain twin file has no final_hash"
