---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE
phase: done
date: 2026-11-15
tags: [testing, determinism, observability]
---

# TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE: investigation

- #918 already records `RunConditions.executor` and classifies anything but `LocalSequentialExecutor` NOT_PINNED; `arm_child` already calls `require_pinned`. The gaps: the gate candidate and `paired`/`paired_arms` trusted their inputs.
- `kernel._worker_manager` is built even for a sequential executor (kernel.py:139), so the record is decided by the executor, not by that object (rpg-planner's ruling).
- A custom non-sequential executor may carry its own `_worker_manager`; the record prefers it, else the kernel's.
- Pooled gate documents have no run of their own, so their `runner` is derived from the documents they pool.
- An older `ok` gate document has no `runner`, so the candidate refuses it; candidates are built from the same run's fresh documents, so no valid input is lost.
- Cached paired results from before this change are not reused: `arm_child.py` is in paired's child hash.
- A legacy base tree is run by this checkout's `arm_child` (CHILD is the tool checkout's file), so the new field is always written; a legacy tree still fails `require_pinned` as it did after #918.
