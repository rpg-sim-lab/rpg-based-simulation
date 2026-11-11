# Implementation Sequence: distributed-workers-experiment

Epic `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`, filed by architecture-planner-u24, 2026-11-09. Routed by the owner
(#715 6731692652); shape chosen by the owner (#715 6731714291, "Epic + ADR first"). Scoping only.

## Order

1. **DONE** TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT: lead-planner (ubuntu). Accepted by the owner (#715 6777076537); now `docs/architecture/distributed_workers_adr.md`.
   Everything below waits on it.
2. TCK-20261109-DISTRIBUTED-WORKERS-DESIGN: architecture. **DRAFT written before 1 by owner leave (#715 6731956846)**, which relaxes
   the ADR-first gate (6731714291) for this child only: `docs/plans/architecture/distributed_workers_experiment_design.md`, inside 1's
   five scoped points, reviewed by the owner together with 1. It follows 1 if 1 narrows the points.

## Not cut yet

Children 2-6 (packet-cost measurement, remote executor, worker entry point and compose profile, contract docs, evidence guard) are cut by their
owning planners after 1 lands; the epic's table gives each one's owner, cost, what it leaves out and its gate.

## Rules

- **Owner review gate (#715 6731938042):** the plan is complete when 1 and 2 are written and children 2-5 are cut; then STOP.
  No implementation child starts, and no heavy-slot run, until the owner has reviewed the whole plan.

- Nothing is built before 1 is accepted.
- The default path never changes: `kernel.py:193-198` selection and `docker compose up` without a profile.
- Any heavy-slot run (child 2) queues behind the RPG queue, and lead-planner-u24 is told before it runs.
- No `docs/engine/**` edit before ubuntu's docs-as-review-source batch lands (#715 6720445592).
- The filing rides in a later implementation PR on this track; pushes and merges are the owner's yes, through lead-planner-u24.
