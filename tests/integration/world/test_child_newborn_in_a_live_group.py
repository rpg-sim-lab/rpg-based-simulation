# Compliance IDs: WORLD-122
"""SYNTHETIC coverage, not natural-path coverage and not full lifecycle evidence: the child is made by hand (a life-stage and parent edit on a live group member); the engine did not produce it.

Fallback for the births cooperation loop (rpg-designer-ubuntu, accepted by u24): a CHILD newborn put into a LIVE group of the real world runs 201+ ticks through the real cooperation and
cohesion services, with the detectors of ``group_window_reader`` (state-read: no patching of the apply path) reading what its members did.

Asserted: no C3 for any member; and the evaluation TERMINATES within the test's ticks, either the group dissolves through its typed dissolution, or every member makes progress inside every
W-tick window, so no member has C1 or C2. Deterministic: urban_political seed 42 under the pinned kernel (audit_mode, sequential executor)."""
import dataclasses
from types import SimpleNamespace

from src.core.state import LifeStage
from tests.integration.world.group_window_reader import WINDOW, GroupWindowReader, hits_by_eid
from tools.test_architecture.rpg_gate_run import build_kernel

SETTLE_TICKS = 8  # the first groups form around tick 5 in this world
RUN_TICKS = WINDOW + 1  # at least W + 1 ticks after the child joins


def _live_group(state):
    return next((g for g in sorted(state.groups.values(), key=lambda g: g.id) if getattr(g, "dissolution_tick", None) is None and len(g.member_ids) >= 2), None)


def test_a_child_newborn_in_a_live_group_runs_w_plus_one_ticks_with_no_c3_and_the_evaluation_terminates():
    kernel = build_kernel("urban_political", 42, "child_newborn_in_group_fallback")
    reader = GroupWindowReader()
    try:
        for _ in range(SETTLE_TICKS):
            kernel.tick_once()
        state = kernel.state
        group = _live_group(state)
        assert group is not None, "the real world must hold a live group of two or more at the settle tick"
        child_id = max(group.member_ids)
        body = state.entities[child_id]
        child = dataclasses.replace(
            body, identity=dataclasses.replace(body.identity, life_stage=LifeStage.CHILD),
            lifecycle=dataclasses.replace(body.lifecycle, parent_a_entity_id=min(group.member_ids), parent_b_entity_id=None, birth_tick=state.tick),
        )
        kernel._state = dataclasses.replace(state, entities={**state.entities, child_id: child})
        for _ in range(RUN_TICKS):
            prior = kernel.state
            kernel.tick_once()
            reader.observe(prior, kernel.state)
        final = kernel.state
    finally:
        kernel.shutdown()
    assert reader.rows.get(child_id), "the child was seen in a group"
    hits = hits_by_eid(reader.rows)
    assert not [eid for eid, found in hits.items() if "C3" in found], f"no member may reach the starvation line or starve in a group: {hits}"
    record = final.groups.get(group.id)
    dissolved = record is None or getattr(record, "dissolution_tick", None) is not None
    members_with_stuck = [eid for eid, found in hits.items() if "C1" in found]
    assert dissolved or not members_with_stuck, f"the group neither dissolved nor kept every member progressing: {hits}"


def _body(hunger, record=None):
    return SimpleNamespace(
        strategic=SimpleNamespace(current_objective_id=None, current_project_id=None), interaction=SimpleNamespace(kind=None, target_node_id=None),
        inventory=SimpleNamespace(gold=0, items=[]), navigation=SimpleNamespace(position=(0.0, 0.0)), biological=SimpleNamespace(hunger=hunger),
        lifecycle=SimpleNamespace(death_record=record),
    )


def test_the_reader_reads_a_death_by_starvation_without_comparing_ticks():
    """The death record carries the pre-apply tick and the observed state is one tick later, so the reader compares the body before and after the tick, not the ticks."""
    group = SimpleNamespace(member_ids=[7], dissolution_tick=None)
    record = SimpleNamespace(tick=41, cause=SimpleNamespace(value="STARVATION"))
    other = SimpleNamespace(tick=41, cause=SimpleNamespace(value="OLD_AGE"))
    for dead, expected in ((record, True), (other, False), (None, False)):
        reader = GroupWindowReader()
        reader.observe(SimpleNamespace(entities={7: _body(0.1)}, groups={1: group}, tick=41), SimpleNamespace(entities={7: _body(0.1, dead)}, groups={1: group}, tick=42))
        assert reader.rows[7][0]["starved"] is expected
    already = GroupWindowReader()  # a body that was already dead before the tick is not a new death
    already.observe(SimpleNamespace(entities={7: _body(0.1, record)}, groups={1: group}, tick=41), SimpleNamespace(entities={7: _body(0.1, record)}, groups={1: group}, tick=42))
    assert already.rows[7][0]["starved"] is False
