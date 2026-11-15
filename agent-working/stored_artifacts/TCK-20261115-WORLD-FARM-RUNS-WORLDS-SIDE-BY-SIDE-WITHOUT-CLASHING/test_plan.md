---
status: active
layer: platform
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING
phase: open
date: 2026-11-15
tags: [platform, architecture, observability, lab-agent]
---

# Test plan: world farm, step one

All tests are unit or small integration tests: no engine runs over 50 ticks, no containers, no Redis server (fakeredis or the
in-memory adapter, whichever the existing stream tests use).

| # | Test | Covers |
|---|---|---|
| T1 | resolver parity: under SIM_ only, RPG_ only, both, and neither, the anomaly worker's config and `ObservabilityConfig` give the same stream name and the same Redis URL (4 cases x 2 values) | AC1 |
| T2 | two worlds, two stream names: events produced under name A are not read by a consumer on name B, and B's DLQ name is `B:dlq` | AC2 |
| T3 | default: with nothing set, every resolver gives `simulation:events` | AC2 |
| T4 | lab default id: two ids made in the same second differ (patch the clock) | AC3 |
| T5 | lab refuse: a second orchestration with an existing `lab_run_id` raises, and the first run's files are byte-identical afterwards; no `rmtree` is called (patched) | AC3 |
| T6 | sweeper and mining: the same refuse test against an existing target dir | AC3 |
| T7 | the run id is a name only: the same world and seed under two different lab run ids give the same final state hash (a short run, at most 50 ticks) | AC5 |
| T8 | per shared append file: two `multiprocessing` writers append 2,000 rows each, with some rows longer than 8 KiB; every line parses with `json.loads`, and the count is 4,000 | AC4 |

Scoped commands, plus the CI command for the touched test dirs:
- `pytest tests/unit/observability tests/unit/lab -q` (adjust to the dirs the new tests land in);
- `pytest -m "not slow" tests/integration -k "lab or stream or sweeper or mining" -q`;
- `ruff check` on the touched files;
- `pytest tests/tools/test_agent_working_paths_guard*.py` before the push.

Not tested: concurrent worlds per host under load (blocker 4, perf's), and the subprocess launch (blocker 5).
