---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN
artifact_type: test_plan
tags: [ai, agent-monitoring]
---

# Test Plan — TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN

Written at close, 2026-11-16. No code changed; the proof is the runs' recorded rows.

## Regression Surface
None: the ticket changes no code.

## New Tests Required
None.

## Proof Plan

| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| AC1 | static | invariant | ticket AC1; `tools/workflow_bash_sites.py` | 0 `bash(` sites | `python3 tools/workflow_bash_sites.py .claude/workflows/implement-ticket.js` |
| AC2 | live Workflow runs | evidence | ticket AC2 and run plan v3; parity: none | a fail run and a pass run with correct outcomes | wf_b59e5ed2-5d3, wf_d6a35058-f5d, wf_f48f4fae-569 |
| AC3 | recorded rows | evidence | ticket AC3; `gate_verdicts.jsonl` | backstop agrees with attested rows | compare rows per run (in the Test Summary) |

## Scoped Pytest Commands
None.

## Anti-Drift Test Guards
None.
