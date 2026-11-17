"""Rows builder for the flight-weighs-the-free-swing Tier 2 trace (rpg-implementer; DRAFT for rpg-designer approval; NOT run). Reads only files, no sim, writes no verdict and no class.
usage: flight_rows.py <base_trace.json> <fix_trace.json> <base_cell.json> <fix_cell.json> [--extra-id N ...]
  base_trace / fix_trace : defeat_trace2.py outputs (rows, decisions, calls, deaths); both must have match == true or the script exits 3 and prints nothing.
  base_cell / fix_cell   : the arm_child cell JSONs of the same world and seed (fix_cell carries flight_counts.fire_list = [tick, subject, site, response]; `final` = {id: [alive, cause, role]}).
Row index: rows[t][id] = [hp, max_hp, alive, work_kind, action, reason, target_id, last_hit_tick, last_attacker_id, lodged, pos] read at the START of tick t. A guard fire in fire_list is stamped with the tick it was decided on.

1. SUBJECTS: ids whose fix-arm death cause is COMBAT and whose base-arm cause is not COMBAT (a base-alive id is included). Per subject:
   t_d = fix death tick; t_f = tick of the last fire_list entry on the subject with tick <= t_d (site, response), else none. When t_f exists:
   fix_hp / base_hp at the start of t_f; fix_last_attacker (the felt attacker the guard saw) and fix_last_hit_tick; felt_blow = the distinct damage_taken values of the fix-arm calls on the subject at fix_last_hit_tick (shown, not summed);
   base decision on t_f (work_kind, action, reason, target); base last_attacker_id at t_f; base alive at the start of t_f+1; both arms' fates (cause, tick).
   Also printed: fix_alive_start_t_f / base_alive_start_t_f, and guard_side_felt_blow (from the fix cell's flight_counts.rows, which keeps at most 2 rows per site) next to the calls-log felt blow when the same (subject, tick) is there.
   Sort key: id, shown as one JSON object per subject.
2. EXTRA IDS (--extra-id): the id's decision on the tick d (its fix death tick, else its base death tick, flagged) and the distinct calls on d, in BOTH arms.
3. ALIVE BY ROLE and the blacksmith's fate, both arms, from the two cell files' `final`.
4. ADDITION 2: up to 3 fix-arm deaths with an opp=True call on the death tick (the call's own `lethal` flag is NOT tested: the free swing is made with is_lethal=False) where the subject has no decision on that tick and the task at the start of that tick is ENTITY_ACT.
   Printed: id, tick, hp (start of tick), death cause, the opp calls' lethal values, swing (distinct damage_taken of the opp calls that tick), attackers, task (work_kind, action, reason). The count of all such deaths is printed as `n_candidates`.
"""
import json
import sys
from collections import Counter


def load(path):
    return json.load(open(path, encoding="utf-8"))


def distinct_calls(trace, ident, tick):
    out, seen = [], set()
    for c in trace["calls"]:
        if str(c.get("defender")) == ident and c.get("tick") == tick:
            key = (tuple(c["attackers"]), c["fn"], c.get("res_damage_taken"), c.get("res_hp_delta"), c["opp"])
            if key in seen:
                continue
            seen.add(key)
            out.append({"fn": c["fn"], "attackers": c["attackers"], "opp": c["opp"], "lethal": c.get("lethal"), "damage_taken": c.get("res_damage_taken"), "outcome": c.get("res_outcome_kind")})
    return out


def fate(trace, ident):
    d = trace["deaths"].get(ident)
    if d is None:
        return None
    return "alive" if d["alive"] else f"{d['cause']} t{d['tick']}"


def row_at(trace, ident, tick):
    return trace["rows"].get(str(tick), {}).get(ident)


def decision(trace, ident, tick):
    return trace["decisions"].get(f"{ident}|{tick}")


def main(args):
    extra = []
    if "--extra-id" in args:
        at = args.index("--extra-id")
        extra = [str(x) for x in args[at + 1:]]
        args = args[:at]
    bt, ft, bc, fc = (load(a) for a in args[:4])
    if not (bt.get("match") and ft.get("match")):
        print("TRACE_MISMATCH: a trace does not match its cell; no rows")
        return 3
    fires = [f for f in fc["flight_counts"]["fire_list"]]  # [tick, subject, site, response]
    subjects = sorted({i for i, d in ft["deaths"].items() if d["cause"] == "COMBAT" and bt["deaths"].get(i, {}).get("cause") != "COMBAT"}, key=int)
    out = {"world": fc["world"], "seed": fc["seed"], "subjects": []}
    for i in subjects:
        t_d = ft["deaths"][i]["tick"]
        mine = [f for f in fires if str(f[1]) == i and f[0] <= t_d]
        row = {"id": i, "kind": ft["deaths"][i]["kind"], "t_d": t_d, "base_fate": fate(bt, i), "fix_fate": fate(ft, i)}
        if not mine:
            row["t_f"] = "none"
        else:
            t_f, _, site, response = max(mine, key=lambda f: f[0])
            fr, br = row_at(ft, i, t_f), row_at(bt, i, t_f)
            bn = row_at(bt, i, t_f + 1)
            lht = fr[7] if fr else None
            blows = sorted({c["damage_taken"] for c in distinct_calls(ft, i, lht)}) if lht is not None else None
            row.update({
                "t_f": t_f, "site": site, "response": response,
                "fix_hp_start_t_f": None if fr is None else fr[0], "base_hp_start_t_f": None if br is None else br[0],
                "fix_alive_start_t_f": None if fr is None else fr[2], "base_alive_start_t_f": None if br is None else br[2],
                "guard_side_felt_blow": [r["felt_blow"] for rows in fc["flight_counts"]["rows"].values() for r in rows if str(r["subject"]) == i and r["tick"] == t_f] or None,
                "fix_last_attacker": None if fr is None else fr[8], "fix_last_hit_tick": lht, "felt_blow_distinct_calls": blows,
                "base_decision_t_f": None if decision(bt, i, t_f) is None else dict(zip(("work_kind", "action", "reason", "target"), decision(bt, i, t_f))),
                "base_last_attacker_t_f": None if br is None else br[8],
                "base_alive_start_t_f_plus_1": None if bn is None else bn[2],
            })
        out["subjects"].append(row)
    for i in extra:
        fd, bd = ft["deaths"].get(i), bt["deaths"].get(i)
        d = fd["tick"] if fd and not fd["alive"] else (bd["tick"] if bd and not bd["alive"] else None)
        item = {"id": i, "tick": d, "tick_is_fix_death_tick": bool(fd and not fd["alive"]), "base_fate": fate(bt, i), "fix_fate": fate(ft, i)}
        for tag, tr in (("base", bt), ("fix", ft)):
            item[tag] = {"decision": decision(tr, i, d), "calls": distinct_calls(tr, i, d), "row_start": row_at(tr, i, d)}
        out.setdefault("extra", []).append(item)
    roles = {}
    for tag, cell in (("base", bc), ("fix", fc)):
        c = Counter()
        for v in cell["final"].values():
            c[(v[2], "alive" if v[0] else "dead")] += 1
        roles[tag] = {f"{r}|{s}": n for (r, s), n in sorted(c.items())}
    out["alive_by_role"] = roles
    out["blacksmith"] = {tag: {i: v for i, v in cell["final"].items() if v[2] == "blacksmith"} for tag, cell in (("base", bc), ("fix", fc))}
    cand = []
    for c in ft["calls"]:
        ident = str(c.get("defender"))
        d = ft["deaths"].get(ident)
        if not (c.get("opp") and d and not d["alive"] and d["tick"] == c.get("tick")):
            continue
        if decision(ft, ident, c["tick"]) is not None:
            continue
        now = row_at(ft, ident, c["tick"])
        if now is None or now[3] != "ENTITY_ACT":
            continue
        cand.append((c["tick"], int(ident), ident, now))
    cand = sorted({(t, n): (t, n, i, now) for t, n, i, now in cand}.values())
    shown = []
    for t, _, ident, now in cand[:3]:
        opp = [c for c in distinct_calls(ft, ident, t) if c["opp"]]
        shown.append({"id": ident, "tick": t, "hp": now[0], "swing": sorted({c["damage_taken"] for c in opp}), "attackers": sorted({a for c in opp for a in c["attackers"]}), "death_cause": ft["deaths"][ident]["cause"], "lethal_values": [c["lethal"] for c in opp],
                      "task": {"work_kind": now[3], "action": now[4], "reason": now[5]}})
    out["addition2"] = {"n_candidates": len(cand), "rows": shown}
    print(json.dumps(out, sort_keys=True, default=str, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
