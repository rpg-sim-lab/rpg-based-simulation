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
    run_ticks(t, set(range(10, 200)), deliver_at={60})       # delivered on tick 60 ends the run; the rest is a new, shorter run
    s = t.summary()
    assert s["runs"][0]["ended_by"] == "delivered"
    assert s["runs"][0]["length"] < 60 and s["k2_count"] == 1       # 61..199 is a second run of length > 100, counted on its own


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
def fake_entity(eid, hunger=0.0, sleep=0.0, gold=10, action=None, target=None, results=(), alive=True, project=None, projects=None):
    task = NS(work_kind="ENTITY_ACT", payload={} if action is None else {"action": action, "target_id": target})
    return NS(id=eid, task=task, biological=NS(hunger=hunger, sleep_debt=sleep), inventory=NS(gold=gold, items=()), identity=NS(latest_intent_results=tuple(results)),
              combat=NS(alive=alive), strategic=NS(current_project_id=project, projects=projects or {}, blockers={}))


def fake_state(tick, entities, buildings=None):
    return NS(tick=tick, entities={e.id: e for e in entities}, buildings=buildings if buildings is not None else {7: NS(kind="inn")})


def make_spy(present=False, acting=False, same_kind=lambda p, k: str(getattr(p.kind, "value", p.kind)) == str(getattr(k, "value", k))):
    return spy_mod.CountSpy(K, frozenset({"EAT", "REST", "SELL", "REPAIR"}), same_kind, lambda h, s: h >= 57.0 or s >= 58.8, lambda e, s: present, lambda e, s: acting, ("ACTIVE", "SUSPENDED"))


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
    # a delivered service (hunger lowered) ends the run
    spy2 = make_spy()
    prior = fake_state(0, [fake_entity(1, hunger=60.0, action="EAT", target=7)])
    for t in range(1, 30):
        new = fake_state(t, [fake_entity(1, hunger=60.0 if t < 20 else 30.0, action="EAT", target=7)])
        spy2.observe(prior, new)
        prior = new
    spy2.finish(30)
    assert spy2.report()["k2"]["runs"][0]["ended_by"] == "delivered" and spy2.report()["delivered_channel_counts"].get("state_change", 0) >= 1


def test_spy_k2_accepted_result_for_the_building_is_delivered_and_refusal_reason_recorded():
    ok = spy_mod.delivered_pairs(fake_entity(1, hunger=60.0), fake_entity(1, hunger=60.0, results=[NS(source_kind="TOWN_SERVICE", source_id=7, accepted=True, reason=None)]), [("EAT", 7)])
    assert ok[0] == [("EAT", 7)] and ok[2] == {"accepted_result": 1}
    refused = spy_mod.delivered_pairs(fake_entity(1, hunger=60.0), fake_entity(1, hunger=60.0, results=[NS(source_kind="TOWN_SERVICE", source_id=7, accepted=False, reason=None)]), [("EAT", 7)])
    assert refused[0] == [] and refused[1] == {("EAT", 7): ["None"]}
    other_building = spy_mod.delivered_pairs(fake_entity(1), fake_entity(1, results=[NS(source_kind="TOWN_SERVICE", source_id=9, accepted=True, reason=None)]), [("EAT", 7)])
    assert other_building[0] == []


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
