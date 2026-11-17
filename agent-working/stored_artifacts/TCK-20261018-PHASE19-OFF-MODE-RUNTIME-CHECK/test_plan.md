---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK
phase: done
date: 2026-11-01
tags: [testing, architecture]
---

# TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK: test_plan

AC1: OFF test passes on main after #803 (7 passed). AC2: injection test per module; ON control loads all four. AC3: codebase follow-on is not in this change. Guards: probe asserts the resolved mode equals the requested mode so a bad SIM_OBS_MODE cannot pass silently.

## Proof Plan
- level: architecture test (fresh subprocess, real Kernel on sandbox_world)
- proof kind: runtime sys.modules assertion with ON-mode control and injected-import negative control
- oracle source: rpg-planner condition on #547 and the four c06 ignore_imports edges in codebase/structure/importlinter.toml
- expected effect: OFF loads none of the four; ON loads all four; an unguarded import in a scratch kernel.py fails the OFF check
- selected commands: `pytest tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py -q`
