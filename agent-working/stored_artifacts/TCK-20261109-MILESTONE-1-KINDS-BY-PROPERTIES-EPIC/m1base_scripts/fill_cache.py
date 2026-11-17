"""Fill the paired cache with the M1-base arms of main 9c398a068, keeping each base run's event files.

Imports tools.rpg_measure.paired from the TOOL checkout (not copied) and uses its helpers; runs each child exactly as paired.run_one does (same env, PYTHONHASHSEED, cwd=tree,
PYTHONPATH=tree, absolute paths) except that keep_events_child.py replaces paired.CHILD and the child sits in a systemd scope (MemoryMax 3500M, no swap) under /usr/bin/time.
Never overwrites a result. One process at a time. STOPs (exit non-zero) on any problem. Run from the venv python, cwd = tool checkout.
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path

TOOL = Path("/mnt/data/Working/rpg-based-simulation")
BASE = Path("/mnt/data2/rpg-measure/m1base")
SHA = "9c398a068d3899e56c11a3b805d07f5c71bd8217"
WRAPPER = BASE / "keep_events_child.py"
WRAPPER_SHA = "651ffc9f70f2b69519f890668d0bbd51bd663cbcb564e07291d4dda2d360bf23"
GATE = Path("/mnt/data2/rpg-measure/lib/busy_gate.sh")
GATE_SHA = "94fe052a081312d8a95d87992b61fe8e251ba8f62af265e7ae2b1f3d85acc293"
TICKS = 5000


def stop(msg, rc=1):
    print("STOP:", msg, flush=True)
    sys.exit(rc)


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    os.chdir(TOOL)
    sys.path.insert(0, str(TOOL))
    from tools.rpg_measure import paired
    if sha256(WRAPPER) != WRAPPER_SHA:
        stop("wrapper sha differs from the approved one", 8)
    if sha256(GATE) != GATE_SHA:
        stop("busy_gate.sh sha differs from the approved one", 8)
    if Path(paired.__file__).resolve().parents[2] != TOOL.resolve():
        stop("paired is not imported from the tool checkout", 8)
    if os.environ.get("PYTHONHASHSEED") not in (None, paired.HASHSEED):
        stop("PYTHONHASHSEED set to something else")
    problem = paired.env_problem(paired.current_env())
    if problem:
        stop("environment refused: " + problem, 2)
    cache = paired.resolve_cache()
    problem = paired.cache_problem(cache)
    if problem:
        stop(f"cache {cache} unusable: {problem}", 2)
    CHILD8 = paired.child_hash()
    print("child hash8", CHILD8, flush=True)
    sha, tree = paired.prepare_tree(TOOL, SHA, cache)
    if sha != SHA:
        stop(f"resolved {sha}")
    tree = tree.resolve()
    ls = subprocess.run(["git", "-C", str(TOOL), "ls-tree", "-r", SHA], check=True, capture_output=True, text=True).stdout.splitlines()
    bad = 0
    for line in ls:
        meta, path = line.split("\t", 1)
        mode, typ, blob = meta.split()
        if typ != "blob":
            continue
        f = tree / path
        if mode == "120000":
            got = subprocess.run(["git", "hash-object", "--stdin"], input=os.readlink(f), capture_output=True, text=True).stdout.strip()
        else:
            got = subprocess.run(["git", "hash-object", str(f)], capture_output=True, text=True).stdout.strip()
        if got != blob:
            print("MISMATCH", path); bad += 1
    print(f"tree {tree}: {len(ls)} blobs checked, mismatches {bad}", flush=True)
    if bad:
        stop("arm tree differs from git ls-tree", 3)
    (BASE / "events").mkdir(parents=True, exist_ok=True)
    (BASE / "rss").mkdir(parents=True, exist_ok=True)
    order = []
    for w in paired.WORLDS:
        order += [(w, 42, False), (w, 42, True)] + [(w, s, False) for s in (43, 44, 45, 46)]
    assert len(order) == 18
    for world, seed, repeat in order:
        out = paired.result_path(cache, sha, TICKS, world, seed, repeat)
        name = f"{world}_s{seed}" + ("_repeat" if repeat else "")
        if out.exists():
            if not (BASE / "events" / name).is_dir():
                stop(f"{name}: result exists but events/{name} missing: refusing")
            print("skip (exists)", name, flush=True); continue
        if paired.child_hash() != CHILD8:
            stop(f"paired.child_hash() changed from {CHILD8} to {paired.child_hash()} (main checkout moved?)", 8)
        if (BASE / "events" / name).exists():
            stop(f"events/{name} exists but no result: refusing")
        g = subprocess.run(["bash", "-c", f". {GATE}; rpg_host_gate"], capture_output=True, text=True)
        print(g.stdout.strip(), flush=True)
        if g.returncode != 0:
            stop("host gate refused", 9)
        out = out.resolve() if out.exists() else out.parent.resolve() / out.name
        out.parent.mkdir(parents=True, exist_ok=True)
        rss = BASE / "rss" / f"{name}.kb"
        env = {**os.environ, "PYTHONHASHSEED": paired.HASHSEED, "PYTHONPATH": str(tree), "M1BASE_EVENTS_NAME": name, "M1BASE_TOOL_ROOT": str(TOOL)}
        cmd = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=3500M", "-p", "MemorySwapMax=0", "/usr/bin/time", "-f", "%M", "-o", str(rss),
               sys.executable, str(WRAPPER), world, str(seed), str(TICKS), str(out)]
        print("START", name, flush=True)
        proc = subprocess.run(cmd, cwd=tree, env=env, capture_output=True, text=True)
        print("END", name, "rc", proc.returncode, "peak_rss_kb", rss.read_text().split()[-1] if rss.exists() and rss.read_text().split() else "?", flush=True)
        if proc.returncode != 0 or not out.exists():
            stop(f"arm run failed ({name}) rc={proc.returncode}: {proc.stderr.strip()[-400:]}", 6)
        paired.write_env_json(out.parent)
        if repeat:
            a = json.loads(paired.result_path(cache, sha, TICKS, world, 42, False).read_text())
            b = json.loads(out.read_text())
            diff = [k for k in ("start_hash", "final_hash") if a[k] != b[k]]
            print("self-check", world, "final_hash", a["final_hash"], "spread", diff or 0, flush=True)
            if diff or a != b:
                stop(f"self-check spread != 0 in {world}: {diff or 'documents differ'}", 5)
    print("ALL 18 RUNS PRESENT", flush=True)


if __name__ == "__main__":
    main()
