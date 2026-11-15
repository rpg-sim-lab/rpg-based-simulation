---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan — TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN

Written at close, 2026-11-16. This ticket was an evidence ticket: its work was three Workflow runs, not a code change, so the plan is the run plan.

The run plan v3 (agent-working-planner, 2026-11-15) is in the ticket's Implementation Notes: preconditions 1-5, a fail run with the unregistered probe tag `native-run-probe`, a pass run with the tag removed, the worktree `scriptPath` and never the named workflow, a 5 s MemAvailable watcher with a 1.5 GB stop, and no retry on a harness fault. What happened is in the ticket's Test Summary.
