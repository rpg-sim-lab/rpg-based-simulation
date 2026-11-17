---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261108-README-DEBUG-RUN-NAMES-AN-ENV-VAR-THE-CODE-NEVER-READS
phase: done
date: 2026-11-08
tags: [documentation, observability]
---

# TCK-20261108-README-DEBUG-RUN-NAMES-AN-ENV-VAR-THE-CODE-NEVER-READS

## Title
The README's full-observability run sets OBS_MODE, which the code never reads, so the command runs in the default LIGHT mode

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Found by lead-planner on 2026-11-08 while preparing the CV bullet 6 note. README.md "Headless CLI mode" shows `OBS_MODE=DEBUG python3 -m src cli --ticks 100 --seed 42   # full observability`.
- `ObservabilityConfig.get_mode` reads only `SIM_OBS_MODE` or `RPG_OBS_MODE` (src/observability/config.py:291) and otherwise returns LIGHT (:298).
- The Makefile's `sim-debug` target uses `SIM_OBS_MODE=DEBUG` (Makefile:183).
- So the README command never enters DEBUG mode. #843 (TCK-20261107-README-OVERVIEW-AND-VERIFICATION-SCOPE) kept the line unchanged and missed it.
- The owner said "yes, proceed" (#715 comment 6711179590).

## Scope
README.md: `OBS_MODE=DEBUG` becomes `SIM_OBS_MODE=DEBUG`.

## Out of Scope
- Other docs: `git grep` found no other bare `OBS_MODE=` under docs/.
- docs/guides/reviewer_replay_check.md:46 "sequential" (lead deferred item D2; not lead-owned).

## Acceptance Criteria
- The README names an env var that `ObservabilityConfig.get_mode` reads.
- No other README change.

## Related Tickets
- TCK-20261107-README-OVERVIEW-AND-VERIFICATION-SCOPE

## Related Docs
- docs/observability/how_to_run_simulation.md

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
src/observability/config.py, Makefile

## Assumptions / Open Questions
None. Checked by reading config.py:284-298. The command was not run.

## Implementation Notes
One-word change.

## Test Summary
Docs-only. Checked by reading config.py:291 and Makefile:183. The command was not run.

## Files Changed
- README.md
- agent-working/tickets/done/TCK-20261108-README-DEBUG-RUN-NAMES-AN-ENV-VAR-THE-CODE-NEVER-READS.md

## Completion Summary
The README's debug run now uses SIM_OBS_MODE, the variable the code reads.
