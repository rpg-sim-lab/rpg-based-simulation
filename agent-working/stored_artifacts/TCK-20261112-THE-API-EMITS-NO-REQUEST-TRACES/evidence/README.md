---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261112-THE-API-EMITS-NO-REQUEST-TRACES
artifact_type: report
tags: [observability, api-design]
---

# Evidence

- `crowded_frontier_42.json`, `time.txt`: the branch cell (crowded_frontier s42, 5000 ticks, head ad460cc67, PYTHONHASHSEED=0). `final_hash` e0e20c2044d7ca861ace880ef6495a411074680571a1d4bf90bee091b52c8e35 equals the reference from cd83111c5 (identical src/data/config to main 5e58ae857), `/mnt/data2/rpg-measure/results/cd83111c5-72320cac-5000/crowded_frontier_42.json`. Peak RSS 179,628 kB, 7m36s.
- `mypy_rcs.txt`, `mypy_time2.txt`: mypy with pipefail on b010fac0b: mypy rc 1 (baseline exists), baseline filter rc 0 with 0 new errors; 1,276 raw errors against 1,338 baseline rows; 802 source files; peak 467,580 kB.
- `lanes_verdicts.txt`, `lanes_time.txt`: `ci_lanes --run --all` (1h07m, peak 1,387,168 kB). Lane failures and their causes are in the ticket's Test Summary.
- `rerun_summary.txt`, `failing_toolsae.txt`: the reruns. The 26 tests/codebase failures are identical on a detached worktree of origin/main c73d76bad and on the branch tree (missing ruff, ast-grep, prek in the dev-only venv).
