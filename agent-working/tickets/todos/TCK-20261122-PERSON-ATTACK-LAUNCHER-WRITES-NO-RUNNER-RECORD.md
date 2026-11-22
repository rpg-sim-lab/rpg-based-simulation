---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD

## Title
The person-attack trace launcher writes no runner.json: its bookkeeping step imports the kit from the caller's directory, not from the kit

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
In the O3 5000t trace (GO #715 7073542579, kit cd3a76430, OUT
`/data/vboxuser/o3-trace-runs/cd3a76430c63e12e45ffdfc4486c411861f304e5/run`), all 12 processes ran and
the seal is valid, but `<OUT>/runner.json` was never written. The launcher's runner.json block
(`tools/rpg_measure/person_attack_launch.sh`, after the cell loop) runs
`"$PY" -c 'from tools.rpg_measure import person_attack_run ...'` without `cd "$KIT"` or
`PYTHONPATH="$KIT"`, unlike every other kit Python call in that script (for example the children at
launch.sh:91). It imported the `tools` package of whatever directory the launcher was started from
and failed: `ImportError: cannot import name 'person_attack_run' from 'tools.rpg_measure'
(.../worktrees/rpg-ubuntu/tools/rpg_measure/__init__.py)` (launcher.log:30-33). RC and status were
unaffected, so the run reported COMPLETE with the record missing. Neither the preflight nor
`LAUNCH_DRY_RUN=1` reaches that block, so no check caught it. Reported by rpg-implementer-ubuntu,
verified by rpg-planner-ubuntu and lead-planner. Lead-planner asked for it to be filed for the next kit.

## Scope
- Run the runner.json block with `cd "$KIT" && PYTHONPATH="$KIT"`, the same as the other kit calls.
- If runner.json cannot be written, set a non-COMPLETE status (for example `INCOMPLETE_RUNNER_RECORD`)
  and a non-zero RC, so a missing record is never reported as COMPLETE.
- A control that runs the bookkeeping block from a directory other than the kit (for example a
  temporary cwd with its own `tools/` package) and asserts that runner.json is written.

## Out of Scope
- The sealed run dir of the cd3a76430 trace: it is never edited and runner.json is never regenerated
  inside it. Whether its twin equality is read from the sealed cell JSONs and summary.json instead is
  rpg-designer's ruling.
- The kit head the designer approved (cd3a76430): the fix lands on the next kit only.

## Acceptance Criteria
1. The launcher started from a directory other than the kit writes `<OUT>/runner.json`.
2. A failed runner.json write gives a non-COMPLETE status and a non-zero RC.
3. The new control fails on the current launcher and passes on the fixed one.

## Related Tickets
- TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES

## Related Docs
- tools/rpg_measure/person_attack_kit_note.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES/rpg_designer_o3_kit_answers_2026-11-21.md

## Related Code Areas
- tools/rpg_measure/person_attack_launch.sh
- tests/tools/test_person_attack_kit.py

## Assumptions / Open Questions
- The next trace kit of this kind also carries lead-planner's future-kit ideas (two processes at a
  time, dropping the plain twins), which need their own decision. This fix does not depend on them.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
