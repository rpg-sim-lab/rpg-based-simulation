---
status: active
layer: platform
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING
phase: open
date: 2026-11-15
tags: [platform, architecture, observability, lab-agent]
---

# Plan: world farm, step one

The implementer is platform-implementer. rpg-planner-ubuntu reviews the src lines by message before the push ask (its option (b),
2026-11-15). platform-planner reviews the PR. There are no runs, no container starts and no `src/engine` edits.

## Steps

1. **Overlap check:** re-run the branch and PR check of investigation §4 on both hosts (u24 through lead-planner). Stop if a live
   branch edits the same lines.
2. **Anomaly worker resolvers** (`src/observability/anomaly/worker.py:416-421`):
   - set `stream_name=ObservabilityConfig.get_stream_name()` and `redis_url=ObservabilityConfig.get_redis_url()`;
   - leave the backend and consumer group as they are;
   - keep the import at module top (ruff PLC0415);
   - if the `__main__` block can't be imported in a test, move the config build into a small module-level function
     (`config_from_env()`) the test calls.
3. **Unique lab ids** (`src/lab/cli.py:155-157`): the default id gets the process id and a short non-seeded nonce, the same shape
   as `default_run_id`: `labrun_{%Y%m%d_%H%M%S}_{pid}_{uuid8}`. This is a name only (investigation §2).
4. **Refuse, never delete** (`src/lab/orchestrator.py`):
   - the rule is to refuse;
   - before the seed loop, if `data/runs/run_{lab_run_id}_seed_{seed}` or the lab run dir already exists for this id, the
     orchestration fails with a clear error naming the id and the existing path, and deletes nothing;
   - remove the two `rmtree` calls (`:173-174`, `:272-273`) and the twin at `:287`.
   - **Why refuse and not auto-rename:** an explicit id is the caller's name for the run, and a silent rename would break anything
     that looks the run up by that name. The default id (step 3) is what makes concurrent runs collision-free.
5. **Sweeper and mining** (`src/observability/sweeper.py:125,236-239`; `mining/controller.py:98,114,254`): the same refuse rule for
   an existing target. If either has no id default that can collide, say so in the ticket and cover it with the same test anyway.
6. **Append files** (investigation §3): classify each row.
   - Shared files in rpg's `src/` get the single `os.write` on an `O_APPEND` fd.
   - Report the rest to their owners (engine to rpg, perf to perf, run_ledger to testing). Change nothing in those owners' files.
   - If every shared file is already safe, item 3 closes on the classification and the test.
7. **Docs:** run `python3 tools/gate_checks/docs_search.py` (or doc-updater) for "SIM_STREAM_NAME", "lab_run_id" and "lab run id",
   and update the docs it names (at least `docs/guides/simulation_quality.md`'s env table if it lists the stream).
8. **Close:** this is hand-orchestrated, so record it with `record_hand_orchestrated_closure.py --tier standard`, then run
   `done_checker_static.py`, the mechanism advisory, and `make docs-registry`; stage `agent-working/agent-monitoring/`.

## Scope guards

- No `src/engine/**` edit. `run_identity.py`'s `overwrite=True` for explicit ids stays, and the lab refuses before it reaches the
  kernel.
- No compose change. If one turns out to be needed, stop and ask platform-planner: compose edits go from `.claude/worktrees/platform`
  only, and `docker compose up` must not change.
- No Bible or parity entry. If a simulation law turns up, stop and ask rpg-planner-ubuntu.
- No edit to `tools/test_architecture/**` without testing-planner's OK.

## Acceptance map

| AC | Step |
|---|---|
| 1, 2 | 2 |
| 3 | 3, 4, 5 |
| 4 | 6 |
| 5 | guards; test_plan T7 |
| 6 | 7 |
| 7 | guards |
