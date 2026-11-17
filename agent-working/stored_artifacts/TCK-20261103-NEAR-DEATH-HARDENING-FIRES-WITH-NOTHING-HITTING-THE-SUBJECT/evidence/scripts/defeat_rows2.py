"""Post-hoc table builder (rpg-implementer-3, DRAFT; reads two defeat_trace2.py output files only, no sim). usage: defeat_rows2.py <base.json> <fix.json> [extra_subject_id ...]
Subjects = people who die by DEFEAT in the fix arm and do not die by DEFEAT in the base arm, plus the extra ids given. t = the subject's fix-arm death tick (or, for an extra subject alive in fix, the base death tick, flagged).
For each subject, in BOTH arms, at t: hp at the start of t and max_hp (rows[t]); grants received before t (tick < t) by source and amount; the fatal swing (hp at start of t minus hp at start of t+1, from rows,
plus the distinct call damages at t from the call log after dropping same-tick identical duplicates, shown not summed); the decision on t (work_kind, action, reason, target); the subject's fate in the other arm.
Flag: base arm at t is not comparable when the subject is not alive at the start of t in that arm, or not in an engagement (no hit in last 10 ticks and no ATTACK/flee action)."""
import json, sys
def load(p): return json.load(open(p))
def main(a):
    B, F = load(a[0]), load(a[1]); extra = [str(x) for x in a[2:]]
    subj = sorted({i for i, d in F["deaths"].items() if d["cause"] == "DEFEAT" and B["deaths"].get(i, {}).get("cause") != "DEFEAT"} | set(extra), key=int)
    def src(g):
        d = g["hp_delta"]
        if d < 0: return "hit" if (g["damage_taken"] > 0 or g["attacker_id"] is not None) else ("hazard" if g["hazard_damage"] > 0 else "neg-other")
        if d == 0: return "zero"
        if d == 1 and g["town_tile"]: return "town_heal"
        return "other_heal"
    out = []
    for i in subj:
        fd = F["deaths"].get(i); bd = B["deaths"].get(i)
        t = fd["tick"] if (fd and fd["tick"] is not None and not fd["alive"]) else (bd["tick"] if bd and bd["tick"] is not None else None)
        row = {"id": i, "kind": (fd or bd or {}).get("kind"), "t": t, "t_is_fix_death_tick": bool(fd and not fd["alive"])}
        for tag, R in (("base", B), ("fix", F)):
            r = R["rows"]; dd = R["deaths"].get(i)
            now = r.get(str(t), {}).get(i); nxt = r.get(str(t + 1), {}).get(i) if t is not None else None
            gs = [g for g in R["grants"] if str(g.get("e")) == i and t is not None and g["tick"] < t]
            by = {}
            for g in gs:
                nx = r.get(str(g["tick"] + 1), {}).get(i)
                by.setdefault(src(g), []).append({"tick": g["tick"], "hp_before": g["hp"], "max_hp_before": g["max_hp"], "amount_constant": 5, "perm_out": g.get("perm_out"), "max_hp_delta_out": g.get("max_hp_delta_out"),
                                                  "observed_max_hp_change_next_tick": None if nx is None else nx[1] - g["max_hp"]})
            cl = []; seen = set()
            for c in R["calls"]:
                if str(c.get("defender")) == i and c.get("tick") == t:
                    k = (tuple(c["attackers"]), c["fn"], c.get("res_damage_taken"), c.get("res_hp_delta"))
                    if k in seen: continue
                    seen.add(k); cl.append({"fn": c["fn"], "attackers": c["attackers"], "opp": c["opp"], "damage_taken": c.get("res_damage_taken"), "outcome": c.get("res_outcome_kind")})
            lht = now[7] if now else None
            row[tag] = {"alive_at_start_of_t": None if now is None else now[2], "hp_start_t": None if now is None else now[0], "max_hp_start_t": None if now is None else now[1],
                        "hp_start_t_plus_1": None if nxt is None else nxt[0], "fatal_swing_hp_drop": None if (now is None or nxt is None) else now[0] - nxt[0], "calls_at_t_distinct": cl,
                        "grants_before_t_by_source": {k: {"n": len(v), "amount_constant": 5 * len(v), "observed_sum_next_tick": sum(x["observed_max_hp_change_next_tick"] or 0 for x in v), "rows": v} for k, v in by.items()}, "grants_before_t_total": len(gs),
                        "decision_on_t": R["decisions"].get(f"{i}|{t}"), "task_start_t": None if now is None else {"work_kind": now[3], "action": now[4], "reason": now[5], "target": now[6]},
                        "hit_in_last_10": bool(lht is not None and t - 10 <= lht < t), "fate": None if dd is None else ("alive" if dd["alive"] else f"{dd['cause']} t{dd['tick']}")}
            row[tag]["comparable"] = bool(now and now[2] and (row[tag]["hit_in_last_10"] or now[4] in ("ATTACK", "FLEE") or now[5] == "PANIC_RETREAT"))
        row["other_arm_fate"] = {"base": row["base"]["fate"], "fix": row["fix"]["fate"]}
        out.append(row)
    print(json.dumps({"subjects": subj, "rows": out}, sort_keys=True, default=str))
if __name__ == "__main__": main(sys.argv[1:])
