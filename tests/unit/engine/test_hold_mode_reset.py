"""A HOLD ends when its holding task is over: the walk-decision reset and the sleep-end reset (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, P3).

* A walk decision (a writer of a mode-less navigation target) resets the movement mode HOLD to WANDER in the update that sets the target,
  through ONE helper (``src.engine.hold_mode.hold_reset_kwargs``), unless an action task is live. The test for "live" is typed state (work kind and
  payload truthiness, plus the pending update's task), never a reason string.
* A collapse's HOLD ends with its SLEEP (the actions phase, ``_hold_ends_with_task``). A typed wait's task ends in its own tick and a killing blow
  ends its task in the kill tick, so neither is reset there: they end at the subject's next walk decision.
* GUARD: an ``ast`` scan of ``src`` finds every ``target_set`` writer that names no mode; each must call the helper or be on the allow-list.
"""
from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from src.core.builder import V2EntityBuilder
from src.core.movement_modes import MovementMode
from src.core.state import TaskComponent
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.hold_mode import action_task_is_live, effective_movement_mode, hold_reset_kwargs
from src.engine.pipeline_phases.actions import _hold_ends_with_task

REPO = Path(__file__).resolve().parents[3]
WANDER_RESET = {"movement_mode_set": MovementMode.WANDER}


def _entity(mode=MovementMode.HOLD, work_kind="ENTITY_ACT", payload=None):
    e = V2EntityBuilder(1).kind("hero").location(5.0, 5.0).lifecycle(active=True).build()
    return replace(e, navigation=replace(e.navigation, movement_mode=mode), task=TaskComponent(work_kind=work_kind, payload=dict(payload or {})))


# --- the helper: typed state, not a reason string ------------------------------------------------------------------------------------------
@pytest.mark.parametrize("payload", [{"action": "SLEEP", "collapse": True}, {"action": "ATTACK", "target_id": 2}, {"anything": 1}, {"reason": None, "x": 0}])
def test_a_live_action_task_keeps_hold_whatever_its_payload_keys_say(payload):
    held = _entity(payload=payload)
    assert action_task_is_live(held, None) is True
    assert hold_reset_kwargs(held) == {}  # a collapsed sleeper (live SLEEP) or any live action: HOLD is never ended by a walk decision


@pytest.mark.parametrize("work_kind,payload", [("ENTITY_ACT", {}), ("ENTITY_BRAIN", {"action": "SLEEP"}), ("ENTITY_MOVE", {"reason": "KEEP_WALKING"})])
def test_no_live_action_task_lets_the_walk_decision_end_the_hold(work_kind, payload):
    held = _entity(work_kind=work_kind, payload=payload)
    assert action_task_is_live(held, None) is False
    assert hold_reset_kwargs(held) == WANDER_RESET


def test_a_typed_wait_past_its_task_is_reset():
    """The wait's task was emptied in its own tick (the actions phase), so the next walk decision resets the mode."""
    assert hold_reset_kwargs(_entity(payload={})) == WANDER_RESET


def test_a_task_ended_by_this_ticks_pending_update_counts_as_not_live():
    held = _entity(payload={"action": "SLEEP", "collapse": True})
    ended = EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={}))
    assert action_task_is_live(held, ended) is False and hold_reset_kwargs(held, ended) == WANDER_RESET
    started = EntityUpdate(entity_id=1, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "EAT"}))
    assert action_task_is_live(_entity(payload={}), started) is True


@pytest.mark.parametrize("mode", [MovementMode.WANDER, MovementMode.PURSUE, MovementMode.RETREAT, MovementMode.REGROUP, MovementMode.GUARD])
def test_a_mode_other_than_hold_is_never_touched(mode):
    assert hold_reset_kwargs(_entity(mode=mode)) == {}


def test_a_pending_mode_write_decides_the_effective_mode():
    e = _entity(mode=MovementMode.WANDER)
    pending_hold = EntityUpdate(entity_id=1, navigation=NavigationUpdate(movement_mode_set=MovementMode.HOLD))
    assert effective_movement_mode(e, pending_hold) == MovementMode.HOLD and hold_reset_kwargs(e, pending_hold) == WANDER_RESET
    pending_pursue = EntityUpdate(entity_id=1, navigation=NavigationUpdate(movement_mode_set=MovementMode.PURSUE))
    assert hold_reset_kwargs(_entity(), pending_pursue) == {}


# --- the writers -----------------------------------------------------------------------------------------------------------------------------
def test_keep_walking_no_longer_inherits_hold():
    """Posture `ignore` re-issues the walk as an ENTITY_MOVE decision; it used to carry the CURRENT mode forward, including a sticky HOLD."""
    from src.core.enums import EntityRole, Faction
    from src.core.state import AuthoritativeState, RegionState
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
    from src.engine.tactical_hold import notice_unengaged_hostile
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    try:
        def fighter(eid, pos, faction):
            role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
            return (V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos).identity(role=role, faction=faction)
                    .combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True).lifecycle(active=True).build())

        def walker(mode):
            e = fighter(1, (10.0, 10.0), Faction.HERO_GUILD)
            props = dict(e.identity.properties)
            props["last_combat_posture"], props["last_combat_posture_target"] = "ignore", 2
            return replace(e, navigation=replace(e.navigation, target=(40.0, 40.0), movement_mode=mode), identity=replace(e.identity, properties=props),
                           task=TaskComponent(work_kind="ENTITY_ACT", payload={}))

        hostile = replace(fighter(2, (10.0, 11.0), Faction.MONSTER_HORDE), task=TaskComponent(work_kind="ENTITY_ACT", payload={}))
        for start, expected in ((MovementMode.HOLD, MovementMode.WANDER), (MovementMode.PURSUE, MovementMode.PURSUE), (MovementMode.WANDER, MovementMode.WANDER)):
            w = walker(start)
            state = AuthoritativeState(tick=5, seed=1, entities={1: w, 2: hostile}, regions={"field": RegionState(id="field", name="Field", bounds=(0, 0, 60, 60))})
            update = notice_unengaged_hostile(state, w, hostile, [hostile], None)
            assert update.task.payload_set["reason"] == "KEEP_WALKING" and update.navigation.movement_mode_set == expected
    finally:
        reset_behavior_consumers()


def test_the_move_to_intent_resets_hold_and_keeps_every_other_mode():
    from src.engine.intent.action_intent import ActionIntent, ActionIntentAdapter

    intent = ActionIntent(kind="MOVE_TO", actor_id=1, payload={"position": (9.0, 9.0)})
    held = ActionIntentAdapter.execute(_entity(payload={}), intent)[1]
    assert held.navigation.target_set == (9.0, 9.0) and held.navigation.movement_mode_set == MovementMode.WANDER
    walking = ActionIntentAdapter.execute(_entity(mode=MovementMode.PURSUE), intent)[1]
    assert walking.navigation.target_set == (9.0, 9.0) and walking.navigation.movement_mode_set is None
    sleeping = ActionIntentAdapter.execute(_entity(payload={"action": "SLEEP", "collapse": True}), intent)[1]
    assert sleeping.navigation.target_set == (9.0, 9.0) and sleeping.navigation.movement_mode_set is None  # the collapsed sleeper keeps HOLD


def test_a_collapse_hold_ends_with_its_sleep_and_nothing_else_does():
    hold_update = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_clear=True, movement_mode_set=MovementMode.HOLD))
    ended = _hold_ends_with_task(EntityUpdate(entity_id=1), _entity())
    assert ended.navigation.movement_mode_set == MovementMode.WANDER  # the entity is in HOLD: reset
    assert _hold_ends_with_task(EntityUpdate(entity_id=1), _entity(mode=MovementMode.PURSUE)).navigation is None  # not in HOLD: untouched
    kept = _hold_ends_with_task(hold_update, _entity(mode=MovementMode.PURSUE))
    assert kept.navigation.movement_mode_set == MovementMode.WANDER  # the pending update sets HOLD, so it is reset as well


# --- the guard: every writer of a target that names no mode ----------------------------------------------------------------------------------
ALLOW_LIST = {  # (file, enclosing function): a bare reaffirm of a held ENTITY_MOVE's payload target each tick, not a walk decision
    ("src/engine/executor.py", "_entity_move_updates"),
    ("src/engine/worker_logic.py", "default_simulation_worker"),
}


def _target_set_calls():
    """Every call that passes ``target_set=<non-None>``: (file, enclosing function, names a mode, uses the helper)."""
    found = []
    for path in sorted((REPO / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            kws = {k.arg: k for k in node.keywords if k.arg}
            tg = kws.get("target_set")
            if tg is None or (isinstance(tg.value, ast.Constant) and tg.value.value is None):
                continue
            func = node
            while func in parents and not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = parents[func]
            fname = func.name if isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)) else "<module>"
            names_mode = "movement_mode_set" in kws
            starred = [k for k in node.keywords if k.arg is None]
            uses_helper = any("hold_reset_kwargs" in ast.dump(k.value) for k in starred)
            found.append((str(path.relative_to(REPO)).replace("\\", "/"), fname, names_mode, uses_helper))
    return found


def test_every_mode_less_target_writer_uses_the_helper_or_is_on_the_allow_list():
    calls = _target_set_calls()
    mode_less = [c for c in calls if not c[2]]
    unaccounted = [c for c in mode_less if not c[3] and (c[0], c[1]) not in ALLOW_LIST]
    assert unaccounted == [], f"a navigation target is written with no movement mode and no hold reset: {unaccounted}"


def test_the_six_walk_decision_writers_call_the_helper():
    helper_users = {(f, fn) for f, fn, _m, helper in _target_set_calls() if helper}
    files = {f for f, _fn in helper_users}
    assert {"src/engine/intent/action_intent.py", "src/engine/tactical_hold.py", "src/systems/strategic_systems/intelligence.py",
            "src/systems/strategic_systems/redirection.py"} <= files
    sites = [c for c in _target_set_calls() if c[3]]
    assert len(sites) == 6, f"expected the six walk-decision writers to use hold_reset_kwargs, found {sites}"


def test_the_regroup_writers_always_name_their_mode():
    regroup = [c for c in _target_set_calls() if c[0] in ("src/systems/strategic_systems/intelligence.py", "src/systems/strategic_systems/redirection.py") and c[2]]
    assert len(regroup) >= 4  # intelligence.py x3 and redirection.py x1 carry movement_mode_set=REGROUP in the same call as target_set
