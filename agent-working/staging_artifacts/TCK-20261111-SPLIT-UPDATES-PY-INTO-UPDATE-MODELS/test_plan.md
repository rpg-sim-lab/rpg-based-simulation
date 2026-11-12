---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS
artifact_type: test_plan
phase: open
date: 2026-11-12
tags: []
---

# Test plan

Behaviour-neutral refactor: no new test rows. Proof of neutrality:
1. AST check: every moved definition equals main's, ignoring docstrings (0 missing, 0 extra, 0 differing).
2. Unit suites at -n 1: tests/unit/core, tests/unit/social, tests/unit/kernel/test_executor_context_parity.py, the faction-write-path and lodged_in guards, the cognition-bundle guard, the four checkpoint tests; then the engine and combat suites.
3. `mypy_gate`; `codebase.health check` with the changed-file list; the mechanism-registry changed-code advisory at close.
4. Plain 5000-tick runs, final hash equal to main 5e58ae857 on crowded_frontier s42 and frontier_marches s42 (908eb3bb1441), one process at a time, after rpg-planner gives HOST FREE.
5. Import compatibility: every moved name still imports from `src.core.updates`.
