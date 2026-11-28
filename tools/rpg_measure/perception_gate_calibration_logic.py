"""Perception-gate calibration own-job logic (TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT; PERC 3a; rpg-designer ruling 9c42fb88).

PURE: no ``src`` import, so the unit tests and the summarizer run anywhere. The spy feeds it plain values.

Definitions (per cell, one arm):
 - ``perceived``: gate calls that returned perceived True, by channel set and by day/night.
 - ``vision_still_small_day`` / ``vision_still_medium_night`` (the NON-VACUITY rows): a perception through the vision channel ALONE of a still body (noise level low or very_low) whose visibility is the arm's
   SMALL size level (by day) or MEDIUM size level (by night). They are the ticket's own rows: base gives 0 for the first at any distance and only touch for the second; fix must give > 0.
 - ``hunts_started`` / ``engagements_started``: a body's current objective changes to one that names a body (``target_entity_id``) and belongs to a hunger project (a hunt) or is a defeat-enemy objective (an engagement).
 - ``bodies_hit`` (REPORTED only): bodies STRUCK on the applied tick (``last_hit_tick`` equals it); the engagement STOP stays on the objective-based count.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional

STILL_LEVELS = ("low", "very_low", "none")


def size_levels(settings_size_visibility: Optional[Mapping[str, str]]) -> Dict[str, str]:
    """The arm's small and medium visibility levels: its calibration record when it has one (the fix arm), else the 02a map (the base arm)."""
    if settings_size_visibility:
        return {"small": settings_size_visibility["small"], "medium": settings_size_visibility["medium"]}
    return {"small": "low", "medium": "medium"}


def classify_perception(perceived: bool, signals_used: Iterable[str], target_signals: Mapping[str, Any], night: bool, levels: Mapping[str, str]) -> Dict[str, Any]:
    """One gate result as the counters it moves: channel key, day/night, and the two non-vacuity rows."""
    used = tuple(signals_used)
    still = str(target_signals.get("noise", "none")).lower() in STILL_LEVELS
    vision_only = used == ("visibility",)
    visibility = str(target_signals.get("visibility", "none")).lower()
    return {
        "perceived": bool(perceived),
        "channels": "+".join(sorted(used)) or "-",
        "night": bool(night),
        "vision_still_small_day": bool(perceived and vision_only and still and not night and visibility == levels["small"]),
        "vision_still_medium_night": bool(perceived and vision_only and still and night and visibility == levels["medium"]),
    }


def objective_started(prior_objective_id: Optional[str], objective: Optional[Mapping[str, Any]]) -> Optional[str]:
    """``'hunt'``, ``'engagement'`` or None for a body whose current objective just changed: ``objective`` = {id, kind, project_kind, target_entity_id}."""
    if objective is None or objective.get("id") == prior_objective_id or objective.get("target_entity_id") is None:
        return None
    # A hunger project's hunt objective names its prey with the kind REACH_LOCATION (ac759e0ba: intelligence.py:1500 `kind=best_candidate.metadata.get("obj_kind") or ObjectiveKind.REACH_LOCATION`; the
    # HUNGER GoalScore, scorers.py:118-120, carries no obj_kind), and an engagement is the combat scorer's DEFEAT_ENEMY (scorers.py:214). The project kind is tested FIRST: whatever its objective kind,
    # a hunger project's body-naming objective is a hunt, so the hunt STOP can never be starved by a DEFEAT_ENEMY hunt.
    if str(objective.get("project_kind", "")).lower() == "hunger":
        return "hunt"
    if "defeat" in str(objective.get("kind", "")).lower():
        return "engagement"
    return None


def settings_finding(arm: Optional[str], gate_calls: int, settings_seen: int) -> Optional[str]:
    """A FINDING (the spy exits rc 6) when ARM=fix but no gate call saw a calibration record: the spy would then silently read the 02a size map and the non-vacuity rows would read 0 as NOT MEASURED."""
    if arm == "fix" and gate_calls > 0 and settings_seen == 0:
        return "ARM=fix but no gate call saw a calibration record (PerceptionGate.settings): the arm tree is not the calibration head, or the gate is reached without it"
    return None


class Counters:
    """The cell's counters; ``report()`` is the JSON the summarizer reads."""

    def __init__(self) -> None:
        self.gate_calls = 0
        self.perceived = 0
        self.by_channel: Dict[str, int] = {}
        self.by_night = {"day": 0, "night": 0}
        self.vision_still_small_day = 0
        self.vision_still_medium_night = 0
        self.perceived_hostile_calls = 0
        self.perceived_hostile_true = 0
        self.hunts_started = 0
        self.engagements_started = 0
        self.bodies_hit = 0
        self.apply_calls = 0

    def gate(self, row: Mapping[str, Any]) -> None:
        self.gate_calls += 1
        if not row["perceived"]:
            return
        self.perceived += 1
        self.by_channel[row["channels"]] = self.by_channel.get(row["channels"], 0) + 1
        self.by_night["night" if row["night"] else "day"] += 1
        self.vision_still_small_day += int(row["vision_still_small_day"])
        self.vision_still_medium_night += int(row["vision_still_medium_night"])

    def hostile(self, result: bool) -> None:
        self.perceived_hostile_calls += 1
        self.perceived_hostile_true += int(bool(result))

    def started(self, kind: Optional[str]) -> None:
        if kind == "hunt":
            self.hunts_started += 1
        elif kind == "engagement":
            self.engagements_started += 1

    def report(self) -> Dict[str, Any]:
        return {"gate_calls": self.gate_calls, "perceived": self.perceived, "by_channel": dict(sorted(self.by_channel.items())), "by_night": dict(self.by_night),
                "vision_still_small_day": self.vision_still_small_day, "vision_still_medium_night": self.vision_still_medium_night,
                "perceived_hostile_calls": self.perceived_hostile_calls, "perceived_hostile_true": self.perceived_hostile_true,
                "hunts_started": self.hunts_started, "engagements_started": self.engagements_started, "bodies_hit": self.bodies_hit, "apply_calls": self.apply_calls}
