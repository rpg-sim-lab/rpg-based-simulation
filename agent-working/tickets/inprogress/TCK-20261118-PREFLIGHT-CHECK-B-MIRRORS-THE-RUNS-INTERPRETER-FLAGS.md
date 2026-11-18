---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261118-PREFLIGHT-CHECK-B-MIRRORS-THE-RUNS-INTERPRETER-FLAGS
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-PREFLIGHT-CHECK-B-MIRRORS-THE-RUNS-INTERPRETER-FLAGS

## Title
Preflight check (b) mirrors the run's interpreter flags

## Status
INPROGRESS

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Check (b) hard-coded `python -I`, so a kit whose real run uses PYTHONPATH = the tree (no `-I`) failed (b) falsely (lane A's failreason move spy). rpg-planner direction: (b) imports with the run's flags.

## Scope
- `import_flags` per process, defaulting to the leading flags of its own `entry`; explicit override allowed; a non-`{python}` entry keeps `-I`.
- README: the count_path rule, the (b) flag rule, the tree-writes line (fixture runs use cwd = the tree; a kit writing data/runs writes into it, so the S9 `diff -rq` excludes data/runs).

## Out of Scope
Reporting tree writes automatically; any src change.

## Acceptance Criteria
- Entry without -I + PYTHONPATH = tree passes (b); entry with -I and no sys.path fix still fails (b); explicit import_flags overrides.
- tests/unit/tools/test_kit_preflight.py passes alone.

## Related Tickets
TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN

## Related Docs
tools/rpg_measure/README.md

## Related Stored Artifacts
None.

## Related Code Areas
tools/rpg_measure/kit_preflight.py, tests/unit/tools/test_kit_preflight.py

## Assumptions / Open Questions
Dated before 2026-11-19, so no durable-state section is required (tooling, no src).

## Implementation Notes
Flags are the leading `-x` tokens after `{python}`; options that take a value (`-X dev`) need an explicit `import_flags`.

## Test Summary
Pending the host run.

## Files Changed
tools/rpg_measure/kit_preflight.py, tools/rpg_measure/README.md, tests/unit/tools/test_kit_preflight.py, this ticket.

## Completion Summary
Pending.
