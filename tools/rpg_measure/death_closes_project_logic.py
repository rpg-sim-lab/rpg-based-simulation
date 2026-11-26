"""Death-closes-project own-job logic (TCK-20261031-DEATH-CLOSES-NO-PROJECT; the rpg-designer's definition, rpg-designer-death-closes-ownjob-definition.md sha256 df2ba4b5...).

PURE: no ``src`` import, so the unit tests and the summarizer run anywhere. The spy feeds it the entity mappings of each applied update; it counts and never judges (the summarizer judges).

Definitions (state after each applied tick):
* a body is DEAD iff ``lifecycle.death_record`` is not None (an old-age body with ``combat.alive`` True is dead). ``dead_key="alive"`` is the m7 mutant of the spy only: it keys "dead" on ``not combat.alive``.
* a live project = a record whose status is ACTIVE or SUSPENDED;  dead_with_live = a DEAD body that holds >= 1 live project OR a non-empty current_project_id.
* a lag row = a body with ``combat.alive`` False and no death_record, holding a live or current project (the disclosed passive-HP lag).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set

LIVE_STATUSES = ("ACTIVE", "SUSPENDED")
#: The set of typed world-event categories masked out of the LIVING EVENT STREAM in the RUN: EMPTY (rpg-designer, 2026-11-26). The only project/quest-named categories, QUEST_COMPLETED and QUEST_FAILED
#: (src/domains/world_emergence/schema.py:25-26; written at quest_opportunity_rewards.py:107 and world_emergence/services.py:292), are QUEST events, and divergence 2.226 leaves ``quest_status`` alone, so masking them
#: would hide a defect: D7 compares the FULL event stream. ``living_event_digest`` still takes an explicit ``categories`` argument (the logic tests e1-e3 of the mask pass one); an exact match, never a substring.
PROJECT_LIFECYCLE_EVENT_CATEGORIES: frozenset = frozenset()
ROW_CAP = 20


def name_of(x: Any) -> Optional[str]:
    """An enum by its value (or name), a string as itself, None as None."""
    if x is None:
        return None
    v = getattr(x, "value", None)
    return str(v if v is not None else getattr(x, "name", x))


def live_ids(projects: Mapping[str, Any]) -> List[str]:
    return sorted(pid for pid, p in projects.items() if name_of(getattr(p, "status", None)) in LIVE_STATUSES)


def death_record(entity: Any) -> Any:
    return getattr(getattr(entity, "lifecycle", None), "death_record", None)


def is_dead(entity: Any, dead_key: str = "death_record") -> bool:
    if dead_key == "alive":
        return not bool(entity.combat.alive)
    return death_record(entity) is not None


def digest(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()[:16]


def living_projection_digest(canonical: Dict[str, Any], dead_ids: Iterable[Any]) -> str:
    """The LIVING PROJECTION of a state: the canonical state dict with, for every DEAD body, its ``strategic`` component dropped (the dict is not modified)."""
    dead = {str(i) for i in dead_ids}
    entities = canonical.get("entities") or {}
    trimmed = {k: ({kk: vv for kk, vv in v.items() if kk != "strategic"} if k in dead and isinstance(v, dict) else v) for k, v in entities.items()}
    return digest({**canonical, "entities": trimmed})


def living_event_digest(events: Iterable[Any], dead_ids: Iterable[Any], categories: Iterable[str] = PROJECT_LIFECYCLE_EVENT_CATEGORIES) -> str:
    """The LIVING EVENT STREAM of one applied update: its typed world events minus the ``categories`` (EMPTY in the run, so the full stream) whose subject is a dead body."""
    dead, drop = {str(i) for i in dead_ids}, set(categories)
    rows = []
    for e in events:
        cat = name_of(getattr(e, "category", None))
        subject = getattr(e, "subject", None)
        if cat in drop and subject is not None and str(subject) in dead:
            continue
        payload = getattr(e, "payload", None) or {}
        rows.append([cat, getattr(e, "region_id", None), subject, getattr(e, "severity", None), sorted((str(k), v) for k, v in payload.items()), getattr(e, "tick", None)])
    return digest(sorted(rows, key=lambda r: json.dumps(r, default=str)))


class DeathTracker:
    """Counts, per applied update, what the bars D1-D5 and the reported rows need. ``observe(prior, new)`` takes ``{id: entity}`` mappings."""

    def __init__(self, dead_key: str = "death_record") -> None:
        self.dead_key = dead_key
        self.dead_info: Dict[Any, Dict[str, Any]] = {}
        self.dwl_by_tick: Dict[int, int] = {}
        self.dwl_rows: List[Dict[str, Any]] = []
        self.dwl_total_rows = 0
        self.d2_rows: List[Dict[str, Any]] = []
        self.d2_total = 0
        self.lag_since: Dict[Any, int] = {}
        self.lag_rows: List[Dict[str, Any]] = []
        self.lag_total = 0
        self.lag_resolved = 0
        self.lag_removed = 0
        self.lag_long: List[Dict[str, Any]] = []
        self.ends_by: Dict[str, int] = {}
        self.ends_total = 0
        self.abandoned_by: Dict[str, int] = {}
        self.death_split: Dict[str, int] = {}
        self.quest_open_after_death: List[Dict[str, Any]] = []
        self.observed_updates = 0

    def _body_state(self, ent: Any):
        strat = ent.strategic
        return live_ids(strat.projects), bool(getattr(strat, "current_project_id", None))

    def observe(self, tick: int, prior: Mapping[Any, Any], new: Mapping[Any, Any]) -> None:
        self.observed_updates += 1
        dwl = 0
        for eid, ent in new.items():
            lives, cur = self._body_state(ent)
            dr = death_record(ent)
            dead = is_dead(ent, self.dead_key)
            pe = prior.get(eid)
            if dead:
                info = self.dead_info.get(eid)
                if info is None:
                    before = set(pe.strategic.projects) if pe is not None else set()
                    info = self.dead_info[eid] = {"tick": tick, "death_tick": getattr(dr, "tick", None), "ids_before": before, "with_live_at_death": bool(lives or cur), "live_ids_at_death": lives, "last_ids": set(ent.strategic.projects), "last_strat": ent.strategic}
                elif info["last_strat"] is not ent.strategic:
                    info["last_ids"], info["last_strat"] = set(ent.strategic.projects), ent.strategic
                if lives or cur:
                    dwl += 1
                    self.dwl_total_rows += 1
                    if len(self.dwl_rows) < ROW_CAP:
                        self.dwl_rows.append({"tick": tick, "id": eid, "live_ids": lives, "current_project_id": getattr(ent.strategic, "current_project_id", None)})
            if (not ent.combat.alive) and dr is None and (lives or cur):
                if eid not in self.lag_since:
                    self.lag_since[eid] = tick
                    self.lag_total += 1
                    if len(self.lag_rows) < ROW_CAP:
                        self.lag_rows.append({"tick": tick, "id": eid, "live_ids": lives})
            if pe is not None:
                self._transitions(tick, eid, ent, pe, dr, dead)
        for eid in list(self.lag_since):
            since = self.lag_since[eid]
            ent = new.get(eid)
            if ent is None:
                self.lag_removed += 1
                del self.lag_since[eid]
                continue
            lives, cur = self._body_state(ent)
            if death_record(ent) is not None and not lives and not cur:
                self.lag_resolved += 1
                del self.lag_since[eid]
            elif tick > since:
                self.lag_long.append({"id": eid, "first_tick": since, "still_at": tick})
                del self.lag_since[eid]
        self.dwl_by_tick[tick] = dwl

    def _transitions(self, tick: int, eid: Any, ent: Any, pe: Any, dr: Any, dead: bool) -> None:
        old = pe.strategic.projects
        for pid, rec in ent.strategic.projects.items():
            prev = old.get(pid)
            if rec is prev or getattr(rec, "ended_by", None) is None or (prev is not None and getattr(prev, "ended_by", None) is not None):
                continue
            by = name_of(rec.ended_by)
            self.ends_by[by] = self.ends_by.get(by, 0) + 1
            self.ends_total += 1
            if name_of(getattr(rec, "status", None)) == "ABANDONED":
                self.abandoned_by[by] = self.abandoned_by.get(by, 0) + 1
            if by != "DEATH":
                continue
            was = name_of(getattr(prev, "status", None)) if prev is not None else "NEW"
            self.death_split[was] = self.death_split.get(was, 0) + 1
            if name_of(getattr(rec, "status", None)) != "ABANDONED" or not dead or getattr(rec, "ended_tick", None) != getattr(dr, "tick", None):
                self.d2_total += 1
                if len(self.d2_rows) < ROW_CAP:
                    self.d2_rows.append({"tick": tick, "id": eid, "project": pid, "status": name_of(getattr(rec, "status", None)), "ended_tick": getattr(rec, "ended_tick", None), "death_tick": getattr(dr, "tick", None), "dead": dead})
            qs = getattr(rec, "quest_status", None)
            if qs is not None and name_of(qs) == "ACTIVE":
                self.quest_open_after_death.append({"tick": tick, "id": eid, "project": pid})

    def report(self) -> Dict[str, Any]:
        d3 = [{"id": eid, "death_tick": i["death_tick"], "missing": sorted(i["ids_before"] - i["last_ids"])} for eid, i in self.dead_info.items() if i["ids_before"] - i["last_ids"]]
        at_death = [{"id": eid, "tick": i["tick"], "live_ids": i["live_ids_at_death"]} for eid, i in self.dead_info.items() if i["with_live_at_death"]]
        return {
            "dead_key": self.dead_key, "observed_updates": self.observed_updates, "distinct_ticks": len(self.dwl_by_tick), "dead_bodies": len(self.dead_info),
            "dwl_sum": sum(self.dwl_by_tick.values()), "dwl_ticks": sorted(t for t, n in self.dwl_by_tick.items() if n), "dwl_rows": self.dwl_rows, "dwl_total_rows": self.dwl_total_rows,
            "d2_violations": self.d2_total, "d2_rows": self.d2_rows, "d3_violations": len(d3), "d3_rows": d3[:ROW_CAP],
            "dead_at_death_with_live": len(at_death), "dead_at_death_with_live_rows": at_death[:ROW_CAP],
            "lag_total": self.lag_total, "lag_resolved": self.lag_resolved, "lag_removed": self.lag_removed, "lag_over_one_tick": len(self.lag_long), "lag_unjudged_at_run_end": len(self.lag_since), "lag_over_one_tick_rows": self.lag_long[:ROW_CAP], "lag_rows": self.lag_rows,
            "ends_by": dict(sorted(self.ends_by.items())), "ends_total": self.ends_total, "abandoned_by": dict(sorted(self.abandoned_by.items())), "death_split": dict(sorted(self.death_split.items())), "quest_open_after_death": self.quest_open_after_death[:ROW_CAP], "quest_open_after_death_count": len(self.quest_open_after_death),
        }
