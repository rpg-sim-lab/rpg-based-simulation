---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261108-KERNEL-CONCURRENCY-DIAGRAMS-SHOW-A-SEED-THE-PACKET-NO-LONGER-CARRIES
phase: open
date: 2026-11-08
tags: [documentation, determinism]
---

# TCK-20261108-KERNEL-CONCURRENCY-DIAGRAMS-SHOW-A-SEED-THE-PACKET-NO-LONGER-CARRIES

## Title
The kernel concurrency design diagrams show a per-packet RNG seed, but since #837 every packet carries the world seed

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
This is batch A (lead part), recent-work item 6, of `agent-working/lead/docs_as_review_source_plan.md` rev 3.2, approved by the owner on 2026-11-08 (#715 comment 6720445592).

`docs/architecture/kernel_concurrency_design_philosophy.md` still describes the pre-#837 packet in two places:
- `:71` (flowchart): "derive per-packet RNG seeds";
- `:130` (sequence diagram): "per-packet seed = composite_hash(base_seed, domain, tick, entity_id)".

Since #837 (531010a9a), `src/engine/executor.py:301` builds each `WorkerPacket` with `seed=state.seed`, the world seed, so `context.seed` means the same thing under either executor. Per-call RNG derivation in `src/platform/rng.py` (doc `:106-107`) is unchanged and stays correct.

## Scope
- Correct the two diagram labels at `:71` and `:130` so they show the packet carrying the world seed, with per-call RNG derived from it.
- Link to the canonical determinism doc instead of restating the derivation (D25 satellite rule).

## Out of Scope
- `docs/engine/contracts/simulation_kernel_contract.md` and `docs/engine/deterministic_execution.md` (items 1 and 2). They are rpg-owned and sent to rpg-planner-ubuntu.
- Any code change.

## Acceptance Criteria
- Neither diagram says the packet carries a per-packet seed.
- The doc's RNG text (`:106-107`) still matches `src/platform/rng.py`.
- `tests/docs/test_doc_path_existence.py` passes.

## Related Tickets
- TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP (same PR)

## Related Docs
- docs/architecture/kernel_concurrency_design_philosophy.md
- docs/engine/deterministic_execution.md
- agent-working/lead/docs_as_review_source_plan.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
src/engine/executor.py, src/core/worker_protocol.py, src/platform/rng.py

## Assumptions / Open Questions
None. Checked on 2026-11-08 by reading the doc's lines 71, 106-107 and 130, and `executor.py:295-305`, at origin/main 297494469.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
