---
status: active
layer: platform
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING
phase: open
date: 2026-11-15
tags: [platform, architecture, observability, lab-agent]
---

# Investigation: world farm, step one

Code-derived on origin/main `0a8f65c3f`, 2026-11-15, by platform-planner. rpg-planner-ubuntu checked the first three cites independently
(2026-11-15).

## 1. Stream name and Redis URL

- The producer side goes through `ObservabilityConfig`:
  - `get_stream_name()` (`src/observability/config.py:324-326`) resolves SIM_STREAM_NAME, then RPG_STREAM_NAME, then
    `simulation:events`;
  - `get_redis_url()` (`:319-321`) resolves SIM_REDIS_URL, then RPG_REDIS_URL, then `redis://localhost:6379/0`.
- `src/observability/stream/factory.py:31` and `src/simulation_quality/feed.py:67` already use `get_stream_name()`.
  - The quality feed also has its own `QUALITY_STREAM_NAME` override (`feed.py:137`). It stays: it is an explicit consumer override,
    not a second default.
- **The gap:** the anomaly worker's `__main__` (`src/observability/anomaly/worker.py:416-421`) reads its settings directly:
  - `SIM_STREAM_NAME` with default `simulation:events`, and no RPG_ fallback;
  - `SIM_REDIS_URL` with default `redis://redis:6379/0`, and no RPG_ fallback, and a different default from the producer's.
- The consumer group and the DLQ follow the stream name (`stream/consumer.py:36,66`). Two streams therefore get separate groups and
  separate DLQs with no extra change.
- **Compose:** `compose.yaml:50,109` set `SIM_REDIS_URL=redis://redis:6379/0` explicitly on backend and ai_worker, and set no stream
  name. So inside compose nothing changes when the worker switches to the shared resolvers.
  - Outside compose, a bare `python -m src.observability.anomaly.worker` with no env would move from `redis://redis:6379/0` to
    localhost. That is the producer's default, and the fix intends it: the producer and its consumer agree.
- The worker logs its whole config (`worker.py:423`). Today the URL carries no credential. If a password URL is ever used, that log
  line prints it. This is noted for the plan, not fixed here.

## 2. Run ids and directory deletion

- `src/lab/cli.py:155-157`: when no `--lab-run-id` is given, the lab defaults to `labrun_{%Y%m%d_%H%M%S}`. **Two lab runs started in
  the same second get the same id.**
- `src/lab/orchestrator.py:171-174` (and `:287`): `run_{lab_run_id}_seed_{seed}` under `data/runs/`, and `rmtree` if it exists. Then
  `:271-274`: `rmtree` of `<lab run dir>/runs/<run_id>` before copying in.
- `src/observability/sweeper.py:125`: `run_{sweep_id}_seed_{seed}`; `:236-239` `rmtree`s the target copy.
- `src/observability/mining/controller.py:98,114`: `run_{experiment_id}_seed_{seed}[_rep_N]`, with a copy step at `:254`.
- **The kernel is the other half, in `src/engine` (not changed here):** `src/engine/run_identity.py:create_run_directory`.
  - With an explicit id (`is_default=False`), it calls `repo.create_run(run_id, manifest, overwrite=True)`: "an explicit run id may
    replace its own directory (the caller named it)".
  - A default id never overwrites (TCK-20261011-DEFAULT-RUN-ID-CANNOT-COLLIDE-ACROSS-SAME-SEED-PROCESSES).
  - So the farm's guarantee has to come from the callers: they must never hand the kernel an explicit id that another live run holds.
- **The run id feeds no seed, RNG draw or hash:**
  - `run_identity.py`'s docstring says "The run id is a name only: it is in no state hash and draws nothing from the simulation RNG".
  - The explicit-id branch of `create_run_directory` returns before any `rng` use.
  - `new_run_id(rng)` (default ids only) is a keyed, stateless `get_int(Domain.INIT, ...)` draw, so it moves no other draw.
  - The lab, sweeper and mining builders pass explicit ids, so their id text never reaches the RNG.
  - The implementer confirms this with a test: the same seed under two different lab run ids gives the same final hash.
- **Readers of the format:** a grep of `src/`, `frontend/src` and `tools/` for `_seed_` and `run_{` finds only the builders above. No
  reader parses `run_..._seed_...` back into parts. The implementer re-runs this grep, adding `tests/` and the lab's
  `repository.py`/`store.py` (which validate `lab_run_id` but do not parse it), before changing anything.

## 3. Append-mode files

- The only explicit `O_APPEND` single-write writer is `tools/test_architecture/run_ledger.py:281-283` (testing's file). It is
  process-safe for one row per `os.write`.
- Python text-mode `open(..., "a")` writes go through a buffer. A line longer than the buffer, or a flush that spans lines, can reach
  the file as more than one `write` syscall. Two processes appending to the **same** file can then interleave inside a line.
- Candidates found (`open(..., "a")` in `src/` and run tooling). The implementer classifies each as per-run (inside one run's
  directory, so never shared) or shared:

| File | Writer | First read |
|---|---|---|
| `src/lab/audit.py:135` | lab audit log | likely shared across lab runs |
| `src/lab/workflows/update_simulation_knowledge.py:205` | knowledge decisions | likely shared |
| `src/observability/understanding/review/store.py:32` | review store | check |
| `src/observability/anomaly/worker.py:350` | anomaly output | check (per run id?) |
| `src/simulation_quality/persistence.py:26` | quality jsonl | check |
| `src/observability/event_recorder.py:112`, `reporting/metric_recorder.py:350`, `cognition/*`, `personality/recorder.py:114` | per-run recorders | likely per run |
| `src/domains/campaigns/narrative_ledger.py:137` | narrative ledger | check |
| `src/engine/kernel.py:828,912` | violations | per run; **src/engine: report only, no change** |
| `tools/perf/tripwire.py:309` | summary | perf's; report only |

- A shared file gets the single-`os.write`-on-`O_APPEND` rule (the run_ledger pattern), or a per-process file. A per-run file needs
  nothing once run ids are unique (§2).
- Anything in `src/engine`, `tools/perf` or `tools/test_architecture` is reported to its owner, not changed.

### Classification (implementer, 2026-11-15)

1. `src/lab/audit.py` (`audit_log.jsonl`, one file per lab session): shared only by processes that log to the same session. It now goes through `append_line` (one `os.write` on an `O_APPEND` fd). **This makes the guarantee explicit; the old code passed the positive control too**: the old open-write-close per call, run under two spawn processes with rows over 8 KiB, also gave 400 parseable lines. So no bug was seen here, and the new test (`tests/unit/lab_agent/test_audit_concurrent_append.py`) pins the rule.
2. `src/lab/workflows/update_simulation_knowledge.py` (`decision_log.jsonl` in the knowledge store): shared across sessions. Same helper.
3. **Shared by default, a real gap:** `src/observability/anomaly/worker.py:_write_anomaly_to_file` writes under the run dir `default` when no run id is set (`status_record.current_run_id or "default"`), so two worlds without a run id share `default/anomaly_events.jsonl`. It goes through `append_line` in the same change as the stream-name edit to that file.
4. Per run, nothing to do once run ids are unique: the review store, `quality_scores.jsonl` (`simulation_quality/persistence.py`, a long-lived handle inside the run dir), the event, metric, cognition and personality recorders. The sweeper's default id is already unique (`sweep_{time}_{uuid6}`); only an explicit `sweep_id` or mining `experiment_id` can collide (the sweeper used `makedirs(exist_ok=True)` and mining never checked), so both get the refuse rule.
5. Report only, no change: `narrative_ledger.py` (the caller passes the path), `src/engine/kernel.py:828,912` (engine; per run), `tools/perf/tripwire.py:309` (perf's), `tools/test_architecture/run_ledger.py` (already one `os.write` on `O_APPEND`; testing's).

## 4. Overlap

- No open PR touches these files.
- 29 old origin branches from 2026-10-14 to 10-20 (including `rpg-d80b` and `rpg-d80c`) differ on at least one. They look like
  squash-merge remnants.
- The implementer re-checks on both hosts before its first edit.
