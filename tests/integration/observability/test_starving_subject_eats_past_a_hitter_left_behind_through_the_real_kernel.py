"""TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER, through the real kernel (crowded_frontier, compiled).

Worker 1 forced into the traced shape of crowded s45 e5 / s46 e4: starving (hunger 100), wounded (hp 10/100), gold 0, two tiles from inn 20003, and last hit 3 ticks before every
tick by raider 24, which stands five tiles away, idle (no attack or pursue task). The fixture holds the raider there and re-stamps the hit each tick, so at whichever tick the worker's
brain runs the hit is three ticks old. Past the starving line a hit acts only while its hitter can reach the subject, so the worker walks to the inn and eats; with the old ten-tick
hit window restored (the control) the hit still acts and the worker does not eat in the same ticks.
"""
from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

WORKER, RAIDER = 1, 24
TICKS = 40


def _run(run_id):
    from src.core.state import TaskComponent
    from tests.helpers.clock import DAY_WORLD_TIME
    from tools.test_architecture.rpg_gate_run import build_kernel

    kernel = build_kernel("crowded_frontier", 42, run_id)
    # The run starts by day, not at world_time 0 (night). The fixture holds the raider in place by rewriting its position, which is not a move, so the raider IS still
    # under the perception law (PERC-02a: a body that has not moved for more than the moving window reads still), and last_moved_tick is deliberately not faked. By night
    # a still body five tiles off is not perceived by the worker, so the raider would leave its hostile set and the hit window, the point of this test, would never be read.
    # By day it is perceived, so the hit window stays what decides (owner #715 6971973729).
    object.__setattr__(kernel.state, "world_time", DAY_WORLD_TIME)
    try:
        for i in range(TICKS):
            state = kernel.state
            worker, raider = state.entities[WORKER], state.entities[RAIDER]
            hungry = worker.biological.hunger
            if i and hungry < 90.0:
                return hungry
            entities = dict(state.entities)
            if i == 0:
                worker = replace(worker, navigation=replace(worker.navigation, position=(42.0, 31.0)), combat=replace(worker.combat, hp=10, max_hp=100),
                                 biological=replace(worker.biological, hunger=100.0, sleep_debt=0.0), inventory=replace(worker.inventory, gold=0))
            worker = replace(worker, combat=replace(worker.combat, last_attacker_id=RAIDER, last_hit_attackers=(RAIDER,), last_hit_tick=state.tick - 3))
            entities[WORKER] = worker
            entities[RAIDER] = replace(raider, navigation=replace(raider.navigation, position=(42.0, 26.0)), task=TaskComponent(work_kind="ENTITY_ACT", payload={}))
            object.__setattr__(state, "entities", entities)
            kernel.tick_once()
        return kernel.state.entities[WORKER].biological.hunger
    finally:
        try:
            kernel.shutdown()
        except Exception:
            pass
        shutil.rmtree(Path("data") / "runs" / run_id, ignore_errors=True)


def test_a_starving_wounded_worker_hit_by_a_raider_that_fell_behind_walks_to_the_inn_and_eats():
    assert _run("d1_hit_reach_cf") < 90.0


def test_the_same_worker_with_the_old_ten_tick_hit_window_does_not_eat_in_the_same_ticks(monkeypatch):
    import src.engine.tactical_threat as threat

    def old_hit_acts_on(hostile, subject, tick):  # the predicate before the reach test: the hit acts for one brain cadence wherever the hitter is
        hit_tick = subject.combat.last_hit_tick
        return hit_tick is not None and hostile.id in subject.combat.last_hit_attackers and tick - hit_tick <= threat.NEED_WAKE_CADENCE

    monkeypatch.setattr(threat, "_hit_acts_on", old_hit_acts_on)
    assert _run("d1_hit_reach_cf_control") >= 90.0
