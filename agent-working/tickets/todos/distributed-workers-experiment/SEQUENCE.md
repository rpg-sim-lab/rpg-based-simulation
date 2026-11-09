# Implementation Sequence: distributed-workers-experiment

Epic `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`, filed by architecture-planner-u24, 2026-11-09. Routed by the owner
(#715 6731692652); shape chosen by the owner (#715 6731714291, "Epic + ADR first"). Scoping only.

## Order

1. TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT: lead-planner (ubuntu), after ubuntu's `lead-docs-review-source` batch lands.
   Everything below waits on it.
2. TCK-20261109-DISTRIBUTED-WORKERS-DESIGN: architecture. BLOCKED on 1.

## Not cut yet

Children 2-5 (packet-cost measurement, remote executor, worker entry point and compose profile, contract docs) are cut by their
owning planners after 1 lands; the epic's table gives each one's owner, cost, what it leaves out and its gate.

## Rules

- Nothing is built before 1 is accepted.
- The default path never changes: `kernel.py:193-198` selection and `docker compose up` without a profile.
- Any heavy-slot run (child 2) queues behind the RPG queue, and lead-planner-u24 is told before it runs.
- No `docs/engine/**` edit before ubuntu's docs-as-review-source batch lands (#715 6720445592).
- The filing rides in a later implementation PR on this track; pushes and merges are the owner's yes, through lead-planner-u24.
