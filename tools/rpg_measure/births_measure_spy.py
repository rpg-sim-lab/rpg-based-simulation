"""S9 spy (the births cooperation-loop diagnostic): per member of EVERY group, per tick, what the member did, and the C1/C2/C3 detectors and the per-eid verdict, all pure and unit-tested.

Criteria are rpg-designer (u24)'s, fixed before any data (rulings of 2026-11-18, f8a00273e and 6588f4c86): window W = 200 consecutive ticks;
- C1 STUCK: >= W consecutive in-group ticks with NO progress, where progress is any of: a goal change, a task change, a successful step, a completed eat/harvest/craft/trade/attack;
- C2 REPEAT-FAIL: >= W consecutive in-group ticks whose only actions are the same failing action (same action, same target, a failure code) and no progress of any kind;
- C3 NEEDS: the member reaches the starvation line (``src.engine.starvation.STARVING_LINE``, the existing one in code) or dies of STARVATION while in the group.
Operational definitions (stated here so the approval can check them; none is changed after the data):
- goal = ``(strategic.current_objective_id, strategic.current_project_id)``; a goal change is a difference from the previous tick.
- task = ``(interaction.kind, interaction.target_node_id)``; a task change is a difference from the previous tick.
- successful step = the applied update gave the member a ``new_position``, or its position differs from the previous tick.
- completed eat/harvest/craft/trade = an ACCEPTED ``IntentResult`` in the member's applied entity update (every resource-transfer kind: carried or corpse food, node harvest, craft, trade), OR
  a typed consume: an applied ``BiologicalUpdate`` for the member with ``hunger_delta < 0`` or ``hunger_set is not None`` (the eat paths that write a typed hunger drop with no IntentResult: the inn meal,
  core_actions eat). That expression is the same typed-consume rule births_spy.py's apply wrapper uses for W5; it is repeated literally here because births_spy needs the births head and this spy must also run on main.
- attack = the member is the ``attacker_id`` of a damaging ``CombatUpdate`` (``damage_taken > 0``) in the applied update.
- failing action = a REJECTED ``IntentResult``; its key is ``(source_kind, source_id, str(reason))``. A tick is a repeat-fail tick when its only actions are rejected results with one and the same key.
- "while in the group" = the ticks at which the member is in ``member_ids`` of a group in the state after the tick that is not dissolved; a stretch is a run of consecutive ticks in ONE group.
The spy only reads; it wraps ``ApplyPath.apply_generation`` to record and returns its result untouched. It imports nothing that exists only on the births head, so it runs on the frozen main tree too.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from src.engine.apply import ApplyPath
from src.engine.starvation import STARVING_LINE

WINDOW = 200
CLASSES = ("C1", "C2", "C3")
NOTHING_CAPTURED = (
    "the cohesion and expulsion test values at every check are not captured (the group services are not instrumented); the typed dissolution reason and tick of every group are",
)


def _is_dissolved(group: Any) -> bool:
    return getattr(group, "dissolution_tick", None) is not None


def _goal(entity: Any) -> tuple:
    return (entity.strategic.current_objective_id, entity.strategic.current_project_id)


def _task(entity: Any) -> tuple:
    return (entity.interaction.kind, entity.interaction.target_node_id)


class GroupSpy:
    """Record-only wrapper over the apply path; ``install()`` patches, ``restore()`` undoes. One row per (member, tick) while the member is in an undissolved group."""

    def __init__(self, start_state: Any) -> None:
        self.start_ids: Set[int] = set(start_state.entities)
        self.rows: Dict[int, List[Dict[str, Any]]] = defaultdict(list)  # eid -> rows in tick order
        self.group_seen: Dict[int, Dict[str, Any]] = {}  # group id -> first/last tick seen undissolved, with the typed dissolution facts once recorded
        self.newborn_in_group: List[Dict[str, Any]] = []  # BALANCE: one row per newborn of ANY kind seen in a group at any tick (eid, kind, group, first tick in a group)
        self.mother: Dict[int, Optional[int]] = {}
        self.conceptions: Set[tuple] = set()  # distinct (mother id, conceived_tick) over every PregnancyState seen on any entity in any tick; getattr, so it is empty on main
        self._patched: List[tuple] = []

    def install(self) -> "GroupSpy":
        original = ApplyPath.__dict__["apply_generation"].__func__
        spy = self

        def apply_generation(prior_state, update, *args, **kwargs):
            new_state = original(prior_state, update, *args, **kwargs)
            spy.observe(prior_state, update, new_state)
            return new_state

        self._patched.append((ApplyPath, "apply_generation", original))
        ApplyPath.apply_generation = staticmethod(apply_generation)
        return self

    def restore(self) -> None:
        for owner, name, original in reversed(self._patched):
            setattr(owner, name, staticmethod(original))
        self._patched.clear()

    def observe(self, prior: Any, update: Any, state: Any) -> None:
        tick = state.tick
        for body in state.entities.values():
            pregnancy = getattr(body.lifecycle, "pregnancy", None)
            if pregnancy is not None:
                self.conceptions.add((body.id, pregnancy.conceived_tick))
        attackers: Set[int] = {
            upd.combat.attacker_id for upd in update.entity_updates.values()
            if upd.combat is not None and upd.combat.attacker_id is not None and upd.combat.damage_taken > 0
        }
        for gid, group in sorted(state.groups.items()):
            seen = self.group_seen.setdefault(gid, {"first_tick": tick, "last_tick": tick, "members_at_first": sorted(group.member_ids)})
            if _is_dissolved(group):
                seen["dissolution_tick"] = group.dissolution_tick
                seen["dissolution_reason"] = str(getattr(getattr(group, "dissolution_reason", None), "value", getattr(group, "dissolution_reason", None)))
                continue
            seen["last_tick"] = tick
            for eid in sorted(group.member_ids):
                body, before = state.entities.get(eid), prior.entities.get(eid)
                if body is None or before is None:
                    continue
                if eid not in self.start_ids and eid not in self.mother:
                    self.mother[eid] = body.lifecycle.parent_a_entity_id
                    self.newborn_in_group.append({"group": gid, "tick": tick, "newborn": eid, "kind": body.kind})
                upd = update.entity_updates.get(eid)
                results = list(upd.intent_results) if upd is not None else []
                accepted = [r for r in results if r.accepted]
                failed = sorted({(str(r.source_kind), str(r.source_id), str(r.reason)) for r in results if not r.accepted})
                consumed = upd is not None and upd.biological is not None and (upd.biological.hunger_delta < 0 or upd.biological.hunger_set is not None)
                moved = (upd is not None and upd.new_position is not None) or tuple(body.navigation.position) != tuple(before.navigation.position)
                record = body.lifecycle.death_record
                self.rows[eid].append({
                    "tick": tick, "group": gid, "goal_changed": _goal(body) != _goal(before), "task_changed": _task(body) != _task(before), "moved": bool(moved),
                    "completed": len(accepted), "consumed": consumed, "attacked": eid in attackers, "failed": failed, "hunger": body.biological.hunger,
                    "starved": record is not None and record.tick == tick and getattr(record.cause, "value", str(record.cause)) == "STARVATION",
                    "life_stage": getattr(body.identity.life_stage, "name", str(body.identity.life_stage)),
                })


def count_births(entities: Any, start_ids: Set[int]) -> int:
    """The births: final-state entities not in the start state, alive or dead, whose lifecycle carries BOTH parent ids (read with getattr, so a main-shaped body gives 0)."""
    return sum(1 for eid, body in entities.items() if eid not in start_ids and _parents(body) == (True, True))


def count_other_adds(entities: Any, start_ids: Set[int]) -> int:
    """The other adds: final-state entities not in the start state that are not births (a risen body, a parentless spawn)."""
    return sum(1 for eid, body in entities.items() if eid not in start_ids and _parents(body) != (True, True))


def _parents(body: Any) -> tuple:
    life = getattr(body, "lifecycle", None)
    return (getattr(life, "parent_a_entity_id", None) is not None, getattr(life, "parent_b_entity_id", None) is not None)


# ---- detectors (pure) -------------------------------------------------------------------------------------------------------------------------------
def _stretches(rows: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Maximal runs of consecutive ticks in one group."""
    out: List[List[Dict[str, Any]]] = []
    for row in rows:
        if out and out[-1][-1]["group"] == row["group"] and out[-1][-1]["tick"] + 1 == row["tick"]:
            out[-1].append(row)
        else:
            out.append([row])
    return out


def _progress(row: Dict[str, Any]) -> bool:
    return bool(row["goal_changed"] or row["task_changed"] or row["moved"] or row["completed"] or row.get("consumed") or row["attacked"])


def _runs(stretch: List[Dict[str, Any]], qualifies, window: int) -> List[Dict[str, Any]]:
    hits, start = [], None
    for index, row in enumerate(stretch + [None]):
        if row is not None and qualifies(stretch, index):
            start = index if start is None else start
            continue
        if start is not None and index - start >= window:
            hits.append({"group": stretch[start]["group"], "first_tick": stretch[start]["tick"], "last_tick": stretch[index - 1]["tick"], "ticks": index - start})
        start = None
    return hits


def c1_stuck(rows: List[Dict[str, Any]], window: int = WINDOW) -> List[Dict[str, Any]]:
    """C1: runs of at least `window` consecutive in-group ticks with no progress of any kind."""
    return [hit for stretch in _stretches(rows) for hit in _runs(stretch, lambda s, i: not _progress(s[i]), window)]


def c2_repeat_fail(rows: List[Dict[str, Any]], window: int = WINDOW) -> List[Dict[str, Any]]:
    """C2: runs of at least `window` consecutive in-group ticks whose only action is one and the same failing action (no progress, exactly one failure key, equal across the run)."""
    hits: List[Dict[str, Any]] = []
    for stretch in _stretches(rows):
        by_key: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
        for row in stretch:
            if not _progress(row) and len(row["failed"]) == 1:
                by_key[tuple(row["failed"][0])].append(row)
        for key, members in by_key.items():
            ticks = {r["tick"] for r in members}
            hits.extend({**hit, "key": list(key)} for hit in _runs(stretch, lambda s, i, t=ticks: s[i]["tick"] in t, window))
    return hits


def c3_needs(rows: List[Dict[str, Any]], starving_line: float = STARVING_LINE) -> List[Dict[str, Any]]:
    """C3: the first in-group tick at which the member's hunger is at or above the starvation line, or it dies of STARVATION (one row per group stretch)."""
    hits = []
    for stretch in _stretches(rows):
        for row in stretch:
            if row["hunger"] >= starving_line or row["starved"]:
                hits.append({"group": row["group"], "first_tick": row["tick"], "hunger": row["hunger"], "starved": row["starved"]})
                break
    return hits


def hits_by_eid(rows_by_eid: Dict[int, List[Dict[str, Any]]], window: int = WINDOW) -> Dict[int, Dict[str, List[Dict[str, Any]]]]:
    """Every member's C1/C2/C3 hits (members with none are left out)."""
    out: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
    for eid, rows in sorted(rows_by_eid.items()):
        found = {"C1": c1_stuck(rows, window), "C2": c2_repeat_fail(rows, window), "C3": c3_needs(rows)}
        if any(found.values()):
            out[eid] = {k: v for k, v in found.items() if v}
    return out


# ---- the per-eid verdict (pure) ----------------------------------------------------------------------------------------------------------------------
def classify(head_hits: Dict[int, Dict[str, list]], main_hits: Dict[int, Dict[str, list]], t0_ids: Set[int], mother: Dict[int, Optional[int]],
             head_rows: Dict[int, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """One row per eid with a head hit, class BLOCK / MAIN-DEFECT / FINDING (an eid with no head hit has no row, class "none"):
    - a t0 member (the id exists at tick 0 on both arms): a head hit of a kind ABSENT for that eid on main is a BLOCK; the same kind on both arms is a MAIN-DEFECT (reported, not a block);
    - a newborn member (not in t0): C3 is a BLOCK; C1 or C2 is a FINDING carrying its life stage, its group and its mother's own C1/C2 status over the same window."""
    rows = []
    for eid, hits in sorted(head_hits.items()):
        if eid in t0_ids:
            kinds = {k: ("MAIN-DEFECT" if k in main_hits.get(eid, {}) else "BLOCK") for k in hits}
            verdict = "BLOCK" if "BLOCK" in kinds.values() else "MAIN-DEFECT"
            rows.append({"eid": eid, "population": "t0", "class": verdict, "kinds": kinds, "hits": hits})
            continue
        mother_id = mother.get(eid)
        mother_hits = head_hits.get(mother_id, {}) if mother_id is not None else {}
        last = head_rows.get(eid, [{}])[-1]
        row = {
            "eid": eid, "population": "newborn", "life_stage": last.get("life_stage"), "group": next(iter(hits.values()))[0].get("group"), "mother": mother_id,
            "mother_C1": "C1" in mother_hits, "mother_C2": "C2" in mother_hits, "hits": hits,
        }
        rows.append({**row, "class": "BLOCK" if "C3" in hits else "FINDING", "kinds": {k: ("BLOCK" if k == "C3" else "FINDING") for k in hits}})
    return rows


def final_verdict(rows: List[Dict[str, Any]]) -> str:
    """BLOCK when any eid is a BLOCK; FINDINGS when any is a FINDING or a MAIN-DEFECT; else CLEAR."""
    classes = {r["class"] for r in rows}
    return "BLOCK" if "BLOCK" in classes else "FINDINGS" if classes & {"FINDING", "MAIN-DEFECT"} else "CLEAR"


def split_counts(rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Hit counts per class, split between t0 and newborn members."""
    out: Dict[str, Dict[str, int]] = {"t0": defaultdict(int), "newborn": defaultdict(int)}  # type: ignore[dict-item]
    for r in rows:
        for kind, hits in r["hits"].items():
            out[r["population"]][kind] += len(hits)
    return {pop: dict(counts) for pop, counts in out.items()}
