---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261118-CPU-STEAL-AND-SWAP-COUNTERS-IN-EVERY-TIMING-RECORD
artifact_type: investigation
phase: done
date: 2026-11-18
tags: [performance]
---

# Investigation

`RunWatch` is the only user of the quiet gate and `cmd_record` is the only writer of per-run gate data (`summary.json` `gates`). `capacity_run` and `profile_tick` do not use it. `read_cpu_jiffies` already folds steal into busy but does not expose it; `rerun_baselines.cpu_counters` reads aggregate steal only for the host-speed probe. The in-run swap check was pinned-only; the record now reads the counters for unpinned runs too without adding a check.
