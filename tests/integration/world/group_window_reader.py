"""Reads what members of live groups did, from the kernel state alone (no patching of the apply path, no measurement kit).

Test support for the two newborn-in-a-group integration tests. It keeps the window and the C1 (stuck) / C3 (needs) definitions those tests were written against, with one stated difference: progress is
read from the STATE before and after each tick, not from the applied update. Progress here = a goal change, a task change, a moved position, a drop in hunger, or a change in the carried items or gold.
C2 (the same failing action repeated) is not read: it needs the applied intent results, and every C2 run is also a C1 run (C2 requires no progress), so a window with no C1 has no C2 either.
A member that only fights in place and changes none of the above reads as stuck, which is the stricter side."""
from collections import defaultdict
from typing import Any, Dict, List

from src.engine.starvation import STARVING_LINE

WINDOW = 200


def _is_dissolved(group: Any) -> bool:
    return getattr(group, "dissolution_tick", None) is not None


def _goal(body: Any) -> tuple:
    return (body.strategic.current_objective_id, body.strategic.current_project_id)


def _task(body: Any) -> tuple:
    return (body.interaction.kind, body.interaction.target_node_id)


def _carried(body: Any) -> tuple:
    return (body.inventory.gold, tuple((getattr(s, "item_id", None), getattr(s, "quantity", None)) for s in body.inventory.items))


class GroupWindowReader:
    """``observe(prior, state)`` once per tick; one row per (member, tick) while the member is in an undissolved group."""

    def __init__(self) -> None:
        self.rows: Dict[int, List[Dict[str, Any]]] = defaultdict(list)

    def observe(self, prior: Any, state: Any) -> None:
        for gid, group in sorted(state.groups.items()):
            if _is_dissolved(group):
                continue
            for eid in sorted(group.member_ids):
                body, before = state.entities.get(eid), prior.entities.get(eid)
                if body is None or before is None:
                    continue
                record = body.lifecycle.death_record
                self.rows[eid].append({
                    "tick": state.tick, "group": gid, "goal_changed": _goal(body) != _goal(before), "task_changed": _task(body) != _task(before),
                    "moved": tuple(body.navigation.position) != tuple(before.navigation.position),
                    "completed": int(_carried(body) != _carried(before)), "consumed": body.biological.hunger < before.biological.hunger, "attacked": False, "failed": [],
                    "hunger": body.biological.hunger, "starved": record is not None and record.tick == state.tick and getattr(record.cause, "value", str(record.cause)) == "STARVATION",
                })


def _stretches(rows: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    out: List[List[Dict[str, Any]]] = []
    for row in rows:
        if out and out[-1][-1]["group"] == row["group"] and out[-1][-1]["tick"] + 1 == row["tick"]:
            out[-1].append(row)
        else:
            out.append([row])
    return out


def _progress(row: Dict[str, Any]) -> bool:
    return bool(row["goal_changed"] or row["task_changed"] or row["moved"] or row["completed"] or row["consumed"] or row["attacked"])


def c1_stuck(rows: List[Dict[str, Any]], window: int = WINDOW) -> List[Dict[str, Any]]:
    """Runs of at least ``window`` consecutive in-group ticks with no progress of any kind."""
    hits: List[Dict[str, Any]] = []
    for stretch in _stretches(rows):
        start = None
        for index, row in enumerate(stretch + [None]):
            if row is not None and not _progress(row):
                start = index if start is None else start
                continue
            if start is not None and index - start >= window:
                hits.append({"group": stretch[start]["group"], "first_tick": stretch[start]["tick"], "last_tick": stretch[index - 1]["tick"], "ticks": index - start})
            start = None
    return hits


def c3_needs(rows: List[Dict[str, Any]], starving_line: float = STARVING_LINE) -> List[Dict[str, Any]]:
    """The first in-group tick of each group stretch at which hunger is at or above the starvation line, or the member dies of STARVATION."""
    hits = []
    for stretch in _stretches(rows):
        for row in stretch:
            if row["hunger"] >= starving_line or row["starved"]:
                hits.append({"group": row["group"], "first_tick": row["tick"], "hunger": row["hunger"], "starved": row["starved"]})
                break
    return hits


def hits_by_eid(rows_by_eid: Dict[int, List[Dict[str, Any]]], window: int = WINDOW) -> Dict[int, Dict[str, List[Dict[str, Any]]]]:
    """Every member's C1/C3 hits (members with none are left out)."""
    out: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
    for eid, rows in sorted(rows_by_eid.items()):
        found = {"C1": c1_stuck(rows, window), "C3": c3_needs(rows)}
        if any(found.values()):
            out[eid] = {k: v for k, v in found.items() if v}
    return out
