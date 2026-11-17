"""Wrapper for `stage2_check.py world` carrying ONE owner waiver (#715 6899865649). The approved checker is untouched and is run as a subprocess; its output is printed verbatim.
Waived only when WAIVE contains exactly crowded_frontier:extinction:role0:6899865649 AND world == crowded_frontier AND the checker's only TRIPPED item is '(iii) extinction role 0'
AND its extinction line shows alive 5-seed sum fix 0 base 3 with per-seed loss exactly [(46, 3, 0)]. Anything else keeps the checker's rc (21 on any other trip, in any world)."""
import os, subprocess, sys
KEY = "crowded_frontier:extinction:role0:6899865649"
def main():
    if len(sys.argv) != 3:
        print(__doc__); return 2
    outdir, w = sys.argv[1], sys.argv[2]
    p = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "stage2_check.py"), "world", outdir, w], capture_output=True, text=True)
    sys.stdout.write(p.stdout); sys.stderr.write(p.stderr)
    if p.returncode != 21: return p.returncode
    lines = p.stdout.splitlines()
    trip = [l for l in lines if l.startswith("  TRIPPED: ")]
    ext = [l for l in lines if l.startswith("  extinction role 0: ")]
    waivers = [x for x in os.environ.get("WAIVE", "").split(",") if x]
    if (w == "crowded_frontier" and KEY in waivers and len(trip) == 1 and trip[0] == "  TRIPPED: (iii) extinction role 0"
            and len(ext) == 1 and "alive 5-seed sum fix 0 base 3 STOP=True" in ext[0] and ext[0].endswith("(seed,base,fix) [(46, 3, 0)]")):
        print(f"WAIVED (owner 6899865649): {w} extinction role 0, alive 5-seed sum fix 0 base 3, per-seed loss (seed,base,fix) [(46, 3, 0)]; the only trip; disclosed per-seed loss")
        return 0
    return p.returncode
sys.exit(main())
