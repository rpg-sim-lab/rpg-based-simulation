"""Unit controls for the K2 fix own-job kit (tools/rpg_measure/k2fix_ownjob_*): planted positives and negatives for every count the designer fixed (A(i), A(ii), B(i), B(ii) false fires, B(iii) still looping,
neutrality), the layout and launcher controls, and the startup resolution. No simulation is run here."""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

REPO = Path(__file__).resolve().parents[2]
KIT = REPO / "tools" / "rpg_measure"
KIT_FILES = ("arm_child.py", "person_attack_spy.py", "person_attack_summary.py", "k2fix_ownjob_spy.py", "k2fix_ownjob_summary.py", "k2fix_ownjob_launch.sh")


def load_from(path, key):
    sys.modules.pop("_arm_child_pinned_runner", None)
    spec = importlib.util.spec_from_file_location(key, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    spec.loader.exec_module(module)
    return module


spy_mod = load_from(KIT / "k2fix_ownjob_spy.py", "_t_ownjob_spy")
summary = load_from(KIT / "k2fix_ownjob_summary.py", "_t_ownjob_summary")

INN = 7
INN_POS = (40, 31)                                                                                    # a real fatigue objective's target is a POSITION (trace v8: [40.0, 31.0]), not a building id


def funcs(bed_refused=False, lodges=True, coin=True, covers=True):
    return {"finds_no_bed": lambda s, e, b: bed_refused, "lodges": lambda b: lodges, "keeps_coin": lambda e: coin, "payment_covers": lambda e, a: covers,
            "building_at": lambda st, pos: next((b for b in st.buildings.values() if b.position == pos), None)}


def project(pid="p1", kind="fatigue", ended=None, target=(40.0, 31.0), objectives=None, active="o1"):
    return NS(id=pid, kind=NS(value=kind), ended_by=None if ended is None else NS(value=ended), objectives=objectives if objectives is not None else [NS(id="o1", target=list(target))], active_objective_id=active)


def entity(eid=1, gold=0, debt=50.0, projects=(), blockers=(), refusals=(), results=(), alive=True, lodged=None, action=None, current=None, outcome=None):
    return NS(id=eid, inventory=NS(gold=gold), biological=NS(sleep_debt=debt), combat=NS(alive=alive), identity=NS(latest_intent_results=tuple(results)),
              navigation=NS(service_refusals=tuple(refusals), lodged_in=lodged), strategic=NS(projects={p.id: p for p in projects}, blockers={b: object() for b in blockers}, current_project_id=current),
              task=NS(payload={} if action is None else dict({"action": action, "target_id": INN}, **({} if outcome is None else {"outcome": outcome}))))


def building(purse=0, functional=True, bid=INN, position=INN_POS):
    return NS(id=bid, functional=functional, position=position, inventory=NS(gold=purse))


def state(tick, entities, buildings=None):
    return NS(tick=tick, entities={e.id: e for e in entities}, buildings=buildings if buildings is not None else {INN: building()})


from dataclasses import dataclass


@dataclass(frozen=True)
class Refusal:                                                                                          # hashable like the real frozen ServiceRefusal
    action: str
    building: int
    tick: int
    reason: str


def refusal(tick, action="EAT"):
    return Refusal(action, INN, tick, "INSUFFICIENT_GOLD")


def new_spy(**kw):
    return spy_mod.OwnJobSpy(kw.pop("funcs", funcs()), kw.pop("limit", 4))


# ---------------------------------------------------------------- A(i): which half refused
def test_classify_way_closed_names_the_half_that_refused():
    prior, ent = state(5, [entity()]), entity()
    inn = prior.buildings[INN]
    assert spy_mod.classify_way_closed(prior, ent, inn, funcs(bed_refused=True)) == "bed_half"
    assert spy_mod.classify_way_closed(prior, ent, inn, funcs(covers=False)) == "purse_half"
    assert spy_mod.classify_way_closed(prior, ent, inn, funcs(covers=True)) == "other"           # neither half: a project that ended for another cause is not counted as a refusal
    assert spy_mod.classify_way_closed(prior, ent, inn, funcs(covers=False, coin=False)) == "other"        # a body without the coin trait is out of the scope
    assert spy_mod.classify_way_closed(prior, ent, inn, funcs(covers=False, lodges=False)) == "other"      # a bedless building too
    assert spy_mod.classify_way_closed(prior, ent, None, funcs(covers=False)) == "other_unresolved"


def test_a_fatigue_objective_with_a_position_target_at_an_inns_tile_resolves_to_that_inn_and_classifies():   # change 1, control 1
    prior = state(9, [entity(projects=[project(target=(40.0, 31.0))])])
    f = funcs(covers=False)
    assert spy_mod.resolve_building(prior, prior.entities[1].strategic.projects["p1"], f).id == INN
    spy = new_spy(funcs=f)
    spy.observe(prior, state(10, [entity(projects=[project(target=(40.0, 31.0), ended="WAY_CLOSED")])]))
    assert spy.report()["A_i"]["purse_half"] == 1 and spy.report()["A_i"]["other_unresolved"] == 0 and spy.report()["A_i"]["events"][0]["building"] == INN
    bed = new_spy(funcs=funcs(bed_refused=True))
    bed.observe(prior, state(10, [entity(projects=[project(ended="WAY_CLOSED")])]))
    assert bed.report()["A_i"]["bed_half"] == 1


def test_a_position_matching_no_building_a_fractional_tile_or_a_scalar_target_is_other_unresolved_and_never_a_half():   # change 1, control 2
    prior = state(9, [entity(projects=[project()])])
    for target in ((12.0, 12.0), (40.5, 31.0), (40.0, 31.25)):
        spy = new_spy(funcs=funcs(covers=False))
        spy.observe(prior, state(10, [entity(projects=[project(target=target, ended="WAY_CLOSED")])]))
        rep = spy.report()["A_i"]
        assert (rep["other_unresolved"], rep["purse_half"], rep["bed_half"]) == (1, 0, 0), target
    scalar = new_spy(funcs=funcs(covers=False))                                                       # the old isdigit shape: a building id as the target is NOT a position
    scalar.observe(prior, state(10, [entity(projects=[project(objectives=[NS(id="o1", target="7")], ended="WAY_CLOSED")])]))
    assert scalar.report()["A_i"]["other_unresolved"] == 1
    none = new_spy(funcs=funcs(covers=False))
    none.observe(prior, state(10, [entity(projects=[project(objectives=[], ended="WAY_CLOSED")])]))
    assert none.report()["A_i"]["other_unresolved"] == 1


def test_the_active_objective_is_used_not_index_zero():                                               # change 1, control 3
    objectives = [NS(id="o0", target=[12.0, 12.0]), NS(id="o1", target=[40.0, 31.0])]
    prior = state(9, [entity(projects=[project(objectives=objectives, active="o1")])])
    assert spy_mod.resolve_building(prior, prior.entities[1].strategic.projects["p1"], funcs()).id == INN
    index_zero = state(9, [entity(projects=[project(objectives=objectives, active="o0")])])
    assert spy_mod.resolve_building(index_zero, index_zero.entities[1].strategic.projects["p1"], funcs()) is None
    no_active = state(9, [entity(projects=[project(objectives=[NS(id="oX", target=[40.0, 31.0])], active=None)])])    # no active objective: the first, as the tree reads it
    assert spy_mod.resolve_building(no_active, no_active.entities[1].strategic.projects["p1"], funcs()).id == INN


def test_a_fatigue_project_ended_way_closed_is_counted_by_half_and_other_kinds_and_ends_are_not():
    spy = new_spy(funcs=funcs(covers=False))
    prior = state(9, [entity(projects=[project()])])
    spy.observe(prior, state(10, [entity(projects=[project(ended="WAY_CLOSED")])]))
    assert spy.report()["A_i"]["purse_half"] == 1 and spy.report()["A_i"]["bed_half"] == 0
    bed = new_spy(funcs=funcs(bed_refused=True))
    bed.observe(prior, state(10, [entity(projects=[project(ended="WAY_CLOSED")])]))
    assert bed.report()["A_i"]["bed_half"] == 1 and bed.report()["A_i"]["purse_half"] == 0
    for ended, kind in (("THREAT_CLEARED", "fatigue"), ("WAY_CLOSED", "hunger")):                # another end, another kind: not counted
        other = new_spy(funcs=funcs(covers=False))
        other.observe(state(9, [entity(projects=[project(kind=kind)])]), state(10, [entity(projects=[project(kind=kind, ended=ended)])]))
        assert other.report()["A_i"]["way_closed_total"] == 0
    already = new_spy(funcs=funcs(covers=False))                                                    # an end that was already there is not a new end
    already.observe(state(9, [entity(projects=[project(ended="WAY_CLOSED")])]), state(10, [entity(projects=[project(ended="WAY_CLOSED")])]))
    assert already.report()["A_i"]["way_closed_total"] == 0


# ---------------------------------------------------------------- A(ii): the next 200 ticks and the collapse line
def test_the_follow_up_of_a_purse_half_end_samples_the_next_200_ticks_and_counts_sleep_actions():
    spy = new_spy(funcs=funcs(covers=False))
    spy.observe(state(9, [entity(projects=[project()])]), state(10, [entity(projects=[project(ended="WAY_CLOSED")])]))
    for t in range(11, 215):
        spy.observe(state(t - 1, [entity()]), state(t, [entity(debt=50.0 + t / 100, action="REST" if t % 2 else "SLEEP", lodged=INN if t > 100 else None)]))
    trace = spy.report()["A_ii"]["follow_ups"][0]
    assert sorted(trace["samples"], key=int) == ["1", "10", "50", "100", "200"] and trace["samples"]["200"]["tick"] == 210 and trace["samples"]["200"]["lodged_in"] == INN and trace["samples"]["50"]["lodged_in"] is None
    assert trace["sleep_action_ticks"] > 90 and trace["rest_action_ticks"] > 90 and trace["sleep_action_ticks"] + trace["rest_action_ticks"] == 200


def test_subjects_reaching_the_collapse_line_are_counted_once_each_and_the_dead_are_not():
    spy = new_spy()
    for t in range(1, 6):
        spy.observe(state(t - 1, [entity(1, debt=97.0), entity(2, debt=98.0, alive=False)]), state(t, [entity(1, debt=98.0 + t), entity(2, debt=99.0, alive=False)]))
    rep = spy.report()["A_ii"]
    assert rep["subjects_at_sleep_debt_98"] == 1 and rep["first_tick_by_subject"] == {"1": 1}


# ---------------------------------------------------------------- B(i)
def test_a_service_blocker_appearing_on_a_subject_is_filed_once_by_action_with_its_first_tick():
    spy = new_spy()
    prior = state(39, [entity(refusals=[refusal(t) for t in (10, 20, 30)])])
    spy.observe(prior, state(40, [entity(refusals=[refusal(t) for t in (10, 20, 30, 40)], blockers=["blocker_service_EAT_7"])]))
    spy.observe(state(40, [entity(blockers=["blocker_service_EAT_7"])]), state(41, [entity(blockers=["blocker_service_EAT_7"])]))      # standing: not filed again
    rep = spy.report()["B_i"]
    assert rep["filed"] == 1 and rep["by_action"] == {"EAT": 1} and rep["first_tick"] == 40 and rep["events"][0]["building"] == INN
    spy.observe(state(41, [entity(blockers=["blocker_service_EAT_7"])]), state(42, [entity()]))
    assert spy.report()["vi"]["blockers_removed"] == 1
    assert new_spy().report()["B_i"]["filed"] == 0                                                   # a world with no refusal files nothing


def test_a_non_service_blocker_is_not_counted():
    spy = new_spy()
    spy.observe(state(1, [entity()]), state(2, [entity(blockers=["blocker_congestion"])]))
    assert spy.report()["B_i"]["filed"] == 0


# ---------------------------------------------------------------- B(ii): false fires
def test_a_blocker_filed_after_a_delivery_inside_its_streak_is_a_false_fire_and_a_clean_streak_is_not():
    # a paid meal at tick 25: the subject's gold falls by 5 and the inn's purse rises by 5
    spy = new_spy()
    spy.observe(state(24, [entity(gold=10)], {INN: building(0)}), state(25, [entity(gold=5)], {INN: building(5)}))
    spy.observe(state(39, [entity(refusals=[refusal(t) for t in (10, 20, 30)])]), state(40, [entity(refusals=[refusal(t) for t in (10, 20, 30, 40)], blockers=["blocker_service_EAT_7"])]))
    rep = spy.report()
    assert rep["B_ii_false_fires"] == 1 and rep["B_ii_events"][0]["delivery_ticks"] == [25]
    clean = new_spy()
    clean.observe(state(39, [entity(refusals=[refusal(t) for t in (10, 20, 30)])]), state(40, [entity(refusals=[refusal(t) for t in (10, 20, 30, 40)], blockers=["blocker_service_EAT_7"])]))
    assert clean.report()["B_ii_false_fires"] == 0
    before = new_spy()                                                                                # a delivery BEFORE the streak started is not a false fire
    before.observe(state(4, [entity(gold=10)], {INN: building(0)}), state(5, [entity(gold=5)], {INN: building(5)}))
    before.observe(state(39, [entity(refusals=[refusal(t) for t in (10, 20, 30)])]), state(40, [entity(refusals=[refusal(t) for t in (10, 20, 30, 40)], blockers=["blocker_service_EAT_7"])]))
    assert before.report()["B_ii_false_fires"] == 0


def test_a_fresh_accepted_result_is_a_delivery_and_a_stale_one_is_not():
    result = NS(transaction_id="t1", accepted=True, source_kind="TOWN_SERVICE", source_id=INN)
    assert spy_mod.delivered(entity(), entity(results=[result]), {INN: building()}, {INN: building()}, "EAT", INN)
    assert not spy_mod.delivered(entity(results=[result]), entity(results=[result]), {INN: building()}, {INN: building()}, "EAT", INN)        # carried over from the prior state
    assert not spy_mod.delivered(entity(gold=10), entity(gold=5), {INN: building(0)}, {INN: building(0)}, "EAT", INN)                          # gold fell but the building was not paid


# ---------------------------------------------------------------- B(iii): still looping
def _filed_spy(filed_tick=40):
    spy = new_spy()
    spy.observe(state(filed_tick - 1, [entity(refusals=[refusal(t) for t in (10, 20, 30)])]), state(filed_tick, [entity(refusals=[refusal(t) for t in (10, 20, 30, 40)], blockers=["blocker_service_EAT_7"])]))
    return spy


def _execute(spy, tick):
    spy.router_call((entity(), {"action": "EAT", "target_id": INN}, tick), {})
    spy.observe(state(tick, [entity(blockers=["blocker_service_EAT_7"])]), state(tick + 1, [entity(blockers=["blocker_service_EAT_7"])]))


def test_an_undelivered_execution_more_than_100_ticks_after_the_filing_while_the_blocker_stands_is_still_looping():
    spy = _filed_spy()
    _execute(spy, 100)                                                                                 # 60 ticks after the filing: inside the allowance
    assert spy.report()["B_iii_still_looping"] == 0 and spy.report()["B_iii_executions_after_filing"] == 1
    _execute(spy, 142)                                                                                 # 102 ticks after the filing
    rep = spy.report()
    assert rep["B_iii_still_looping"] == 1 and rep["B_iii_events"][0] == {"subject": 1, "action": "EAT", "building": INN, "filed": 40, "execution_tick": 142}


def test_a_delivered_execution_a_removed_blocker_and_another_way_are_not_still_looping():
    spy = _filed_spy()
    spy.router_call((entity(), {"action": "EAT", "target_id": INN}, 200), {})
    spy.observe(state(200, [entity(gold=10, blockers=["blocker_service_EAT_7"])], {INN: building(0)}), state(201, [entity(gold=5, blockers=["blocker_service_EAT_7"])], {INN: building(5)}))      # paid: delivered
    assert spy.report()["B_iii_still_looping"] == 0
    gone = _filed_spy()
    gone.observe(state(100, [entity(blockers=["blocker_service_EAT_7"])]), state(101, [entity()]))     # the blocker stood no longer
    gone.router_call((entity(), {"action": "EAT", "target_id": INN}, 300), {})
    gone.observe(state(300, [entity()]), state(301, [entity()]))
    assert gone.report()["B_iii_still_looping"] == 0
    other = _filed_spy()
    other.router_call((entity(), {"action": "EAT", "target_id": INN + 1}, 300), {})
    other.observe(state(300, [entity(blockers=["blocker_service_EAT_7"])]), state(301, [entity(blockers=["blocker_service_EAT_7"])]))
    assert other.report()["B_iii_still_looping"] == 0


def test_a_served_held_rest_after_the_filing_is_not_still_looping_even_while_the_blocker_stands():       # change 2
    for kwargs in ({"outcome": "SUCCESS"}, {"lodged": INN}):
        spy = new_spy()
        spy.observe(state(39, [entity(refusals=[refusal(t, "REST") for t in (10, 20, 30)])]), state(40, [entity(refusals=[refusal(t, "REST") for t in (10, 20, 30, 40)], blockers=["blocker_service_REST_7"])]))
        for tick in range(150, 350):                                                                  # lodged or served and held for 200 ticks, the blocker still standing
            spy.router_call((entity(), {"action": "REST", "target_id": INN}, tick), {})
            spy.observe(state(tick, [entity(blockers=["blocker_service_REST_7"], action="REST", **kwargs)]), state(tick + 1, [entity(blockers=["blocker_service_REST_7"], action="REST", **kwargs)]))
        rep = spy.report()
        assert rep["B_iii_still_looping"] == 0 and rep["B_iii_held_executions_after_filing"] == 200 and rep["B_iii_executions_after_filing"] == 0, kwargs
    unheld = new_spy()                                                                                # the same executions with neither marker are undelivered: still looping
    unheld.observe(state(39, [entity(refusals=[refusal(t, "REST") for t in (10, 20, 30)])]), state(40, [entity(refusals=[refusal(t, "REST") for t in (10, 20, 30, 40)], blockers=["blocker_service_REST_7"])]))
    unheld.router_call((entity(), {"action": "REST", "target_id": INN}, 200), {})
    unheld.observe(state(200, [entity(blockers=["blocker_service_REST_7"], action="REST")]), state(201, [entity(blockers=["blocker_service_REST_7"], action="REST")]))
    assert unheld.report()["B_iii_still_looping"] == 1
    other_building = state(200, [entity(blockers=["blocker_service_REST_7"], action="REST", outcome="SUCCESS")])    # held marker for ANOTHER target (payload target_id is INN here): checked by is_held
    assert spy_mod.is_held(other_building.entities[1], "REST", INN) and not spy_mod.is_held(other_building.entities[1], "REST", INN + 1) and not spy_mod.is_held(other_building.entities[1], "EAT", INN)


def test_the_still_looping_boundary_is_more_than_100_ticks_after_the_filing():                           # designer mutant m4 (100 -> 99)
    at_100, at_101 = _filed_spy(40), _filed_spy(40)
    _execute(at_100, 140)                                                                              # exactly 100 ticks after the filing: allowed
    _execute(at_101, 141)                                                                              # 101: still looping
    assert at_100.report()["B_iii_still_looping"] == 0 and at_101.report()["B_iii_still_looping"] == 1


def test_a_sell_blocker_makes_b_iii_not_readable_never_zero_and_the_summary_says_not_measured(tmp_path):
    spy = new_spy()
    spy.observe(state(39, [entity(refusals=[refusal(t, "SELL") for t in (10, 20, 30)])]), state(40, [entity(refusals=[refusal(t, "SELL") for t in (10, 20, 30, 40)], blockers=["blocker_service_SELL_7"])]))
    rep = spy.report()
    assert rep["B_iii_still_looping"] == "not readable for SELL" and rep["B_iii_not_readable_for"] == ["SELL"]
    _all_cells(tmp_path, fix_spy={"B_i": {"filed": 1, "by_action": {"SELL": 1}}, "B_iii_still_looping": "not readable for SELL", "B_iii_not_readable_for": ["SELL"]})
    assert any(f.split(": ", 1)[1].startswith("NOT MEASURED: B(iii) is not readable for SELL") for f in summary.summarize(tmp_path)["flags"])


def test_the_router_wrapper_is_a_pass_through_and_restores():
    class Router:
        result = []

        @staticmethod
        def execute_action(entity, payload=None, current_tick=0, neighbor_view=None, context=None):
            return Router.result

    class Apply:
        @staticmethod
        def apply_generation(prior, update, *a, **k):
            return NS(tick=prior.tick + 1, entities={}, buildings={})

    original = Router.__dict__["execute_action"]
    spy = new_spy().install(Apply, Router)
    assert Router.execute_action(entity(), {"action": "EAT", "target_id": INN}, 5) is Router.result and spy.router_seen == {5: [(1, "EAT", INN)]}
    spy.restore()
    assert Router.__dict__["execute_action"].__func__ is original.__func__


# ---------------------------------------------------------------- the summary rules
def _doc(out, arm, name, final_hash, spy=None):
    base = out / arm
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{name}_plain.json").write_text(json.dumps({"final_hash": final_hash, "fatal": None, "logging_errors": []}))
    document = dict({"final_hash": final_hash, "fatal": None, "logging_errors": [], "spy_exceptions": [], "findings": [], "A_i": {"purse_half": 0, "bed_half": 0}, "B_i": {"filed": 0, "by_action": {}},
                     "B_ii_false_fires": 0, "B_iii_still_looping": 0, "A_ii": {"subjects_at_sleep_debt_98": 2, "follow_ups": []}, "vi": {}}, **(spy or {}))
    (base / f"{name}_spy.json").write_text(json.dumps(document))


def _all_cells(out, fix_hash="h", fix_spy=None):
    for world, seed, ticks in summary.CELLS:
        name = f"{world}_s{seed}_t{ticks}"
        _doc(out, "main", name, "h")
        _doc(out, "fix", name, fix_hash, fix_spy)


def test_the_summary_passes_a_neutral_run_and_voids_a_cell_whose_spy_hash_differs(tmp_path):
    _all_cells(tmp_path)
    doc = summary.summarize(tmp_path)
    assert doc["all_valid"] and doc["flags"] == [] and summary.main([str(tmp_path)]) == 0
    _doc(tmp_path, "fix", "crowded_frontier_s42_t5000", "h")
    (tmp_path / "fix" / "crowded_frontier_s42_t5000_spy.json").write_text(json.dumps({"final_hash": "other", "fatal": None, "logging_errors": [], "spy_exceptions": [], "findings": []}))
    assert not summary.summarize(tmp_path)["all_valid"]


def test_neutrality_stops_when_both_counts_are_zero_and_the_hash_differs_but_not_when_a_count_is_positive(tmp_path):
    _all_cells(tmp_path, fix_hash="different")
    flags = summary.summarize(tmp_path)["flags"]
    assert flags and all(f.split(": ", 1)[1].startswith("STOP: neutrality") for f in flags) and len(flags) == len(summary.CELLS) and summary.main([str(tmp_path)]) == 2
    other = tmp_path / "b"
    _all_cells(other, fix_hash="different", fix_spy={"A_i": {"purse_half": 2, "bed_half": 0}})                       # A(i) > 0: a different hash is expected, not a leak
    assert summary.summarize(other)["flags"] == []
    third = tmp_path / "c"
    _all_cells(third, fix_hash="different", fix_spy={"B_i": {"filed": 1, "by_action": {"EAT": 1}}})
    assert summary.summarize(third)["flags"] == []


def test_any_unresolved_way_closed_end_makes_a_not_measured_cell_and_never_a_neutrality_stop(tmp_path):
    _all_cells(tmp_path, fix_hash="different", fix_spy={"A_i": {"purse_half": 0, "bed_half": 0, "other_unresolved": 3}})
    flags = summary.summarize(tmp_path)["flags"]
    assert flags and all(f.split(": ", 1)[1].startswith("NOT MEASURED: A(i)") for f in flags) and not any("STOP" in f for f in flags) and summary.main([str(tmp_path)]) == 2
    main_side = tmp_path / "m"
    for world, seed, ticks in summary.CELLS:                                                           # an unresolved end on the MAIN arm also voids the neutrality judgement
        name = f"{world}_s{seed}_t{ticks}"
        _doc(main_side, "main", name, "h", {"A_i": {"purse_half": 0, "bed_half": 0, "other_unresolved": 1}})
        _doc(main_side, "fix", name, "different")
    assert all("NOT MEASURED: A(i)" in f for f in summary.summarize(main_side)["flags"])


def test_false_fires_and_still_looping_are_failures(tmp_path):
    _all_cells(tmp_path, fix_spy={"B_ii_false_fires": 1, "B_iii_still_looping": 2})
    flags = summary.summarize(tmp_path)["flags"]
    assert any("B(ii) false fires" in f for f in flags) and any("B(iii) still looping" in f for f in flags) and summary.main([str(tmp_path)]) == 2


# ---------------------------------------------------------------- the layout, the launcher and the startup resolution
def build_kit_layout(root, with_pinned_runner=True):
    (root / "tools" / "rpg_measure").mkdir(parents=True)
    for name in KIT_FILES:
        shutil.copy(KIT / name, root / "tools" / "rpg_measure" / name)
    if with_pinned_runner:
        (root / "tools" / "test_architecture").mkdir(parents=True)
        shutil.copy(REPO / "tools" / "test_architecture" / "pinned_runner.py", root / "tools" / "test_architecture" / "pinned_runner.py")
    return root


def test_the_spy_resolves_the_pinned_runner_from_the_tool_checkout_layout_and_a_flat_dir_cannot(tmp_path):
    kit = build_kit_layout(tmp_path / "kit")
    spy = load_from(kit / "tools" / "rpg_measure" / "k2fix_ownjob_spy.py", "_layout_ownjob_spy")
    assert hasattr(spy, "main") and hasattr(spy.load_sibling("arm_child")._pinned_runner(), "require_pinned")
    flat = tmp_path / "a" / "b" / "flat"
    flat.mkdir(parents=True)
    shutil.copy(KIT / "arm_child.py", flat / "arm_child.py")
    arm = load_from(flat / "arm_child.py", "_flat_arm_child_ownjob")
    with pytest.raises(FileNotFoundError):
        arm._pinned_runner()


def _launch(kit, tmp_path, **env):
    import os
    full = {**os.environ, "KIT": str(kit), "OUT": str(tmp_path / "out"), "TREE_MAIN": str(tmp_path / "tmain"), "TREE_FIX": str(tmp_path / "tfix"), "LAUNCH_DRY_RUN": "1", **env}
    return subprocess.run(["bash", str(kit / "tools" / "rpg_measure" / "k2fix_ownjob_launch.sh")], env=full, capture_output=True, text=True, timeout=60)


def test_the_launcher_prechecks_the_pinned_runner_refuses_a_used_tree_and_dry_runs_both_arms_of_every_cell(tmp_path):
    kit = build_kit_layout(tmp_path / "kit", with_pinned_runner=False)
    done = _launch(kit, tmp_path)
    assert done.returncode == 1 and "pinned_runner.py is missing" in done.stdout
    kit = build_kit_layout(tmp_path / "kit2")
    done = _launch(kit, tmp_path)
    lines = [l for l in done.stdout.splitlines() if l.startswith("CELL ")]
    assert done.returncode == 0 and len(lines) == 8 and sum(" main " in l for l in lines) == 4 and sum(" fix " in l for l in lines) == 4
    assert any("urban_political s42 2400t" in l for l in lines) and all(f"{kit}/tools/rpg_measure/k2fix_ownjob_spy.py" in l for l in lines)
    used = _launch(kit, tmp_path, TREE_FIX=str(tmp_path / "k2k3_tree2_main_d084b9248"))
    assert used.returncode == 18


# ---------------------------------------------------------------- kit v3: payload first, raw target recorded, every end followed, the collapse window
def _end(prior_entity, project_ended, f=None):
    spy = new_spy(funcs=f or funcs(covers=False))
    spy.observe(state(9, [prior_entity]), state(10, [entity(projects=[project_ended])]))
    return spy


def test_an_end_whose_objective_lacks_a_target_still_resolves_through_the_prior_payload_target_id():              # designer control 1
    objective = [NS(id="o1", target=None, kind=NS(value="reach_location"))]
    spy = _end(entity(projects=[project(objectives=objective)], action="REST"), project(objectives=objective, ended="WAY_CLOSED"))
    event = spy.report()["A_i"]["events"][0]
    assert event["building"] == INN and event["resolved_by"] == "payload" and event["half"] == "purse_half" and spy.report()["A_i"]["other_unresolved"] == 0


def test_the_prior_payload_is_tried_first_then_the_exact_tile_and_neither_resolving_is_other_unresolved():
    both = _end(entity(projects=[project()], action="EAT"), project(ended="WAY_CLOSED"))                           # payload names the inn AND the tile names it: the payload decides
    assert both.report()["A_i"]["events"][0]["resolved_by"] == "payload"
    tile_only = _end(entity(projects=[project()], action=None), project(ended="WAY_CLOSED"))                          # the task was cleared: the tile
    assert tile_only.report()["A_i"]["events"][0]["resolved_by"] == "tile" and tile_only.report()["A_i"]["events"][0]["building"] == INN
    prior = entity(projects=[project()], action="REST")
    not_a_building = NS(**{**vars(prior), "task": NS(payload={"action": "REST", "target_id": 999})})                  # a payload target that is not a building of the prior state: not used, the tile is
    assert _end(not_a_building, project(ended="WAY_CLOSED")).report()["A_i"]["events"][0]["resolved_by"] == "tile"
    nothing = _end(NS(**{**vars(prior), "task": NS(payload={"action": "REST", "target_id": 999})}), project(objectives=[NS(id="o1", target=[12.0, 12.0])], ended="WAY_CLOSED"))
    rep = nothing.report()["A_i"]
    assert rep["other_unresolved"] == 1 and rep["events"][0]["resolved_by"] is None and rep["events"][0]["building"] is None


def test_every_end_records_the_raw_target_the_objective_id_and_kind_and_the_prior_payload():
    objective = [NS(id="o7", target=[12.0, 12.0], kind=NS(value="reach_location"))]
    spy = _end(entity(projects=[project(objectives=objective, active="o7")], action="REST"), project(objectives=objective, active="o7", ended="WAY_CLOSED"))
    event = spy.report()["A_i"]["events"][0]
    assert (event["raw_target"], event["objective_id"], event["objective_kind"], event["prior_payload_action"], event["prior_payload_target_id"], event["project"]) == ([12.0, 12.0], "o7", "reach_location", "REST", INN, "p1")
    scalar = _end(entity(projects=[project()]), project(objectives=[NS(id="o1", target="7")], ended="WAY_CLOSED")).report()["A_i"]["events"][0]
    assert scalar["raw_target"] == "7"                                                                                  # a non-position target is recorded as it is


def test_every_end_is_followed_for_200_ticks_whatever_half_it_has():
    for f, half in ((funcs(covers=False), "purse_half"), (funcs(bed_refused=True), "bed_half"), (funcs(covers=True), "other")):
        spy = _end(entity(projects=[project()], action="REST"), project(ended="WAY_CLOSED"), f)
        spy.observe(state(10, [entity()]), state(11, [entity(debt=60.0)]))
        traces = spy.report()["A_ii"]["follow_ups"]
        assert len(traces) == 1 and traces[0]["half"] == half and "1" in traces[0]["samples"], half
    unresolved = _end(entity(projects=[project()]), project(objectives=[NS(id="o1", target=[12.0, 12.0])], ended="WAY_CLOSED"))
    assert unresolved.report()["A_ii"]["follow_ups"][0]["half"] == "other_unresolved"


def test_a_subject_reaching_the_collapse_line_keeps_its_last_200_ticks_before_the_first_reach():
    spy = new_spy()
    for t in range(1, 301):
        debt = 98.0 if t == 300 else 40.0 + t * 0.1                                                                    # below the line until tick 300
        spy.observe(state(t - 1, [entity(debt=debt)]), state(t, [entity(debt=debt, action="REST" if t % 2 else "SLEEP", lodged=INN if t > 250 else None, gold=5)]))
    window = spy.report()["A_ii"]["collapse_windows"]
    assert len(window) == 1 and window[0]["tick"] == 300 and window[0]["window_ticks"] == 200
    assert sorted(window[0]["samples"], key=int) == ["1", "10", "50", "100", "200"] and window[0]["samples"]["1"]["tick"] == 299 and window[0]["samples"]["200"]["tick"] == 100
    assert window[0]["sleep_action_ticks"] + window[0]["rest_action_ticks"] == 200 and window[0]["lodged_ticks"] == 49 and spy.report()["A_ii"]["subjects_at_sleep_debt_98"] == 1
    again = new_spy()                                                                                                     # a second reach does not open a second window
    for t in range(1, 6):
        again.observe(state(t - 1, [entity(debt=99.0)]), state(t, [entity(debt=99.0)]))
    assert len(again.report()["A_ii"]["collapse_windows"]) == 1


def test_the_cell_subset_override_runs_and_summarizes_only_the_named_cells(tmp_path, monkeypatch):
    kit = build_kit_layout(tmp_path / "kit")
    done = _launch(kit, tmp_path, OWNJOB_CELLS="frontier_living_world:42:5000")
    lines = [l for l in done.stdout.splitlines() if l.startswith("CELL ")]
    assert done.returncode == 0 and len(lines) == 2 and all("frontier_living_world s42 5000t" in l for l in lines) and {" main " in l for l in lines} == {True, False}
    monkeypatch.setenv("OWNJOB_CELLS", "frontier_living_world:42:5000")
    _doc(tmp_path, "main", "frontier_living_world_s42_t5000", "h")
    _doc(tmp_path, "fix", "frontier_living_world_s42_t5000", "different", {"A_i": {"purse_half": 1, "bed_half": 0, "other_unresolved": 0}})
    doc = summary.summarize(tmp_path)
    assert [c["cell"] for c in doc["cells"]] == ["frontier_living_world_s42_t5000"] and doc["all_valid"] and doc["flags"] == []
    monkeypatch.delenv("OWNJOB_CELLS")
    assert len(summary.configured_cells()) == 4
