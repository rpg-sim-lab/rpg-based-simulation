"""Unit controls for the K2/K3 re-count kit (tools/rpg_measure/k2k3_count_*): planted positives, negatives and mutants for the fixed count definitions
(rpg-designer-k2-k3-count-definitions.md, sha256 992b7ce37e1a...940cd5855). No simulation is run here."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

KIT = Path(__file__).resolve().parents[2] / "tools" / "rpg_measure"


def load(name):
    spec = importlib.util.spec_from_file_location(f"_t_{name}", KIT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    import sys
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


logic = load("k2k3_count_logic")
spy_mod = load("k2k3_count_spy")
K = 10


def run_ticks(tracker, dispatch_ticks, deliver_at=(), end=None, action="EAT", b=7, subject=1):
    """Feed one subject: it dispatches (action, b) on every tick in ``dispatch_ticks``; a service is delivered on the ticks in ``deliver_at``."""
    last = end if end is not None else max(dispatch_ticks) + 2
    for t in range(1, last + 1):
        tracker.step(t, subject, True, True, (action, b) if t in dispatch_ticks else None, [(action, b)] if t in deliver_at else [], {(action, b): ["None"]}, {b: "inn"})
    tracker.finish(last)


# ---------------------------------------------------------------- K2
def test_k2_planted_positive_a_run_over_100_counts():
    t = logic.K2Tracker(K)
    run_ticks(t, set(range(10, 131)))                       # 121 consecutive failing dispatches
    s = t.summary()
    assert s["k2_count"] == 1 and s["runs_over_100"] == 1 and s["runs_all"] == 1
    assert s["long_runs"][0]["length"] == 121 and s["long_runs"][0]["first_failed"] == 10 and s["long_runs"][0]["last_failed"] == 130   # a dispatch at t is judged on the apply of t+1


def test_k2_run_of_exactly_100_is_not_counted_and_101_is():
    for span, expect in ((100, 0), (101, 1)):                # span consecutive failing dispatches => run length span; only > 100 counts
        t = logic.K2Tracker(K)
        run_ticks(t, set(range(10, 10 + span)))
        assert t.summary()["k2_count"] == expect


def test_k2_delivered_service_ends_the_run():
    t = logic.K2Tracker(K)
    run_ticks(t, set(range(10, 60)) | {70}, deliver_at={40})   # delivered on tick 40 ends the run; the earlier failing dispatches stay a run
    s = t.summary()
    assert s["runs"][0]["ended_by"] == "delivered" and s["runs"][0]["length"] == 29      # dispatches 10..38 failed; the delivery on tick 40 judges the dispatch of 39
    t2 = logic.K2Tracker(K)
    run_ticks(t2, set(range(10, 200)), deliver_at={60})         # Amendment 2: the later executions of the SAME attempt are held repeats, never a new run
    assert t2.summary()["k2_count"] == 0 and t2.summary()["held_repeats"]["EAT"] > 100


def test_k2_gap_larger_than_k_splits_runs():
    t = logic.K2Tracker(K)
    run_ticks(t, set(range(10, 80)) | set(range(95, 170)))   # a 15-tick gap with no dispatch: two runs
    assert t.summary()["runs_all"] == 2


def test_k2_gap_of_exactly_k_keeps_the_run():
    t2 = logic.K2Tracker(K)
    run_ticks(t2, set(range(10, 60)) | set(range(70, 200)))  # failed ticks 59 and 70: 11 apart (> K): split
    assert t2.summary()["runs_all"] == 2
    t3 = logic.K2Tracker(K)
    run_ticks(t3, set(range(10, 60)) | set(range(69, 200)))  # failed ticks 59 and 69: exactly K apart: ONE run
    assert t3.summary()["runs_all"] == 1


def test_k2_different_building_or_action_is_a_different_run():
    t = logic.K2Tracker(K)
    for tick in range(1, 220):
        t.step(tick, 1, True, True, ("EAT", 7 if tick % 2 else 8), [], {}, {7: "inn", 8: "inn"})   # alternates: each triple's failed ticks are 2 apart, same run per building
    t.finish(220)
    s = t.summary()
    assert {(r["action"], r["building"]) for r in s["runs"]} == {("EAT", 7), ("EAT", 8)}


def test_k2_death_ends_the_run_and_is_recorded():
    t = logic.K2Tracker(K)
    for tick in range(1, 50):
        t.step(tick, 1, True, True, ("REST", 3), [], {}, {3: "inn"})
    t.step(50, 1, True, False, None, [], {}, {})
    s = t.summary()
    assert s["runs"][0]["ended_by"] == "died"
    t2 = logic.K2Tracker(K)
    t2.step(1, 1, True, True, ("REST", 3), [], {}, {})
    t2.step(2, 1, True, True, ("REST", 3), [], {}, {})
    t2.step(3, 1, False, False, None, [], {}, {})
    assert t2.summary()["runs"][0]["ended_by"] == "removed"


def test_k2_reasons_are_recorded_as_found_including_none_and_absent():
    t = logic.K2Tracker(K)
    for tick in range(1, 30):
        t.step(tick, 1, True, True, ("EAT", 7), [], {("EAT", 7): ["None"] if tick < 15 else ["absent"]}, {7: "inn"})
    t.finish(30)
    reasons = t.summary()["runs"][0]["reasons"]
    assert set(reasons) == {"None", "absent"}


def test_k2_denominators():
    t = logic.K2Tracker(K)
    run_ticks(t, set(range(10, 30)))
    s = t.summary()
    assert s["subjects_with_dispatch"] == 1 and s["alive_subject_ticks"] > 0 and s["dispatch_ticks"] == 20 and s["runs_over_10"] == 1


@pytest.mark.parametrize("mutant", ["no_delivered_end", "gap_ignored"])
def test_k2_mutants_are_caught(mutant):
    """A mutated tracker must fail the planted controls (the controls are not vacuous)."""
    t = logic.K2Tracker(K)
    if mutant == "no_delivered_end":
        t._delivered = lambda key, tick: None
        run_ticks(t, set(range(10, 200)), deliver_at={60})
        assert t.summary()["runs"][0]["ended_by"] != "delivered"          # the real tracker ends the run as delivered (control above): the mutant does not
    else:
        t = logic.K2Tracker(10 ** 6)
        run_ticks(t, set(range(10, 80)) | set(range(95, 170)))
        assert t.summary()["runs_all"] == 1                               # the real tracker gives 2 (control above)


# ---------------------------------------------------------------- K3
def dec(eid, tick, need, klass):
    return {"eid": eid, "tick": tick, "need": need, "klass": klass}


def test_k3_classes():
    assert logic.classify_k3({"threat": True}, {"same_kind_current_live": False, "current_project_id": None}) == "excluded_threat"
    assert logic.classify_k3({"threat": False}, {"same_kind_current_live": True, "current_project_id": "p"}) == "win"
    assert logic.classify_k3({"threat": False}, {"same_kind_current_live": False, "current_project_id": "p"}) == "loss_L1"
    assert logic.classify_k3({"threat": False}, {"same_kind_current_live": False, "current_project_id": None}) == "loss_L2"


def test_k3_planted_positive_counts_losses_and_episodes():
    s = logic.k3_summary([dec(1, 10, "hunger", "loss_L1"), dec(1, 20, "hunger", "loss_L2"), dec(1, 30, "hunger", "win"), dec(1, 40, "hunger", "loss_L1"),
                          dec(2, 10, "fatigue", "loss_L2"), dec(2, 15, "fatigue", "excluded_threat"), dec(3, 5, "hunger", "excluded_threat")])
    assert s["k3_count"] == 4
    assert s["per_need"]["hunger"]["k3_count"] == 3 and s["per_need"]["hunger"]["episodes"] == 2          # 10-20 one episode, a win, then 40
    assert s["per_need"]["fatigue"]["k3_count"] == 1 and s["per_need"]["fatigue"]["excluded_threat"] == 1
    assert s["per_need"]["hunger"]["decisions"] == 5 and s["per_need"]["hunger"]["subjects"] == 2
    assert s["per_need"]["hunger"]["excluded_threat"] == 1


def test_k3_excluded_does_not_break_an_episode_and_win_does():
    s = logic.k3_summary([dec(1, 1, "hunger", "loss_L1"), dec(1, 2, "hunger", "excluded_threat"), dec(1, 3, "hunger", "loss_L1")])
    assert s["per_need"]["hunger"]["episodes"] == 1


# ---------------------------------------------------------------- spy against fake states
def fake_entity(eid, hunger=0.0, sleep=0.0, gold=10, action=None, target=None, results=(), alive=True, project=None, projects=None, lodged=None):
    task = NS(work_kind="ENTITY_ACT", payload={} if action is None else {"action": action, "target_id": target})
    return NS(id=eid, task=task, biological=NS(hunger=hunger, sleep_debt=sleep), inventory=NS(gold=gold, items=()), identity=NS(latest_intent_results=tuple(results)),
              combat=NS(alive=alive), navigation=NS(lodged_in=lodged), strategic=NS(current_project_id=project, projects=projects or {}, blockers={}))


def building(purse=0, kind="inn"):
    return NS(kind=kind, inventory=NS(gold=purse, items=()))


def fake_state(tick, entities, buildings=None):
    return NS(tick=tick, entities={e.id: e for e in entities}, buildings=buildings if buildings is not None else {7: building()})


SERVICE_KINDS = {"REST": ["home", "inn"], "EAT": ["inn"], "SELL": ["shop"], "REPAIR": ["blacksmith"]}


def make_spy(present=False, acting=False, same_kind=lambda p, k: str(getattr(p.kind, "value", p.kind)) == str(getattr(k, "value", k))):
    return spy_mod.CountSpy(K, frozenset({"EAT", "REST", "SELL", "REPAIR"}), same_kind, lambda h, s: h >= 57.0 or s >= 58.8, lambda e, s: present, lambda e, s: acting, ("ACTIVE", "SUSPENDED"), SERVICE_KINDS)


def test_spy_k2_planted_positive_over_fake_states_and_delivery_channels():
    spy = make_spy()
    prior = fake_state(0, [fake_entity(1, action="EAT", target=7)])
    for t in range(1, 140):
        new = fake_state(t, [fake_entity(1, hunger=60.0, action="EAT", target=7)])
        spy.observe(prior, new)
        prior = new
    spy.finish(140)
    rep = spy.report()
    assert rep["k2"]["k2_count"] == 1 and rep["reach"]["service_dispatches_seen"] > 100
    assert rep["refusal_reasons_seen"] == {"absent": rep["refusal_reasons_seen"]["absent"]}
    assert rep["service_actions_read"] == ["EAT", "REPAIR", "REST", "SELL"]
    # a PAID meal (subject gold down, the inn's purse up by the same) ends the run (Amendment 1, A1); a bare hunger drop would not (control (b))
    spy2 = make_spy()
    prior = fake_state(0, [fake_entity(1, hunger=60.0, gold=10, action="EAT", target=7)])
    for t in range(1, 30):
        paid = t == 20
        new = fake_state(t, [fake_entity(1, hunger=30.0 if paid else 60.0, gold=5 if paid else 10, action="EAT", target=7)], {7: building(purse=5 if paid else 0)})
        spy2.observe(prior, new)
        prior = new
    spy2.finish(30)
    assert spy2.report()["k2"]["runs"][0]["ended_by"] == "delivered" and spy2.report()["delivered_channel_counts"].get("paid_transfer", 0) >= 1


def pair_result(prior, ent, prior_purse=0, purse=0, b=7, action="EAT", pair_building=7):
    return spy_mod.delivered_pairs(prior, ent, [(action, b)], {7: building(prior_purse), 8: building(prior_purse)}, {7: building(purse if pair_building == 7 else prior_purse), 8: building(purse if pair_building == 8 else prior_purse)})


def test_spy_k2_accepted_result_for_the_building_is_delivered_and_refusal_reason_recorded():
    ok = pair_result(fake_entity(1, hunger=60.0), fake_entity(1, hunger=60.0, results=[NS(source_kind="TOWN_SERVICE", source_id=7, accepted=True, reason=None)]))
    assert ok[0] == [("EAT", 7)] and ok[2] == {"accepted_result": 1}
    refused = pair_result(fake_entity(1, hunger=60.0), fake_entity(1, hunger=60.0, results=[NS(source_kind="TOWN_SERVICE", source_id=7, accepted=False, reason=None)]))
    assert refused[0] == [] and refused[1] == {("EAT", 7): ["None"]}
    other_building = pair_result(fake_entity(1), fake_entity(1, results=[NS(source_kind="TOWN_SERVICE", source_id=9, accepted=True, reason=None)]))
    assert other_building[0] == []


# ---- Amendment 1, A1: the service's OWN change at b (controls a-d)
def test_a_rest_refused_while_sleep_debt_falls_with_no_payment_is_not_delivered_and_the_run_grows():            # control (a)
    r = pair_result(fake_entity(1, sleep=50.0), fake_entity(1, sleep=40.0), action="REST")
    assert r[0] == [] and r[2] == {"need_drop_unpaid": 1}
    spy = make_spy()
    prior = fake_state(0, [fake_entity(1, sleep=90.0, action="REST", target=7)])
    for t in range(1, 140):
        new = fake_state(t, [fake_entity(1, sleep=90.0 - 0.1 * t, action="REST", target=7)])          # sleeps rough: sleep_debt falls by itself, nothing is paid
        spy.observe(prior, new)
        prior = new
    spy.finish(140)
    rep = spy.report()
    assert rep["k2"]["k2_count"] == 1 and rep["delivered_channel_counts"].get("need_drop_unpaid", 0) > 100 and "paid_transfer" not in rep["delivered_channel_counts"]


def test_an_eat_refused_while_hunger_falls_from_carried_food_with_gold_unchanged_is_not_delivered():            # control (b)
    r = pair_result(fake_entity(1, hunger=80.0, gold=10), fake_entity(1, hunger=60.0, gold=10))
    assert r[0] == [] and r[2] == {"need_drop_unpaid": 1}


def test_an_eat_paid_to_the_building_is_delivered():                                                          # control (c): subject -5, b +5
    r = pair_result(fake_entity(1, hunger=80.0, gold=10), fake_entity(1, hunger=60.0, gold=5), prior_purse=0, purse=5)
    assert r[0] == [("EAT", 7)] and r[2] == {"paid_transfer": 1}
    short = pair_result(fake_entity(1, hunger=80.0, gold=10), fake_entity(1, hunger=60.0, gold=5), prior_purse=0, purse=3)   # the purse must rise by at least the subject's loss
    assert short[0] == []


def test_an_eat_paid_at_another_building_is_not_delivered_for_b():                                             # control (d)
    r = pair_result(fake_entity(1, hunger=80.0, gold=10), fake_entity(1, hunger=60.0, gold=5), prior_purse=0, purse=5, pair_building=8)
    assert r[0] == []


def test_a_sell_delivers_on_the_reverse_payment_or_the_item_moving():
    ent0, ent1 = fake_entity(1, gold=5), fake_entity(1, gold=9)
    r = spy_mod.delivered_pairs(ent0, ent1, [("SELL", 7)], {7: building(10, "shop")}, {7: building(6, "shop")})
    assert r[0] == [("SELL", 7)] and r[2] == {"paid_transfer": 1}
    nothing = spy_mod.delivered_pairs(ent0, ent1, [("SELL", 7)], {7: building(10, "shop")}, {7: building(10, "shop")})
    assert nothing[0] == []


# ---- Amendment 1, A2: per-action dispatch visibility, the router channel (controls e-f)
def test_an_accepted_eat_result_with_no_seen_dispatch_is_a_miss_and_eat_is_not_measured():                    # control (e)
    spy = make_spy()
    prior = fake_state(0, [fake_entity(1)])
    new = fake_state(1, [fake_entity(1, results=[NS(source_kind="TOWN_SERVICE", source_id=7, accepted=True, reason=None)])])       # an accepted inn service, no task and no router call before it
    spy.observe(prior, new)
    rep = spy.report()
    assert rep["dispatch_visibility"]["EAT"]["misses"] == 1 and rep["dispatch_visibility"]["EAT"]["measured"] is False
    assert rep["dispatch_visibility"]["REST"]["measured"] is False                                          # an unattributed town-service result is a miss for every action the inn serves
    assert rep["dispatch_visibility"]["SELL"]["measured"] is True                                           # a shop action is not touched by an inn result
    assert rep["k2"]["k2_count_by_action"]["EAT"] is None and "EAT" in rep["k2"]["not_measured_actions"]    # NOT MEASURED, never 0


def test_a_seen_dispatch_makes_the_action_measured():
    spy2 = make_spy()
    spy2.observe(fake_state(0, []), fake_state(1, [fake_entity(1, action="EAT", target=7)]))                     # the post-apply task of tick 1 is the dispatch of t=1 ...
    spy2.observe(fake_state(1, [fake_entity(1, action="EAT", target=7)]), fake_state(2, [fake_entity(1, results=[NS(source_kind="TOWN_SERVICE", source_id=7, accepted=True, reason=None)])]))
    vis2 = spy2.report()["dispatch_visibility"]["EAT"]
    assert vis2["measured"] is True and vis2["seen_by_task"] == 1 and vis2["accepted_results"] == 1


def test_a_router_channel_dispatch_with_no_post_apply_task_still_opens_and_extends_a_run():                  # control (f)
    spy = make_spy()
    prior = fake_state(0, [fake_entity(1)])
    for t in range(1, 150):
        spy.router_call((fake_entity(1), {"action": "EAT", "target_id": 7}, t - 1), {})                        # executed while the apply of tick t is produced; the post-apply task never shows EAT
        new = fake_state(t, [fake_entity(1, hunger=60.0)])
        spy.observe(prior, new)
        prior = new
    spy.finish(150)
    rep = spy.report()
    assert rep["k2"]["k2_count"] == 1 and rep["k2"]["long_runs"][0]["action"] == "EAT" and rep["dispatch_visibility"]["EAT"]["seen_by_router"] > 100 and rep["dispatch_visibility"]["EAT"]["seen_by_task"] == 0
    assert rep["reach"]["router_service_calls"] == 149


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

    class Score:
        @staticmethod
        def apply_modifiers(entity, state, scores):
            return []

    orig = Router.__dict__["execute_action"]
    spy = make_spy().install(Apply, Score, Router)
    assert Router.execute_action(fake_entity(1), {"action": "EAT", "target_id": 7}, 5) is Router.result
    assert Router.execute_action(fake_entity(1), {"action": "WORK"}, 5) is Router.result
    assert spy.router_calls == 2 and spy.router_service_calls == 1 and spy.router_seen == {5: [(1, "EAT", 7)]}
    spy.restore()
    assert Router.__dict__["execute_action"].__func__ is orig.__func__


def test_the_last_decision_of_a_tick_wins_and_is_stated():
    spy = make_spy()
    ent = fake_entity(1, hunger=70.0)
    for utility in (80.0, 90.0):
        spy.decision(ent, fake_state(10, [ent]), [NS(kind=NS(value="hunger"), utility=utility, target_id=7, target_pos=None)])
    assert spy.duplicate_decisions == 1 and spy.pending_decisions[1]["utility"] == 90.0
    assert "last decision of a tick wins" in spy.report()["decision_policy"]


# ---- Amendment 1, A3: the 7-cell K3 rule and the rule text
def vcell(name, seed, stage, k3=0, k2=0, valid=True, not_measured=()):
    return {"name": name, "world": "frontier_living_world", "seed": seed, "stage": stage, "valid": valid, "k2_count_measured": k2, "k2_not_measured": list(not_measured), "k3_count": k3}


S42 = [vcell("crowded_frontier_s42", 42, 1), vcell("frontier_living_world_s42", 42, 1), vcell("urban_political_s42", 42, 1)]
S46 = [vcell("urban_political_s46", 46, 1)]
STAGE2 = [vcell(f"frontier_living_world_s{s}", s, 2) for s in (43, 44, 45, 46)]


def test_the_close_rule_text_names_the_amendment_and_cannot_close_k3_with_only_the_s42_cells():
    assert "Amendment 1 e6cc644c" in logic.RULE_SOURCE and "992b7ce3" in logic.RULE_SOURCE
    only_s42 = logic.close_verdicts(S42 + S46)
    assert only_s42["k3"].startswith("NOT PROPOSED") and "PROPOSE CLOSE" not in only_s42["k3"] and only_s42["rule_source"] == logic.RULE_SOURCE


def test_the_k3_close_needs_all_seven_valid_cells_at_zero():
    assert logic.close_verdicts(S42 + S46 + STAGE2)["k3"] == "PROPOSE CLOSE (K3 = 0 in all 7 cells)"
    assert logic.close_verdicts(S42 + S46 + STAGE2[:3])["k3"].startswith("NOT PROPOSED")
    bad = STAGE2[:3] + [vcell("frontier_living_world_s46", 46, 2, valid=False)]
    assert logic.close_verdicts(S42 + S46 + bad)["k3"].startswith("NOT PROPOSED")
    assert logic.close_verdicts(S42 + S46 + STAGE2[:3] + [vcell("frontier_living_world_s46", 46, 2, k3=2)])["k3"].startswith("STAYS HARD")
    dup = [STAGE2[0]] * 4                                                            # four copies of one cell are one cell, not four
    assert logic.close_verdicts(S42 + S46 + dup)["k3"].startswith("NOT PROPOSED")


def test_a_nonzero_s42_k3_total_stays_hard_without_stage_two_and_an_invalid_s42_cell_is_void():
    nonzero = [vcell("crowded_frontier_s42", 42, 1, k3=1)] + S42[1:]
    assert logic.close_verdicts(nonzero + S46)["k3"].startswith("STAYS HARD")
    assert logic.close_verdicts([dict(S42[0], valid=False)] + S42[1:] + S46)["k3"].startswith("VOID")


def test_k2_is_not_proposed_for_close_while_an_action_is_not_measured_and_stays_hard_on_a_count():
    assert logic.close_verdicts(S42 + S46)["k2"].startswith("PROPOSE CLOSE")
    nm = logic.close_verdicts(S42 + [vcell("urban_political_s46", 46, 1, not_measured=["EAT"])])
    assert nm["k2"].startswith("NOT PROPOSED") and "EAT" in nm["k2"]
    assert logic.close_verdicts(S42 + [vcell("urban_political_s46", 46, 1, k2=1)])["k2"].startswith("STAYS HARD")
    assert logic.close_verdicts(S42)["k2"].startswith("VOID")


def test_the_visibility_summary_marks_an_unseen_action_with_results_and_a_wrong_building_kind():
    vis = logic.DispatchVisibility({"EAT": "TOWN_SERVICE", "REST": "TOWN_SERVICE", "SELL": "SHOP_SELL"}, {"EAT": ["inn"], "REST": ["inn", "home"], "SELL": ["shop"]})
    assert vis.candidates("TOWN_SERVICE", "home") == ["REST"]
    vis.note_accepted("SHOP_SELL", 3, "shop", [])
    s = vis.summary()
    assert s["SELL"]["measured"] is False and s["EAT"]["measured"] is True and s["EAT"]["visibility_tested"] is False
def k3_cycle(spy, entity_state_d, entity_state_d1, tick_d=10):
    """One decision at state tick d, read on row d+1."""
    spy.decision(entity_state_d, fake_state(tick_d, [entity_state_d]), [NS(kind=NS(value="hunger"), utility=80.0, target_id=7, target_pos=None)])
    spy.observe(fake_state(tick_d, [entity_state_d]), fake_state(tick_d + 1, [entity_state_d1]))


def proj(kind, status="ACTIVE"):
    return NS(kind=NS(value=kind), status=status)


def test_spy_k3_planted_positive_l1_l2_win_and_threat():
    spy = make_spy()
    k3_cycle(spy, fake_entity(1, hunger=70.0), fake_entity(1, project="p", projects={"p": proj("combat")}))                      # L1: another kind is current
    k3_cycle(spy, fake_entity(2, hunger=70.0), fake_entity(2), tick_d=20)                                                          # L2: nothing current
    k3_cycle(spy, fake_entity(3, hunger=70.0), fake_entity(3, project="q", projects={"q": proj("hunger")}), tick_d=30)             # win
    k3_cycle(spy, fake_entity(4, hunger=70.0), fake_entity(4, project="r", projects={"r": proj("combat")}), tick_d=40)             # (L1 again, other subject)
    rep = spy.report()
    pn = rep["k3"]["per_need"]["hunger"]
    assert (pn["wins"], pn["loss_L1"], pn["loss_L2"], pn["k3_count"], pn["subjects"]) == (1, 2, 1, 3, 4)
    assert rep["reach"]["escalated_need_wins"] == 4
    threat = make_spy(present=True)
    k3_cycle(threat, fake_entity(1, hunger=70.0), fake_entity(1))
    assert threat.report()["k3"]["per_need"]["hunger"]["excluded_threat"] == 1 and threat.report()["k3"]["k3_count"] == 0


def test_spy_k3_not_escalated_winner_is_not_a_decision_and_suspended_same_kind_is_a_win_only_if_live():
    spy = make_spy()
    spy.decision(fake_entity(1, hunger=40.0), fake_state(5, [fake_entity(1, hunger=40.0)]), [NS(kind=NS(value="hunger"), utility=80.0, target_id=7, target_pos=None)])
    assert spy.report()["reach"]["escalated_need_wins"] == 0                                   # below raw >= 0.6 x 95
    k3_cycle(spy, fake_entity(1, hunger=70.0), fake_entity(1, project="p", projects={"p": proj("hunger", "SUSPENDED")}))
    assert spy.report()["k3"]["per_need"]["hunger"]["wins"] == 1                                  # SUSPENDED is live in the tree's own LIVE_PROJECT_STATUSES


def test_spy_k3_fatigue_uses_the_sleep_test_and_winner_must_have_a_target_and_utility_20():
    spy = make_spy()
    ent = fake_entity(1, sleep=70.0)
    spy.decision(ent, fake_state(5, [ent]), [NS(kind=NS(value="fatigue"), utility=30.0, target_id=None, target_pos=(1, 1))])
    assert spy.report()["reach"]["escalated_need_wins"] == 1
    spy2 = make_spy()
    spy2.decision(ent, fake_state(5, [ent]), [NS(kind=NS(value="fatigue"), utility=10.0, target_id=7, target_pos=None)])      # below the selection's utility 20
    spy2.decision(ent, fake_state(5, [ent]), [NS(kind=NS(value="fatigue"), utility=50.0, target_id=None, target_pos=None)])    # no target
    assert spy2.report()["reach"]["escalated_need_wins"] == 0


def test_spy_wrappers_are_pass_through_and_restore():
    class Apply:
        @staticmethod
        def apply_generation(prior, update, *a, **k):
            return NS(tick=prior.tick + 1, entities={}, buildings={})

    class Score:
        marker = None

        @staticmethod
        def apply_modifiers(entity, state, scores):
            return Score.marker

    Score.marker = []
    orig_a, orig_s = Apply.__dict__["apply_generation"], Score.__dict__["apply_modifiers"]
    spy = make_spy().install(Apply, Score)
    assert Score.apply_modifiers(NS(id=1, biological=NS(hunger=0.0, sleep_debt=0.0), strategic=NS(current_project_id=None)), fake_state(1, []), []) is Score.marker
    out = Apply.apply_generation(NS(tick=3, entities={}, buildings={}), None)
    assert out.tick == 4
    spy.restore()
    assert Apply.__dict__["apply_generation"].__func__ is orig_a.__func__ and Score.__dict__["apply_modifiers"].__func__ is orig_s.__func__


def test_the_tree_exposes_every_field_the_kit_reads():
    """Kit finding check against THIS checkout (the frozen tree is a git archive of the same head): a name the tree lacks is a finding, never a substitution."""
    import sys
    root = str(KIT.parents[1])
    sys.path.insert(0, root)
    try:
        facts = spy_mod.read_tree_facts()
    finally:
        sys.path.remove(root)
    assert facts["findings"] == []
    assert set(facts["service_kinds"]) >= {"EAT", "REST", "SELL", "REPAIR"} and facts["k"] == 10


# ---- Amendment 2, A4: a held service repeat is not a dispatch (controls g-j)
def spy_run(spy, ticks, make_state, start=1):
    prior = make_state(start - 1)
    for t in range(start, start + ticks):
        new = make_state(t)
        spy.observe(prior, new)
        prior = new
    return prior


def test_a_rest_paid_once_then_repeated_for_200_ticks_gives_no_run_and_200_held_repeats():                    # control (g)
    spy = make_spy()
    def make(t):                                         # the bed is paid at t=2 (subject -5, inn +5); every later tick executes REST again with no payment
        return fake_state(t, [fake_entity(1, sleep=80.0, gold=5 if t >= 2 else 10, action="REST", target=7)], {7: building(purse=5 if t >= 2 else 0)})
    spy_run(spy, 210, make)
    spy.finish(211)
    rep = spy.report()
    assert rep["k2"]["runs_all"] == 0 and rep["k2"]["k2_count"] == 0
    assert rep["k2"]["held_repeats"]["REST"] >= 200 and rep["delivered_channel_counts"]["held_repeat"] >= 200


def test_a_rest_executed_200_ticks_and_never_delivered_still_gives_a_run():                                   # control (h)
    spy = make_spy()
    spy_run(spy, 205, lambda t: fake_state(t, [fake_entity(1, sleep=80.0, action="REST", target=7)]))
    spy.finish(206)
    rep = spy.report()
    assert rep["k2"]["k2_count"] == 1 and rep["k2"]["long_runs"][0]["length"] > 100 and rep["k2"]["held_repeats"] == {}


def test_a_rest_with_the_bed_granted_lodged_in_b_is_held_from_the_first_tick_with_no_payment_seen():            # control (i)
    spy = make_spy()
    spy_run(spy, 210, lambda t: fake_state(t, [fake_entity(1, sleep=80.0, action="REST", target=7, lodged=7)]))
    spy.finish(211)
    rep = spy.report()
    assert rep["k2"]["runs_all"] == 0 and rep["k2"]["held_repeats"]["REST"] >= 200
    other = make_spy()                                                                                      # lodged elsewhere is no evidence for b
    spy_run(other, 210, lambda t: fake_state(t, [fake_entity(1, sleep=80.0, action="REST", target=7, lodged=8)], {7: building(), 8: building()}))
    other.finish(211)
    assert other.report()["k2"]["k2_count"] == 1


def test_after_the_task_changes_target_a_new_undelivered_rest_at_b_prime_is_a_new_run():                      # control (j)
    spy = make_spy()
    def make(t):
        if t < 60:                                       # REST at 7, paid at t=2, then held
            return fake_state(t, [fake_entity(1, sleep=80.0, gold=5 if t >= 2 else 10, action="REST", target=7)], {7: building(purse=5 if t >= 2 else 0), 8: building()})
        return fake_state(t, [fake_entity(1, sleep=80.0, gold=5, action="REST", target=8)], {7: building(purse=5), 8: building()})      # a NEW target, never delivered
    spy_run(spy, 230, make)
    spy.finish(231)
    runs = spy.report()["k2"]["runs"]
    assert [(r["action"], r["building"]) for r in runs] == [("REST", 8)] and runs[0]["length"] > 100


def test_a_held_attempt_that_stops_and_restarts_is_a_new_attempt():
    t = logic.K2Tracker(K)
    for tick in range(1, 40):
        t.step(tick, 1, True, True, {("REST", 7)} if tick < 20 or tick > 25 else set(), [("REST", 7)] if tick == 3 else [], {}, {7: "inn"})
    t.finish(40)
    s = t.summary()
    assert s["runs_all"] == 2 and s["runs"][0]["ended_by"] == "delivered" and s["runs"][1]["first_failed"] == 26   # the first attempt: one failure, delivered, then held 3..19; a gap; REST again at b is a NEW attempt with no delivery: failures from the restart
    assert s["held_repeats"]["REST"] >= 15


def run_context_of(**kw):
    return spy_mod.run_context(fake_entity(1, sleep=kw.get("sleep", 70.0), action="REST", target=7, lodged=kw.get("lodged")), ("REST", 7))


def test_the_run_contexts_carry_lodged_in_sleep_debt_and_payload():
    ctx = run_context_of(lodged=7)
    assert ctx["lodged_in"] == 7 and ctx["sleep_debt"] == 70.0 and ctx["payload"] == {"action": "REST", "target_id": 7}
    spy = make_spy()
    spy_run(spy, 30, lambda t: fake_state(t, [fake_entity(1, sleep=80.0, action="REST", target=7)]))
    spy.finish(31)
    run = spy.report()["k2"]["runs"][0]
    assert run["first_context"]["sleep_debt"] == 80.0 and run["last_context"]["payload"]["action"] == "REST"


def _neg_cell(tmp_path, runs, hash_spy="h"):
    import json
    base = {"final_hash": "h", "logging_errors": [], "fatal": None}
    (tmp_path / "urban_political_s42_plain.json").write_text(json.dumps(base))
    spy = dict(base, final_hash=hash_spy, probe_errors=[], spy_exceptions=[], findings=[], reach={"service_dispatches_seen": 5, "escalated_need_wins": 0, "router_service_calls": 5},
               k2={"runs": runs, "held_repeats": {"REST": 9}})
    (tmp_path / "urban_political_s42_spy.json").write_text(json.dumps(spy))


def _run(action, lodged, length=30, building=7):
    ctx = {"lodged_in": lodged, "sleep_debt": 70.0, "payload": {"action": action}}
    return {"subject": 1, "action": action, "building": building, "building_kind": "inn", "first_failed": 10, "last_failed": 10 + length - 1, "length": length, "ended_by": "died", "reasons": {"None": 3},
            "first_context": ctx, "last_context": ctx}


def test_the_negative_control_lists_every_run_over_10_and_passes_when_no_rest_run_was_lodged(tmp_path):
    summary = load("k2k3_count_summary")
    _neg_cell(tmp_path, [_run("EAT", None), _run("REST", None, 8), _run("REST", 9)])
    doc = summary.neg_summary(tmp_path)
    assert doc["valid"] is True and len(doc["runs_over_10"]) == 2 and doc["kit_defect_rest_runs"] == [] and doc["verdict"].startswith("NO DEFECT")
    assert summary.main(["--neg", str(tmp_path)]) == 0


def test_the_negative_control_stops_on_a_rest_run_whose_subject_was_lodged_at_its_building(tmp_path):
    summary = load("k2k3_count_summary")
    _neg_cell(tmp_path, [_run("REST", 7)])
    doc = summary.neg_summary(tmp_path)
    assert len(doc["kit_defect_rest_runs"]) == 1 and doc["verdict"].startswith("STOP")
    assert summary.main(["--neg", str(tmp_path)]) == 2
    _neg_cell(tmp_path, [_run("REST", 8)])                                       # lodged at ANOTHER building is not the defect
    assert summary.neg_summary(tmp_path)["kit_defect_rest_runs"] == []


def test_the_negative_control_is_void_when_the_spy_hash_differs(tmp_path):
    summary = load("k2k3_count_summary")
    _neg_cell(tmp_path, [_run("EAT", None)], hash_spy="other")
    assert summary.neg_summary(tmp_path)["verdict"] == "VOID"


def test_the_rule_text_names_both_amendments():
    assert "Amendment 1 e6cc644c" in logic.RULE_SOURCE and "Amendment 2 125c8a23" in logic.RULE_SOURCE
