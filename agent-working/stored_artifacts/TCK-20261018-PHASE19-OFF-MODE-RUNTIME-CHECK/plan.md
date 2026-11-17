---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK
phase: done
date: 2026-11-01
tags: [testing, architecture]
---

# TCK-20261018-PHASE19-OFF-MODE-RUNTIME-CHECK: plan

File: tests/architecture/test_phase19_off_mode_imports_none_of_the_four.py (new). A fresh-subprocess probe builds a Kernel from sandbox_world seed 42 (PROD_SMALL), runs one tick_once and shutdown, and reports the kernel's resolved obs mode and which of the four modules are in sys.modules. Tests: OFF loads none; LIGHT control loads all four; an unguarded import injected into a scratch copy of src/ (never the repo) is caught, once per module; the module list equals the four kernel ignore_imports edges in importlinter.toml c06. No src edits. Codebase follow-on (name the test in the toml phase19 comment) stays with testing-planner.
