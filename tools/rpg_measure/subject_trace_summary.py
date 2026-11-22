"""The side-by-side evidence tables of the #992 wolf-starvation read. EVIDENCE ONLY: nothing here says which reading (exposed or regression) holds, and the rendered text has no verdict line.

Input: the spy cells of ``subject_trace_spy`` (``<arm>__<world>__s<seed>__spy.json``, NEW and BASE) and the plan. For every subject of the plan, per arm:
  attempts       the subject's legality calls per target, with the reason counts (legal / illegal and each ReasonCode name)
  friendly_fire  FRIENDLY_FIRE_ILLEGAL rows of NEW whose (attacker, target, tick) has no FRIENDLY_FIRE_ILLEGAL row on BASE, with what BASE holds at that key (a different reason, or no call at all because the two runs diverged)
  curves         hunger and hp every ``SAMPLE`` ticks (and the first and last tick of the window), the lowest hp, the highest hunger
  hits_taken     per source: count and summed damage (the typed hit record), and the first and last tick
  ways / steps   the open ways and the open food steps as RUNS of identical readings (from, to, values)
  carcasses      the carcasses in reach as runs (id, edible, in way range)
  last_hunt      the last tick the subject hunted (the hunt step's own candidate equals the target of its task or objective), that target, and the evidence of why the hunt ended: prey dead, a refusal at the legality check, the prey
                 striking back, prey out of the hunt radius, else unknown. ``end`` is the first of those that holds in that order; every flag is listed so a reader can apply another order.
  death          the typed death record the run itself holds (cause, tick, last attacker), first seen at
Nothing is read from outside the cells and the plan.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SAMPLE = 25                     # one curve point per 25 ticks
HUNT_LOOKAROUND = 20            # ticks either side of the last hunt tick in which a refusal or a blow from the prey counts as its end
HUNT_RADIUS = 10.0              # src/ai/goals/opening_steps.py HUNT_RADIUS (Manhattan): the radius a hunt is held to
FRIENDLY_FIRE = "FRIENDLY_FIRE_ILLEGAL"
ARMS = ("new", "base")


def cell_path(cells: Path, arm: str, world: str, seed: int) -> Path:
    return cells / f"{arm}__{world}__s{seed}__spy.json"


def subject_rows(doc: Dict[str, Any], subject_id: int) -> List[Dict[str, Any]]:
    return sorted((r for r in doc.get("rows", []) if r["id"] == subject_id), key=lambda r: r["tick"])


def attempts(doc: Dict[str, Any], subject_id: int) -> Dict[str, Dict[str, Any]]:
    """Per target: {calls, legal, illegal, reasons: {name: n}}; the legality calls, not the attack counts (one ATTACK can make two calls)."""
    out: Dict[str, Dict[str, Any]] = {}
    for r in doc.get("legality_rows", []):
        if r["attacker_id"] != subject_id:
            continue
        entry = out.setdefault(str(r["target_id"]), {"calls": 0, "legal": 0, "illegal": 0, "reasons": {}})
        entry["calls"] += 1
        entry["legal" if r["legal"] else "illegal"] += 1
        entry["reasons"][r["reason"]] = entry["reasons"].get(r["reason"], 0) + 1
    return out


def curves(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    points = [(r["tick"], r["after"].get("needs", {}).get("hunger"), r["after"].get("hp")) for r in rows if r["after"].get("present")]
    sampled = [list(p) for i, p in enumerate(points) if i == 0 or i == len(points) - 1 or p[0] % SAMPLE == 0]
    hungers = [p[1] for p in points if p[1] is not None]
    hps = [p[2] for p in points if p[2] is not None]
    return {"every": SAMPLE, "points": sampled, "hp_min": min(hps) if hps else None, "hunger_max": max(hungers) if hungers else None}


def hits_by_source(doc: Dict[str, Any], subject_id: int) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for event in (doc.get("hits_taken") or {}).get(str(subject_id), []):
        attackers, damages = event.get("attackers") or [], event.get("damages") or []
        for index, source in enumerate(attackers):
            entry = out.setdefault(str(source), {"hits": 0, "damage": 0, "first_tick": event["tick"], "last_tick": event["tick"]})
            entry["hits"] += 1
            entry["damage"] += damages[index] if index < len(damages) else 0
            entry["last_tick"] = event["tick"]
    return out


def runs_of(rows: List[Dict[str, Any]], reading: Any) -> List[Dict[str, Any]]:
    """Runs of identical readings: [{from, to, value}], the reading of a row from ``reading(row)`` (None skips the row's reading as 'no read')."""
    runs: List[Dict[str, Any]] = []
    for row in rows:
        value = reading(row)
        if runs and runs[-1]["value"] == value and row["tick"] - runs[-1]["to"] <= 1:
            runs[-1]["to"] = row["tick"]
        else:
            runs.append({"from": row["tick"], "to": row["tick"], "value": value})
    return runs


def ways_reading(row: Dict[str, Any]) -> Any:
    ways = row.get("ways")
    return None if ways is None else {"ways": ways["ways"], "open_food_steps": ways["open_food_steps"]}


def carcass_reading(row: Dict[str, Any]) -> Any:
    ways = row.get("ways")
    return None if ways is None else [[c["id"], c["edible"], c["in_way_range"]] for c in ways["carcasses"]]


def hunt_target(row: Dict[str, Any]) -> Optional[int]:
    """The creature the hunt step names AND the subject's own task or objective targets, on the PRIOR state of that tick; None when it was not hunting."""
    ways = row.get("ways")
    step = ((ways or {}).get("steps") or {}).get("HUNT") or {}
    candidate = step.get("target_entity_id")
    if not step.get("available") or candidate is None:
        return None
    before = row["before"]
    targeted = {before.get("payload", {}).get("target_id"), ((before.get("strategic") or {}).get("objective") or {}).get("target_entity_id")}
    return candidate if any(t is not None and str(t) == str(candidate) for t in targeted) else None


def prey_gone(row: Dict[str, Any], target: int) -> bool:
    """True when the row's own counterpart reading of ``target`` says it is absent or dead (a target the row has no reading of is not gone)."""
    reading = row.get("counterparts", {}).get(str(target))
    return reading is not None and (not reading.get("present") or not reading.get("alive", True))


def classify_hunt_end(rows: List[Dict[str, Any]], legality: List[Dict[str, Any]], hits: List[Dict[str, Any]], subject_id: int) -> Dict[str, Any]:
    """PURE. The last hunt and the evidence of why it ended. ``end`` is the first that holds of: prey_dead, hunt_refused, prey_struck_back, out_of_range_or_fled; else unknown (also when the subject never hunted: ``no_hunt_rows``)."""
    hunts = [(r["tick"], hunt_target(r)) for r in rows if hunt_target(r) is not None]
    if not hunts:
        return {"end": "no_hunt_rows", "last_hunt_tick": None, "target": None, "flags": {}}
    last_tick, target = hunts[-1]
    window = range(last_tick - HUNT_LOOKAROUND, last_tick + HUNT_LOOKAROUND + 1)
    later = [r for r in rows if r["tick"] >= last_tick]
    dead_tick = next((r["tick"] for r in later if prey_gone(r, target)), None)
    against = [x for x in legality if x["attacker_id"] == subject_id and x["target_id"] == target and x["tick"] in window]
    refused = [x for x in against if not x["legal"]]
    struck = [e for e in hits if target in (e.get("attackers") or []) and e["tick"] in window]
    after_row = next((r for r in later[1:]), None)
    distance = (after_row or {}).get("counterparts", {}).get(str(target), {}).get("manhattan") if after_row else None
    died = next((r["tick"] for r in rows if r["after"].get("alive") is False), None)
    flags = {"prey_dead_tick": dead_tick, "legality_calls_at_target": len(against), "refused": [{"tick": x["tick"], "reason": x["reason"]} for x in refused], "last_call_at_target": (against[-1]["reason"] if against else None),
             "struck_back": [{"tick": e["tick"], "hp_delta": e.get("hp_delta")} for e in struck], "manhattan_to_prey_next_row": distance, "beyond_hunt_radius": distance is not None and distance > HUNT_RADIUS, "subject_dead_tick": died}
    if dead_tick is not None:
        end = "prey_dead"
    elif refused and not against[-1]["legal"]:
        end = "hunt_refused"
    elif struck:
        end = "prey_struck_back"
    elif flags["beyond_hunt_radius"]:
        end = "out_of_range_or_fled"
    else:
        end = "unknown"
    return {"end": end, "last_hunt_tick": last_tick, "target": target, "flags": flags}


def friendly_fire_new_only(new_doc: Dict[str, Any], base_doc: Dict[str, Any], subject_id: int) -> Dict[str, Any]:
    """The NEW FRIENDLY_FIRE_ILLEGAL rows of the subject whose (attacker, target, tick) has no FRIENDLY_FIRE_ILLEGAL row on BASE, each with what BASE holds at that very key."""
    base_at: Dict[Tuple[int, int, int], List[Dict[str, Any]]] = {}
    for r in base_doc.get("legality_rows", []):
        base_at.setdefault((r["attacker_id"], r["target_id"], r["tick"]), []).append({"legal": r["legal"], "reason": r["reason"]})
    new_rows = [r for r in new_doc.get("legality_rows", []) if r["attacker_id"] == subject_id and r["reason"] == FRIENDLY_FIRE]
    only = []
    for r in new_rows:
        held = base_at.get((r["attacker_id"], r["target_id"], r["tick"]), [])
        if not any(h["reason"] == FRIENDLY_FIRE for h in held):
            only.append({"tick": r["tick"], "target_id": r["target_id"], "base_at_key": held})
    return {"new_friendly_fire_rows": len(new_rows), "new_only": only, "new_only_count": len(only), "new_only_with_no_base_call_at_key": sum(1 for o in only if not o["base_at_key"])}


def arm_view(doc: Dict[str, Any], subject_id: int) -> Dict[str, Any]:
    rows = subject_rows(doc, subject_id)
    hits = (doc.get("hits_taken") or {}).get(str(subject_id), [])
    return {"rows": len(rows), "attempts": attempts(doc, subject_id), "curves": curves(rows), "hits_taken": hits_by_source(doc, subject_id), "ways": runs_of(rows, ways_reading), "carcasses": runs_of(rows, carcass_reading),
            "last_hunt": classify_hunt_end(rows, doc.get("legality_rows", []), hits, subject_id), "death": (doc.get("death_records") or {}).get(str(subject_id)), "final_hash": doc.get("final_hash")}


def summarize(cells: Path, plan: Dict[str, Any], world: str) -> Dict[str, Any]:
    docs: Dict[Tuple[str, int], Dict[str, Any]] = {}
    for seed in plan["seeds_with_subjects"]:
        for arm in ARMS:
            docs[(arm, seed)] = json.loads(cell_path(cells, arm, world, seed).read_text(encoding="utf-8"))
    subjects: Dict[str, Any] = {}
    for seed in plan["seeds_with_subjects"]:
        for subject in plan["subjects_by_seed"][str(seed)]:
            sid = subject["id"]
            subjects[f"s{seed}/{sid}"] = {"seed": seed, "id": sid, "windows": subject["windows"], "new": arm_view(docs[("new", seed)], sid), "base": arm_view(docs[("base", seed)], sid),
                                          "friendly_fire": friendly_fire_new_only(docs[("new", seed)], docs[("base", seed)], sid)}
    return {"plan_sha256": plan["plan_sha256"], "world": world, "sample_every": SAMPLE, "hunt_lookaround": HUNT_LOOKAROUND, "hunt_radius": HUNT_RADIUS, "subjects": subjects}


def render(document: Dict[str, Any]) -> str:
    """Plain text, NEW then BASE per subject. No verdict line."""
    lines = [f"# #992 wolf-starvation read: evidence (plan {document['plan_sha256']}, world {document['world']})", "Evidence only: no line below says which reading holds.", ""]
    for key, sub in sorted(document["subjects"].items()):
        lines += [f"## {key}  windows {sub['windows']}"]
        ff = sub["friendly_fire"]
        lines += [f"FRIENDLY_FIRE_ILLEGAL rows on NEW: {ff['new_friendly_fire_rows']}; absent on BASE at the same (target, tick): {ff['new_only_count']} ({ff['new_only_with_no_base_call_at_key']} with no BASE legality call at that key)"]
        for item in ff["new_only"][:40]:
            lines.append(f"  t{item['tick']} target {item['target_id']} BASE at that key: {item['base_at_key'] or 'no call'}")
        for arm in ARMS:
            view = sub[arm]
            death = view["death"]
            lines += ["", f"### {arm.upper()}  rows {view['rows']}  death {('%s at t%s (first seen t%s, last attacker %s)' % (death['record']['cause'], death['record']['tick'], death['first_seen_tick'], death['record']['last_attacker_id'])) if death and death.get('record') else 'none in the run'}"]
            lines.append("attempts per target (legality calls; reasons):")
            for target, entry in sorted(view["attempts"].items(), key=lambda kv: int(kv[0])):
                lines.append(f"  target {target}: {entry['calls']} calls, {entry['legal']} legal, {entry['illegal']} illegal {entry['reasons']}")
            c = view["curves"]
            lines.append(f"hunger / hp every {c['every']} ticks (tick, hunger, hp): {c['points']}  (hp min {c['hp_min']}, hunger max {c['hunger_max']})")
            lines.append(f"hits taken by source: {view['hits_taken'] or 'none'}")
            lines.append("open ways and food steps (runs):")
            lines += [f"  t{r['from']}-{r['to']}: {r['value']}" for r in view["ways"]]
            lines.append("carcasses in reach, [id, edible, in way range] (runs):")
            lines += [f"  t{r['from']}-{r['to']}: {r['value']}" for r in view["carcasses"]]
            hunt = view["last_hunt"]
            lines.append(f"last HUNT: tick {hunt['last_hunt_tick']} target {hunt['target']}; the hunt ended: {hunt['end']}; flags {json.dumps(hunt['flags'], sort_keys=True)}")
        lines.append("")
    return "\n".join(lines) + "\n"
