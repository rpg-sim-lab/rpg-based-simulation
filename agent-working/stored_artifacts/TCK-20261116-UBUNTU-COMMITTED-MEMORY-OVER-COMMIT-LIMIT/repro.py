"""Read-only repro for TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT (steps 1 and 2).
probe <gb> <n>   : hold <gb> GB of touched private writable memory, spawn /usr/bin/python3 -c pass <n> times, log errno per failure.
suite            : run the tests/tools f-z half as one process (-n 0), sample the pytest PID once a second.
Both abort (exit 2, no retry) if MemAvailable < 1.5 GB. Logs only numbers and names; no command lines or environment."""
import errno, json, mmap, os, re, signal, subprocess, sys, threading, time
RANGE = re.compile(r"^[0-9a-f]+-[0-9a-f]+ ")

FLOOR_KB = int(1.5 * 1024 * 1024)

def meminfo():
    d = {}
    for line in open("/proc/meminfo"):
        k, v = line.split(":")[0], line.split()[1]
        if k in ("MemAvailable", "Committed_AS", "CommitLimit", "SwapFree"):
            d[k] = int(v)
    return d

def accounted_kb(pid):
    acc = cur = 0
    try:
        for line in open(f"/proc/{pid}/smaps"):
            if RANGE.match(line):
                cur = 0
            elif line.startswith("Size:"):
                cur = int(line.split()[1])
            elif line.startswith("VmFlags:") and "ac" in line.split()[1:]:
                acc += cur
    except OSError:
        pass
    return acc

def proc(pid):
    out = {}
    try:
        for line in open(f"/proc/{pid}/status"):
            if line.startswith(("VmRSS", "VmData")):
                out[line.split(":")[0]] = int(line.split()[1])
    except OSError:
        pass
    return out

def sampler(pid, log, stop, abort):
    while not stop.is_set():
        m = meminfo()
        row = {"t": round(time.time() - T0, 1), **m, **proc(pid), "ac_kb": accounted_kb(pid)}
        log.write(json.dumps(row) + "\n"); log.flush()
        if m["MemAvailable"] < FLOOR_KB:
            abort.set(); stop.set(); return
        stop.wait(1.0)

T0 = time.time()

def probe(gb, n):
    size = int(gb * 1024 ** 3)
    buf = mmap.mmap(-1, size, flags=mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS)
    for off in range(0, size, 4096):
        buf[off] = 1
    stop, abort = threading.Event(), threading.Event()
    log = open(sys.argv[3], "w")
    threading.Thread(target=sampler, args=(os.getpid(), log, stop, abort), daemon=True).start()
    fails = {}
    t = time.time()
    for i in range(n):
        if abort.is_set():
            print(json.dumps({"ABORT": "MemAvailable below 1.5 GB", "at_iteration": i})); os._exit(2)
        try:
            r = subprocess.run(["/usr/bin/python3", "-c", "pass"], capture_output=True)
            if r.returncode:
                fails[f"rc{r.returncode}"] = fails.get(f"rc{r.returncode}", 0) + 1
        except OSError as e:
            k = errno.errorcode.get(e.errno, str(e.errno))
            fails[k] = fails.get(k, 0) + 1
    stop.set()
    print(json.dumps({"mode": "probe", "parent_gb": gb, "spawns": n, "failures_by_errno": fails, "seconds": round(time.time() - t, 1), "after": meminfo()}))

def suite():
    cmd = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=3G", "-p", "MemorySwapMax=0", "taskset", "-c", "4-5",
           "/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python", "-m", "pytest", "-n", "0", "-q", "--tb=line", "-rfE",
           "-p", "no:cacheprovider", "-m", "not slow and not extra_slow"] + sorted(
        "tests/tools/" + f for f in os.listdir("tests/tools") if f.startswith("test_") and f[5] in "fghijklmnopqrstuvwxyz" and f.endswith(".py"))
    out = open(sys.argv[2], "w")
    p = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
    stop, abort = threading.Event(), threading.Event()
    log = open(sys.argv[3], "w")
    th = threading.Thread(target=sampler, args=(p.pid, log, stop, abort), daemon=True); th.start()
    while p.poll() is None:
        if abort.is_set():
            os.killpg(p.pid, signal.SIGTERM); print(json.dumps({"ABORT": "MemAvailable below 1.5 GB"})); os._exit(2)
        time.sleep(0.5)
    stop.set()
    print(json.dumps({"mode": "suite", "rc": p.returncode, "seconds": round(time.time() - T0, 1)}))

if __name__ == "__main__":
    if sys.argv[1] == "probe":
        probe(float(sys.argv[2]), 200)      # argv: probe <gb> <logfile>
    else:
        suite()                              # argv: suite <outfile> <logfile>
