---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN
phase: done
date: 2026-11-19
tags: [process-improvement]
---

# Plan
1. rpg_gate_report: skip fail/drift rows whose key and state are in main's report, vs_main in JSON/markdown/log, fallback on any doubt. 2. rpg_gate_main_report (+ .yaml bound): select and fetch main's newest completed report. 3. Workflow: actions: read on the report job, fetch step before Evaluate. 4. Replay and fetch tests, workflow-shape test, reference doc note.
