"""K2 / K3 count logic: PURE, no import of the frozen tree. Definitions are the rpg-designer's, fixed before any data
(``rpg-designer-k2-k3-count-definitions.md``, sha256 992b7ce37e1a...940cd5855); nothing here redefines them. A field the tree does not expose is reported
(``findings``), never substituted.

K2 (a service dispatch that keeps failing): ``K2Tracker.step`` is fed once per tick and subject, from the POST-APPLY state of tick t.
  dispatch at t  = the subject's task is ENTITY_ACT with an action in the service-action set the spy read from the tree and a building target b.
  failed at t+1  = the apply of tick t+1 delivered no service for (subject, action, b); ``delivered`` is decided by the spy (accepted result for b, or the service's own state change).
  run            = maximal sequence of failed dispatches of one (subject, action, b), consecutive failed ticks at most K = NEED_WAKE_CADENCE apart; it ends at a delivered service
                   for that triple, at death/removal, or at a gap of more than K with no dispatch of that triple. Length = last failed - first failed + 1. One K2 count = a run of length > 100.
K3 (an escalated need wins scoring and loses the switch): ``classify_k3`` is fed one decision with its row-d state read and its row-d+1 outcome.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

K2_LONG = 100
K2_MID = 10

HUNGER_KIND = "hunger"
FATIGUE_KIND = "fatigue"
NEED_KINDS = (HUNGER_KIND, FATIGUE_KIND)


# ----------------------------------------------------------------------------- K2
class K2Tracker:
    """Per (subject, action, building) failure runs. ``k`` is the tree's NEED_WAKE_CADENCE (passed in, read from the tree by the spy)."""

    def __init__(self, k: int) -> None:
        self.k = int(k)
        self.pending: Dict[int, Optional[Tuple[str, int]]] = {}      # subject -> the dispatch (action, building) of the previous tick
        self.open: Dict[Tuple[int, str, int], Dict[str, Any]] = {}   # (subject, action, building) -> the run being built
        self.closed: List[Dict[str, Any]] = []
        self.dispatch_ticks = 0
        self.dispatch_subjects: set = set()
        self.alive_subject_ticks = 0

    def _close(self, key: Tuple[int, str, int], ended: str) -> None:
        run = self.open.pop(key, None)
        if run is None:
            return
        run["ended_by"] = ended
        run["length"] = run["last_failed"] - run["first_failed"] + 1
        self.closed.append(run)

    def _delivered(self, key: Tuple[int, str, int], tick: int) -> None:
        """A delivered service ends the run of that triple (if any)."""
        self._close(key, "delivered")

    def _failed(self, key: Tuple[int, str, int], failed_tick: int, reasons: List[Any], kind: Optional[str]) -> None:
        run = self.open.get(key)
        if run is not None and failed_tick - run["last_failed"] > self.k:
            self._close(key, "gap")
            run = None
        if run is None:
            self.open[key] = run = {"subject": key[0], "action": key[1], "building": key[2], "building_kind": kind, "first_failed": failed_tick, "last_failed": failed_tick,
                                    "failed_dispatches": 0, "reasons": Counter()}
        run["last_failed"] = failed_tick
        run["failed_dispatches"] += 1
        for reason in reasons:
            run["reasons"][str(reason)] += 1

    def step(self, tick: int, subject: int, present: bool, alive: bool, dispatch: Optional[Tuple[str, int]], delivered: List[Tuple[str, int]],
             reasons: Optional[Dict[Tuple[str, int], List[Any]]] = None, building_kinds: Optional[Dict[int, str]] = None) -> None:
        """``dispatch`` = (action, building_id) of the task on the post-apply state of ``tick`` (None when not a service dispatch); ``delivered`` = the (action, building_id) pairs the apply of ``tick`` delivered;
        ``reasons`` = the refusal reasons the apply of ``tick`` gave for each (action, building) pair, recorded as found (typed, None, or the string 'absent')."""
        reasons = reasons or {}
        building_kinds = building_kinds or {}
        if not present or not alive:
            self.pending.pop(subject, None)
            for key in [k for k in self.open if k[0] == subject]:
                self._close(key, "removed" if not present else "died")
            return
        self.alive_subject_ticks += 1
        prev = self.pending.get(subject)
        for pair in delivered:                                           # a delivered service ends that triple's run whether or not it was the pending dispatch
            self._delivered((subject, pair[0], pair[1]), tick)
        if prev is not None and prev not in delivered:                 # the dispatch of t-1 was not delivered by the apply of t: FAILED at t (the dispatch tick is t-1)
            self._failed((subject, prev[0], prev[1]), tick - 1, reasons.get(prev, ["absent"]), building_kinds.get(prev[1]))
        self.pending[subject] = dispatch
        if dispatch is not None:
            self.dispatch_ticks += 1
            self.dispatch_subjects.add(subject)
        for key in [k for k in self.open if k[0] == subject and tick - self.open[k]["last_failed"] > self.k and (dispatch is None or (dispatch[0], dispatch[1]) != (k[1], k[2]))]:
            self._close(key, "gap")

    def finish(self, final_tick: int) -> None:
        """End of the cell: every open run is closed as ``open_at_end`` (not a delivered / died ending)."""
        for key in list(self.open):
            self._close(key, "open_at_end")

    def summary(self, blockers_for=None) -> Dict[str, Any]:
        runs = sorted(self.closed, key=lambda r: (r["first_failed"], r["subject"], r["action"], r["building"]))
        out_runs = []
        for r in runs:
            row = dict(r)
            row["reasons"] = dict(r["reasons"])
            out_runs.append(row)
        long_runs = [r for r in out_runs if r["length"] > K2_LONG]
        return {"k": self.k, "runs": out_runs, "runs_all": len(out_runs), "runs_over_10": sum(1 for r in out_runs if r["length"] > K2_MID), "runs_over_100": len(long_runs),
                "k2_count": len(long_runs), "long_runs": long_runs, "dispatch_ticks": self.dispatch_ticks, "subjects_with_dispatch": len(self.dispatch_subjects),
                "alive_subject_ticks": self.alive_subject_ticks}


# ----------------------------------------------------------------------------- K3
def classify_k3(state_row: Dict[str, Any], outcome: Dict[str, Any]) -> str:
    """One decision whose winner is already an escalated need of row d (the caller checks). Returns ``excluded_threat`` (row d has a present threat to life: tier 1 outranks the need, SURV-07),
    ``win`` (row d+1: the subject's current project is a live project of the winner's kind, per the tree's ``same_kind``; the spy passes that as ``same_kind_current_live``),
    ``loss_L1`` (another kind is current) or ``loss_L2`` (no current project and none of that kind created)."""
    if state_row.get("threat"):
        return "excluded_threat"
    if outcome.get("same_kind_current_live"):
        return "win"
    if outcome.get("current_project_id") is not None:
        return "loss_L1"
    return "loss_L2"


def k3_summary(decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """``decisions``: each {eid, need, tick, klass, ...}. Counts: one K3 count = one losing decision (L1 or L2) outside the threat exclusion. Episodes = consecutive losing decisions of one subject and need with no winning decision between."""
    by_need: Dict[str, Counter] = {n: Counter() for n in NEED_KINDS}
    subjects: Dict[str, set] = {n: set() for n in NEED_KINDS}
    episodes: Dict[str, int] = {n: 0 for n in NEED_KINDS}
    last: Dict[Tuple[int, str], str] = {}
    for d in sorted(decisions, key=lambda x: (x["tick"], x["eid"])):
        need, klass = d["need"], d["klass"]
        by_need[need][klass] += 1
        subjects[need].add(d["eid"])
        key = (d["eid"], need)
        if klass in ("loss_L1", "loss_L2") and last.get(key) not in ("loss_L1", "loss_L2"):
            episodes[need] += 1
        if klass != "excluded_threat":                          # an excluded decision neither wins nor loses; it does not break an episode
            last[key] = klass
    result: Dict[str, Any] = {"per_need": {}}
    total_losses = 0
    for need in NEED_KINDS:
        c = by_need[need]
        losses = c["loss_L1"] + c["loss_L2"]
        total_losses += losses
        result["per_need"][need] = {"decisions": sum(c.values()), "wins": c["win"], "loss_L1": c["loss_L1"], "loss_L2": c["loss_L2"], "excluded_threat": c["excluded_threat"],
                                    "k3_count": losses, "episodes": episodes[need], "subjects": len(subjects[need])}
    result["k3_count"] = total_losses
    return result
