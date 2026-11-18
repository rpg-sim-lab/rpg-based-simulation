"""READ-ONLY stop-rule check for one dying_window_v8 cell JSON, FATAL-INPUT variant (owner row #715 6905475847). New file; dying_stop_check.py c31cc811 is unchanged beside it. It only loads the JSON and prints; it writes nothing.
Usage: python3 dying_stop_check_fatal.py <cell.json> [--expect-combat-death ID[,ID...]]
  (i)   any row with hold_open True and hold_writer None -> STOP (as c31cc811; alive rows only, a dead row carries no hold fields).
  (iii) errors > 0 or match is not True -> STOP (as c31cc811).
  (ii)  NEW. For every subject whose rows carry a death_record with cause COMBAT (the first alive:false row, tick == D):
          (a) the death_record names a killer (last_attacker_id is not None);
          (b) on the subject's LAST ALIVE row (the row before the dead row), that killer is in the engaged_hostiles list, OR in `near` with distance <= that neighbour's own combat range;
          (c) position_last_alive is present (not None) on the dead row.
        Any of (a), (b), (c) missing -> STOP. A subject named in --expect-combat-death with no COMBAT death_record in its rows -> STOP too. The fatal blow itself is not required to be a recorded
        resolve_multi_attack call (ordinary hits go through resolve_attack, which the spy does not wrap); the rule judges what the killer's position and range were on the subject's last alive row.
Every input the rule judges on is printed (killer id, engaged list, the killer's near entry with distance and range, the last alive row's tick and hp, position_last_alive, hp_last_alive).
Exit 0 = no rule tripped, 21 = at least one tripped, 2 = bad input. It reports facts and the rule outcomes only; it classes nothing else."""
import json, sys

def main(a):
    if not a or a[0].startswith("-"):
        print(__doc__); return 2
    exp = set()
    if len(a) == 3 and a[1] == "--expect-combat-death":
        exp = {x for x in a[2].split(",") if x}
    elif len(a) != 1:
        print(__doc__); return 2
    d = json.load(open(a[0]))
    trip = []
    print(f"cell {a[0]}: spy {d.get('spy')} world {d.get('world')} seed {d.get('seed')} ticks {d.get('ticks')} errors {d.get('errors')} match {d.get('match')} counts {d.get('counts')}")
    if d.get("errors") != 0 or d.get("match") is not True:
        trip.append("(iii)")
    print(f"  (iii) errors {d.get('errors')} (need 0), match {d.get('match')} (need True): {'TRIPPED' if '(iii)' in trip else 'ok'}")
    bad_i = []
    for e, rows in sorted(d["rows"].items()):
        for r in rows:
            if r.get("alive") and r.get("hold_open") and r.get("hold_writer") is None:
                bad_i.append((e, r["tick"]))
    print(f"  (i) rows with hold_open True and hold_writer None: {len(bad_i)} {bad_i[:20]}: {'TRIPPED' if bad_i else 'ok'}")
    if bad_i:
        trip.append("(i)")
    for e, rows in sorted(d["rows"].items()):
        ticks = [r["tick"] for r in rows]
        hold_rows = sum(1 for r in rows if r.get("alive") and r.get("hold_open"))
        dead = [r for r in rows if not r.get("alive")]
        dr = next((r.get("death_record") for r in dead if r.get("death_record")), None)
        dtick = dead[0]["tick"] if dead else None
        cause = dr.get("cause") if isinstance(dr, dict) else None
        atk = [(r["tick"], len(r["attacks"]), sum(1 for x in r["attacks"] if x.get("result_fields"))) for r in rows if r.get("attacks")]
        print(f"  subject e{e}: rows {len(rows)} ticks {ticks[0]}..{ticks[-1]} alive_rows {sum(1 for r in rows if r.get('alive'))} hold_open_rows {hold_rows} first_dead_row_tick {dtick} death_record {dr} attack_rows (tick, records, with_result_fields) {atk}")
        if cause == "COMBAT":
            drow = dead[0]
            alive_rows = [r for r in rows if r.get("alive")]
            last = alive_rows[-1] if alive_rows else None
            killer = dr.get("last_attacker_id") if isinstance(dr, dict) else None
            a_ok = killer is not None
            eng = (last or {}).get("engaged_hostiles") or []
            nb = next((x for x in ((last or {}).get("near") or []) if killer is not None and x.get("id") == killer), None)
            in_eng = killer in eng if killer is not None else False
            in_near = bool(nb) and nb.get("distance") is not None and nb.get("range") is not None and nb["distance"] <= nb["range"]
            b_ok = last is not None and (in_eng or in_near)
            c_ok = drow.get("position_last_alive") is not None
            print(f"    (ii) COMBAT death at t{dtick}: killer {killer}; last alive row t{(last or {}).get('tick')} hp {(last or {}).get('hp')} pos {(last or {}).get('position')}; engaged {eng}; killer near entry {({k: nb.get(k) for k in ('id', 'distance', 'range', 'position', 'task_label', 'task_payload', 'movement_mode')} if nb else None)}; position_last_alive {drow.get('position_last_alive')} hp_last_alive {drow.get('hp_last_alive')}")
            print(f"      (a) names a killer: {a_ok}; (b) killer in engaged ({in_eng}) or near within its range ({in_near}): {b_ok}; (c) position_last_alive present: {c_ok}: {'ok' if (a_ok and b_ok and c_ok) else 'TRIPPED'}")
            if not (a_ok and b_ok and c_ok):
                trip.append(f"(ii) e{e}")
        elif e in exp:
            print(f"    (ii) e{e} expected a COMBAT death_record inside the window but death_record cause is {cause!r}: TRIPPED")
            trip.append(f"(ii) e{e} no COMBAT death_record")
    print("  TRIPPED: " + ("; ".join(trip) if trip else "none"))
    return 21 if trip else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
