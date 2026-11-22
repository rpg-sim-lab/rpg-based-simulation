---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD
phase: done
date: 2026-11-22
tags: []
---

# TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD

## Title
The person-attack trace launcher writes no runner.json: its bookkeeping step imports the kit from the caller's directory, not from the kit

## Status
DONE

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

## Durable state, lifecycle and clocks
N/A: a launcher bookkeeping fix in read-only trace tooling; no simulation state, no src/ change and no clock is touched.

## Implementation Notes
Fixed in the combined kit (head 83a752cde), shipped by the kit + evidence PR of TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES. `tools/rpg_measure/person_attack_launch.sh`: every kit Python call goes through one function `kitpy` (`cd "$KIT"` and `PYTHONPATH="$KIT"`); the runner.json step is `write_runner_record` (it calls `person_attack_run.write_record`, which writes the file and reads it back) inside `finish_record`, which turns a failed write into `STATUS=RECORD_NOT_WRITTEN` and `RC=6`, so a missing record is never COMPLETE; `LAUNCH_RECORD_ONLY=1` runs that step alone, from the caller's directory, as the control. The stage-2 launcher (`subject_trace_launch.sh`) carries the same rule from the start.

## Test Summary
`tests/tools/test_person_attack_kit.py::test_the_stage_1_runner_record_is_written_from_a_cwd_outside_the_kit_and_a_failed_write_is_never_complete` (AC1: run from a cwd outside the kit, `<OUT>/runner.json` is written and the kit `python -c` disk check also works there; AC2: an unwritable record gives exit 6 and `STATUS=RECORD_NOT_WRITTEN RC=6`), plus `test_write_record_names_the_twin_equality_and_every_return_code_of_the_plan` and `test_every_stage_1_kit_python_call_goes_through_kitpy`; for stage 2 `test_the_runner_record_is_written_from_a_cwd_outside_the_kit`, `test_a_runner_record_that_cannot_be_written_exits_non_zero_and_says_so`, `test_every_kit_python_call_in_the_launcher_goes_through_kitpy_and_a_failed_record_is_never_complete`. AC3 (the control fails without the fix) by mutation, run and recorded: replacing `kitpy` by a bare interpreter call (no cd, no PYTHONPATH) makes the cwd-outside-the-kit control fail; replacing the `RECORD_NOT_WRITTEN` handling by a no-op makes the failed-write control fail. `pytest tests/tools/test_person_attack_kit.py tests/tools/test_subject_trace_kit.py` -> 127 passed (`--basetemp` on /data).

## Files Changed
tools/rpg_measure/person_attack_launch.sh, tools/rpg_measure/person_attack_run.py (`write_record`, `plan_for`), tools/rpg_measure/subject_trace_launch.sh, tests/tools/test_person_attack_kit.py, tests/tools/test_subject_trace_kit.py: all new in this PR (part of the trace kit; the fix is in the kit's first merge to main, not a patch to an existing file).

## Completion Summary
All three acceptance criteria are met at kit head 83a752cde: (1) the launcher started from a directory other than the kit writes `<OUT>/runner.json` (control above); (2) a failed write gives RECORD_NOT_WRITTEN and RC 6; (3) the controls fail on the defective forms (mutation). The real evidence: the stage-1 full run (`/data/vboxuser/o3-trace-runs/83a752cdebb64a20224b764727b41a76f08adaa5/stage1/run`, SEAL 60c1cb69b692e5e28fc08428a4a435f71ca32ae9c45076fbe8c8eb06b5c88404) wrote a real runner.json, sha256 b160fe534d919dfca998ef81a528b3a878af083f852ff87163d660cc8d779e35 (status COMPLETE, 12 of 12 return codes 0, twin_equal true for all six cells), and the stage-2 run wrote its own. Not touched, as scoped: the sealed cd3a76430 run, whose runner.json was never written and is never regenerated.
