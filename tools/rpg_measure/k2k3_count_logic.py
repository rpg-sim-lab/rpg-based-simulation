"""K2 / K3 count logic: PURE, no import of the frozen tree. Definitions are the rpg-designer's, fixed before any data
(``rpg-designer-k2-k3-count-definitions.md``, sha256 992b7ce37e1a...940cd5855); nothing here redefines them. A field the tree does not expose is reported
(``findings``), never substituted.

K2 (a service dispatch that keeps failing): ``K2Tracker.step`` is fed once per tick and subject, from the POST-APPLY state of tick t.
  dispatch at t  = the subject's task is ENTITY_ACT with an action in the service-action set the spy read from the tree and a building target b.
  failed at t+1  = the apply of tick t+1 delivered no service for (subject, action, b); ``delivered`` is decided by the spy (accepted result for b, or the service's own state change).
  run            = maximal sequence of failed dispatches of one (subject, action, b), consecutive failed ticks at most K = NEED_WAKE_CADENCE apart; it ends at a delivered service
                   for that triple, at death/removal, or at a gap of more than K with no dispatch of that triple. Length = last failed - first failed + 1. One K2 count = a run of length > 100.
AMENDMENT 1 (rpg-designer-k2k3-kit-v1-review.md, e6cc644c87cff181..., written before any data; it only tightens): A1 "delivered" is the paid transfer at b or an accepted result, never a bare need drop; A2 every service dispatch must be seen
(router pass-through plus the post-apply task, per-action visibility control, a miss means NOT MEASURED, never 0); A3 K3's close needs frontier_living_world s43-46 as well (7 cells).
K3 (an escalated need wins scoring and loses the switch): ``classify_k3`` is fed one decision with its row-d state read and its row-d+1 outcome.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

K2_LONG = 100
K2_MID = 10

HUNGER_KIND = "hunger"
FATIGUE_KIND = "fatigue"
NEED_KINDS = (HUNGER_KIND, FATIGUE_KIND)
SPEC_SHA = "992b7ce37e1a7325a9afab517cd87ce65221627ea2ddd2be4377962940cd5855"
AMENDMENT_1_SHA_PREFIX = "e6cc644c87cff1818180"          # rpg-designer-k2k3-kit-v1-review.md (the full sha256 is in the review's own record)
RULE_SOURCE = f"992b7ce3 + Amendment 1 {AMENDMENT_1_SHA_PREFIX}"
K3_S42_CELLS = 3
K3_CLOSE_CELLS = 7                                         # A3: the three s42 cells plus frontier_living_world s43-46
DECISION_POLICY = "the last decision of a tick wins: a second apply_modifiers call for the same subject and tick overwrites the pending decision (duplicates are counted)"


# ----------------------------------------------------------------------------- K2
class K2Tracker:
    """Per (subject, action, building) failure runs. ``k`` is the tree's NEED_WAKE_CADENCE (passed in, read from the tree by the spy)."""

    def __init__(self, k: int) -> None:
        self.k = int(k)
        self.pending: Dict[int, Set[Tuple[str, int]]] = {}      # subject -> the dispatches (action, building) of the previous tick (post-apply task and router channel)
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

    def step(self, tick: int, subject: int, present: bool, alive: bool, dispatch: Any, delivered: List[Tuple[str, int]],
             reasons: Optional[Dict[Tuple[str, int], List[Any]]] = None, building_kinds: Optional[Dict[int, str]] = None) -> None:
        """``dispatch`` = the (action, building_id) pair(s) of the post-apply task of ``tick`` (None, one tuple, or an iterable of tuples; the caller merges the router channel into ``pending`` for the PREVIOUS tick before calling);
        ``delivered`` = the (action, building_id) pairs the apply of ``tick`` delivered; ``reasons`` = the refusal reasons the apply of ``tick`` gave for each pair, recorded as found (typed, 'None', or 'absent')."""
        reasons = reasons or {}
        building_kinds = building_kinds or {}
        if not present or not alive:
            self.pending.pop(subject, None)
            for key in [k for k in self.open if k[0] == subject]:
                self._close(key, "removed" if not present else "died")
            return
        self.alive_subject_ticks += 1
        now: Set[Tuple[str, int]] = set() if dispatch is None else ({dispatch} if isinstance(dispatch, tuple) else set(dispatch))
        for pair in delivered:                                           # a delivered service ends that triple's run whether or not it was a pending dispatch
            self._delivered((subject, pair[0], pair[1]), tick)
        for prev in sorted(self.pending.get(subject, set())):           # a dispatch of t-1 the apply of t did not deliver FAILED (the dispatch tick is t-1)
            if prev not in delivered:
                self._failed((subject, prev[0], prev[1]), tick - 1, reasons.get(prev, ["absent"]), building_kinds.get(prev[1]))
        self.pending[subject] = now
        if now:
            self.dispatch_ticks += 1
            self.dispatch_subjects.add(subject)
        for key in [k for k in self.open if k[0] == subject and tick - self.open[k]["last_failed"] > self.k and (k[1], k[2]) not in now]:
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


# ----------------------------------------------------------------------------- A2: per-action dispatch visibility
class DispatchVisibility:
    """Every accepted service result (source kind, building b) for a subject at t must be preceded by a SEEN dispatch of an action of that source kind at b by that subject at t-1 (union of the router channel and the post-apply task).
    A miss, or accepted results with 0 seen dispatches, makes that action's K2 NOT MEASURED, never 0. ``TOWN_SERVICE`` results carry no action (F1), so an unseen one is a miss for EVERY town-service action the building kind serves."""

    def __init__(self, action_source: Dict[str, str], service_kinds: Dict[str, Iterable[str]]) -> None:
        self.action_source = dict(action_source)
        self.service_kinds = {a: set(v) for a, v in service_kinds.items()}
        self.accepted: Counter = Counter()
        self.misses: Counter = Counter()
        self.seen: Counter = Counter()              # dispatches seen by either channel, per action
        self.seen_router: Counter = Counter()
        self.seen_task: Counter = Counter()

    def note_dispatch(self, action: str, router: bool, task: bool) -> None:
        self.seen[action] += 1
        if router:
            self.seen_router[action] += 1
        if task:
            self.seen_task[action] += 1

    def candidates(self, source_kind: str, building_kind: Optional[str]) -> List[str]:
        return sorted(a for a, k in self.action_source.items() if k == source_kind and (source_kind != "TOWN_SERVICE" or building_kind in self.service_kinds.get(a, set())))

    def note_accepted(self, source_kind: str, building: int, building_kind: Optional[str], pending: Iterable[Tuple[str, int]]) -> bool:
        """Returns True when the accepted result was preceded by a seen dispatch."""
        cand = self.candidates(source_kind, building_kind)
        seen = sorted(a for a, b in pending if b == building and a in cand)
        if seen:
            self.accepted[seen[0]] += 1
            return True
        for a in cand:
            self.accepted[a] += 1
            self.misses[a] += 1
        return False

    def summary(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for action in sorted(self.action_source):
            measured = not (self.misses[action] > 0 or (self.accepted[action] > 0 and self.seen[action] == 0))
            out[action] = {"accepted_results": self.accepted[action], "misses": self.misses[action], "dispatches_seen": self.seen[action], "seen_by_router": self.seen_router[action],
                           "seen_by_task": self.seen_task[action], "measured": measured, "visibility_tested": self.accepted[action] > 0,
                           "status": "MEASURED" if measured else "NOT MEASURED (never 0)"}
        return out


# ----------------------------------------------------------------------------- the close rules (A3)
def close_verdicts(cells: List[Dict[str, Any]]) -> Dict[str, Any]:
    """PURE. ``cells``: each {name, world, seed, stage (1|2), valid, k2_count_measured, k2_not_measured (list of actions), k3_count}. Stage 1 = the three s42 cells plus urban_political s46; stage 2 = frontier_living_world s43-46.
    K2 (rule: 992b7ce3 + Amendment 1): proposed for close only when the four stage-1 cells are valid, every K2 count is 0 and NO action is NOT MEASURED in any of them; any K2 count > 0 stays HARD.
    K3 (A3): a nonzero s42 total stays HARD with no stage 2 needed; a close needs K3 = 0 in all 7 cells (three s42 plus frontier s43-46), each valid; with fewer than 7 valid cells it can never print a close."""
    s42 = [c for c in cells if c["seed"] == 42]
    stage1 = [c for c in cells if c["stage"] == 1]
    stage2 = [c for c in cells if c["stage"] == 2]
    out: Dict[str, Any] = {"rule_source": RULE_SOURCE}
    # K2
    k2_cells = stage1
    if len(k2_cells) < 4 or not all(c["valid"] for c in k2_cells):
        out["k2"] = "VOID: a stage-1 cell is missing or invalid, no rule applied"
    elif any(c["k2_count_measured"] > 0 for c in k2_cells):
        out["k2"] = "STAYS HARD: a K2 count > 0"
    elif any(c["k2_not_measured"] for c in k2_cells):
        out["k2"] = "NOT PROPOSED: K2 is 0 only for the measured actions; an action is NOT MEASURED (" + ", ".join(sorted({a for c in k2_cells for a in c["k2_not_measured"]})) + ")"
    else:
        out["k2"] = "PROPOSE CLOSE (K2 = 0 in all 4 cells, every service action measured)"
    # K3
    s42_valid = [c for c in s42 if c["valid"]]
    if len(s42) < K3_S42_CELLS or len(s42_valid) < K3_S42_CELLS:
        out["k3"] = "VOID: an s42 cell is missing or invalid, no rule applied"
    elif sum(c["k3_count"] for c in s42) > 0:
        out["k3"] = "STAYS HARD: the s42 total is nonzero (stage 2 not needed)"
    else:
        valid_all = [c for c in s42 + stage2 if c["valid"]]
        if len(valid_all) < K3_CLOSE_CELLS or len({c["name"] for c in valid_all}) < K3_CLOSE_CELLS:
            out["k3"] = f"NOT PROPOSED: s42 total is 0 but only {len(valid_all)} of {K3_CLOSE_CELLS} cells are valid (stage 2: frontier_living_world s43-46 still needed)"
        elif sum(c["k3_count"] for c in valid_all) > 0:
            out["k3"] = "STAYS HARD: a K3 count > 0 in a stage-2 cell"
        else:
            out["k3"] = "PROPOSE CLOSE (K3 = 0 in all 7 cells)"
    return out
