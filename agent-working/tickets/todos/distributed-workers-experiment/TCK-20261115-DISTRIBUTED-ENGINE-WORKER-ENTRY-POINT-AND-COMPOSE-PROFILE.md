---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261115-DISTRIBUTED-ENGINE-WORKER-ENTRY-POINT-AND-COMPOSE-PROFILE
phase: open
date: 2026-11-15
tags: [platform, architecture, determinism, security]
---

# TCK-20261115-DISTRIBUTED-ENGINE-WORKER-ENTRY-POINT-AND-COMPOSE-PROFILE

## Title
An `engine-worker` container entry point and an opt-in `distributed` compose profile, so the distributed-workers mode can run its
Collection pool in a container. `docker compose up` with no profile starts exactly today's services.

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Child 4 of `TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`. The cut line is in
`docs/plans/architecture/distributed_workers_experiment_design.md` §9, and the shape in §7.
- The owner approved **filing it as a ticket only, nothing built** (#715 6889952914, item D; owner's words 6889947724).
- **HELD/shelved: no-go as designed, see design §14; owner #715 6917359910 ("R5 now, R3 later").** Child 3 is re-cut after
  Milestone 1 and the next-gen contract spec as a worker-resident replica with typed per-tick deltas (design §14). This ticket's
  scope below is written against the old child 3 and is re-scoped when that re-cut lands. This replaces the earlier gate (the
  owner's whole-plan review, #715 6731938042).
- The ADR is `docs/architecture/distributed_workers_adr.md`, accepted #715 6777076537.

## Scope
Recorded now, against the old child 3 design (re-scoped when the R3 re-cut lands):
1. **Image entry point.**
   - An `engine-worker` service from the same backend image (`docker/backend.Dockerfile`), holding N worker processes behind one
     gRPC listener (design §7, §4).
   - It is not `ai_worker`, the anomaly consumer.
   - The gRPC dependency is the optional `distributed` extra (design §4). The default image does not carry it. The image change is
     made so the default build is byte-for-byte the same build as today's; it adds a separate stage or build arg.
2. **`distributed` compose profile.**
   - It adds the `engine-worker` service.
   - The engine side runs as a CLI run in the backend image under the same profile.
   - The worker port is on the compose-internal network only and **never published to the host** (owner's trust-boundary guard,
     design §4).
   - The per-run secret reaches the worker as a compose secret or env, never in a manifest, log or argv.
3. **Opt-in smoke workflow.**
   - One containerized smoke run repeats child 3's equivalence on one world: an identical final hash under `PROOF_DIGEST_SCHEME`,
     and the `TICK_END` trail versus `LocalSequentialExecutor`.
   - It is triggered on request, not in `test.yml` or `slow-regression.yml` (epic table, child 4).
4. A runbook in `docs/runbooks/` for starting the profile and reading the smoke result.

## Out of Scope
- Anything built while shelved (owner 6917359910; design §14).
- The remote executor, transport, codec and handshake code (child 3, rpg-planner, `src/engine`).
- Kubernetes or Helm; scaling beyond one host; the API/engine split; API reach (design §5).
- mTLS, unless child 3's security review moves it into the first build (design §4).
- The packet-cost measurement (child 2, perf-planner) and the contract docs (child 5).

## Acceptance Criteria
1. `docker compose config` and `docker compose up` with no profile give exactly today's services and settings, checked with a diff
   of `docker compose config` against main.
2. With `--profile distributed`, `engine-worker` starts from the backend image, and no port of it is published to the host. A test
   reads `compose.yaml` and fails on any `ports:` entry for that service (design §8a).
3. The default backend image build is unchanged; the gRPC extra is only in the worker build.
4. The smoke workflow is opt-in (manual trigger), and its one-world equivalence run matches the local executor's final hash and
   `TICK_END` trail.
5. The secret never appears in `docker compose config` output, logs, the manifest or argv.
6. The runbook exists and is linked from the profile's comment in `compose.yaml`.

## Related Tickets
- TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT (parent; child 4)
- TCK-20261109-DISTRIBUTED-WORKERS-DESIGN (the design)
- TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING (separate epic; filed the same day)
- TCK-20261115-DISTRIBUTED-WORKERS-REMOTE-WORKER-MANAGER (child 3, rpg-planner; filed on u24, ticket only; this ticket waits on it)

## Related Docs
- docs/architecture/distributed_workers_adr.md
- docs/plans/architecture/distributed_workers_experiment_design.md
- docs/runbooks/compose-api-key.md

## Related Stored Artifacts
- none

## Related Code Areas
- compose.yaml
- docker/backend.Dockerfile
- pyproject.toml
- .github/workflows/

## Assumptions / Open Questions
- **Where the entry point's Python lives (open).** A worker `main` module under `src/` routes to rpg. This is settled with
  rpg-planner when child 3 lands, because child 3 defines the server side.
- `pyproject.toml`/`uv.lock` (the extra) go through the leads (design §4).
- The smoke run and any container start go through lead-planner (heavy slot).
- Compose edits are made from `.claude/worktrees/platform` only.

## Implementation Notes
Filed only (owner, 6889952914 item D). Shelved (owner 6917359910). No staging artifacts until the R3 re-cut of child 3 exists;
then this ticket is re-scoped and the standard-tier artifacts are written before dispatch.

## Test Summary
Not started.

## Files Changed
- none yet

## Completion Summary
Open. HELD/shelved, no-go as designed, see design §14; owner #715 6917359910.
