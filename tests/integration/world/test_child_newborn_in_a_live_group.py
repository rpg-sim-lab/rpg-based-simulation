# Compliance IDs: WORLD-122
"""SYNTHETIC coverage, not natural-path coverage and not full lifecycle evidence: the child is made by hand (a life-stage and parent edit on a live group member); the engine did not produce it.

Fallback for the births cooperation loop (rpg-designer-ubuntu, accepted by u24): a CHILD newborn put into a LIVE group of the real world runs 201+ ticks through the real cooperation and
cohesion services, with the S9 spy's own detectors (imported, so the definitions cannot drift) reading what its members did.

Asserted: no C3 for any member; and the evaluation TERMINATES within the test's ticks, either the group dissolves through its typed dissolution, or every member makes progress inside every
W-tick window, so no member has C1 or C2. Deterministic: urban_political seed 42 under the pinned kernel (audit_mode, sequential executor)."""
import dataclasses

from src.core.state import LifeStage
from tools.rpg_measure import s9_spy
from tools.rpg_measure.s9_spy import GroupSpy, hits_by_eid
from tools.test_architecture.rpg_gate_run import build_kernel

WINDOW = s9_spy.WINDOW
SETTLE_TICKS = 8  # the first groups form around tick 5 in this world
RUN_TICKS = WINDOW + 1  # at least W + 1 ticks after the child joins


def _live_group(state):
    return next((g for g in sorted(state.groups.values(), key=lambda g: g.id) if getattr(g, "dissolution_tick", None) is None and len(g.member_ids) >= 2), None)


def test_a_child_newborn_in_a_live_group_runs_w_plus_one_ticks_with_no_c3_and_the_evaluation_terminates():
    kernel = build_kernel("urban_political", 42, "child_newborn_in_group_fallback")
    spy = GroupSpy(kernel.state).install()
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
        spy.start_ids.discard(child_id)  # the spy now reads this body as a newborn
        for _ in range(RUN_TICKS):
            kernel.tick_once()
        final = kernel.state
    finally:
        spy.restore()
        kernel.shutdown()
    assert child_id in spy.mother or any(r["newborn"] == child_id for r in spy.newborn_in_group), "the child was seen in a group"
    hits = hits_by_eid(spy.rows)
    assert not [eid for eid, found in hits.items() if "C3" in found], f"no member may reach the starvation line or starve in a group: {hits}"
    record = final.groups.get(group.id)
    dissolved = record is None or getattr(record, "dissolution_tick", None) is not None
    members_with_stuck_or_repeat = [eid for eid, found in hits.items() if "C1" in found or "C2" in found]
    assert dissolved or not members_with_stuck_or_repeat, f"the group neither dissolved nor kept every member progressing: {hits}"
