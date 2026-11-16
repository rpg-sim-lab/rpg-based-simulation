---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261109-DISTRIBUTED-WORKERS-DESIGN
artifact_type: plan
---

# Plan — TCK-20261109-DISTRIBUTED-WORKERS-DESIGN

**Reconstructed at close from the accepted design; no tests run (doc deliverable).** This file was written on 2026-11-16, when
the ticket closed. It was not written as pre-work. It maps the ticket's scope items to where the design answers them.

| Scope item | Design section |
|---|---|
| 1 seam | §3 (a `RemoteWorkerManager` behind the existing adapter, not a new `IWorkExecutor`) |
| 2 wire format | §4 (per-chunk encode, gRPC, `ChunkCodec` seam, two-way auth, response MAC) |
| 3 selection | §5 (CLI and harness only) |
| 4 slow or dead worker | §6 (local recompute, counted; a raised exception is handled as locally) |
| 5 equivalence proof | §2.4, §8 |
| 6 compose profile | §7 (`engine-worker`, `distributed` profile) |
| 7 testing strategy | §8, §8a (testing-planner's placement, 2026-11-09) |
| 8 cut lines | §9 |

## History
- DRAFT 2026-11-09, by owner leave (#715 6731956846).
- Revised for the owner's §10 answers (#715 6776551375) and the scale direction (#715 6776564953).
- Ubuntu review 2/2 approved with changes D1-D5, and its re-check was clean.
- ACCEPTED at `f517f1fdf` (#715 6777076537).
- Amended for decision B, the per-purpose multi-mode §13 (#715 6910997558).
- Amended for "R5 now, R3 later" (§14.2, #715 6917359910).

## Cost and what it left out
One doc session per revision, with no runs. Left out: code, measurement (child 2) and the contract text (child 5).
