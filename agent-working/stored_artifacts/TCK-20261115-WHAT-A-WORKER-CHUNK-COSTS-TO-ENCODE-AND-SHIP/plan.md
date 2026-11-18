---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP
phase: open
artifact_type: plan
date: 2026-11-16
tags: [performance]
---

# Plan: chunk cost probe (cheap form)

Owner go: option B, #715 6910997558 (relayed by lead-planner 2026-11-16); exemption #715 6889952914. A heavy-slot go is still needed per run.

## What the probe does
`chunk_cost_probe.py` (this folder; no `tools/` home, no `src/` edit):
1. Builds the pinned kernel (`tools/test_architecture/rpg_gate_run.build_kernel`: PinnedNormalGovernor, LocalSequentialExecutor, audit mode, budget 1e9).
2. Swaps the kernel's executor for a wrapper that calls the real sequential executor first and returns its results unchanged.
3. On each measured tick, a side path runs the real `ConcurrentExecutionAdapter.execute` on its own adapter instance (its own freeze cache), whose manager only captures the packets. That times **packet build** (views, packets, `validate_packet_batch`).
4. Chunks the packets with the worker manager's formulas: `thread` (today's PROD_SMALL path: `min(50, n // (2*workers))`) or `process` (mega-chunks: `n // workers`), workers = 2.
5. Per chunk, with GC off around the timed block: `pickle.dumps` (encode), `pickle.loads` (decode), `_process_chunk_wrapper(decoded, default_simulation_worker)` (compute on the decoded copy, as a remote worker would), result encode, result decode, `ProtocolValidator.validate_result_batch` (validate). Sizes: request bytes, request bytes without the private caches (`worker_protocol.py` `_region_index_cache` ... `_ground_item_map_cache`), response bytes, and on every 20th measured tick the per-packet-encoded sum (design §4 "either way").
6. Positive control: `--no-probe` runs the same kernel without the side path; `final_hash` (`CanonicalStateHasher`) must match.

## Run set (heavy slot, after stage 0)
Per gate world (`frontier_living_world`, `urban_political`, `crowded_frontier`), seed 42, warmup 20, 200 measured ticks: one `--chunking thread`, one `--chunking process`, one `--no-probe`. 9 runs, one at a time, quiet gate before each, under the 3G cap on CPUs 4-5.

## Verdict rule
Per world and chunking: median and p90 of `codec_over_compute` = (encode + decode + result encode + result decode) / compute per chunk.
- Ratio clearly above 1 on all 3 worlds for both chunkings: conclusive, the codec costs more than the work it carries (pickle as the codec, at today's chunk shape); child 3 would ship a cost it cannot earn back without a different codec or chunk shape.
- Ratio clearly below 1: conclusive the other way.
- Straddling 1, or worlds disagree: INCONCLUSIVE; say what the full form (transport and a real worker) would settle.
Network transfer time is not in the cheap form: marked unknown (bytes are given so a bandwidth can be applied).
