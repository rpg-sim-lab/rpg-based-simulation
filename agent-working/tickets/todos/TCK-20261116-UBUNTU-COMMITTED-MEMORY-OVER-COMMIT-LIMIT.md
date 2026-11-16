---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT
phase: open
date: 2026-11-16
tags: [ai, testing]
---

# TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT

## Title
On host ubuntu, committed memory sits above the commit limit, so one large uncapped process gets ENOMEM even while MemAvailable is several GB.

## Status
OPEN

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
1. A measured breakdown of committed memory by process kind, at one named time, with no credential or token detail.
2. The hypothesis is stated as confirmed, rejected or unresolved, citing the repro.
3. An options list with a recommendation, for the owner, through lead-planner.

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
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
