"""Merchant 37 (frontier_living_world seed 42, the v1 gate's V3 death) in a forced equivalent, through the real kernel.

Wounded (hp 10/85), gold 0, hunger 100, beside inn 20003 in unclaimed space, with predator_hunter 45 adjacent. With starvation weighed as a present threat
(SURV-07 amendment, row 83) the merchant takes a hunger project and eats; with the old threat gate restored (the control) it does not within the same ticks.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

TICKS = 60


def _run_merchant(run_id, gold=0):
    from tools.test_architecture.rpg_gate_run import build_kernel

    kernel = build_kernel("frontier_living_world", 42, run_id)
    try:
        state = kernel.state
        merchant, hunter = state.entities[37], state.entities[45]
        entities = dict(state.entities)
        entities[37] = replace(merchant, navigation=replace(merchant.navigation, position=(41.0, 31.0)), combat=replace(merchant.combat, hp=10, max_hp=85),
                               biological=replace(merchant.biological, hunger=100.0, sleep_debt=0.0), inventory=replace(merchant.inventory, gold=gold, items=[]))
        entities[45] = replace(hunter, navigation=replace(hunter.navigation, position=(41.0, 30.0)))
        object.__setattr__(state, "entities", entities)
        for _ in range(TICKS):
            kernel.tick_once()
            if kernel.state.entities[37].biological.hunger < 90.0:
                break
        return kernel.state.entities[37].biological.hunger
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def step_lands_next_to_predator(prior_merchant_pos, new_merchant_pos, prior_predator_pos):
    """The designer's metric: a tick counts only when the MERCHANT's own position changed, and then the Chebyshev distance from its NEW position to the predator's position on the PRIOR state must be above 1.
    A tick where only the predator moved, or the merchant held, never counts. Returns True when the step lands next to the predator."""
    if tuple(new_merchant_pos) == tuple(prior_merchant_pos):
        return False
    return max(abs(new_merchant_pos[0] - prior_predator_pos[0]), abs(new_merchant_pos[1] - prior_predator_pos[1])) <= 1


def test_the_step_metric_flags_a_merchant_step_that_lands_next_to_a_still_predator_and_nothing_else():
    """The failing control for the broke-merchant metric: a planted step next to a still predator is flagged; a step away, a held merchant beside the predator, and a tick where only the predator moved are not."""
    assert step_lands_next_to_predator((41.0, 31.0), (41.0, 29.0), (40.0, 28.0)) is True  # the step lands diagonally next to the predator
    assert step_lands_next_to_predator((41.0, 31.0), (41.0, 29.0), (41.0, 30.0)) is True
    assert step_lands_next_to_predator((41.0, 31.0), (41.0, 33.0), (41.0, 30.0)) is False  # a step away
    assert step_lands_next_to_predator((41.0, 31.0), (41.0, 31.0), (41.0, 30.0)) is False  # the merchant held; the predator is adjacent but did the moving
    assert step_lands_next_to_predator((41.0, 31.0), (41.0, 31.0), (41.0, 31.0)) is False


def _run_broke_merchant(run_id):
    """The same scene as `_run_merchant` with no gold, observed tick by tick: (the lowest hunger, the gold held at the end, whether a hunger project's objective was the open FORAGE step's target, and
    the ticks where the merchant's own step landed next to the predator, by `step_lands_next_to_predator`)."""
    from src.ai.goals.base import OpeningStepKind
    from src.ai.goals.opening_steps import opening_steps
    from tools.test_architecture.rpg_gate_run import build_kernel

    kernel = build_kernel("frontier_living_world", 42, run_id)
    try:
        state = kernel.state
        merchant, hunter = state.entities[37], state.entities[45]
        entities = dict(state.entities)
        entities[37] = replace(merchant, navigation=replace(merchant.navigation, position=(41.0, 31.0)), combat=replace(merchant.combat, hp=10, max_hp=85),
                               biological=replace(merchant.biological, hunger=100.0, sleep_debt=0.0), inventory=replace(merchant.inventory, gold=0, items=[]))
        entities[45] = replace(hunter, navigation=replace(hunter.navigation, position=(41.0, 30.0)))
        object.__setattr__(state, "entities", entities)
        lowest, forage_pull, landed = 100.0, False, []
        for _ in range(TICKS):
            prior = kernel.state
            prior_m, prior_h = prior.entities[37], prior.entities.get(45)
            kernel.tick_once()
            st = kernel.state
            m = st.entities[37]
            lowest = min(lowest, m.biological.hunger)
            cur = m.strategic.current_project_id
            proj = m.strategic.projects.get(cur) if cur else None
            if proj is not None and str(getattr(proj.kind, "value", proj.kind)) == "hunger":
                first = opening_steps(m, st)[0]
                obj = next((o for o in proj.objectives if o.id == proj.active_objective_id), None)
                if first.kind is OpeningStepKind.FORAGE and first.available and obj is not None and tuple(obj.target_position or ()) == tuple(first.target_pos):
                    forage_pull = True
            if prior_h is not None and prior_h.combat.alive and step_lands_next_to_predator(prior_m.navigation.position, m.navigation.position, prior_h.navigation.position):
                landed.append((st.tick, tuple(m.navigation.position), tuple(prior_h.navigation.position)))
        return lowest, kernel.state.entities[37].inventory.gold, forage_pull, landed
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


@pytest.mark.xfail(strict=True, reason="TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT invariant A7: a need path yields to a present threat; with the designer's corrected metric the broke merchant's forage walk still lands next to the predator (ticks 5-7: (42,31), (42,30), (42,29) beside the still predator at (41,30))")
def test_a_starving_wounded_merchant_with_no_gold_beside_an_inn_is_not_fed_and_its_pull_goes_to_forage():
    """Owner-approved claim (#715 answer 7080142180 to ask 7079540676, item ii): "A starving body with no gold beside an inn is NOT served a meal: there is no free relief (D73, #781). Its hunger pull goes to
    its next open way (SURV-07: earn, or seek work), and it still weighs the threat as before. It does not eat for free, and it does not walk into a hitter it was already avoiding to get there."
    Asserted: no meal served (hunger never below 90, no gold gained), the hunger project's objective is the open FORAGE step's target, and none of its own steps lands next to the predator (Chebyshev <= 1 from the new position to the predator's position on the prior state)."""
    lowest, gold, forage_pull, landed = _run_broke_merchant("v3_ii_merchant_broke")
    assert lowest >= 90.0, "no meal was served"
    assert gold == 0
    assert forage_pull, "the pull goes to FORAGE (the next open way)"
    assert not landed, f"a step of the merchant's own landed next to the predator (tick, new position, the predator's position on the prior state): {landed}"


def test_the_same_merchant_with_the_old_threat_gate_does_not_eat_in_the_same_ticks(monkeypatch):
    import src.ai.goals.scorers as scorers

    from src.ai.goals.present_threat import present_threat_to

    monkeypatch.setattr(scorers, "_hunger_escalated_unless_threatened", scorers._escalated_unless_threatened)
    monkeypatch.setattr(scorers, "acting_threat_to", present_threat_to)  # the old gate reads states (wounded, adjacent, outmatched), not acts
    assert _run_merchant("v3_ii_merchant_control") >= 90.0


def test_a_starving_wounded_merchant_who_can_pay_in_reach_of_an_inn_gets_a_hunger_project_and_eats():
    """The same scene as the gold-0 one above, but the merchant can pay (D73): it holds the price of a meal, so the inn is an open way and the threat weighing decides."""
    from src.engine.service_prices import EAT_PRICE_GOLD
    assert _run_merchant("v3_ii_merchant_pays", gold=EAT_PRICE_GOLD) < 90.0


def test_the_same_paying_merchant_with_the_old_threat_gate_does_not_eat_in_the_same_ticks(monkeypatch):
    import src.ai.goals.scorers as scorers

    from src.ai.goals.present_threat import present_threat_to
    from src.engine.service_prices import EAT_PRICE_GOLD

    monkeypatch.setattr(scorers, "_hunger_escalated_unless_threatened", scorers._escalated_unless_threatened)
    monkeypatch.setattr(scorers, "acting_threat_to", present_threat_to)  # the old gate reads states (wounded, adjacent, outmatched), not acts
    assert _run_merchant("v3_ii_merchant_pays_control", gold=EAT_PRICE_GOLD) >= 90.0
