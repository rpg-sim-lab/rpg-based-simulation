"""World-end report for C: death bar (world_check.py), lodger row (lodger_check.py), and the per-world summary Usage: worldF.py <world> <dir>. Exit 7 tier-1, 9 lodger STOP, 10 hard law not {}."""
import json, sys, subprocess, collections
W, D = sys.argv[1], sys.argv[2]; PY = sys.executable; T = "/data/vboxuser/Work/groups_base"
rc = 0
r1 = subprocess.run([PY, f"{T}/world_check.py", W, D], capture_output=True, text=True); print(r1.stdout.strip())
if r1.returncode == 7: rc = 7
r2 = subprocess.run([PY, f"{T}/lodger_check.py", W, D], capture_output=True, text=True); print(r2.stdout.strip())
if r2.returncode == 9 and rc == 0: rc = 9
for lab in ("base", "branch"):
    tot = collections.Counter(); forms = 0; dis = 0; reform = 0; hl = collections.Counter(); ful = 0; late = 0; ow = 0
    for s in (42, 43, 44, 45, 46):
        try: d = json.load(open(f"{D}/{W}_s{s}_{lab}.json"))
        except FileNotFoundError: continue
        tot.update(x[2] for x in d["deaths"]); forms += len(d["forms"]); dis += len(d["dis"]); hl.update(d.get("hard_law", {}))
        ful += sum(1 for x in d["dis"] if x[4] == "BINDING_CONTRACT_NOT_ACTIVE" and x[5] == "FULFILLED")
        late += sum(1 for x in d["dis"] if x[4] == "BINDING_CONTRACT_NOT_ACTIVE" and x[5] == "FULFILLED" and len(x) > 8 and x[8] is not None and x[0] > x[8])
        key = collections.Counter(tuple(f[2]) for f in d["forms"]); reform += sum(1 for k, v in key.items() if v > 1)
        ow += len(d["forms"]) - len({f[1] for f in d["forms"]})  # a group id handed out twice in a run
    print(f"  SUMMARY {W} {lab}: deaths {dict(tot)} formations {forms} dissolutions {dis} same-member-set re-forms {reform} duplicate group ids {ow} FULFILLED ends {ful} (lag>0: {late}) hard_law {dict(hl)}")
    if lab == "branch" and hl and rc == 0: rc = 10
sys.exit(rc)
