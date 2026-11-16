---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Plan — TCK-20261116-UBUNTU-COMMITTED-MEMORY-OVER-COMMIT-LIMIT

Host measurement, no code. Scope item 1: a read-only breakdown of committed memory by process kind (names and numbers only, no command lines, environment or tokens). Scope item 2: a controlled repro, run on lead-planner's slot go (#715 6908488337; steps 1 and 2 only, step 3 conditional and never authorised): step 1 a synthetic fork probe at parent sizes 0.5, 1 and 2 GB, unscoped and in the 3G scope; step 2 the `tests/tools` f-z half as one process in the 3G scope. Scope item 3: an options list for the owner through lead-planner. No host setting changed, no session stopped. `repro.py` in this folder is the script; `step1.log`, `step2.result` and the `*.samples.jsonl` files are its outputs.
