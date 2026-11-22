"""V1 through the real pipeline (TCK-20261019-V1-COUNTS-A-HUNGER-DROP-AS-BACKED-ONLY-WHEN-AN-ACCEPTED-TRANSFER-MOVED-SOMETHING).

A real ``build_kernel`` run, the real events file and the real ``compute``. A hungry worker with no coin has a hunger drop that nothing backs (no coin, no item moved,
no accepted transfer), so V1 must fire. The free meal that used to cause such a drop no longer exists (D73), so the positive control plants the drop (see the test). The V1 row names a kind group, not an entity, so the forced eater is pinned through its own state: it is
the only entity seeded broke and hungry, and the test records the tick its hunger fell with its purse still empty. The control gives the same worker coin:
its meal is charged (the purse falls), the drop is backed, and the worker adds nothing to the V1 row.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from tests.integration.observability.test_gate_validity_checks_fire_through_the_real_kernel import _set_entities, run_gate_metrics, validity_rows

pytestmark = pytest.mark.integration

TICKS = 80


def _forced_worker(gold: int):
    """Returns (prepare, watch, seen): `prepare` seeds the worker, `watch` records after each tick whether its hunger fell and whether its purse moved."""
    seen = {"id": None, "group": None, "hunger_fell": 0, "purse_fell": 0, "unbacked": 0, "last": None}

    def prepare(kernel) -> None:
        from src.ai.goals.kind_group import kind_group

        state = kernel.state
        inn = next(b for b in state.buildings.values() if b.kind == "inn")
        from src.core.species import occupation_of  # label selector moved to occupation at step 4
        worker = next(e for e in state.entities.values() if occupation_of(e) == "worker" and e.combat.alive)
        entities = dict(state.entities)
        entities[worker.id] = replace(
            worker, navigation=replace(worker.navigation, position=(inn.position[0] + 1.0, inn.position[1])),
            biological=replace(worker.biological, hunger=100.0), inventory=replace(worker.inventory, items=[], gold=gold))
        _set_entities(kernel, entities)
        seen.update(id=worker.id, group=kind_group(entities[worker.id]), last=(100.0, gold))

    def watch(kernel, n: int) -> None:
        entity = kernel.state.entities[seen["id"]]
        hunger, purse = entity.biological.hunger, entity.inventory.gold
        before_hunger, before_purse = seen["last"]
        if hunger < before_hunger:
            seen["hunger_fell"] += 1
            if purse < before_purse:
                seen["purse_fell"] += 1
            elif purse == before_purse:
                seen["unbacked"] += 1
        seen["last"] = (hunger, purse)

    return prepare, watch, seen


def _v1(run_id: str, gold: int):
    prepare, watch, seen = _forced_worker(gold)
    row = validity_rows(run_gate_metrics(run_id, TICKS, prepare=prepare, after_tick=watch))["V1"]
    return row, seen


PLANT_TICK, PLANTED_DROP = 10, 20.0


def test_v1_fires_for_an_unbacked_hunger_drop_planted_through_the_real_kernel(monkeypatch):
    """V1's claim is unchanged: the counter fires on a hunger drop with no accepted transfer behind it. Its old natural source, a broke worker eating the free meal, no longer exists (D73: nothing is free, so
    a broke body is never fed), so the drop is PLANTED: a TEST-ONLY hunger decrease on the forced worker, with no resource transfer in the same update, added to the tick's real update at ``PLANT_TICK`` and
    committed by the real apply path (`ApplyPath.apply_generation`), then read by the real ledger and `compute`. The planted drop is the only drop the worker has (it holds no coin, so it eats nowhere)."""
    from src.core.updates import BiologicalUpdate, EntityUpdate
    from src.engine.apply import ApplyPath

    prepare, watch, seen = _forced_worker(0)
    real_apply = ApplyPath.apply_generation
    planted = {"n": 0}

    def planting_apply(prior_state, update, next_tick=None, *args, **kwargs):
        # the per-tick commit only (the same-episode grief flush keeps the tick): one plant, on the update object the ledger will also read
        if planted["n"] == 0 and seen["id"] is not None and prior_state.tick == PLANT_TICK and next_tick == prior_state.tick + 1:
            drop = EntityUpdate(entity_id=seen["id"], biological=BiologicalUpdate(hunger_delta=-PLANTED_DROP))
            existing = update.entity_updates.get(seen["id"])
            update.entity_updates[seen["id"]] = existing.merge(drop) if existing is not None else drop
            planted["n"] += 1
        return real_apply(prior_state, update, next_tick, *args, **kwargs)

    monkeypatch.setattr(ApplyPath, "apply_generation", staticmethod(planting_apply))
    row = validity_rows(run_gate_metrics("gate_pos_v1", TICKS, prepare=prepare, after_tick=watch))["V1"]
    assert planted["n"] == 1, planted  # the plant happened once, through the real commit
    assert seen["unbacked"] == 1, seen  # exactly the planted drop: hunger fell once while the purse (and items) did not move
    assert row["violations"] >= seen["unbacked"], (row, seen)
    keys = {e["group_key"]: e["ticks"] for e in row["examples"]}
    assert keys.get(f"{seen['group']}|without_transfer", 0) >= seen["unbacked"], (keys, seen)


def test_v1_does_not_count_the_same_worker_when_it_pays_for_the_meal():
    row, paid = _v1("gate_pos_v1_control", gold=200)
    assert paid["purse_fell"] >= 1 and paid["unbacked"] == 0, paid  # its meal was charged, so the drop is backed
    keys = {e["group_key"]: e["ticks"] for e in row.get("examples", [])}
    assert keys.get(f"{paid['group']}|without_transfer", 0) == 0, (keys, paid)
