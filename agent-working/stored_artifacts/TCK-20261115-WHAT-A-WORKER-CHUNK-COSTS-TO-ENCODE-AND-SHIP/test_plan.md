---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP
phase: open
artifact_type: test_plan
date: 2026-11-16
tags: [performance]
---

# Test plan: chunk cost probe

The probe is a measuring instrument kept in staging, not product code, so its checks are run checks:
1. **Positive control (required):** per world, `final_hash` of the probe runs equals the `--no-probe` run. A mismatch voids that world's figures.
2. **Counts add up:** per tick, the sum of chunk `packets` equals `packets`; chunk sizes match the formula for that chunking.
3. **Validation passes:** `validate_result_batch` raises on a mismatch, so a completed run means every decoded chunk's results matched its packets.
4. **Quiet host:** quiet gate passes before each run (perf_baseline_policy §2.2); a run that fails the gate is not used.
5. **Spread:** report median and p90; a tick or chunk outlier with no explanation is reported, not dropped silently.
