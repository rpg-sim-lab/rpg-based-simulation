---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, engine, determinism, platform]
---

# Distributed-workers experiment mode: design (DRAFT)

**Status: DRAFT, for the owner's review together with the ADR amendment.** Design only: no code, tests or runs were written for
it, and no number here is measured. Written by architecture-planner-u24 for `TCK-20261109-DISTRIBUTED-WORKERS-DESIGN`, child 1 of
`TCK-20261109-EPIC-DISTRIBUTED-WORKERS-EXPERIMENT`. Drafted before child 0 (`TCK-20261109-DISTRIBUTED-WORKERS-ADR-AMENDMENT`) lands,
by owner leave (#715 6731956846); it stays inside child 0's five scoped points, and if the ADR narrows them, this doc follows the ADR.
Nothing under the epic is built before the owner has reviewed the whole plan (#715 6731938042). Code facts were read on `main` at
`e755dc3d1`.

**Decisions this doc does not take.** The ADR is lead-planner's. Test-layer and lane placement is testing-planner's (its answer,
2026-11-09, is in §8). Packet-cost measurement is perf-planner's. The engine-side code is rpg-planner's; images and
compose are platform-planner's.

## 1. What the mode is, and what it is not

An **opt-in experiment** that runs the Collection phase's worker packets in a separate container. Nothing else moves: Scheduling,
Resolution, Cleanup, Advancement and Persistence stay in the engine process, and the engine stays the **one writer** that validates,
sorts and applies every result.

It is **not** a speed-up. Collection was 6 to 26 % of a tick (Amdahl ceiling 1.06 to 1.35x, `docs/performance/tick_cost_growth.md`),
and each tick adds a network round trip and serialization of large world views. A result slower than sequential is a valid outcome.
It is **not** an API/engine split, an engine replica, a multi-host deploy or a broker change.

## 2. Constraints (from child 0)

1. One writer: workers compute `WorkerResult`s only; `ProtocolValidator.validate_result_batch` checks them against the source
   packets (`kernel.py:556`, and inside the adapter at `executor.py:367`); results are sorted before apply (`worker_contract.md` §3).
2. "One process" is relaxed for the Collection pool only, and only under the opt-in mode.
3. The default is unchanged: `kernel.py:193-198` selection, `LocalSequentialExecutor`, `ConcurrentExecutionAdapter`, `WorkerManager`
   and `docker compose up` with no profile.
4. Determinism: same world and seed give an identical `flat-sha256-v3` final hash and `TICK_END` trail to `LocalSequentialExecutor`,
   or the mode is unclaimed (PERF-D2 DET-PORT-1, `docs/engine/deterministic_execution.md`, "Scope of the guarantee"). Outcomes never
   depend on worker speed (`worker_manager.py:192`).
5. An experiment by owner choice (#715 6731714291), standing in for Mode 5's reopen condition.

## 3. The seam: a remote worker manager behind the existing adapter

**Proposal:** add a `RemoteWorkerManager` with the same `execute_batch(packets, worker_fn, force_local, concurrency_limit)` contract
as `WorkerManager` (`worker_manager.py:107`), and hand it to the **existing** `ConcurrentExecutionAdapter(worker_manager=...)`
(`executor.py:213`), passed to `Kernel(executor=...)`.

Why this rather than a new `IWorkExecutor`:
- **Packet building stays in one place.** The adapter builds every `WorkerPacket` (`executor.py` up to `:333`) and
  `test_the_executor_is_the_only_place_that_builds_a_worker_packet` (`tests/unit/kernel/test_executor_context_parity.py:141`)
  holds unchanged. A new executor would be a second packet builder, the drift #837 guards against.
- **Validation stays in one place.** The adapter keeps `_source_packets` and validates results (`executor.py:339,367`).
- **Selection is untouched.** The explicit `executor` branch at `kernel.py:193-194` already exists; nothing in the
  `max_worker_count` branches changes.
- **The worker function is importable by name.** The adapter passes `default_simulation_worker` (`executor.py:341-345`), a
  module-level function, so the worker container calls the same function from the same image.

## 4. Wire format and transport

- **Encode per chunk, not per packet.** The adapter freezes the large world views once per batch and shares them across packets
  (`_batch_views`, `executor.py:221-232`). One `pickle.dumps` per chunk keeps that sharing (pickle's memo writes a shared object
  once); per-packet encoding would copy `all_entities`, `regions`, `spatial_grid` and the tile maps into every packet. The private
  caches (`worker_protocol.py:93-98`) are rebuilt on the worker. Child 2 measures the size either way.
- **Transport: stdlib first.** `multiprocessing.connection` (`Listener`/`Client` over TCP, with HMAC `authkey`) carries pickled
  chunks with no new dependency. HTTP, gRPC or Redis Streams add a dependency or a broker hop for a synchronous per-tick call; they
  are rejected for the experiment unless child 2 shows the stdlib path is the bottleneck.
- **Trust boundary.** Unpickling network input runs code. The worker listens only on the compose-internal network, authenticated
  by `authkey`; it is never published to the host. This is an experiment profile, not a deploy surface.
- **Same build, or refuse.** At connect, the worker reports its image digest and a content fingerprint; the engine refuses a
  worker whose build differs (a different build is DET-PORT-2, not claimable).

## 5. Selection: how a run opts in

Default (cheaper): **CLI and test harness only.** A run opts in by building the kernel with
`executor=ConcurrentExecutionAdapter(RemoteWorkerManager(address, authkey))`; a CLI flag or env var names the worker address.
Reaching it from the API is a larger change, because `V2EngineManager` builds `Kernel(profile=..., state=..., rng=...)` with no
executor (`src/api/engine_manager.py:139`); that is left out unless the owner asks for it.

## 6. Slow or dead worker rule

**Proposal:** after a bounded wait per chunk, the engine computes that chunk **locally**, through the same
`_execute_locally` path (`worker_manager.py:213-224`), from the same packets. The worker function is pure over the packet, so the
results are identical; the fallback is counted and recorded in the run manifest, and a run with any fallback says so in its report.
It **never** answers with a FAILURE no-op: in `WorkerManager` a chunk that raised is answered with FAILURE no-ops (`:192-194`), and
a timeout answered that way would make the outcome depend on speed (constraint 4).

The bound is liveness, not outcome, so it may be wall-clock without breaking determinism: whichever side computes the chunk, the
result is the same. Alternative for the owner: fail the run loudly on the first timeout (simpler; loses runs on a flaky worker).

Open check (unverified): the rule holds only if `default_simulation_worker` reads nothing outside its packet. The parity test fails
on an undeclared **state** read (`test_executor_context_parity.py:109`), but a read of a process-global singleton (the content
catalog, registries) is not covered; a separate container must load the same content. Child 3 verifies this before it builds the
transport, and the content fingerprint of §4 covers the content side.

## 7. Compose profile

A `distributed` profile adds one service, named `engine-worker` (not to be confused with `ai_worker`, the anomaly consumer at
`compose.yaml:81-89`), from the same backend image, holding N worker processes behind one listener. The engine side runs as a CLI
run in the backend image under the same profile. `docker compose up` without the profile starts exactly today's services.

## 8. Testing strategy (reusing the existing layers)

Placement below is **testing-planner's answer** (2026-11-09, cross-session reply to architecture-planner-u24; advice for the draft,
not an owner approval). Levels are `docs/testing/test_taxonomy.md` §5; markers are `domain("substrate")` with `level("unit")` or
`level("kernel_integration")` (§10).

**Behaviour evidence does not change.** The rpg gate, paired arms and the gate baseline
(`tests/simulation_quality/rpg_gate/baselines/rpg_gate_v1.json`) run on the pinned sequential runner (`tools/rpg_measure`) only.
This is a **guard, not only policy** (testing-planner): the run manifest records the executor mode, and the gate candidate, paired
arms and `rpg_measure` each refuse a non-sequential executor, with a unit test per refusal (child 6). The mode's one claim is
**equivalence**, DET-PORT-1 under PERF-D2 (a backend counts only in a passing parity matrix), proved the way
`tests/integration/kernel/test_executor_equivalence_long.py` proves threads against sequential: the **field-by-field content compare
is the primary check and the canonical hash secondary**, because the digest may omit fields that decisions read
(`TCK-20261103-STATE-DIGEST-MAY-OMIT-FIELDS-THAT-DECISIONS-READ`); zero worker FAILURE no-ops on both arms.

| Child | Level and place | What is new, and why no existing test covers it | Lane |
|---|---|---|---|
| 2 packet cost | none (a measurement) | a size and time record per world; no test layer measures serialization | one-off on the u24 heavy slot, after the owner's review, lead-planner-u24 told first |
| 3 remote manager | unit, `tests/unit/kernel/`: `test_executor_context_parity.py` extended with the remote manager as a third packet consumer | the parity test checks what the packet answers; new is that the answers survive encode and decode | PR, `unit-core-world` |
| 3 | unit: (a) chunk round trip (encode, decode, same results), with a **negative case**: an unknown or missing field, or a version or build mismatch, refuses loudly on decode and never defaults; (b) the dead-worker rule: a timed-out chunk is recomputed locally, identical, never a FAILURE no-op, and the fallback is a **typed counter or record** the test reads (not a log line or reason string); (c) a **late result** arriving after the local recompute is dropped, never applied twice (the regression-prone path) | no test has a network boundary or a timeout; `WorkerManager` has neither | PR, `unit-core-world` |
| 3 | kernel integration, `tests/integration/kernel/`: loopback equivalence (a worker on localhost, no docker) vs `LocalSequentialExecutor` on one world. It **must pass under the medium budget** (60 s alarm, 4 GB) **measured on the slow VM**, with the wall time stated in the PR; if it does not, cut ticks or use a smaller world, **never** mark it `resource_budget_large`. 300 ticks of two arms on `crowded_frontier` is likely already near 60 s, so the tick count is set by that measurement | the long test covers threads only and runs in the slow lane; a PR-time remote arm catches a broken transport early | PR, `integration` |
| 3 | extra_slow: a **sibling file**, remote vs sequential, not a third arm on `test_executor_equivalence_long.py` (its cases sit at the alarm: urban s42 548.7 s locally, frontier s44 alarmed at 601 s). Start with `crowded_frontier` s45 (it carries the known seed cause); more cases only with measured times. **Each new slow-lane test needs testing-planner's sign-off with a measured wall on the slow VM under 540 s**; the slow job is already about 1 h 40 | the same matrix, one more backend: the DET-PORT-1 claim's evidence | `slow-regression.yml` (runs `slow or extra_slow`) |
| 4 compose profile | containerized smoke: the integration case run through the `distributed` profile on one world; `level("kernel_integration")` if it is a pytest | nothing runs compose with an engine worker; `test.yml`'s `docker-build` job builds the image only | a new opt-in workflow or manual dispatch, **platform-planner's call** (not testing's: its globs are `test.yml`, `slow-regression*.yml`, `rpg-gate-report.yml`); kept out of `test.yml` and `slow-regression.yml`; testing-planner reviews its content and placement on request |
| 5 contract docs | none new; existing docs tests (`tests/unit/docs`) keep passing | doc only | PR, `unit-infra` |
| 6 evidence guard | unit: one refusal test each for the gate candidate, paired arms and `rpg_measure`, plus the manifest's executor-mode field | today only policy keeps the mode out of behaviour evidence | PR, the lanes of those tools |

Left out: multi-host networks, tail latency, real container networking beyond one host, and any timing claim.

## 9. Cut lines for children 2 to 5

| # | Child | Owner | Cost (measurement included) | Leaves out |
|---|---|---|---|---|
| 2 | packet-cost measurement | perf-planner | **cheap form:** per-chunk pickled size and encode/decode time on the 3 gate worlds at seed 42, in-process (minutes). **Full form** only if inconclusive: loopback round trip through one worker container (about an hour) | multi-host; contention; tail latency |
| 3 | `RemoteWorkerManager`, transport, rule of §6, the tests of §8 | rpg-planner | code + unit and integration tests; the extra_slow arm adds about 4 x 2000-tick runs to the slow lane | the container (child 4); API reach (§5) |
| 4 | `engine-worker` entry point and the `distributed` profile | platform-planner | image entry point and profile; one containerized smoke run | k8s/Helm; scaling beyond one host |
| 5 | `worker_contract.md` §5 and `infrastructure_overview.md` (the mode; the `ai_worker` wording at `:159`) | docs/engine owner via lead-planner | doc only | everything else |
| 6 | executor-mode field in the run manifest; refusal of a non-sequential executor in the gate candidate (`tools/test_architecture`), paired arms and `rpg_measure`, with a unit test each | testing-planner scopes it (the gate candidate is its domain); `rpg_measure` and the manifest field with rpg-planner | code + 3 small unit tests, no runs | anything beyond refusing; the mode itself |

Order: 6 first (cheap, and it makes the evidence rule a guard before the mode exists), 2's cheap form, then 3, then 4; 5 any time after
child 0 and ubuntu's docs batch. Every child waits for the owner's review.

## 10. Choices for the owner

1. **Dead-worker rule:** local recompute, recorded (recommended), or fail the run on the first timeout.
2. **Selection reach:** CLI and harness only (recommended), or also the API (needs `engine_manager.py:139` to pass an executor).
3. **Transport:** stdlib `multiprocessing.connection` (recommended), unless child 2 shows it is the bottleneck.

## 11. Risks

- **Slower than sequential**, likely; the experiment reports it rather than hides it.
- **Hidden reads outside the packet** (§6 open check): a singleton the worker container loads differently gives a split. The
  long equivalence test is the backstop; the content fingerprint is the guard.
- **Packet-field drift** across a third consumer: covered by keeping one packet builder (§3) and the parity test.
- **Pickle trust boundary** (§4): internal network and `authkey` only.
