---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT
phase: done
date: 2026-11-16
tags: [ai, testing]
---

# TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT

## Title
On host ubuntu, ENOMEM appeared in the implement-ticket Test phase while MemAvailable was several GB and committed memory sat above the commit limit; the cause is open.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Filed by agent-working-planner on 2026-11-16, at lead-planner's request, under the owner's hand-finish plan (#715 6894904885). It is the finding from the capped confirmation of the native implement-ticket pass re-run `wf_f48f4fae-569`.

Evidence, host ubuntu, 2026-11-15/16:
- `wf_f48f4fae-569` ran `pytest tests/tools/ -m "not slow and not extra_slow"` in one uncapped process. It reported 57 failures and 7 errors as `OSError: Cannot allocate memory` in subprocesses, plus one pytest `MemoryError` INTERNALERROR. A 5 s watcher never saw MemAvailable below 3.71 GB.
- The same tests, run by agent-working-implementer as six chunks plus the failed node ids, used `-n 0` and `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`. They gave 6,025 passed and 2 failed, both unrelated (a registry drift before regeneration, and one flake). There was no ENOMEM or MemoryError in any log. Recorded in TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT's Test Summary.
- Readings during the runs: `vm.overcommit_memory=0`, CommitLimit 13.48 GB, Committed_AS 13.36-14.8 GB, MemTotal 9.7 GB, swap 8 GB, MemAvailable 5.0-6.2 GB.

So commit is at or over the limit for long stretches, while real free memory is several GB. Lead-planner's hypothesis is that about 20 long-lived Claude sessions (and their MCP servers) reserve virtual memory they never touch, and that this reservation fills the commit space rather than their RSS. Under overcommit mode 0, the kernel's heuristic then refuses some large allocations or forks from a big process. This is a hypothesis, not a finding.

## Scope
1. Measure where the committed memory goes, read-only: Committed_AS over time, and the top processes by committed virtual memory (for example VmSize or the sum of private writable mappings from `/proc/<pid>/status` or `smaps_rollup`) set against their RSS. Group by kind: Claude sessions, MCP servers, test runs, other.
2. Confirm or reject the hypothesis that the sessions' unused reservations cause the ENOMEM, with one controlled repro: a single large process forking under the current commit level, and the same under the 3G scope.
3. Recommend options to the owner, without applying any. For example:
   - a per-session cap;
   - fewer idle sessions;
   - a swap or overcommit change (host settings are the owner's);
   - require every heavy run to use the capped scope, which the host rule already asks for.
   Record the trade-offs.

## Out of Scope
- Changing any host setting (sysctl, swap, systemd defaults). Only the owner does that.
- Stopping or restarting any session.
- The pipeline's Test phase design: TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS.

## Acceptance Criteria
1. [x] A measured breakdown of committed memory by process kind, at one named time, with no credential or token detail.
2. [x] The hypothesis is stated as confirmed, rejected or unresolved, citing the repro.
3. [x] An options list with a recommendation, for the owner, through lead-planner.

## Related Tickets
- TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS
- TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT (capped confirmation evidence)
- TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN

## Related Docs
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
- none

## Related Code Areas
- none (host measurement)

## Assumptions / Open Questions
- u24 went down on 2026-11-15 on an uncapped parallel run (lead-planner). Whether u24 shows the same commit pattern is a useful comparison, through lead-planner-u24.
- The read-only measurement is light. The repro in item 2 is a heavy run and needs a per-run lead go.

## Implementation Notes
Hand-orchestrated under #715 6908488337 and 6894904885. Process names and numbers only: no command lines, environment or tokens were read or recorded. The full write-up is `agent-working/stored_artifacts/TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT/investigation.md`; the repro script and its outputs are beside it.

## Test Summary
No code changed. Evidence:
- **AC1, committed memory by process kind, 2026-11-16 06:01Z (readable processes only):** Committed_AS 14.72 GB against CommitLimit 13.48 GB, `vm.overcommit_memory=0`, MemAvailable 5.43 GB. The 10 `claude` processes hold 55.9 GB mapped but only 2.5 GB accounted (about 17 percent of the accounted total); the 29 `python3` processes hold 5.1 GB accounted for 1.2 GB RSS (about 45 percent); gnome-shell 0.5 GB. About 72 of 206 processes could not be read, which accounts for part of a 3.3 GB gap to Committed_AS, so these shares hold only for the processes that could be read.
- **Kernel mechanism:** in `mm/util.c` `__vm_enough_memory` at the **upstream v6.17 tag**, mode 0 refuses only a single request larger than total RAM plus swap and never compares Committed_AS with CommitLimit. The host runs **Ubuntu 6.17.0-41**, which may carry patches, so this is the upstream behaviour and not a check of the Ubuntu build.
- **Step 1, the fork probe.** The parent holds N GB of touched private writable memory, then spawns `/usr/bin/python3 -c pass` 200 times; the probe logs each exec's errno itself. MemAvailable and Committed_AS are the lowest and highest values its 1 s sampler logged during the run (CommitLimit 13.48 GB; every run started at 5.8-6.1 GB MemAvailable). **Units: every "GB" in this ticket is the `/proc/meminfo` kB value divided by 1,000,000.**

| parent | scope | spawns | failures | time | lowest MemAvailable | peak Committed_AS |
|---|---|---|---|---|---|---|
| 0.5 GB | unscoped | 200 | 0 | 4.8 s | 5.49 GB | 14.13 GB |
| 0.5 GB | scoped | 200 | 0 | 5.2 s | 5.45 GB | 14.17 GB |
| 1 GB | unscoped | 200 | 0 | 4.9 s | 4.92 GB | 14.69 GB |
| 1 GB | scoped | 200 | 0 | 4.6 s | 4.80 GB | 14.69 GB |
| 2 GB | unscoped | 200 | 0 | 4.8 s | 3.90 GB | 15.74 GB |
| 2 GB | scoped | 200 | 0 | 5.0 s | 3.93 GB | 15.74 GB |

- **Step 2, the `tests/tools` f-z half as one process,** `-n 0`, in the 3G / swap 0 scope on CPUs 4-5, started at 6.07 GB MemAvailable: 505.3 s wall (503.21 s in pytest); **4,244 passed, 15 failed, 26 skipped, 28 deselected, 1 xfailed**; no ENOMEM or MemoryError in the log; the pytest process peaked at **0.79 GB RSS and 0.81 GB accounted**; lowest MemAvailable **4.02 GB**, peak Committed_AS **15.74 GB** (498 samples). The 15 failures were defects in the TEST-PHASE ticket's workflow edit, fixed there. Step 3 (the same half uncapped) was not run: it was conditional and no go was given.
- The cgroup2 mount has no `memory_localevents`, so the `memory.events max 2340` on `user.slice` counts our own capped scopes and is not evidence about the native run. No limit exists above the session scope today; the scope in use on 2026-11-15 is unknown.

## Files Changed
- agent-working/tickets/done/TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT.md (this ticket)
- agent-working/stored_artifacts/TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT/ (investigation, plan, test plan, repro.py, outputs)

## Completion Summary
**AC2, the hypothesis: rejected.** That unused reservations by about 20 sessions fill the commit space and make large allocations or forks fail is rejected on mechanism (upstream mode 0 never compares Committed_AS with CommitLimit) and by the repro (no failure at a 2 GB parent with Committed_AS 15.7 GB over a 13.48 GB limit; none in a 4,300-test single process). The Claude sessions are about 17 percent of the accounted commit among readable processes. **The cause of the 2026-11-15 ENOMEM in the native run is unresolved,** with the candidates: (a) a real momentary exhaustion that the 5 s watcher missed; (b) a memory.max or pids.max limit on the scope the Workflow's agents ran in that day, unknown and untestable now; (c) something specific to `posix_spawn` or `vfork` in Python 3.13 under pressure (no evidence from 1,200 spawns).

**AC3, options for the owner, through lead-planner:**
1. **Keep the current rule: heavy runs capped and chunked.** Recommended. It costs nothing, and the Test phase now enforces it on the pipeline path through `tools/delivery/capped_pytest.py` (TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS). Trade-off: a hand-run raw `pytest tests/tools/` is still uncapped, and the original cause stays unknown.
2. **A per-session memory cap on Claude sessions.** Trade-off: the sessions hold only about 17 percent of the accounted commit, so it would not address what was measured, and a cap that kills a session loses its work.
3. **A 1 s watcher on future heavy runs,** so a spike is caught next time. Trade-off: a small helper, and it tests candidate (a) only if the failure recurs.
4. **A host overcommit or swap change.** Not recommended: the evidence says commit pressure is not the cause, and host settings are the owner's.
5. **To test candidate (b), record the cgroup of the Workflow's agents (memory.max, pids.max, memory.events) at the start of any future native run.** Trade-off: only useful if a native run happens again, and the owner has stopped them.

**What is and is not confirmed (for the owner).** Confirmed: the 57 failures and 7 errors in the native Test phase were environmental, not code; the same tests passed in capped chunks and as the 59 failing node ids, with no ENOMEM. **Not confirmed, and open: the mechanism.** That includes commit pressure (rejected above) and also "one uncapped process" as the cause, since a 99-test rerun failed the same way and a 4,300-test single process ran clean under the cap.

**Correction note for text already on main** (merged in #929; I did not edit these done/ files). They name commit pressure or the single uncapped process as the cause instead of as a hypothesis:
- `agent-working/tickets/done/TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT.md`, the Test Summary row about the 57 failures and 7 errors and the "Marker filter" paragraph;
- `agent-working/tickets/done/implement-ticket-native-port/TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN.md`, the Result paragraph and the bullet about the uncapped `tests/tools` run;
- `agent-working/stored_artifacts/TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN/investigation.md`, the bullet about the Test phase running `tests/tools` in one uncapped process;
- `agent-working/tickets/done/implement-ticket-native-port/TCK-20260930-IMPLEMENT-TICKET-NATIVE-PORT.md`, the Known gap sentence about the uncapped `tests/tools` run.
Read them as: the failures were environmental; the mechanism is open (this ticket).

Known gap: the 72 processes this user could not read are not in the breakdown. Step 3 was not run, so the uncapped single-process case is untested on this host.
