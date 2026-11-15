---
status: historical
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING
phase: done
date: 2026-11-15
tags: [platform, architecture, observability, lab-agent]
---

# TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING

## Title
World farm, step one: two worlds run at the same time on one host without sharing an event stream, deleting each other's lab run
data, or interleaving a ledger line.

## Status
DONE

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
Written by platform-implementer under rpg-planner-ubuntu's option (b) (these lines are plumbing; rpg reviews the diff by message before the push ask). Overlap check clear on both hosts (ubuntu: no remote branch or open PR; u24: lead-planner-u24, rpg-planner). No `src/engine/**`, compose, Bible or parity change; no container started; no run over 20 ticks.
1. **One stream per world** (`src/observability/anomaly/worker.py`): new module-level `config_from_env()` builds the worker config with `ObservabilityConfig.get_stream_name()` and `get_redis_url()` (SIM_ then RPG_ then the producer's default), so the worker and the producer agree under SIM_ only, RPG_ only, both and neither. The `__main__` block calls it. With nothing set the name is still `simulation:events`.
   - **Behaviour change, outside compose:** a bare `python -m src.observability.anomaly.worker` with no URL set moves from `redis://redis:6379/0` to the producer's `redis://localhost:6379/0`. Compose sets `SIM_REDIS_URL` explicitly, so the compose stack is unchanged.
2. **Refuse, never delete** (new `src/observability/world_farm_io.py`: `ensure_run_dir_free`, `RunDirectoryInUseError(FileExistsError)`): the lab orchestrator (`ensure_seed_run_dirs_free`, called before the lab dir is created), the sweeper (sweep dir and per-seed run dirs) and the mining controller (experiment dir and per-run dirs, checked before anything is created through a new pure `MiningRunMatrixBuilder.plan_runs`) refuse an existing target. All four `rmtree` calls on these paths are gone (their targets sit inside a directory the same call just refused or created). The up-front check is the early, friendly error; **the exclusive create is the claim** (`claim_run_dir`, `os.makedirs` without `exist_ok`): the orchestrator's per-seed dir, the sweeper's per-run dir and the mining controller's per-run dir are created that way, so two processes given one id cannot both succeed. That also covers the mutation lab's `run_id_prefix` dirs.
3. **Unique default ids** (`src/lab/cli.py`): `default_lab_run_id()` = `labrun_{UTC time}_{pid}_{8 hex}`; a mutation lab started without an id now gets `mutlab_` plus the same suffix (it was `mutlab_{UTC time}`, unique only to the second). A `mutation_lab_id` given by the caller is the caller's choice; re-running a mutation lab under the same id is refused (the per-variant `run_id_prefix` dirs already exist), which is intended.
4. **Found by the work, beyond the plan: the mutation lab shared one run directory across every variant and every mutation lab.** `src/lab/mutation_orchestrator.py` ran every variant under `lab_run_id="lab_run"`, so all of them used `data/runs/run_lab_run_seed_<n>` (the old `rmtree` hid it; two concurrent mutation labs overwrote each other). `ScenarioLabOrchestrator` now takes an optional `run_id_prefix` (a name only) and the mutation lab passes `{mutation_lab_id}_{variant_id}`. The prefix is on the constructor, not on `run_lab`, so `run_lab`'s argument count does not grow.
5. **Append safety** (investigation §3): `append_line` (one `os.write` on an `O_APPEND` fd) is used by `src/lab/audit.py`, `update_simulation_knowledge.py` (decision log) and the anomaly worker's `default` run dir fallback. The old audit append also passed the positive control (it makes the guarantee explicit). Per-run files need nothing once ids are unique; engine, perf and run_ledger files are reported, not changed.
6. **Test hygiene forced by the refusal** (rpg-planner-ubuntu and platform-planner review of bbbcf1cd0 rejected a global cleanup fixture: under `pytest -n auto --dist loadgroup` a time-window cleanup can delete another worker's live run dir). A run directory a test leaves behind is now refused on the next run, so the 14 modules that run labs or sweeps under fixed ids in the shared `data/runs` use the opt-in fixture `remove_named_run_dirs` (`tests/named_run_dirs.py`): before and after each test it deletes exactly the `data/runs/run_<prefix>_seed_*` directories that test's own ids name (`RUN_ID_PREFIXES[test name]` in the module, collected from a recorded run), never by time window, and the fixture is not autouse (`tests/conftest.py` is unchanged). A `chdir` to a private folder was tried first and rejected: relative content paths load lazily, and a registry first loaded from the temp folder came up empty and broke later real-kernel tests.
   - `tests/unit/observability/test_run_index_builder.py` re-ran the same sweep id to regenerate files; that is the reuse now refused, so its second step asserts the refusal and the untouched corrupted run dir. **Lost check:** that the index builder survives a freshly corrupted run. The builder is inline in `ScenarioSweeper.run_sweep` (not callable alone), so it is not exercised now. Filed by rpg-planner-ubuntu as
     TCK-20261115-SWEEP-RUN-INDEX-BUILDER-CANNOT-BE-CALLED-ON-ITS-OWN
     (extract it into a callable so the corrupted-run check can return).
7. **Docs:** `docs/guides/simulation_quality.md` (one stream per world; the Redis URL default change), `docs/simulation/lab_contract.md` (run ids, refuse rule, append rule), and the regenerated `docs/performance/wall_clock_inventory.{md,json}` (reads moved into named functions; line numbers in the table refreshed).

## Test Summary
- **observed (this host, ubuntu):**
  - New tests: `tests/unit/observability/test_world_farm_io.py` (5; two spawn processes x 500 rows, a fifth of them over 8 KiB: 1000 lines all `json.loads`, none lost), `tests/unit/lab_agent/test_audit_concurrent_append.py` (2 x 200 audit rows), `tests/unit/observability/test_stream_name_resolution.py` (T1-T3, 4 env cases x name and URL, two worlds, the default), `tests/unit/lab/test_lab_run_id_uniqueness.py` (T4, T5), `tests/integration/observability/test_world_farm_run_id_rules.py` (T6 sweep and mining refusals, T7 the same seed under two sweep ids gives the same final state hash, 20 ticks).
  - Scoped suites (`tests/cli tests/unit/lab tests/integration/lab tests/unit/lab_agent tests/integration/lab_agent tests/unit/observability tests/integration/observability tests/integration/test_anomaly_worker_failure.py tests/certification/test_artifact_budget.py tests/unit/content/test_content_usage_matrix.py`): 1680 passed, 6 skipped under CI's own flags `-n 2 --dist loadgroup -m "not slow and not extra_slow"` (pytest-xdist 3.8.0, the version in `uv.lock`, installed into a private scratchpad folder and put on `PYTHONPATH` for these runs only), run TWICE back to back with no seed run dir and no mutation lab folder left behind (the second run proves reruns are safe), and earlier serially (1642 and 1679 passed). The serial runs of the 14 patched modules also leave the shared `data/runs` empty of `_seed_` dirs.
  - `tests/architecture tests/static`: pass. Perf inventories in sync (20 passed), REGISTRY no-drift and paths guard pass.
- **slow test, run once by itself:** `tests/integration/lab/test_species_relations_metamorphic_validation.py` (about 5 minutes; it passes here and on a plain `origin/main` snapshot). **Robustness gap in that test (rpg's):** it writes a temporary `human_to_human` row into the tracked `data/content/social/species_relations.yaml` and restores it in a `finally`; when the process is killed it stays dirty, and the next run then fails its non-vacuity guard (`assert (True, True) == (False, True)`). My own killed run did this; the file was confirmed to differ by exactly that row and restored with `git checkout --`. Passed on to rpg.
- **not run here (environment):** `tests/codebase` code-health family (47 failures) needs `ruff`, `mypy_baseline`, `ast-grep` from the `lint` dependency group, which this venv lacks. I ran the repo's pinned `ruff==0.17.0` through `uvx --from ruff==0.17.0 ruff check` (a download of that one pinned tool) on every edited `src` file: the new file has no findings, no edited file gained one (orchestrator 33 -> 32, the rest unchanged). The CI `Code health` job is the first real run of the ratchet.
- No simulation result changes: nothing in `src/engine` or the tick changed; T7 shows the id is a name only.

## Files Changed
- `src/observability/world_farm_io.py` (new), `src/observability/anomaly/worker.py`, `src/observability/sweeper.py`, `src/observability/mining/controller.py`, `src/lab/cli.py`, `src/lab/orchestrator.py`, `src/lab/mutation_orchestrator.py`, `src/lab/audit.py`, `src/lab/workflows/update_simulation_knowledge.py`.
- Tests: the five new files above, `tests/lab_run_dir_cleanup.py` (new), `tests/conftest.py` (one import), `tests/unit/observability/test_run_index_builder.py` (second step).
- Docs: `docs/guides/simulation_quality.md`, `docs/simulation/lab_contract.md`, `docs/performance/wall_clock_inventory.{md,json}`, `docs/REGISTRY.yaml`.
- `agent-working/`: the investigation (section 3 classification), the child-4 ticket's child-3 citations (ride-along for platform-planner).

## Completion Summary
Closed: implemented, reviewed by message (rpg-planner-ubuntu: OK on the follow-up, platform-planner: F1 to F5 resolved) and green locally; the PR review comment is recorded after the PR opens.

Limits (stated, not hidden):
- **What the claim leaves open:** (1) the kernel side, `create_run_directory(..., overwrite=True)` (`src/engine/run_identity.py:33-35`). After `claim_run_dir` the kernel still gets an explicit id and replaces the directory we just claimed; if that replace is remove-then-create there is a short window where the path does not exist and a second claimer of the same id could create it and then lose it. That also covers anything that reaches it directly without the lab, sweeper or mining controller. Filed by rpg-planner-ubuntu as
  TCK-20261115-AN-EXPLICIT-RUN-ID-DELETES-AN-EXISTING-RUN-DIRECTORY
  (its only caller is `kernel.py:188`, reached by the lab, sweep and mining builders, plus `readiness/harness.py:105`, `calibrate_simq.py:309`, `rpg_gate_run` and `arm_child`); this ticket only names it. (2) A per-seed `data/runs` dir whose prefix is not tied to a claimed dir: closed for the mutation lab by the exclusive per-seed create, open for any new caller that builds its own `run_{x}_seed_{n}` path.
- **Redis URL default (behaviour change outside compose):** the anomaly worker now uses the producer's resolvers, so a bare `python -m src.observability.anomaly.worker` with no `SIM_REDIS_URL`/`RPG_REDIS_URL` moves from `redis://redis:6379/0` to the producer's `redis://localhost:6379/0`; compose sets `SIM_REDIS_URL` explicitly and is unchanged.
- **Appends:** one `os.write` on an `O_APPEND` fd keeps lines whole on a local Linux filesystem; this is not guaranteed on network filesystems (NFS and similar).
- **Lost test check:** the index builder against a freshly corrupted run (above; TCK-20261115-SWEEP-RUN-INDEX-BUILDER-CANNOT-BE-CALLED-ON-ITS-OWN).
- **Known test-isolation limit:** a test must not `chdir` to a temp folder and then run the engine, because the content catalog loads lazily from relative paths and would be cached empty for the rest of the worker; such tests use unique ids and the named cleanup instead.
- **Not run here:** the `tests/codebase` code-health family (needs `ruff`, `mypy_baseline`, `ast-grep`); CI Code health is the first real ratchet run. Pinned `ruff==0.17.0` via `uvx` showed no new finding on any edited `src` file.
- `docs/performance/wall_clock_inventory.{md,json}` were regenerated by the tool (no hand edits); `modules_reachable_from_kernel` 501 -> 506 is drift on main, not this change: the set is identical (506) at `dd9c7c54f`, at `origin/main` and in this tree.
