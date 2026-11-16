"""READ-ONLY stop-rule check for one dying_window_v8 cell JSON (designer's rules for run 1, applied to any cell). It only loads the JSON and prints; it writes nothing.
Usage: python3 dying_stop_check.py <cell.json> [--expect-combat-death ID[,ID...]]
  (i)   any row with hold_open True and hold_writer None -> STOP.
  (ii)  for every subject whose rows carry a death_record with cause COMBAT (an alive:false row, tick == D), that dead row itself must carry >=1 attacks record with non-empty result_fields and the subject as defender (earlier hits alone do not satisfy it);
        none -> STOP. A subject named in --expect-combat-death with no COMBAT death_record in its rows -> STOP too (the fix-arm death was expected inside the window).
  (iii) errors > 0 or match is not True -> STOP.
Exit 0 = no rule tripped (every number printed), 21 = at least one tripped, 2 = bad input. It reports facts and the rule outcomes only; it classes nothing else."""
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
            fatal = [x for x in (drow.get("attacks") or []) if x.get("result_fields") and str(x.get("defender")) == str(e)]
            ok = len(fatal) > 0
            print(f"    (ii) COMBAT death at t{dtick}: attacks records ON the dead row itself with non-empty result_fields and subject e{e} as defender: {len(fatal)} (attackers {[x.get('attackers') for x in fatal]}); earlier hits alone do not count: {'ok' if ok else 'TRIPPED'}")
            if not ok:
                trip.append(f"(ii) e{e}")
        elif e in exp:
            print(f"    (ii) e{e} expected a COMBAT death_record inside the window but death_record cause is {cause!r}: TRIPPED")
            trip.append(f"(ii) e{e} no COMBAT death_record")
    print("  TRIPPED: " + ("; ".join(trip) if trip else "none"))
    return 21 if trip else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
