# M1-base record scripts (u24 copies, rpg-designer approved)

These are the exact scripts that record M1-base on u24 (owner #715 6912633288; method recorded by lead-planner-u24). They are byte-identical to the approved copies on u24 (`*_approved` in /mnt/data2/rpg-measure). Another host copies them unchanged, then edits ONLY the host-local lines below. Its adapted copies get their own shas, and rpg-designer reviews them with a line diff against these.

| File | sha256 (approved) | Host-local lines (change for another host) |
|---|---|---|
| keep_events_child.py | 651ffc9f70f2b69519f890668d0bbd51bd663cbcb564e07291d4dda2d360bf23 | :15 `EVENTS_ROOT`; :21 the default `M1BASE_TOOL_ROOT` (tool checkout path) |
| fill_cache.py | ba741299a34a3a4b4ec1f193db68f0200e9dbda81ba520c3b16b10a0bd202651 | :10 `TOOL`, :11 `BASE`, :15 `GATE` (paths); the pinned shas of the other three files; :96 `MemoryMax=3500M` (memory cap) |
| run_m1base.sh | c059700f98a75b9a43c445e0c391aa450f8dd29a74b617ec2aaf629502ba5a44 | :4 `BASE`, :5 `TOOL`, :6 `PY` (the interpreter; env8 keys on it); the cache via `RPG_MEASURE_CACHE` |
| busy_gate.sh | 94fe052a081312d8a95d87992b61fe8e251ba8f62af265e7ae2b1f3d85acc293 | :8 `RPG_PROJECT_PATHS`; :10 and :14 the 3500 MB memory floor |

Two lessons are built in:
- paired.py `run_arm(repeat=True)` unlinks and reruns repeat arms, so the assembler step uses `--collected`, which executes nothing;
- `tools/rpg_measure/arm_child.py` deletes its run dir (:147), so the wrapper MOVES it to events/ for the offline SimQ read after D80C.

## busy_gate v2 (2026-11-16, rpg-designer approved)
`busy_gate_v2.sh`, sha256 f35f1f9178a961c3f274327021584d1ec5407b9bc74e6fc1a79eb7a74f3dc4a9: adds `keep_events_child` to RPG_HEAVY_WORDS, so a running M1-base cell is visible to other runners' gates. `fill_cache` is deliberately NOT listed (it calls the gate itself). The recorded M1-base used v1 (94fe052a); fill_cache.py pins v1, so a rerun bumps that pin under review.
