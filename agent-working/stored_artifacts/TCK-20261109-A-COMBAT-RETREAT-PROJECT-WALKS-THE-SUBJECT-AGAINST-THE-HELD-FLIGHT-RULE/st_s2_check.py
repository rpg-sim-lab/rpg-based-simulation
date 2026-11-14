"""Read-only anomaly check of one spied cell JSON. Prints STOP:<reasons> or OK. Never edits anything."""
import json, sys
d = json.load(open(sys.argv[1])); r = []
ex = d["exceptions"]
if ex["mt"] or ex["rm"] or ex["ex"]: r.append(f"exceptions mt={ex['mt']} rm={ex['rm']} ex={ex['ex']} {ex['first5']}")
if d.get("match") is False: r.append("hash MISMATCH")
if d.get("decision_hook_missed"): r.append("decision hook missed")
g = d["gate_holds"]
if g["freeze_stop_ge50_no_hit"]: r.append(f"FREEZE stop no-hit {g['freeze_stop_ge50_no_hit']}")
if g["freeze_stop_held_at_last_tick"]: r.append(f"FREEZE stop held at last tick {g['freeze_stop_held_at_last_tick']}")
deaths = d["death"]
for p in d["s1_pins"]["runs_ge_50"]:
    why = []
    if p["ticks"] >= 500: why.append("500+")
    if p["last_tick"] >= 4999: why.append("held at last tick")
    dt = deaths.get(str(p["entity"]))
    if dt and dt[0] is not None and p["first_tick"] <= dt[0] <= p["last_tick"] + 1: why.append("death in window")
    if why: r.append(f"S1 pin stop {why} {p}")
print("STOP:" + " | ".join(r) if r else "OK")
