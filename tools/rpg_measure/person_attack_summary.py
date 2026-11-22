"""Summarizer for the person-attack trace (offline: it reads the cells' JSON files, it never runs inside a simulation).

Input: a directory of cell files written by ``person_attack_run`` (``<arm>__<world>__s<seed>__plain.json`` and ``...__spy.json``). Output: the derived views (a)-(e) and the pre-set rules R1-R7
(rpg-designer, set BEFORE data; the brief is stored word for word at agent-working/stored_artifacts/TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES/
o3_trace_brief_relayed_2026-11-21.md on rpg-planner-ubuntu's seat). Every rule is evaluated mechanically and names the attacker ids on a miss. Rules only tighten; nothing here edits a rule.

MEASUREMENT CHOICES (each is approved with the kit shas, none is a rule change; items 8-10 are the designer's answers):
 1. NIGHT is ONE instrument for both arms: ``is_night`` from the NEW tree's ``src/core/calendar.py`` (loaded by file path; its sha256 is recorded), applied to the row's ``world_time`` (the world clock the state
    carries, not the tick) of the engagement's FIRST attack. BASE's own simulation had no ``is_night`` and its night checks read the raw clock (SURV-08, amendment "the clock"), so BASE's day/night split is the shared
    instrument's view, not what BASE's agents used.
 2. PERIODS: the table ``PERIODS`` is pinned in this file with its quote and source (``PERIODS_QUOTE``, ``PERIODS_SOURCE``, ``MISSING_LAW_QUOTE``), so the kit sha256 covers it. Keyed by species id, the same table for both arms.
    A species not in the table is NEVER defaulted: its engagements are ``period_unknown`` and counted (choice 9).
 3. INSIDE the active period: diurnal = not is_night, nocturnal = is_night, any hour = always (the kit's reading of SURV-08).
 4. ENGAGEMENT: attack events (hit or miss) by one attacker on one victim; a gap of <= 50 ticks between consecutive events stays in the engagement, a gap > 50 opens a new one (controls: 50 and 51).
 5. OUTCOME of an engagement, first match: ``victim_killed`` (any event leaves the victim not alive), ``victim_fled`` (the victim's movement mode is RETREAT after an event, or a mode row RETREAT within the engagement
    plus the gap), ``attacker_fled`` (the same for the attacker), ``unresolved_at_end`` (the run ended within the gap of its last event), else ``disengaged``.
 6. R3 is evaluated on the tighter reading: the largest number of engagements one attacker STARTS inside any rolling window of 2400 ticks (the calendar-day bin count is reported too).
 7. R7 reads the O3-group hits only (the attackers the trace is about); the same counts over every attacker are reported as ``all_attackers_info``. A DECISION between two hits of one victim is: its mode after the first hit
    (Rulings of 2026-11-22, C1/C2: a chain of consecutive hits resets when two consecutive hits on the victim are more than 50 ticks apart, the engagement rule; and any attack BY a watched id, on any target, hit or miss, is a fight decision of that id.)
    in {RETREAT (flight), PURSUE (fight)}, or it attacked on that tick (fight), or a mode row in {RETREAT, PURSUE} between the two ticks, or its mode before the second hit in {RETREAT, PURSUE}. Asleep = the task action is
    in lodging_rules.SLEEP_ACTIONS, lodged = navigation.lodged_in set, both read from the state BEFORE the hit.
 8. ARMS (rpg-designer's answer, relayed at rpg-planner-ubuntu's seat commit a3eedf7e7): R1-R5 and R7 are judged on NEW; BASE is context, computed and shown side by side. A miss on NEW AND on BASE in the same seed reads
    "BUG CANDIDATE, pre-existing (not attributed to #953/#954)"; a miss on NEW only reads "BUG CANDIDATE, attributed". R6 is NEW vs BASE (a miss is attributed). Every miss names the attacker ids.
 9. NOT ASSESSABLE IS NOT A PASS. In a seed with >= 10 engagements, if the engagements of attackers whose species is not in the table are >= 10% of the seed's engagements, R5 reads ``NOT_CLEARED`` (counts as HELD)
    and lists the species. Below 10%, R5 decides on the engagements it can assess and reports the unassessable share. The 10% threshold and "decides on the assessed engagements only (>= 90% of them inside
    the active period)" were CONFIRMED by rpg-designer (follow-up to the answers at rpg-planner-ubuntu's seat, a3eedf7e7 lineage). Every R5 miss carries the tag ``SURV-08 law MISSING in code``.
10. OVERALL (``verdict``, rpg-designer's pre-data ruling, relayed at rpg-planner-ubuntu's seat): NO seed is exempt below 10 engagements. R1 (holds by construction, still checked and reported), R3, R4 and R7 are judged in
    EVERY seed at any count, R6 in every seed with >= 10 NEW hits; R2 and R5 are share rules and read ``NOT_EVALUATED (n<10)`` below 10 engagements. ``run_line`` says "R2/R5 NOT EVALUATED (n<10)" when no NEW seed reaches 10.
    CLEARED only if R3, R4, R6 and R7 hold in every seed AND R2 and R5 hold wherever evaluated. Any miss on NEW = BUG CANDIDATE (attributed if any miss is attributed, else pre-existing); otherwise any NOT_CLEARED / unassessable /
    invalid NEW cell = HELD (a miss outranks HELD, HELD outranks CLEARED); otherwise CLEARED.
11. GROUP SCOPE (ruled by rpg-designer): R1-R7 and the verdict apply to the attackers whose kind group is exactly a member of ``TIED_GROUPS`` (today only "meat", the brief's "FLW meat O3.attacks_on_people" row), each tied group
    judged separately; its R1 reads "every counted attacker is in that exact group (and its declared diet is that group's classes)". Every other O3 group (the gate's own O3 predicate, e.g. ``meat+plant+prepared``) is reported in
    full under ``groups`` (engagements, attackers, pairs, hit states, the rules computed as "context, no verdict") and has NO effect on any verdict. Which rows are O3 is decided by the spy with the ledger's own key and the gate's
    predicate (``o3_label``), never here.
MEASUREMENT LABEL (in the output as ``measurement_labels``): the night split is a MEASUREMENT made with NEW's ``is_night`` applied offline to both arms; BASE's agents never used it.
Usage: python person_attack_summary.py --dir <cells dir> --calendar-tree <NEW tree> --out <summary.json>
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

ENGAGEMENT_GAP = 50
TICKS_PER_DAY = 2400  # src/core/calendar.py:9 at 87792e3e8
MIN_ENGAGEMENTS = 10
MIN_HITS = 10
NOT_EVALUATED = "NOT_EVALUATED (n<10)"
NOT_ASSESSABLE_SHARE = 0.10  # a seed whose engagements by unknown-species attackers reach this share is NOT CLEARED (R5 not assessable): ruled by rpg-designer
R5_TAG = "SURV-08 law MISSING in code"
MEASUREMENT_LABELS = [
    "night/day and 'inside the active period' are a MEASUREMENT: NEW's calendar.is_night applied offline to the world_time of both arms' events; BASE's agents never used it (BASE has no is_night, its night checks read the raw clock)",
    "periods are the SURV-08 owner amendment Q5(a) table pinned in this file; no kit declares a period in code at either sha (SURV-08: 'Repository evidence: MISSING')",
]
PERIODS_SOURCE = "docs/world_rules/life-body/survival-needs.md:1042-1044 at 87792e3e8 (owner amendment Q5(a), 2026-11-17); the line at :1045 is MISSING_LAW_QUOTE"
PERIODS_QUOTE = (
    "**Amendment, the periods (decided by the owner, 2026-11-17, Q5(a)).** Diurnal: human, elf, dwarf, "
    "orc, lizardfolk, small_plant_eater, dragonkin. Nocturnal: goblin, wolf, spider, undead, troll. "
    "Any hour: slime, spirit."
)
MISSING_LAW_QUOTE = "**Repository evidence: MISSING (2026-11-17).** No kind declares a period; one night window applies to every kind (roadmap §12.1), and the night checks read the raw clock, so every tick after 1800 counts as night."
TIED_GROUPS = ("meat",)  # the O3 groups tied to #953/#954 (ruled by rpg-designer): the brief's "FLW meat O3.attacks_on_people" row (0.6 -> 24.0 per seed); O3 rows are keyed by the EXACT kind group (rpg_gate_metrics.py:396-411);
# FLW `meat` is the only O3 row in all 20 saved gate reports and v2 (lead's attribution check), so it has no other member today. Each tied group gets R1-R7 and its own verdict; every other O3 group is context, no verdict.
DIURNAL, NOCTURNAL, ANY_HOUR = "diurnal", "nocturnal", "any_hour"
PERIODS: Dict[str, str] = {
    **{species: DIURNAL for species in ("human", "elf", "dwarf", "orc", "lizardfolk", "small_plant_eater", "dragonkin")},
    **{species: NOCTURNAL for species in ("goblin", "wolf", "spider", "undead", "troll")},
    **{species: ANY_HOUR for species in ("slime", "spirit")},
}
DECISION_MODES = ("RETREAT", "PURSUE")
MOTIVES = ("DEFEND", "HUNT", "HOSTILE", "OBJECTIVE", "UNCLASSED")  # first match wins (M3, final draft section 9: the engine's own BASIS for a fight, PREDATION or FACTION_HOSTILE, before a goal-carried OBJECTIVE)
NO_INPUTS = "NO_INPUTS"                                              # never a motive: the first row has no motive inputs (or prior_bodies_present is False); counted separately, never folded into UNCLASSED
MOTIVE_KEYS = MOTIVES + (NO_INPUTS,)
NO_INPUTS_NOT_ASSESSABLE_SHARE = 0.10                                # R1: at >= 10% of a cell's judged engagements R1 reads NOT_CLEARED (held), mirroring R5
RULE_NAMES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7")


def load_is_night(calendar_path: Path) -> Tuple[Callable[[int], bool], str]:
    """``is_night`` of the NEW tree's calendar module, loaded by file path, and the file's sha256."""
    spec = importlib.util.spec_from_file_location("_person_attack_new_calendar", calendar_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.is_night, hashlib.sha256(calendar_path.read_bytes()).hexdigest()


def inside_period(species: str, night: bool) -> Optional[bool]:
    """True/False for a species in the table, None (``period_unknown``) otherwise. Never defaulted."""
    period = PERIODS.get(species)
    if period is None:
        return None
    return True if period == ANY_HOUR else (night if period == NOCTURNAL else not night)


def engagement_motive(first_row: Dict[str, Any]) -> Dict[str, Any]:
    """PURE. The motive class of an engagement from its FIRST attack's row (the inputs were read on that attack's PRIOR state). It reads ONLY three typed values: the Relation VALUE of
    relation(attacker, victim) (``relation_attacker_to_victim``), the bool ``attacked_me_recently_victim_on_attacker`` (the victim hit the attacker recently) and whether the attacker's active objective
    ``target_entity_id`` equals the victim's id. First match (M3): DEFEND, HUNT (PREDATION), HOSTILE (FACTION_HOSTILE), OBJECTIVE, else UNCLASSED: the engine's own basis for a fight (PREDATION, FACTION_HOSTILE) comes before a
    goal-carried OBJECTIVE, because combat_engage / defeat_enemy and a hunger hunt both set the objective target to the victim; ``objective_target_is_victim`` stays a typed input, reported per motive as information.
    M4: a first row with no motive inputs, or with ``prior_bodies_present`` False, is ``NO_INPUTS``, never a motive. The payload reason, the objective kind, the project kind, the mode and every other recorded input are INFORMATION:
    they are returned under ``info`` and never change the class (control)."""
    mi = first_row.get("motive_inputs") or {}
    objective = mi.get("attacker_objective") or {}
    typed = {"relation_attacker_to_victim": mi.get("relation_attacker_to_victim"), "attacked_me_recently_victim_on_attacker": mi.get("attacked_me_recently_victim_on_attacker"),
             "objective_target_is_victim": objective.get("target_entity_id") is not None and objective.get("target_entity_id") == first_row.get("victim_id")}
    if not mi or mi.get("prior_bodies_present") is False:
        motive = NO_INPUTS
    elif typed["attacked_me_recently_victim_on_attacker"] is True:
        motive = "DEFEND"
    elif typed["relation_attacker_to_victim"] == "PREDATION":
        motive = "HUNT"
    elif typed["relation_attacker_to_victim"] == "FACTION_HOSTILE":
        motive = "HOSTILE"
    elif typed["objective_target_is_victim"]:
        motive = "OBJECTIVE"
    else:
        motive = "UNCLASSED"
    info = {"task_reason": mi.get("task_reason"), "task_action": mi.get("task_action"), "objective_kind": objective.get("kind"), "project_kind": objective.get("project_kind"),
            "attacker_mode_before": mi.get("attacker_mode_before"), "relation_victim_to_attacker": mi.get("relation_victim_to_attacker"), "relation_call_form": mi.get("relation_call_form"),
            "attacker_can_eat_victim": mi.get("attacker_can_eat_victim"), "relation_form": mi.get("relation_form"), "relation_source_default": mi.get("relation_source_default"),
            "own_relation_value": mi.get("relation_attacker_to_victim"), "inputs_missing": not mi, "prior_bodies_present": mi.get("prior_bodies_present")}
    return {"motive": motive, "typed_inputs": typed, "info": info}


def build_engagements(rows: List[Dict[str, Any]], mode_rows: List[Dict[str, Any]], final_tick: int, is_night: Callable[[int], bool], only_o3: bool = True) -> List[Dict[str, Any]]:
    """The attack events grouped into engagements (see the module docstring, choices 4 and 5): the O3-group rows by default, EVERY row with ``only_o3=False`` (the motive tables)."""
    pairs: Dict[Tuple[int, int], List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row["in_o3_group"] or not only_o3:
            pairs[(row["attacker_id"], row["victim_id"])].append(row)
    retreats: Dict[int, List[int]] = defaultdict(list)
    for mode_row in mode_rows:
        if mode_row["mode"] == "RETREAT":
            retreats[mode_row["id"]].append(mode_row["tick"])
    engagements: List[Dict[str, Any]] = []
    for (attacker_id, victim_id), events in sorted(pairs.items()):
        events = sorted(events, key=lambda r: r["tick"])
        groups: List[List[Dict[str, Any]]] = []
        for event in events:
            if groups and event["tick"] - groups[-1][-1]["tick"] <= ENGAGEMENT_GAP:
                groups[-1].append(event)
            else:
                groups.append([event])
        for group in groups:
            first, last = group[0], group[-1]
            start, end = first["tick"], last["tick"]

            def fled(who: int, mode_key: str) -> bool:
                return any(e[mode_key] == "RETREAT" for e in group) or any(start <= t <= end + ENGAGEMENT_GAP for t in retreats.get(who, []))

            if any(not e["victim_alive_after"] for e in group):
                outcome = "victim_killed"
            elif fled(victim_id, "victim_mode_after"):
                outcome = "victim_fled"
            elif fled(attacker_id, "attacker_mode_after"):
                outcome = "attacker_fled"
            elif end + ENGAGEMENT_GAP >= final_tick:
                outcome = "unresolved_at_end"
            else:
                outcome = "disengaged"
            night = bool(is_night(first["world_time"]))
            engagements.append({
                "attacker_id": attacker_id, "attacker_kind": first["attacker_kind"], "attacker_species": first["attacker_species"], "attacker_group": first["attacker_group"], "attacker_diet": first["attacker_diet"],
                "victim_id": victim_id, "victim_species": first["victim_species"], "start_tick": start, "end_tick": end, "start_world_time": first["world_time"], "events": len(group),
                "hits": sum(1 for e in group if e["hit"]), "misses": sum(1 for e in group if not e["hit"]), "kills": sum(1 for e in group if e["hit"] and e.get("outcome_kind") == "KILL"),
                **{k: v for k, v in engagement_motive(first).items()}, "attacker_can_eat_victim": (first.get("motive_inputs") or {}).get("attacker_can_eat_victim"), "night": night, "inside_period": inside_period(first["attacker_species"], night), "outcome": outcome,
            })
    return sorted(engagements, key=lambda e: (e["start_tick"], e["attacker_id"], e["victim_id"]))


def per_attacker(engagements: List[Dict[str, Any]], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """View (b): per attacker id."""
    out: Dict[int, Dict[str, Any]] = {}
    for eng in engagements:
        entry = out.setdefault(eng["attacker_id"], {"attacker_id": eng["attacker_id"], "kind": eng["attacker_kind"], "species": eng["attacker_species"], "diet": eng["attacker_diet"], "group": eng["attacker_group"],
                                                    "engagements": 0, "hits": 0, "victims": set(), "night_engagements": 0, "day_engagements": 0})
        entry["engagements"] += 1
        entry["hits"] += eng["hits"]
        entry["victims"].add(eng["victim_id"])
        entry["night_engagements" if eng["night"] else "day_engagements"] += 1
    return [{**{k: v for k, v in e.items() if k != "victims"}, "distinct_victims": len(e["victims"])} for _, e in sorted(out.items())]


def per_pair(engagements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """View (c): per (attacker, victim) pair, with the outcome of each engagement."""
    out: Dict[Tuple[int, int], Dict[str, Any]] = {}
    for eng in engagements:
        entry = out.setdefault((eng["attacker_id"], eng["victim_id"]), {"attacker_id": eng["attacker_id"], "victim_id": eng["victim_id"], "engagements": 0, "outcomes": []})
        entry["engagements"] += 1
        entry["outcomes"].append(eng["outcome"])
    return [v for _, v in sorted(out.items())]


def hit_states(rows: List[Dict[str, Any]], mode_rows: List[Dict[str, Any]], only_o3: bool = True, attack_rows: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """View (e): per hit, the victim's state, its movement mode and whether a flight or fight decision followed (module docstring, choice 7). An attack by a watched id (``attack_rows``, any target) is a fight decision of that id."""
    decisions: Dict[int, List[int]] = defaultdict(list)
    for mode_row in mode_rows:
        if mode_row["mode"] in DECISION_MODES:
            decisions[mode_row["id"]].append(mode_row["tick"])
    for attack in attack_rows or []:
        decisions[attack["attacker_id"]].append(attack["tick"])
    out = []
    for row in rows:
        if not row["hit"] or (only_o3 and not row["in_o3_group"]):
            continue
        state = "lodged" if row["victim_lodged_before"] else ("asleep" if row["victim_asleep_before"] else "awake")
        decision = "flight" if row["victim_mode_after"] == "RETREAT" else ("fight" if (row["victim_attacked_same_tick"] or row["victim_mode_after"] == "PURSUE") else "none")
        out.append({"tick": row["tick"], "attacker_id": row["attacker_id"], "victim_id": row["victim_id"], "victim_state": state, "victim_mode_before": row["victim_mode_before"],
                    "victim_mode_after": row["victim_mode_after"], "decision": decision, "_decisions": decisions.get(row["victim_id"], []), "_row": row})
    return out


def hit_chains(rows: List[Dict[str, Any]], mode_rows: List[Dict[str, Any]], only_o3: bool = True, attack_rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """R7's two measures: the longest run of consecutive hits on one victim while it was asleep or lodged at every hit, and the longest run of consecutive hits with no decision between them.
    A chain resets when two consecutive hits on the victim are more than ENGAGEMENT_GAP ticks apart (the engagement rule), so one chain never spans separate engagements."""
    by_victim: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for hit in hit_states(rows, mode_rows, only_o3, attack_rows):
        by_victim[hit["victim_id"]].append(hit)
    worst_asleep: Dict[str, Any] = {"run": 0}
    worst_none: Dict[str, Any] = {"run": 0}
    for victim_id, hits in sorted(by_victim.items()):
        hits.sort(key=lambda h: h["tick"])
        asleep_run, none_run = 0, 0
        for i, hit in enumerate(hits):
            if i > 0 and hit["tick"] - hits[i - 1]["tick"] > ENGAGEMENT_GAP:
                asleep_run, none_run = 0, 0
            if hit["victim_state"] in ("asleep", "lodged"):
                asleep_run += 1
            else:
                asleep_run = 0
            if asleep_run > worst_asleep["run"]:
                worst_asleep = {"run": asleep_run, "start_tick": hits[i - asleep_run + 1]["tick"], "victim_id": victim_id, "attackers": sorted({h["attacker_id"] for h in hits[i - asleep_run + 1:i + 1]}), "end_tick": hit["tick"]}
            if i == 0 or none_run == 0:
                none_run = 1
            else:
                prev = hits[i - 1]
                between = (prev["decision"] != "none" or hit["victim_mode_before"] in DECISION_MODES or any(prev["tick"] <= t <= hit["tick"] for t in hit["_decisions"]))
                none_run = 1 if between else none_run + 1
            if none_run > worst_none["run"]:
                worst_none = {"run": none_run, "start_tick": hits[i - none_run + 1]["tick"], "victim_id": victim_id, "attackers": sorted({h["attacker_id"] for h in hits[i - none_run + 1:i + 1]}), "end_tick": hit["tick"]}
    return {"asleep_or_lodged_run": worst_asleep, "no_decision_run": worst_none}


def max_in_window(starts: List[int], window: int) -> int:
    """The largest number of values of ``starts`` inside any rolling span of ``window`` ticks (a span covers ticks t .. t+window-1)."""
    starts = sorted(starts)
    best, lo = 0, 0
    for hi, tick in enumerate(starts):
        while tick - starts[lo] >= window:
            lo += 1
        best = max(best, hi - lo + 1)
    return best


def _result(applies: bool, value_result: str, not_evaluated: str = "NOT_APPLICABLE", **detail: Any) -> Dict[str, Any]:
    """A rule's result: ``value_result`` when the rule applies, else ``not_evaluated`` with the value it would have had in ``if_applied``."""
    out = {"applies": applies, "result": value_result if applies else not_evaluated, **detail}
    if not applies:
        out["if_applied"] = value_result
    return out


def rules_for_cell(rows: List[Dict[str, Any]], mode_rows: List[Dict[str, Any]], engagements: List[Dict[str, Any]], all_rows: Optional[List[Dict[str, Any]]] = None, group: Optional[str] = None, attack_rows: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """R1-R5 and R7 for one (arm, seed) cell over ``rows`` (the group in scope); ``all_rows`` (default ``rows``) feeds R7's all-attackers information."""
    share_rules_apply = len(engagements) >= MIN_ENGAGEMENTS  # R2 and R5 are share rules: NOT EVALUATED below 10 engagements; R1, R3, R4 and R7 are judged in every seed at any count
    attackers = per_attacker(engagements, rows)
    total = len(engagements)
    out: Dict[str, Dict[str, Any]] = {}
    unclassed = [e for e in engagements if e["motive"] == "UNCLASSED"]
    no_inputs = [e for e in engagements if e["motive"] == NO_INPUTS]
    non_edible_hunt = [e for e in engagements if e["motive"] == "HUNT" and e.get("attacker_can_eat_victim") is not True]
    bad = sorted({e["attacker_id"] for e in unclassed + non_edible_hunt})
    no_inputs_share = (len(no_inputs) / total) if total else 0.0
    r1_detail = dict(rule="MOTIVE CONSISTENCY: every judged engagement has a motive (UNCLASSED fails), and a HUNT needs the attacker's declared diet to be able to eat the victim's body; a NO_INPUTS engagement is not assessable",
                     unclassed=[{"attacker_id": e["attacker_id"], "victim_id": e["victim_id"], "start_tick": e["start_tick"], "typed_inputs": e["typed_inputs"], "info": e["info"]} for e in unclassed],
                     non_edible_hunt=[{"attacker_id": e["attacker_id"], "victim_id": e["victim_id"], "start_tick": e["start_tick"], "attacker_can_eat_victim": e.get("attacker_can_eat_victim")} for e in non_edible_hunt],
                     unclassed_share=(len(unclassed) / total) if total else 0.0, no_inputs=len(no_inputs), no_inputs_share=no_inputs_share)
    if no_inputs_share >= NO_INPUTS_NOT_ASSESSABLE_SHARE:
        out["R1"] = _result(True, "NOT_CLEARED", attacker_ids=sorted({e["attacker_id"] for e in no_inputs}), note="R1 not assessable: NO_INPUTS engagements are >= 10% of the judged engagements (held)", would_fail_on_the_rest=bool(bad), **r1_detail)
    else:
        out["R1"] = _result(True, "FAIL" if bad else "PASS", attacker_ids=bad, note="a miss is a defect for testing and this seed is no evidence" if bad else "", **r1_detail)
    top = max(attackers, key=lambda a: a["engagements"], default=None)
    share = (top["engagements"] / total) if top and total else 0.0
    out["R2"] = _result(share_rules_apply, "FAIL" if share > 0.5 else "PASS", NOT_EVALUATED, max_share=share, attacker_ids=[top["attacker_id"]] if top and share > 0.5 else [], top_attacker=top["attacker_id"] if top else None)
    starts: Dict[int, List[int]] = defaultdict(list)
    day_bins: Dict[Tuple[int, int], int] = defaultdict(int)
    for eng in engagements:
        starts[eng["attacker_id"]].append(eng["start_tick"])
        day_bins[(eng["attacker_id"], eng["start_world_time"] // TICKS_PER_DAY)] += 1
    rolling = {aid: max_in_window(ticks, TICKS_PER_DAY) for aid, ticks in starts.items()}
    over = sorted(aid for aid, n in rolling.items() if n > 3)
    out["R3"] = _result(True, "FAIL" if over else "PASS", attacker_ids=over, max_rolling_2400=max(rolling.values(), default=0), max_day_bin=max(day_bins.values(), default=0))
    pair_counts = per_pair(engagements)
    over_pairs = [(p["attacker_id"], p["victim_id"], p["engagements"]) for p in pair_counts if p["engagements"] >= 5]
    out["R4"] = _result(True, "FAIL" if over_pairs else "PASS", attacker_ids=sorted({p[0] for p in over_pairs}), pairs=over_pairs)
    unknown = [e for e in engagements if e["inside_period"] is None]
    unknown_share = len(unknown) / total if total else 0.0
    unknown_info = {"unassessable_share": unknown_share, "period_unknown": len(unknown), "species": sorted({e["attacker_species"] for e in unknown})}
    if unknown_share >= NOT_ASSESSABLE_SHARE:
        out["R5"] = _result(share_rules_apply, "NOT_CLEARED", NOT_EVALUATED, attacker_ids=sorted({e["attacker_id"] for e in unknown}), note="R5 not assessable: counts as HELD", **unknown_info)
    else:
        known = [e for e in engagements if e["inside_period"] is not None]
        inside = sum(1 for e in known if e["inside_period"])
        frac = inside / len(known) if known else 1.0
        miss = frac < 0.9
        out["R5"] = _result(share_rules_apply, "FAIL" if miss else "PASS", NOT_EVALUATED, inside_fraction=frac, tag=R5_TAG if miss else "", attacker_ids=sorted({e["attacker_id"] for e in known if not e["inside_period"]}) if miss else [], **unknown_info)
    chains = hit_chains(rows, mode_rows, attack_rows=attack_rows)
    a, n = chains["asleep_or_lodged_run"], chains["no_decision_run"]
    fail = a["run"] >= 3 or n["run"] >= 5
    out["R7"] = _result(True, "FAIL" if fail else "PASS", attacker_ids=sorted(set(a.get("attackers", []) if a["run"] >= 3 else []) | set(n.get("attackers", []) if n["run"] >= 5 else [])),
                        asleep_or_lodged_run=a, no_decision_run=n, all_attackers_info=hit_chains(all_rows if all_rows is not None else rows, mode_rows, only_o3=False, attack_rows=attack_rows))
    return out


def hits_per_engagement(engagements: List[Dict[str, Any]]) -> Dict[str, Any]:
    hits = [e["hits"] for e in engagements]
    return {"engagements": len(hits), "median": statistics.median(hits) if hits else None, "max": max(hits) if hits else None}


def rule_r6(new_eng: List[Dict[str, Any]], base_eng: List[Dict[str, Any]]) -> Dict[str, Any]:
    """R6 (NEW vs BASE): in a seed with >= 10 NEW hits, NEW's hits per engagement (median and max) <= 2x BASE's, OR (BASE has no engagements AND NEW's max <= 10 hits); else a BUG CANDIDATE naming the engagements."""
    new_hits = sum(e["hits"] for e in new_eng)
    new, base = hits_per_engagement(new_eng), hits_per_engagement(base_eng)
    applies = new_hits >= MIN_HITS
    if not new_eng:
        return _result(applies, "PASS", "NOT_APPLICABLE", new=new, base=base, new_hits=new_hits, attacker_ids=[])
    if not base_eng:
        ok = new["max"] <= 10
        names = [] if ok else [e for e in new_eng if e["hits"] > 10]
    else:
        ok = new["median"] <= 2 * base["median"] and new["max"] <= 2 * base["max"]
        names = [] if ok else [e for e in new_eng if e["hits"] > 2 * base["max"] or e["hits"] > 2 * base["median"]]
    return _result(applies, "PASS" if ok else "FAIL", "NOT_APPLICABLE", new=new, base=base, new_hits=new_hits, attacker_ids=sorted({e["attacker_id"] for e in names}),
                   engagements=[{"attacker_id": e["attacker_id"], "victim_id": e["victim_id"], "start_tick": e["start_tick"], "hits": e["hits"]} for e in names])


def rows_of(rows: List[Dict[str, Any]], engagements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The rows that belong to ``engagements`` (same attacker and victim, a tick inside its span)."""
    spans: Dict[Tuple[int, int], List[Tuple[int, int]]] = defaultdict(list)
    for eng in engagements:
        spans[(eng["attacker_id"], eng["victim_id"])].append((eng["start_tick"], eng["end_tick"]))
    return [r for r in rows if any(lo <= r["tick"] <= hi for lo, hi in spans.get((r["attacker_id"], r["victim_id"]), ()))]


def motive_stats(engagements: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Per motive key (the five classes and NO_INPUTS, separate from UNCLASSED): engagements, hits, kills and ``objective_target_is_victim`` (how many of them were goal-carried, information); for HUNT also
    ``edible_kill_share`` (the share of its kills whose attacker's declared diet could eat the victim's body at the first attack) as INFORMATION. ``eaten_share`` needs a consumption signal this kit does not observe, so it is
    reported as null with its basis (the designer's HUNT eaten_share is info only)."""
    out: Dict[str, Dict[str, Any]] = {}
    for motive in MOTIVE_KEYS:
        engs = [e for e in engagements if e["motive"] == motive]
        entry: Dict[str, Any] = {"engagements": len(engs), "hits": sum(e["hits"] for e in engs), "kills": sum(e["kills"] for e in engs), "objective_target_is_victim": sum(1 for e in engs if e["typed_inputs"]["objective_target_is_victim"])}
        if motive == "HUNT":
            killing = [e for e in engs if e["kills"] > 0]
            entry["edible_kill_share"] = (sum(1 for e in killing if e.get("attacker_can_eat_victim") is True) / len(killing)) if killing else None
            entry["eaten_share"], entry["eaten_share_basis"] = None, "consumption is not observed by this kit; edible_kill_share is the nearest raw read"
        out[motive] = entry
    return out


def label_defects(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The recount rule (rpg-designer): on every stage-1 spy row ``in_o3_group == (attacker_group is a tied group) == (attacker_diet is exactly that group's classes)``; with TIED_GROUPS ("meat",) that is
    ``in_o3_group == (attacker_group == "meat") == (attacker_diet == ["meat"])``. A mismatch is a LABELLING defect: the cell is not judged (it goes to testing)."""
    tied_diets = [g.split("+") for g in TIED_GROUPS]
    return [{"tick": r["tick"], "attacker_id": r["attacker_id"], "in_o3_group": r["in_o3_group"], "attacker_group": r["attacker_group"], "attacker_diet": r["attacker_diet"]} for r in rows
            if not (bool(r["in_o3_group"]) == (r["attacker_group"] in TIED_GROUPS) == (r["attacker_diet"] in tied_diets))][:20]


def cell_validity(plain: Optional[Dict[str, Any]], spy: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The twin and wiring checks of one cell: both files present, equal final hashes, the spy's counting cross-check OK, no logged errors, PINNED runners, same ticks."""
    problems: List[str] = []
    if plain is None or spy is None:
        return {"valid": False, "problems": ["plain or spy file missing"], "twin_hashes_equal": None}
    equal = plain.get("final_hash") == spy.get("final_hash")
    if not equal:
        problems.append("twin hashes differ")
    if spy.get("wiring") != "OK":
        problems.append(f"spy wiring {spy.get('wiring')}")
    for name, doc in (("plain", plain), ("spy", spy)):
        if doc.get("logging_errors"):
            problems.append(f"{name} logged {len(doc['logging_errors'])} ERROR+ lines")
        if doc.get("runner") != "PINNED":
            problems.append(f"{name} runner {doc.get('runner')}")
    if plain.get("ticks") != spy.get("ticks"):
        problems.append("ticks differ")
    if spy.get("control") is not None:
        problems.append("spy file is a control run")
    defects = label_defects(spy.get("rows", []))
    if defects:
        problems.append(f"labelling defect on {len(defects)}+ rows: in_o3_group, attacker_group and attacker_diet disagree (not judged; for testing)")
    return {"valid": not problems, "problems": problems, "twin_hashes_equal": equal}


def load_cells(directory: Path) -> Dict[Tuple[str, str, int], Dict[str, Optional[Dict[str, Any]]]]:
    cells: Dict[Tuple[str, str, int], Dict[str, Optional[Dict[str, Any]]]] = {}
    for path in sorted(directory.glob("*__s*__*.json")):
        if path.name.endswith(".exit.json"):
            continue
        arm, world, seed_part, kind = path.stem.split("__")
        slot = cells.setdefault((arm, world, int(seed_part[1:])), {"plain": None, "spy": None})
        slot[kind] = json.loads(path.read_text(encoding="utf-8"))
    return cells


def group_cell_view(group_rows: List[Dict[str, Any]], mode_rows: List[Dict[str, Any]], final_tick: int, is_night: Callable[[int], bool], attack_rows: Optional[List[Dict[str, Any]]] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Engagements and the views (a)-(e) of one group's O3 rows in one cell."""
    eng = build_engagements(group_rows, mode_rows, final_tick, is_night)
    view = {"engagements_count": len(eng), "hits": sum(e["hits"] for e in eng), "engagements": eng, "per_attacker": per_attacker(eng, group_rows), "per_pair": per_pair(eng),
            "hit_states": [{k: v for k, v in h.items() if not k.startswith("_")} for h in hit_states(group_rows, mode_rows, attack_rows=attack_rows)], "period_unknown": sum(1 for e in eng if e["inside_period"] is None)}
    return eng, view


def summarize(cells: Dict[Tuple[str, str, int], Dict[str, Optional[Dict[str, Any]]]], is_night: Callable[[int], bool]) -> Dict[str, Any]:
    """Per tied group: R1-R7 and its verdict; per untied O3 group: the same views and rules as context with no verdict (module docstring, choices 10 and 11)."""
    out: Dict[str, Any] = {"measurement_labels": MEASUREMENT_LABELS, "tied_groups": list(TIED_GROUPS), "cells": {}, "groups": {}, "engagement_gap": ENGAGEMENT_GAP,
                           "motive": {"classes": list(MOTIVES), "no_inputs_key": NO_INPUTS, "label": "motive read by each arm's own engine", "forms_by_arm": {}, "cell_meta": {}, "note": "per motive, every group (including 'none') and every victim, both arms: engagements, hits, kills (context, no verdict); the motive x group table is by_arm", "cells": {}, "by_arm": {}}}
    engagements: Dict[Tuple[str, str, str, int], List[Dict[str, Any]]] = {}   # (group, arm, world, seed)
    group_names = set(TIED_GROUPS)
    for key, pair in sorted(cells.items()):
        arm, world, seed = key
        validity = cell_validity(pair["plain"], pair["spy"])
        label = f"{arm}/{world}/s{seed}"
        entry: Dict[str, Any] = {"validity": validity}
        out["cells"][label] = entry
        if not validity["valid"]:
            for group in TIED_GROUPS:
                g = out["groups"].setdefault(group, {"tied": True, "cells": {}, "rules": {name: {} for name in RULE_NAMES}})
                for name in ("R1", "R2", "R3", "R4", "R5", "R7"):
                    g["rules"][name].setdefault(world, {}).setdefault(arm, {})[f"s{seed}"] = {"applies": False, "result": "NOT_ASSESSABLE", "problems": validity["problems"]}
            continue
        spy = pair["spy"]
        entry.update({"motive_call_form": spy.get("motive_call_form"), "ticks": spy["ticks"], "final_hash": spy["final_hash"], "o3_count": spy["o3_total_spy"], "o3_count_ledger": spy["o3_total_ledger"], "o3_by_group": spy["o3_by_group_spy"],
                      "declared_o3_groups": spy.get("declared_o3_groups"), "undeclared_o3_groups": spy.get("undeclared_o3_groups")})
        cell_motive = out["motive"]["cells"].setdefault(label, {})
        motive_rows = [r for r in spy["rows"] if r.get("motive_inputs")]
        out["motive"]["forms_by_arm"].setdefault(arm, set()).add(spy.get("motive_relation_form"))
        out["motive"]["cell_meta"][label] = {"relation_form": spy.get("motive_relation_form"), "call_form": spy.get("motive_call_form"), "rows": len(spy["rows"]), "rows_with_motive_inputs": len(motive_rows),
                                             "source_default_share": (sum(1 for r in motive_rows if r["motive_inputs"].get("relation_source_default")) / len(motive_rows)) if motive_rows else None}
        for any_group in sorted({r["attacker_group"] for r in spy["rows"]}):          # EVERY group (including 'none'), every victim: context, never a verdict
            all_eng = build_engagements([r for r in spy["rows"] if r["attacker_group"] == any_group], spy["mode_rows"], spy["final_tick"], is_night, only_o3=False)
            stats = motive_stats(all_eng)
            cell_motive[any_group] = {"motives": stats, "engagements": len(all_eng), "unclassed_share": (stats["UNCLASSED"]["engagements"] / len(all_eng)) if all_eng else 0.0, "no_inputs_share": (stats[NO_INPUTS]["engagements"] / len(all_eng)) if all_eng else 0.0}
            arm_total = out["motive"]["by_arm"].setdefault(arm, {}).setdefault(any_group, {m: {"engagements": 0, "hits": 0, "kills": 0, "objective_target_is_victim": 0} for m in MOTIVE_KEYS})
            for m in MOTIVE_KEYS:
                for k in ("engagements", "hits", "kills", "objective_target_is_victim"):
                    arm_total[m][k] += stats[m][k]
        present = {r["attacker_group"] for r in spy["rows"] if r["in_o3_group"]}
        group_names |= present
        for group in sorted(set(TIED_GROUPS) | present):
            tied = group in TIED_GROUPS
            group_rows = [r for r in spy["rows"] if r["attacker_group"] == group and r["in_o3_group"]]
            eng, view = group_cell_view(group_rows, spy["mode_rows"], spy["final_tick"], is_night, spy.get("attack_rows"))
            engagements[(group, arm, world, seed)] = eng
            g = out["groups"].setdefault(group, {"tied": tied, "cells": {}, "rules": {name: {} for name in RULE_NAMES}} if tied else {"tied": False, "cells": {}})
            rules = rules_for_cell(group_rows, spy["mode_rows"], eng, spy["rows"], group, spy.get("attack_rows"))
            if tied:
                g["cells"][label] = view
                for name, value in rules.items():
                    g["rules"][name].setdefault(world, {}).setdefault(arm, {})[f"s{seed}"] = value
                for motive in MOTIVE_KEYS:                   # every rule result split by motive
                    engs_m = [e for e in eng if e["motive"] == motive]
                    if engs_m:
                        for name, value in rules_for_cell(rows_of(group_rows, engs_m), spy["mode_rows"], engs_m, spy["rows"], group, spy.get("attack_rows")).items():
                            g.setdefault("rules_by_motive", {}).setdefault(motive, {}).setdefault(name, {}).setdefault(world, {}).setdefault(arm, {})[f"s{seed}"] = value
            else:
                g["cells"][label] = {**view, "verdict": None, "label": "context, no verdict", "rules_as_context": rules}
    for group in TIED_GROUPS:
        g = out["groups"].setdefault(group, {"tied": True, "cells": {}, "rules": {name: {} for name in RULE_NAMES}})
        for (grp, arm, world, seed), eng in sorted(engagements.items()):
            if grp != group or arm != "new":
                continue
            base = engagements.get((group, "base", world, seed))
            g["rules"]["R6"].setdefault(world, {}).setdefault("new_vs_base", {})[f"s{seed}"] = rule_r6(eng, base) if base is not None else {"applies": False, "result": "NOT_ASSESSABLE", "problems": ["no valid BASE cell"]}
        for (grp, arm, world, seed), eng in sorted(engagements.items()):                     # R6 split by motive (NEW vs BASE, same motive)
            base = engagements.get((group, "base", world, seed))
            if grp != group or arm != "new" or base is None:
                continue
            for motive in MOTIVE_KEYS:
                new_m, base_m = [e for e in eng if e["motive"] == motive], [e for e in base if e["motive"] == motive]
                if new_m:
                    g.setdefault("rules_by_motive", {}).setdefault(motive, {}).setdefault("R6", {}).setdefault(world, {}).setdefault("new_vs_base", {})[f"s{seed}"] = rule_r6(new_m, base_m)
        g["verdict_detail"] = verdict_detail(g["rules"], g["cells"], group)
    out["motive"]["forms_by_arm"] = {arm: sorted(forms, key=str) for arm, forms in out["motive"]["forms_by_arm"].items()}
    out["verdict_detail"] = combine_verdicts([out["groups"][grp]["verdict_detail"] for grp in TIED_GROUPS])
    out["verdict"] = out["verdict_detail"]["headline"]
    return out


def verdict_detail(rules: Dict[str, Any], group_cells: Dict[str, Any], group: str) -> Dict[str, Any]:
    """The verdict of ONE tied group on NEW (module docstring, choices 8-10): misses (attributed when NEW only, pre-existing when BASE misses the same rule in the same seed), HELD items, the run line and the headline."""
    misses: List[Dict[str, Any]] = []
    held: List[Dict[str, Any]] = []
    evaluated = [f"{label.split('/')[1]}/{label.split('/')[2]}" for label, view in sorted(group_cells.items()) if label.startswith("new/") and view.get("engagements_count", 0) >= MIN_ENGAGEMENTS]
    for name in RULE_NAMES:
        for world, per_arm in sorted(rules[name].items()):
            side = per_arm.get("new_vs_base" if name == "R6" else "new", {})
            for seed, res in sorted(side.items()):
                where = {"group": group, "rule": name, "world": world, "seed": seed}
                if res["result"] == "FAIL" and res.get("applies"):
                    base = per_arm.get("base", {}).get(seed)
                    pre_existing = name != "R6" and bool(base and base.get("applies") and base["result"] == "FAIL")
                    misses.append({**where, "attribution": "pre-existing (not attributed to #953/#954)" if pre_existing else "attributed", "attacker_ids": res.get("attacker_ids", []), "tag": res.get("tag", ""),
                                   "base_attacker_ids": base.get("attacker_ids", []) if pre_existing else []})
                elif res["result"] in ("NOT_CLEARED", "NOT_ASSESSABLE") and (res.get("applies") or res["result"] == "NOT_ASSESSABLE"):
                    held.append({**where, "result": res["result"], "attacker_ids": res.get("attacker_ids", []), "species": res.get("species", []), "problems": res.get("problems", [])})
    if any(m["attribution"] == "attributed" for m in misses):
        headline = "BUG CANDIDATE, attributed"
    elif misses:
        headline = "BUG CANDIDATE, pre-existing (not attributed to #953/#954)"
    elif held:
        headline = "HELD"
    else:
        headline = "CLEARED"
    run_line = "R2/R5 evaluated in: " + ", ".join(evaluated) if evaluated else "R2/R5 NOT EVALUATED (n<10): no NEW seed reaches 10 engagements; R1, R3, R4, R6 and R7 decide"
    return {"group": group, "headline": headline, "run_line": run_line, "misses": misses, "held": held, "evaluated_seeds": evaluated}


def combine_verdicts(details: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The overall verdict over the tied groups: attributed miss > pre-existing miss > HELD > CLEARED; every group's own line is kept."""
    misses = [m for d in details for m in d["misses"]]
    held = [h for d in details for h in d["held"]]
    if any(m["attribution"] == "attributed" for m in misses):
        headline = "BUG CANDIDATE, attributed"
    elif misses:
        headline = "BUG CANDIDATE, pre-existing (not attributed to #953/#954)"
    elif held:
        headline = "HELD"
    else:
        headline = "CLEARED"
    return {"headline": headline, "run_line": "; ".join(f"{d['group']}: {d['run_line']}" for d in details), "misses": misses, "held": held,
            "evaluated_seeds": [f"{d['group']}:{seed}" for d in details for seed in d["evaluated_seeds"]], "by_group": {d["group"]: d["headline"] for d in details}}


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, type=Path)
    ap.add_argument("--calendar-tree", required=True, type=Path, help="the NEW tree: its src/core/calendar.py supplies is_night for BOTH arms")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    is_night, calendar_sha = load_is_night(args.calendar_tree / "src" / "core" / "calendar.py")
    doc = summarize(load_cells(args.dir), is_night)
    doc["calendar_sha256"] = calendar_sha
    doc["periods_table"] = PERIODS
    doc["periods_source"], doc["periods_quote"], doc["missing_law_quote"] = PERIODS_SOURCE, PERIODS_QUOTE, MISSING_LAW_QUOTE
    args.out.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str), encoding="utf-8")
    print(json.dumps({"cells": {k: v["validity"]["valid"] for k, v in doc["cells"].items()}, "verdict": doc["verdict"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
