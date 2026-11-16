---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT
artifact_type: investigation
tags: [ai, agent-monitoring]
---

# Investigation — TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT

Read-only measurement, host ubuntu, 2026-11-16 06:01Z, by agent-working-implementer. Process **names and numbers only**: no command lines, no environment, no token or credential detail was read or recorded.

## Host readings
MemTotal 10.18 GB, MemAvailable 5.43 GB, SwapTotal 8.39 GB (4.40 GB free), CommitLimit 13.48 GB, **Committed_AS 14.72 GB**, `vm.overcommit_memory=0`, `vm.overcommit_ratio=50`.

## Committed memory by process kind
From `/proc/<pid>/smaps`, summing mappings that carry the kernel's `ac` (VM_ACCOUNT) flag, which is what counts toward Committed_AS, against mapped size and RSS. Only the processes this user can read are included.

| kind (process name) | processes | mapped | accounted | RSS |
|---|---|---|---|---|
| claude | 10 | 55.9 GB | **2.5 GB** (about 250 MB each) | 3.6 GB |
| python3 | 29 | 11.0 GB | **5.1 GB** (one 1.1 GB; the rest about 75-310 MB) | 1.2 GB |
| gnome-shell | 1 | 4.5 GB | 0.5 GB | 0.08 GB |
| desktop services (a few) | about 10 | small | 0.1-0.2 GB each | small |
| total readable | 134 | 105 GB | about 11.4 GB | 5.5 GB |

About 72 of the 206 processes could not be read (`smaps` of other users' processes), so the total misses about 3.3 GB of the 14.72 GB. **The shares below hold only for what could be read.** Read that way, the ten Claude sessions are about 17 percent of the accounted commit and the python processes (MCP servers and test runs) about 45 percent. The sessions' large mappings are mostly not accounted, so their reservations are not what fills the commit space.

## Other read-only checks
- No memory limit anywhere above the session: `memory.max`, `memory.high` and `pids.max` are `max` on the session scope, `user-1000.slice` and `user.slice`; `oom` and `oom_kill` are 0 at every level.
- `memory.events` on `user-1000.slice` and `user.slice` shows `max 2340`. The cgroup2 mount has no `memory_localevents` option (it has `memory_recursiveprot`), so these events are hierarchical: they most likely count our own `MemoryMax=3G` test scopes touching their limit during the capped chunks. It is **not** evidence about the native run.
- The kernel journal for 2026-11-15 12:00-14:00 has 4 lines and none mention OOM, a killed process or an allocation failure.

## What the real failure looked like
The Test agent's pytest output in `wf_f48f4fae-569`'s transcript (a 99-test rerun, 18.9 s) shows `/usr/lib/python3.13/subprocess.py:1801: OSError: [Errno 12] Cannot allocate memory: '/usr/bin/python3'` on three tests, the exec of the system python from a test subprocess. That is a **small** run, so "one pytest process grew over 6,000 tests" does not by itself explain it.

## Hypothesis status
Unresolved. The sessions-reservation hypothesis is not supported by the readable processes. Under `overcommit_memory=0` the kernel checks each single request, not the total against CommitLimit, so Committed_AS over CommitLimit alone should not refuse a fork. The repro is what separates the remaining explanations.

## Repro design (needs lead-planner's per-run slot go; nothing here has been run)
Aim: separate the explanations for `ENOMEM` on an exec or fork while MemAvailable is several GB. Candidates: (H1) a long-running parent grows large in private writable memory and its children must be committed against it; (H2) a short host-wide squeeze that a 5 s sampler misses; (H3) something specific to the tests that spawn `/usr/bin/python3`. The small 99-test rerun that still hit ENOMEM argues against H1 alone.

Common to every run: one run at a time, nothing else heavy on the host (names of the top RSS processes recorded at start and end); `MemAvailable` at least 3.5 GB at the start; a 1 s read-only sampler logs MemAvailable, Committed_AS, and the parent PID's VmRSS and accounted (`ac`) size; the run aborts if MemAvailable falls under 1.5 GB; no host setting changes and no session stopped.

1. **Synthetic fork probe (about 5 min, at most 3 GB).** A parent holds N GB of private writable memory (N = 0.5, 1, 2, 3), then calls `subprocess.run(["/usr/bin/python3", "-c", "pass"])` 200 times. Run once outside any scope and once inside `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`. Count failures with their errno. This tests H1 in isolation from the test suite.
2. **Real suite, capped (about 20 min).** The `tests/tools` f-z half, `-n 0`, in the 3G scope, as one process with the sampler on the pytest PID. Compare its growth curve with the chunked runs that already passed.
3. **Real suite, uncapped (about 20 min, the risky one).** The same f-z half with no cap, aborted at the MemAvailable floor above. Count `ENOMEM` and the parent's size when the first one appears. If step 2 shows no ENOMEM and step 3 does, the cap matters; if neither does, the original failure came from a squeeze at that time (H2) and a host-wide sampler at 1 s decides it.

Decision rule: ENOMEM in step 1 above a parent size confirms H1 and gives the size; ENOMEM only in step 3 points at the suite; none anywhere leaves H2, and the finding is that the pipeline's cap and chunking removed the failure whatever the cause was.
