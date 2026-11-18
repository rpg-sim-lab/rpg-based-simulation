---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261118-CPU-STEAL-AND-SWAP-COUNTERS-IN-EVERY-TIMING-RECORD
phase: done
date: 2026-11-18
tags: [performance]
---

# Plan

1. `quiet_gate.read_steal_jiffies` reads the steal field (aggregate and per CPU) of `/proc/stat`; `None` when unreadable.
2. `RunWatch` takes steal and swap readings at start and finish for pinned and unpinned runs and stores `cpu_steal`, `swap_in_pages`, `swap_out_pages` in `fields`; steal above 5 % sets a warning only.
3. `cmd_record` merges `watch.fields` into each `gates` entry of `summary.json` (tools-side sidecar; `src/perf` untouched).
4. Unit tests with fake readers; one paragraph in `perf_baseline_policy.md` 2.2.
