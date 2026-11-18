# Compliance IDs: WORLD-122
"""S9 spy and runner: the C1/C2/C3 detectors with a synthetic stuck member, a repeat-fail and a starving member, and one positive control per verdict class."""
import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.group_record import GroupRecord
from src.core.state import AuthoritativeState, IntentResult
from src.core.updates import BiologicalUpdate, CombatUpdate, EntityUpdate, StateUpdate
from src.engine.starvation import STARVING_LINE
from tools.rpg_measure import s9_run, s9_spy
from tools.rpg_measure.s9_spy import GroupSpy, c1_stuck, c2_repeat_fail, c3_needs, classify, final_verdict, hits_by_eid, split_counts

W = s9_spy.WINDOW


def row(tick, group=1, **kw):
    base = {"tick": tick, "group": group, "goal_changed": False, "task_changed": False, "moved": False, "completed": 0, "consumed": False, "attacked": False, "failed": [], "hunger": 0.0, "starved": False, "life_stage": "ADULT"}
    return {**base, **kw}


def rows(n, start=1, **kw):
    return [row(start + i, **kw) for i in range(n)]


# ---- the detector controls --------------------------------------------------------------------------------------------------------------------------
def test_c1_a_stuck_member_is_flagged_at_the_window_and_progress_resets_it():
    assert c1_stuck(rows(W))[0] == {"group": 1, "first_tick": 1, "last_tick": W, "ticks": W}
    assert c1_stuck(rows(W - 1)) == []
    broken = rows(150) + [row(151, moved=True)] + rows(150, start=152)
    assert c1_stuck(broken) == [], "a successful step splits the run below the window"
    for kind in ({"goal_changed": True}, {"task_changed": True}, {"completed": 1}, {"attacked": True}):
        assert c1_stuck(rows(150) + [row(151, **kind)] + rows(150, start=152)) == []


def test_c1_a_run_does_not_cross_a_group_boundary_or_a_gap():
    assert c1_stuck(rows(150) + rows(150, start=151, group=2)) == []
    assert c1_stuck(rows(150) + rows(150, start=400)) == []


def test_c2_the_same_failing_action_for_the_window_is_flagged_and_a_different_or_mixed_action_is_not():
    key = ["CARRIED_FOOD", "0", "no food"]
    assert c2_repeat_fail(rows(W, failed=[key]))[0]["key"] == key
    mixed = [row(t, failed=[key if t % 2 else ["NODE", "9", "empty"]]) for t in range(1, W + 1)]
    assert c2_repeat_fail(mixed) == []
    with_progress = rows(150, failed=[key]) + [row(151, failed=[key], moved=True)] + rows(150, start=152, failed=[key])
    assert c2_repeat_fail(with_progress) == []
    assert c2_repeat_fail(rows(W, failed=[key, ["NODE", "9", "empty"]])) == [], "two different failures in one tick are not the same single action"


def test_c3_a_member_reaching_the_starving_line_or_starving_in_the_group_is_flagged_once_per_stretch():
    below = rows(10, hunger=STARVING_LINE - 1)
    assert c3_needs(below) == []
    assert c3_needs(below + [row(11, hunger=STARVING_LINE)])[0]["first_tick"] == 11
    assert c3_needs([row(1), row(2, starved=True)])[0]["starved"] is True


# ---- the per-eid verdict classes ----------------------------------------------------------------------------------------------------------------------
STUCK = {"C1": [{"group": 1, "first_tick": 1, "last_tick": W, "ticks": W}]}
STARVE = {"C3": [{"group": 1, "first_tick": 5, "hunger": 99.0, "starved": False}]}


def test_class_1_a_head_only_t0_hit_is_a_block():
    rows_ = classify({10: STUCK}, {}, {10}, {}, {10: [row(1)]})
    assert [(r["eid"], r["class"]) for r in rows_] == [(10, "BLOCK")] and final_verdict(rows_) == "BLOCK"


def test_class_2_the_same_hit_on_both_arms_is_a_main_defect_not_a_block():
    rows_ = classify({10: STUCK}, {10: STUCK}, {10}, {}, {10: [row(1)]})
    assert [(r["eid"], r["class"]) for r in rows_] == [(10, "MAIN-DEFECT")] and final_verdict(rows_) == "FINDINGS"


def test_a_t0_member_with_a_different_kind_on_main_is_still_a_block_for_the_kind_main_lacks():
    rows_ = classify({10: {**STUCK, **STARVE}}, {10: STUCK}, {10}, {}, {10: [row(1)]})
    assert rows_[0]["class"] == "BLOCK" and rows_[0]["kinds"] == {"C1": "MAIN-DEFECT", "C3": "BLOCK"}


def test_class_3_a_newborn_c3_is_a_block():
    rows_ = classify({77: STARVE}, {}, {10}, {77: 10}, {77: [row(1, life_stage="CHILD")]})
    assert [(r["eid"], r["class"]) for r in rows_] == [(77, "BLOCK")] and final_verdict(rows_) == "BLOCK"


def test_class_4_a_newborn_c1_is_a_finding_with_its_life_stage_group_and_the_mothers_c1_c2_status():
    rows_ = classify({77: STUCK, 10: STUCK}, {10: STUCK}, {10}, {77: 10}, {77: [row(1, life_stage="CHILD", group=1)], 10: [row(1)]})
    finding = next(r for r in rows_ if r["eid"] == 77)
    assert finding["class"] == "FINDING" and finding["life_stage"] == "CHILD" and finding["group"] == 1
    assert finding["mother"] == 10 and finding["mother_C1"] is True and finding["mother_C2"] is False
    assert final_verdict([finding]) == "FINDINGS"
    assert final_verdict([]) == "CLEAR"


def test_hit_counts_split_between_t0_and_newborn_members():
    rows_ = classify({10: STUCK, 77: STUCK}, {}, {10}, {77: 10}, {10: [row(1)], 77: [row(1)]})
    assert split_counts(rows_) == {"t0": {"C1": 1}, "newborn": {"C1": 1}}


def test_hits_by_eid_runs_all_three_detectors_and_leaves_clean_members_out():
    out = hits_by_eid({1: rows(W), 2: rows(5, moved=True), 3: rows(3, hunger=STARVING_LINE)})
    assert set(out) == {1, 3} and set(out[1]) == {"C1"} and set(out[3]) == {"C3"}


# ---- the spy ----------------------------------------------------------------------------------------------------------------------------------------
def _body(entity_id, pos=(5.0, 5.0)):
    return V2EntityBuilder(entity_id).kind("human").location(*pos).build()


def test_the_spy_records_a_step_a_completed_transaction_a_failure_and_an_attack_per_member_per_tick():
    group = GroupRecord(id=1, leader_id=1, member_ids={1, 2}, anchor=(5.0, 5.0), formation_tick=0)
    prior = AuthoritativeState(tick=9, seed=1, entities={1: _body(1), 2: _body(2)}, groups={1: group}, next_entity_id=3)
    after = AuthoritativeState(tick=10, seed=1, entities={1: _body(1, (6.0, 5.0)), 2: _body(2)}, groups={1: group}, next_entity_id=3)
    spy = GroupSpy(prior)
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, intent_results=[IntentResult(transaction_id="t", accepted=True, reason=None, source_kind="CARRIED_FOOD", source_id=0)]),
        2: EntityUpdate(entity_id=2, intent_results=[IntentResult(transaction_id="u", accepted=False, reason="no food", source_kind="NODE", source_id=7)],
                        combat=CombatUpdate(damage_taken=3, attacker_id=1)),
    })
    spy.observe(prior, update, after)
    one, two = spy.rows[1][0], spy.rows[2][0]
    assert one["moved"] and one["completed"] == 1 and one["attacked"] is True and one["failed"] == []
    assert two["failed"] == [("NODE", "7", "no food")] and not two["moved"] and two["completed"] == 0
    assert spy.group_seen[1]["first_tick"] == 10


def test_the_spy_marks_a_newborn_member_and_stops_recording_a_dissolved_group():
    group = GroupRecord(id=1, leader_id=1, member_ids={1, 5}, anchor=(5.0, 5.0), formation_tick=0)
    prior = AuthoritativeState(tick=9, seed=1, entities={1: _body(1), 5: _body(5)}, groups={1: group}, next_entity_id=6)
    spy = GroupSpy(AuthoritativeState(tick=0, seed=1, entities={1: _body(1)}, next_entity_id=2))
    spy.observe(prior, StateUpdate(), dataclasses.replace(prior, tick=10))
    assert spy.newborn_in_group == [{"group": 1, "tick": 10, "newborn": 5, "kind": "human"}]
    dissolved = dataclasses.replace(group, dissolution_tick=11)
    spy.observe(prior, StateUpdate(), dataclasses.replace(prior, tick=11, groups={1: dissolved}))
    assert len(spy.rows[1]) == 1 and spy.group_seen[1]["dissolution_tick"] == 11


# ---- the runner's judge ------------------------------------------------------------------------------------------------------------------------------
def _doc(rows_by_eid, start_ids, mother=None):
    return {"rows": {str(k): v for k, v in rows_by_eid.items()}, "start_ids": start_ids, "mother": mother or {}, "window": W, "groups": {}, "starving_line": STARVING_LINE,
            "newborn_in_group": [], "not_captured": [], "final_hash": "h"}


def test_the_judge_prints_block_when_head_alone_has_a_stuck_t0_member_and_clear_when_both_are_clean():
    stuck, clean = rows(W), rows(5, moved=True)
    report = s9_run.judge(_doc({10: stuck}, [10]), _doc({10: clean}, [10]), s9_spy)
    assert report["verdict"] == "BLOCK" and report["eids"][0]["eid"] == 10
    assert s9_run.judge(_doc({10: clean}, [10]), _doc({10: clean}, [10]), s9_spy)["verdict"] == "CLEAR"
    assert s9_run.judge(_doc({10: stuck}, [10]), _doc({10: stuck}, [10]), s9_spy)["verdict"] == "FINDINGS"


def test_a_member_whose_only_activity_is_an_inn_meal_is_not_stuck_and_a_missing_meal_is():
    """The eat paths that write a typed hunger drop with no IntentResult (inn meal, core_actions eat) are progress."""
    meals = [row(t, consumed=(t % 150 == 0)) for t in range(1, 401)]
    assert c1_stuck(meals) == [], "a typed consume every 150 ticks keeps every stretch below the window"
    assert c1_stuck(rows(400)) != []


def test_the_spy_records_a_typed_hunger_drop_and_a_hunger_set_as_a_consume_and_a_hunger_rise_as_none():
    group = GroupRecord(id=1, leader_id=1, member_ids={1, 2, 3}, anchor=(5.0, 5.0), formation_tick=0)
    prior = AuthoritativeState(tick=9, seed=1, entities={1: _body(1), 2: _body(2), 3: _body(3)}, groups={1: group}, next_entity_id=4)
    after = dataclasses.replace(prior, tick=10)
    spy = GroupSpy(prior)
    update = StateUpdate(entity_updates={
        1: EntityUpdate(entity_id=1, biological=BiologicalUpdate(hunger_delta=-20.0)),
        2: EntityUpdate(entity_id=2, biological=BiologicalUpdate(hunger_set=0.0)),
        3: EntityUpdate(entity_id=3, biological=BiologicalUpdate(hunger_delta=1.0)),
    })
    spy.observe(prior, update, after)
    assert [spy.rows[e][0]["consumed"] for e in (1, 2, 3)] == [True, True, False]


def _plain(h):
    return {"final_hash": h}


def test_a_spied_hash_that_differs_from_its_plain_twin_makes_the_verdict_invalid_and_prints_no_class():
    stuck = rows(W)
    head, main = _doc({10: stuck}, [10]), _doc({10: rows(5, moved=True)}, [10])
    ok = s9_run.judge(head, main, s9_spy, _plain("h"), _plain("h"))
    assert ok["verdict"] == "BLOCK" and ok["twin_hash_equal"] == {"head": True, "main": True}
    bad = s9_run.judge(head, main, s9_spy, _plain("other"), _plain("h"))
    assert bad["verdict"] == "INVALID" and bad["eids"] == [] and bad["twin_hash"]["head"] == {"spied": "h", "plain": "other"}
    bad_main = s9_run.judge(head, main, s9_spy, _plain("h"), _plain("other"))
    assert bad_main["verdict"] == "INVALID"


def test_the_follow_up_fires_when_the_verdict_is_not_clear_or_any_group_is_alive_on_head_and_not_otherwise():
    dead, alive = {"1": {"alive_at_end": False}}, {"7": {"alive_at_end": True}, "9": {"alive_at_end": False}}
    assert s9_run.follow_up("CLEAR", dead, alive) == {"fired": False, "verdict": "CLEAR", "head_alive_at_end": [], "main_alive_at_end": [7]}, "a group alive on main alone does not fire it"
    assert s9_run.follow_up("CLEAR", alive, dead)["fired"] is True and s9_run.follow_up("CLEAR", alive, dead)["head_alive_at_end"] == [7]
    assert s9_run.follow_up("FINDINGS", dead, dead)["fired"] is True and s9_run.follow_up("BLOCK", dead, dead)["fired"] is True and s9_run.follow_up("INVALID", dead, dead)["fired"] is True
    assert s9_run.follow_up_line(s9_run.follow_up("CLEAR", dead, dead)).startswith("FOLLOW-UP: cohesion-capture NOT FIRED")
    assert "FIRED (verdict BLOCK" in s9_run.follow_up_line(s9_run.follow_up("BLOCK", dead, alive))


def test_the_judge_carries_the_follow_up_in_both_the_valid_and_the_invalid_report():
    head = {**_doc({10: rows(5, moved=True)}, [10]), "groups": {"3": {"alive_at_end": True}}}
    main = {**_doc({10: rows(5, moved=True)}, [10]), "groups": {}}
    valid = s9_run.judge(head, main, s9_spy, _plain("h"), _plain("h"))
    assert valid["verdict"] == "CLEAR" and valid["follow_up"]["fired"] is True and valid["follow_up"]["head_alive_at_end"] == [3]
    assert s9_run.judge(head, main, s9_spy, _plain("x"), _plain("h"))["follow_up"]["fired"] is True


def test_births_and_conceptions_counts_two_newborns_one_pregnancy_and_zero_on_a_main_shaped_state():
    from src.core.pregnancy import PregnancyState
    from src.systems.lifecycle_systems.genetics import GeneticProfile

    group = GroupRecord(id=1, leader_id=1, member_ids={1, 2}, anchor=(5.0, 5.0), formation_tick=0)
    pregnant = dataclasses.replace(_body(1), lifecycle=dataclasses.replace(_body(1).lifecycle, pregnancy=PregnancyState(
        father_entity_id=2, conceived_tick=30, due_tick=2430, litter_size=1, father_genetic_profile=GeneticProfile())))
    start = AuthoritativeState(tick=0, seed=1, entities={1: _body(1), 2: _body(2)}, next_entity_id=3)
    state = AuthoritativeState(tick=10, seed=1, entities={1: pregnant, 2: _body(2), 3: _body(3), 4: _body(4)}, groups={1: group}, next_entity_id=5)
    spy = GroupSpy(start)
    spy.observe(state, StateUpdate(), state)
    spy.observe(state, StateUpdate(), dataclasses.replace(state, tick=11))
    assert s9_spy.count_births(state.entities, spy.start_ids) == 2, "bodies 3 and 4, alive or dead"
    assert len(spy.conceptions) == 1, "the same (mother, conceived_tick) seen on two ticks counts once"
    main_shaped = type("Lifecycle", (), {})()
    body = type("Body", (), {"id": 1, "lifecycle": main_shaped})()
    main_state = type("State", (), {"tick": 5, "entities": {1: body}, "groups": {}})()
    empty = GroupSpy(start)
    empty.observe(main_state, StateUpdate(), main_state)
    assert len(empty.conceptions) == 0, "a lifecycle with no pregnancy field reads as no conception"


def test_the_judge_report_carries_births_and_conceptions_for_both_arms():
    head = {**_doc({10: rows(5, moved=True)}, [10]), "births": 2, "conceptions": 1}
    main = {**_doc({10: rows(5, moved=True)}, [10]), "births": 0, "conceptions": 0}
    report = s9_run.judge(head, main, s9_spy, _plain("h"), _plain("h"))
    assert report["births"] == {"head": 2, "main": 0} and report["conceptions"] == {"head": 1, "main": 0}


def test_the_runner_prints_the_newborns_in_any_group_as_a_count_and_rows_of_any_kind(capsys, monkeypatch, tmp_path):
    report = {"verdict": "CLEAR", "eids": [], "twin_hash": {}, "births": {"head": 1, "main": 0}, "conceptions": {"head": 1, "main": 0}, "follow_up": s9_run.follow_up("CLEAR", {}, {}),
              "newborn_in_group_head": [{"group": 4, "tick": 120, "newborn": 77, "kind": "wolf"}, {"group": 4, "tick": 130, "newborn": 78, "kind": "human"}]}
    monkeypatch.setattr(s9_run, "judge", lambda *a, **k: report)
    monkeypatch.setattr(s9_run.subprocess, "run", lambda cmd, **kw: type("P", (), {"returncode": 0, "stderr": ""})())
    for arm in ("head", "head_plain", "main", "main_plain"):
        (tmp_path / f"{arm}.json").write_text("{}")
    monkeypatch.setattr(s9_run, "load_spy", lambda path: s9_spy)
    s9_run.main(["--tree", str(tmp_path), "--main-tree", str(tmp_path), "--out", str(tmp_path), "--go", "x"])
    out = capsys.readouterr().out
    assert "newborns in any group at any tick (head, any kind): 2" in out
    assert "newborn eid 77 kind wolf group 4 first tick in a group 120" in out and "newborn eid 78 kind human group 4 first tick in a group 130" in out
