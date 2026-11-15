---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING
phase: open
date: 2026-11-15
tags: [platform, architecture, observability, lab-agent]
---

# TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING

## Title
World farm, step one: two worlds run at the same time on one host without sharing an event stream, deleting each other's lab run
data, or interleaving a ledger line.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Child 3 of `TCK-20261109-EPIC-NEXT-GENERATION-ENGINE`, from the feasibility review's §7 blockers ("cheapest first"), items 1 to 3.
- The owner approved filing and building it (#715 6889952914, item B; owner's words 6889947724): "platform-planner files and builds
  the next-gen world farm (next-gen epic child 3): a Redis stream per world, unique lab run ids, process-safe ledger appends. No
  src/engine change."
- Owner priority: the farm comes first among the epic's children (#715 6735575831, Q3 (c)).
- Claimed on #634 (6889978228).

A farm here means **one world per process**. Two worlds sharing one process (every process-global per world) is not this ticket. The
review calls it the largest item, and a one-world-per-process farm never needs it.

## Scope
1. **One event stream per world.**
   - Today: the producer resolves the stream from `SIM_STREAM_NAME`, then `RPG_STREAM_NAME`, default `simulation:events`
     (`src/observability/config.py:326`).
   - The anomaly worker reads `SIM_STREAM_NAME` only, with no `RPG_STREAM_NAME` fallback
     (`src/observability/anomaly/worker.py:418`). So a world started with only `RPG_STREAM_NAME` set would publish to a stream its
     anomaly consumer never reads.
   - The same worker block has the same gap on the Redis URL: `worker.py:419` defaults to `redis://redis:6379/0` with no
     `RPG_REDIS_URL` fallback, while `config.py` defaults to localhost.
   - Wanted: a world started with its own stream name has its producer and all its consumers (anomaly worker, quality feed) on that
     one name. The worker calls the producer's resolver (`get_stream_name()`, or the same SIM_ then RPG_ then default order), not a
     second copy (rpg condition 1). The Redis URL gets the same treatment in the same change. With nothing set, the name stays
     `simulation:events`, and compose's explicit `SIM_REDIS_URL` keeps the in-network URL.
2. **Unique lab run ids.**
   - Today: `src/lab/orchestrator.py:171-174` (and the twin at `:287`) builds `run_{lab_run_id}_seed_{seed}` under `data/runs/` and
     `rmtree`s any existing dir. Two concurrent lab runs given the same `lab_run_id` delete each other's run data.
   - Two other builders use the same pattern: `src/observability/sweeper.py:125` and `src/observability/mining/controller.py:98,114`.
     They are covered here too, unless the investigation shows why one is out (then it goes in Out of Scope with the reason).
   - Wanted: no run directory that belongs to another run is ever `rmtree`'d. The plan says which rule it picks, unique ids or
     refuse an existing dir, against how `LabSessionStore` and `src/lab/repository.py`'s `_validate_lab_run_id` treat ids today
     (rpg condition 2).
   - Before any id-format change: grep `src/`, `frontend/` and `tools/` for readers that parse `run_..._seed_...`, and keep them
     working.
   - The investigation shows, with a line, that the run id feeds no seed, RNG or hashed state.
3. **Process-safe run-ledger appends.**
   - The review marks this `[U]` (unverified).
   - `tools/test_architecture/run_ledger.py:281-283` (testing's file) already writes each row as one `os.write` on an `O_APPEND`
     descriptor.
   - `src/observability/run_ledger.py` is an in-run observer that emits events, not a shared file.
   - Wanted: the investigation lists every file appended by more than one world process, and gives each one an append rule and a test
     where two processes write concurrently and every line parses. Where the rule already holds, the item closes on that evidence and
     a test (rpg condition 3). Any change to `tools/test_architecture/run_ledger.py` goes through testing-planner.

## Out of Scope
- Any `src/engine/**` change (owner, 6889952914; all `src/engine` work under both epics is paused until after Milestone 1).
- The review's blockers 4 to 6:
  - the measured cap of N worlds per host (perf-planner, under its own exemption, later);
  - the lab and sweeper launching subprocesses;
  - the API (one container per world, or a keyed manager).
- Two worlds in one process.
- Compose changes. The default `docker compose up` does not change. If a compose line turns out to be needed, it is made from
  `.claude/worktrees/platform` only (lead, 2026-11-15).
- Gate, paired and capacity tooling's own farm (`rpg_gate_harness.py`, `paired.py`); those already run one world per subprocess.

## Acceptance Criteria
1. Producer and anomaly worker resolve the same stream name and the same Redis URL under SIM_ only, RPG_ only, both, and neither
   (a test per case).
2. Two worlds started with different stream names publish to, and are consumed from, their own streams only: a test with two names
   finds no event from world A on world B's stream. With no name set, every reader and writer resolves `simulation:events`, as
   today.
3. A lab run whose `lab_run_id` is already in use never deletes the existing run's directory. A test runs two orchestrations with
   the same id and checks that the first run's files survive. The sweeper and mining controller have the same guarantee, or are
   out of scope with a reason. Every reader of the `run_..._seed_...` format still works.
4. Every file that two world processes append to is listed in the investigation with its append rule. Each has a test with two
   concurrent writer processes where every line parses (`json.loads`), and none is lost.
5. No `src/engine/**` file changes, and no simulation result changes: gate and paired hashes are unchanged (the change is outside
   the tick). The scoped tests for `src/lab` and `src/observability` pass.
6. The docs that describe the stream name and lab run ids say the new rule (doc-updater, or `tools/gate_checks/docs_search.py`).
7. No Bible or parity entry is needed. If the work finds a simulation law involved, it stops and asks rpg-planner-ubuntu
   (rpg condition 5).

## Related Tickets
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (parent; child 3)
- TCK-20260702-OBSISO-BROKER-CONFIG (done; the stream-name default it fixed)
- TCK-20261019-COMPOSE-BACKEND-PUBLISHES-EVENT-STREAM-TO-REDIS (done; compose's stream settings)
- TCK-20261115-DISTRIBUTED-ENGINE-WORKER-ENTRY-POINT-AND-COMPOSE-PROFILE (separate epic; filed the same day)

## Related Docs
- docs/plans/architecture/next_generation_engine_feasibility_review.md
- docs/architecture/next_generation_engine_adr.md
- docs/guides/simulation_quality.md

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING/ (investigation, plan, test plan)

## Related Code Areas
- src/observability/config.py
- src/observability/anomaly/worker.py
- src/simulation_quality/worker.py
- src/lab/orchestrator.py
- src/lab/repository.py
- src/lab/store.py
- tools/test_architecture/run_ledger.py

## Assumptions / Open Questions
- **Who writes the code: answered (rpg-planner-ubuntu, 2026-11-15, option (b)).** platform-implementer writes items 1 and 2 under
  this ticket. rpg-planner-ubuntu reviews by message before the push ask, because these lines are plumbing, not RPG logic. Testing's
  OK is needed for any edit to `tools/test_architecture/run_ledger.py`.
- **Overlap check (rpg condition 4), 2026-11-15 on origin/main 0a8f65c3f:**
  - No open PR touches these files (#921, #881, #813, #811, #781).
  - 29 old origin branches (2026-10-14 to 10-20, among them `rpg-d80b` and `rpg-d80c`) differ on at least one of them. They look like
    remnants left after squash merges.
  - The implementer re-checks before its first edit, on both hosts (u24 through lead-planner).
- Whether other files are appended by every world (lab summaries, `data/ledgers/`, monitoring) is the investigation's first question.

## Implementation Notes
Standard tier: `plan.md`, `investigation.md` and `test_plan.md` are in `agent-working/staging_artifacts/<this id>/`, written by
platform-planner on 2026-11-15. Key finding: the kernel's `create_run_directory` overwrites a dir for an explicit id
(`src/engine/run_identity.py`), so the lab refuses before it reaches the kernel; nothing in `src/engine` changes. No
heavy-slot run and no container start is needed. If one turns out to be, it goes through lead-planner first.

## Test Summary
Not started.

## Files Changed
- none yet

## Completion Summary
Open.
