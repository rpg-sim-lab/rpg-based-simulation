"""TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER, through the real kernel (crowded_frontier, compiled).

Worker 1 forced into the traced shape of crowded s45 e5 / s46 e4: starving (hunger 100), wounded (hp 10/100), gold 0, two tiles from inn 20003, and last hit 3 ticks before every
tick by a raider five tiles away, idle (no attack or pursue task). The raider is orc 34 of crowded_frontier (seed 42): a large body (visibility high) that the worker PERCEIVES by day and
regards as hostile on the same path the hit window reads (asserted at every tick before the worker's brain runs, see `_preconditions`), with combat.range 1 so five tiles is beyond its
reach (`max(1, hostile.combat.range)`, tactical_threat._hit_acts_on). The fixture holds the raider on one tile, asserted unoccupied before each rewrite, and re-stamps the hit each tick, so
at whichever tick the worker's brain runs the hit is three ticks old. Past the starving line a hit acts only while its hitter can reach the subject, so the worker walks to the inn and eats;
with the old ten-tick hit window restored (the control) the hit still acts and the worker does not eat in the same ticks.

(A goblin raider, the earlier body, is small: visibility low. A still low-visibility body is never perceived short of touch (PERC-02a, best score .132 < .2), so the worker never counted it a
hostile and neither the hit window nor its control was exercised.)
"""
from __future__ import annotations

import os
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

WORKER, RAIDER = 1, 34
HELD_TILE = (42, 26)  # five tiles from the worker (42, 31); no unenterable tile exists in that band (plain and forest), so the fixture asserts it is unoccupied before every rewrite
TICKS = 40


def _preconditions(state, worker, raider):
    """At the tick the worker's brain runs: the raider is perceived (a), is in the hostile set the hit window is read from, with a hit three ticks old (b), and stands beyond its reach (c)."""
    from src.core.calendar import is_night
    from src.engine.appraisal import perceives
    from src.engine.hostility import perceived_hostile
    from src.engine.tactical_threat import NEED_WAKE_CADENCE
    from src.engine.tile_distance import manhattan_tile_distance

    night = is_night(state.world_time)
    assert perceives(worker, raider, night=night, tick=state.tick), f"tick {state.tick}: the worker does not perceive the raider"
    assert perceived_hostile(worker, raider, night=night, tick=state.tick), f"tick {state.tick}: the raider is not in the worker's hostile set"
    assert state.tick - worker.combat.last_hit_tick <= NEED_WAKE_CADENCE and raider.id in worker.combat.last_hit_attackers, f"tick {state.tick}: the hit is outside the window"
    dist = manhattan_tile_distance(worker.navigation.position, raider.navigation.position)
    assert dist > max(1, raider.combat.range), f"tick {state.tick}: the raider ({dist} tiles) is within its reach {max(1, raider.combat.range)}"


def _run(run_id, gold=0):
    from src.config.profiles import PROD_SMALL
    from src.core.state import TaskComponent
    from src.engine.executor import LocalSequentialExecutor
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository
    from tests.helpers.clock import DAY_WORLD_TIME
    from tests.helpers.kernel_pinning import PinnedNormalGovernor

    # The pinned kernel of tools.test_architecture.rpg_gate_run.build_kernel, built from a state rebuilt with a day clock instead of a compiled world's world_time 0 (night).
    # The fixture holds the raider in place by rewriting its position, which is not a move, so the raider IS still under the perception law (PERC-02a: a body that has not
    # moved for more than the moving window reads still), and last_moved_tick is deliberately not faked. By night a still body five tiles off is not perceived by the worker,
    # so the raider would leave its hostile set and the hit window, the point of this test, would never be read. By day it is perceived, so the hit window stays what decides
    # (owner #715 6971973729).
    spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context("crowded_frontier")
    state, _report = WorldCompiler.compile(spec, 42, context=context)
    # Mirrors tools/test_architecture/rpg_gate_run.build_kernel (PROD_SMALL budget 1e9, PinnedNormalGovernor, LocalSequentialExecutor, audit_mode/no_frame_pacing); keep in sync, or replace with a state hook if build_kernel gains one.
    kernel = Kernel(
        PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), replace(state, world_time=DAY_WORLD_TIME), DeterministicRNG(42),
        governor=PinnedNormalGovernor(), executor=LocalSequentialExecutor(),
        flags={"audit_mode": True, "no_frame_pacing": True}, run_id=run_id,
    )
    try:
        for i in range(TICKS):
            state = kernel.state
            worker, raider = state.entities[WORKER], state.entities[RAIDER]
            hungry = worker.biological.hunger
            if i and hungry < 90.0:
                return hungry
            entities = dict(state.entities)
            crowd = [e.id for e in entities.values() if e.id != RAIDER and e.combat.alive and (int(e.navigation.position[0]), int(e.navigation.position[1])) == HELD_TILE]
            assert not crowd, f"tick {state.tick}: bodies {crowd} stand on the raider's held tile {HELD_TILE}"
            if i == 0:
                worker = replace(worker, navigation=replace(worker.navigation, position=(42.0, 31.0)), combat=replace(worker.combat, hp=10, max_hp=100),
                                 biological=replace(worker.biological, hunger=100.0, sleep_debt=0.0), inventory=replace(worker.inventory, gold=gold))
            worker = replace(worker, combat=replace(worker.combat, last_attacker_id=RAIDER, last_hit_attackers=(RAIDER,), last_hit_tick=state.tick - 3))
            entities[WORKER] = worker
            entities[RAIDER] = replace(raider, navigation=replace(raider.navigation, position=(42.0, 26.0)), task=TaskComponent(work_kind="ENTITY_ACT", payload={}))
            _preconditions(state, worker, entities[RAIDER])
            object.__setattr__(state, "entities", entities)
            kernel.tick_once()
        return kernel.state.entities[WORKER].biological.hunger
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def _no_hard_law_violation(caplog):
    assert not [r.getMessage() for r in caplog.records if "Hard Law Violation" in r.getMessage()]


@pytest.mark.xfail(strict=True, reason="TCK-20261122-A-RESOLVED-OBJECTIVE-PULLS-A-FLEEING-SUBJECT-BACK-TOWARD-IT invariant A7: a need path yields to a present threat; today the gold-0 worker's forage walk leads it into the hitter it was avoiding (its `_preconditions` fail: the raider is within reach)")
def test_a_starving_wounded_worker_with_no_gold_is_not_fed_and_does_not_walk_into_the_hitter_it_was_avoiding(caplog):
    """Owner-approved claim (#715 answer 7080142180 to ask 7079540676, item ii): "A starving body with no gold beside an inn is NOT served a meal: there is no free relief (D73, #781). Its hunger pull goes to
    its next open way (SURV-07: earn, or seek work), and it still weighs the threat as before. It does not eat for free, and it does not walk into a hitter it was already avoiding to get there."
    `_run` asserts at every tick (`_preconditions`) that the raider stays beyond its reach of the worker; the final hunger must not fall below 90 (no free meal)."""
    assert _run("d1_hit_reach_cf_broke") >= 90.0
    _no_hard_law_violation(caplog)


def test_a_starving_wounded_worker_who_can_pay_hit_by_a_raider_that_fell_behind_walks_to_the_inn_and_eats(caplog):
    """The same scene as the gold-0 one above, but the worker can pay (D73): it holds the price of a meal, so the inn is an open way and the threat weighing is what decides."""
    from src.engine.service_prices import EAT_PRICE_GOLD
    assert _run("d1_hit_reach_cf_pays", gold=EAT_PRICE_GOLD) < 90.0
    _no_hard_law_violation(caplog)


def test_the_same_paying_worker_with_the_old_ten_tick_hit_window_does_not_eat_in_the_same_ticks(monkeypatch, caplog):
    import src.engine.tactical_threat as threat
    from src.engine.service_prices import EAT_PRICE_GOLD

    def old_hit_acts_on(hostile, subject, tick):  # the predicate before the reach test: the hit acts for one brain cadence wherever the hitter is
        hit_tick = subject.combat.last_hit_tick
        return hit_tick is not None and hostile.id in subject.combat.last_hit_attackers and tick - hit_tick <= threat.NEED_WAKE_CADENCE

    monkeypatch.setattr(threat, "_hit_acts_on", old_hit_acts_on)
    assert _run("d1_hit_reach_cf_pays_control", gold=EAT_PRICE_GOLD) >= 90.0
    _no_hard_law_violation(caplog)
