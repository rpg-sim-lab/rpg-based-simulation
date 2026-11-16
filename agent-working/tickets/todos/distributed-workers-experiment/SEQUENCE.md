# Implementation Sequence: distributed-workers-experiment

Epic `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`, filed by architecture-planner-u24, 2026-11-09. Routed by the owner
(#715 6731692652); shape chosen by the owner (#715 6731714291, "Epic + ADR first"). Scoping only.

## Owner decision 2026-11-15 (#715 6889952914, owner's words 6889947724)

This supersedes any older gate text below where they differ.
- **Child 6, the evidence guard: file and build** (owner item A). testing-planner scopes it; rpg-planner does `rpg_measure` and the
  manifest field. It is small, with no runs. rpg-planner's ruling: `RunConditions` gets an Optional `worker_manager` qualname,
  which testing-planner builds under item A. It is the one exception to the owner review gate in Rules.
- **Child 2, the packet-cost measurement, cheap form: exempt from the perf pause** (owner item C, #715 6556861718). It is
  measurement only, and the exemption is recorded in `TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE`. perf-planner
  filed it as `TCK-20261115-WHAT-A-WORKER-CHUNK-COSTS-TO-ENCODE-AND-SHIP`. It takes the heavy slot in turn through the leads. The
  full (container) form is not covered.
- **Children 3, 4 and 5: filed as tickets only, nothing built** (owner item D):
  - child 3, the remote worker manager: rpg-planner, filed as `TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER`;
  - child 4, the engine-worker entry point and compose profile: platform-planner (ubuntu); recorded under Not cut yet;
  - child 5, the contract docs: through the ubuntu lead.
  The owner's whole-plan review (#715 6731938042) still gates their implementation.
- **Still paused:**
  - the languages/architecture re-design (owner, 2026-11-14, #715 6875162764);
  - all `src/engine` work under this epic until after Milestone 1.

## Order

1. **DONE** TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT: lead-planner (ubuntu). Accepted by the owner (#715 6777076537); now `docs/architecture/distributed_workers_adr.md`.
   Everything below waits on it.
2. TCK-20261109-DISTRIBUTED-WORKERS-DESIGN: architecture. **Design ACCEPTED** by the owner at `f517f1fdf` (#715 6777076537):
   `docs/plans/architecture/distributed_workers_experiment_design.md`. It was drafted before 1 by owner leave (#715 6731956846). The
   children follow its §9 order: 6, 2, 3, 4, 5.

## Not cut yet

Children 2-6 (packet-cost measurement, remote executor, worker entry point and compose profile, contract docs, evidence guard) are cut by their
owning planners after 1 lands; the epic's table gives each one's owner, cost, what it leaves out and its gate. **Child 3 is filed
2026-11-15 as a ticket only:** `TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER` (rpg-planner; owner #715 6889952914, item
D). Nothing is built. It is gated by the owner review gate below and by the `src/engine` pause until after Milestone 1.

- **Child 4, filed 2026-11-15 as a ticket only:** `TCK-20261115-DISTRIBUTED-ENGINE-WORKER-ENTRY-POINT-AND-COMPOSE-PROFILE`
  (platform-planner; owner #715 6889952914, item D). Nothing is built. It is BLOCKED on child 3 and on the owner review gate below.

## Rules

- **Owner review gate (#715 6731938042):** the plan is complete when 1 and 2 are written and children 2-5 are cut; then STOP.
  No implementation child starts, and no heavy-slot run, until the owner has reviewed the whole plan.
  - **Exceptions (owner #715 6889952914):** child 6, the evidence guard, is filed and built now (item A). Child 2's cheap form
    runs under its perf-pause exemption (item C). Children 3-5 are filed only (item D), and this gate still holds for their
    implementation.

- Nothing is built before 1 is accepted.
- The default path never changes: `kernel.py:193-198` selection and `docker compose up` without a profile.
- Any heavy-slot run (child 2) queues behind the RPG queue, and lead-planner-u24 is told before it runs.
- No `docs/engine/**` edit before ubuntu's docs-as-review-source batch lands (#715 6720445592).
- The filing rides in a later implementation PR on this track; pushes and merges are the owner's yes, through lead-planner-u24.
