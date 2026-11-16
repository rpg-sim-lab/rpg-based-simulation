"""The reset of a HOLD movement mode by a walk decision (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, plan v3).

A HOLD is the mode of a holding task (a typed wait, a kill, a collapse). Kill and collapse holds end with their task (``pipeline_phases/actions.py``).
A typed wait's HOLD stays until the subject's next decision that sets a walk; that decision resets the mode to the navigation default, WANDER,
in the same update that sets the walk's target. Every writer of a mode-less navigation target calls ``hold_reset_kwargs`` for it, so the rule lives
in one place (tests/unit/engine/test_hold_mode_reset.py scans ``src`` for a writer that does not).

A reset NEVER ends a HOLD while an action task is live. The state does not store which task entered the HOLD, so the test is "an action task is
live", read as typed state: the work kind and the truthiness of the payload (the predicate of ``MovementCandidateSelector.holds_action_task``), and
the pending update's task when it carries one (an update that empties the payload has ended the task this tick). It never reads a reason string.
It errs toward keeping HOLD: a typed wait's HOLD that persists while the subject has since started an unrelated live action is not reset by a walk
decision until that action ends; that never makes a walk cheaper than before.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from src.core.movement_modes import MovementMode


def effective_movement_mode(entity: Any, ent_upd: Optional[Any]) -> MovementMode:
    """The mode in force after this tick's pending update: its ``movement_mode_set`` when it carries one, else the entity's own."""
    nav = getattr(ent_upd, "navigation", None) if ent_upd is not None else None
    mode = getattr(nav, "movement_mode_set", None) if nav is not None else None
    current: MovementMode = entity.navigation.movement_mode
    return mode if mode is not None else current


def action_task_is_live(entity: Any, ent_upd: Optional[Any]) -> bool:
    """True when an action task (``ENTITY_ACT`` with a non-empty payload) is in force after this tick's pending update."""
    task_upd = getattr(ent_upd, "task", None) if ent_upd is not None else None
    kind = task_upd.work_kind_set if task_upd is not None and task_upd.work_kind_set is not None else entity.task.work_kind
    payload = task_upd.payload_set if task_upd is not None and task_upd.payload_set is not None else entity.task.payload
    return kind == "ENTITY_ACT" and bool(payload)


def hold_reset_kwargs(entity: Any, ent_upd: Optional[Any] = None) -> Dict[str, Any]:
    """``{"movement_mode_set": WANDER}`` when a walk decision for ``entity`` must end its HOLD (the mode is HOLD and no action task is live), else ``{}``.

    Spread it into the ``NavigationUpdate`` (or ``replace``) that sets the walk's target: ``NavigationUpdate(target_set=t, **hold_reset_kwargs(entity))``.
    An empty dict leaves the update's own mode (or none) untouched, so a pending mode write is never erased."""
    if effective_movement_mode(entity, ent_upd) == MovementMode.HOLD and not action_task_is_live(entity, ent_upd):
        return {"movement_mode_set": MovementMode.WANDER}
    return {}
