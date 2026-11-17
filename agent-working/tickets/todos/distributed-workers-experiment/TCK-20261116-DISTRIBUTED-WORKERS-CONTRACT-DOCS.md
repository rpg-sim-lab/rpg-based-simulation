---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261116-DISTRIBUTED-WORKERS-CONTRACT-DOCS
phase: open
date: 2026-11-16
tags: []
---

# TCK-20261116-DISTRIBUTED-WORKERS-CONTRACT-DOCS

## Title
Distributed workers child 5: the engine contract docs for a distributed mode beside the unchanged single-process mode (doc only; filing only)

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Child 5 of TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (the epic table row 5; docs/plans/architecture/distributed_workers_experiment_design.md). The owner chose option B on the whole-plan review, #715 6910997558. The owner's words: "yes, go with B, remember that don't touch the original design, just build a multi-modes core, like we can use single mode for some purposes and distributed mode for some other purposes".

Under B, child 5 may proceed as doc work. This ticket is the FILING ONLY: nothing is dispatched and nothing is written yet. It was filed by rpg-planner (docs/engine routes to rpg) at the ubuntu lead's request, relayed by lead-planner-u24.

The text this ticket would change, on main:
- `docs/engine/contracts/worker_contract.md` §5 lists "No distributed workers (network boundaries)" as a non-goal.
- `docs/engine/contracts/infrastructure_overview.md` (~:159) describes `ai_worker` as a "Scaling pool executing computationally intense AI predictions". Per the epic's fact 5, it is the anomaly worker (`python -m src.observability.anomaly.worker`) and never imports the engine.

## Scope
1. `worker_contract.md` §5: describe two per-purpose modes. The single-process mode is UNCHANGED and stays the default: `kernel.py` executor selection, and `docker compose up` without a profile. A distributed mode is opt-in, for named purposes. The existing laws (§3 merge at the tick boundary through `ApplyPath` alone, §4 backpressure and fallback, no shared mutable state, no asynchronous result application) are restated as holding in BOTH modes, or narrowed for the distributed mode only where child 3's contract says so. Write the "No distributed workers" non-goal as "no distributed workers in the single-process mode", not deleted.
2. `infrastructure_overview.md`: add the distributed mode (the opt-in compose profile from child 4) beside the existing topology, and correct the `ai_worker` wording at ~:159 to what it is (the anomaly worker; no engine import).
3. `docs/guidelines/intentional_divergences.md`: only if the distributed mode's behaviour differs from the single mode's. It must not, by the ADR; any difference found is a stop to the owner.
4. Wording follows child 3's contract (TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER) and the next-gen contract spec. This child is written only from what those settle, and it describes nothing child 3 hasn't fixed.

## Out of Scope
- Any src, compose or config change (children 3 and 4, held under B).
- The packet-cost measurement (child 2).
- Changing the single-process mode in any way (owner, 6910997558).
- `kernel.md`, `system_overview.md`, `kernel_concurrency_design_philosophy.md` beyond a cross-reference.

## Acceptance Criteria
- worker_contract.md §5 and infrastructure_overview.md describe both modes as per-purpose and coexisting. The single mode's text and default are unchanged in meaning.
- The ai_worker line matches its code (`src/observability/anomaly/worker.py`).
- Docs search and `make knowledge-index-update` are run; the docs-truth checks pass.
- No divergence entry unless behaviour differs. If it does, that's an owner stop.

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (epic; row 5)
- TCK-20261109-DISTRIBUTED-WORKERS-DESIGN
- TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER (child 3; held under B)
- TCK-20261115-DISTRIBUTED-ENGINE-WORKER-ENTRY-POINT-AND-COMPOSE-PROFILE (child 4; held under B)

## Related Docs
- docs/engine/contracts/worker_contract.md; docs/engine/contracts/infrastructure_overview.md; docs/architecture/distributed_workers_adr.md; docs/plans/architecture/distributed_workers_experiment_design.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/kernel.py (executor selection); src/observability/anomaly/worker.py; docker-compose.yml (profiles)

## Assumptions / Open Questions
- Dispatch is a later owner ask. Under B, child 5 is allowed to proceed, but its wording depends on child 3's contract, which is held. So writing waits until child 3's contract and the next-gen spec settle the distributed mode's laws, unless the owner says to write the mode-split framing now.
- The docs-as-review-source batch gate on `docs/engine/**` (#715 6720445592): check that it has landed before writing.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
