"""Mechanical proof that the mypy and pyrefly baseline re-keys changed only path, line and column: the before/after multisets of (message, code) are EQUAL.
Run from the repo root: python3 rekey_multiset_proof.py <before-ref> <after-ref>"""
import collections, json, re, subprocess, sys
b, a = sys.argv[1], sys.argv[2]
def show(ref, path): return subprocess.check_output(["git", "show", f"{ref}:{path}"], text=True)
def mypy(ref):
    c = collections.Counter()
    for l in show(ref, "codebase/baselines/mypy_baseline.txt").splitlines():
        m = re.match(r"\S+?:\d+: error: (.*)$", l)
        if m: c[m.group(1)] += 1  # message plus the trailing [code]
    return c
def pyrefly(ref):
    return collections.Counter((e["name"], e["concise_description"], e["severity"]) for e in json.loads(show(ref, "codebase/baselines/pyrefly_baseline.json"))["errors"])
for name, fn in (("mypy", mypy), ("pyrefly", pyrefly)):
    x, y = fn(b), fn(a)
    print(f"{name}: before {sum(x.values())} rows, after {sum(y.values())} rows, multisets equal: {x == y}")
    if x != y: print("  DIFF", (x - y) + (y - x))
