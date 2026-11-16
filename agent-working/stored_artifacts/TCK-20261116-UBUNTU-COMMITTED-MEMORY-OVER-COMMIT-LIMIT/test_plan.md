---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test Plan — TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT

## Regression Surface
None: the ticket changes no code.

## New Tests Required
None.

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1 | host measurement | evidence | ticket AC1; `/proc/meminfo`, `/proc/<pid>/smaps` | a breakdown by process kind at one named time | `investigation.md`, "Committed memory by process kind" |
| AC2 | live repro | evidence | ticket AC2; the decision rule in `investigation.md` | hypothesis stated confirmed, rejected or unresolved, citing the repro | `repro.py probe`, `repro.py suite`; `step1.log`, `step2.result` |
| AC3 | options list | recommendation | ticket AC3 | options with trade-offs and a recommendation, for the owner through lead-planner | this ticket's Completion Summary |

## Scoped Pytest Commands
None.

## Anti-Drift Test Guards
None.
