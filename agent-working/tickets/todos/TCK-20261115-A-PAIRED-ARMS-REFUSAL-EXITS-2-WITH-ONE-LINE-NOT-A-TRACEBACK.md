---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-A-PAIRED-ARMS-REFUSAL-EXITS-2-WITH-ONE-LINE-NOT-A-TRACEBACK
phase: open
date: 2026-11-15
tags: [testing, determinism]
---

# TCK-20261115-A-PAIRED-ARMS-REFUSAL-EXITS-2-WITH-ONE-LINE-NOT-A-TRACEBACK

## Title
An arm that is not runner PINNED, or whose dists differ from its key, is refused with exit 2 and one line, not exit 1 and a traceback

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
These are non-blocking follow-ups from rpg-planner-ubuntu's review of #927 (comment 927#6894210385), relayed by lead-planner-u24 on 2026-11-15.
In `tools/rpg_measure/paired.py`, `refuse_non_pinned` raises `NotPinnedArmError` and `refuse_wrong_dists` raises `DistsMismatchError`. Nothing in `main()` catches either one.
A caller therefore gets exit 1 and a Python traceback. Every other refusal in the same file goes through `_refuse()`: exit 2, a `REFUSED:` line on stderr, and `outcome=REFUSED` in the verdict document. The module docstring also says refusals exit 2.
A second, smaller item: `tests/unit/tools/test_paired_env_key.py::test_the_arm_child_writes_dists_from_the_tool_checkouts_own_module` checks for a literal string in the source of `arm_child.py`. The test is brittle. Any reformatting breaks it, and it does not prove the behaviour.

## Scope
1. In `paired.main()`, catch `NotPinnedArmError` and `DistsMismatchError` on both the local path and the `--collected` path. Map each one to `_refuse(verdict, detail, message)`, which exits 2, prints one `REFUSED:` line naming the arms, and writes a verdict with `outcome=REFUSED`. Keep the exception classes so direct callers and tests can still use them.
2. Tests: for each of the two errors, on the local and the collected path, check exit 2, a stderr line that starts with `REFUSED:`, no traceback, a verdict file with `outcome: REFUSED`, and no table printed. The existing `pytest.raises` tests that call the function directly stay.
3. Replace the source-text test with a behavioural one. Run `arm_child` with a stub world, the same way the other stub-child tests do. Check that the `dists` in the arm document equals `env_digest.installed_dists_digest()` loaded from the tool checkout. Then check that changing the tool-checkout module's output changes the document, which proves the arm tree's copy is not the one being used.

## Out of Scope
- Changes to the env8 key, the dists digest, or what gets refused. Only the exit path changes.
- The AC9 spy hook (held until ubuntu's HOLD-LINE hook lands).

## Acceptance Criteria
- [ ] AC1: a non-PINNED arm exits 2 with one `REFUSED:` line and a REFUSED verdict, on both the local and the `--collected` path.
- [ ] AC2: a dists mismatch does the same.
- [ ] AC3: the source-text assertion is gone, and a stub-child test checks where `dists` comes from by behaviour. The PR body shows that test failing when `arm_child` reads `dists` from the arm tree's module.
- [ ] AC4: `tests/unit/tools/test_paired_env_key.py`, `test_rpg_measure_collected.py`, `test_paired_arms.py` and `test_arm_child_pinned_check.py` pass. The child hash only moves if `arm_child.py` changes; if it does, the PR body says so.

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (parent T2, inprogress)
- TCK-20261115-PAIRED-ARMS-EVIDENCE-SETS-NEED-THEIR-REPEAT-AND-ONE-LOCKED-ENVIRONMENT (#927, introduced DistsMismatchError)
- TCK-20261115-A-NON-SEQUENTIAL-RUN-IS-REFUSED-BY-THE-GATE-CANDIDATE-PAIRED-ARMS-AND-RPG-MEASURE (#924, introduced NotPinnedArmError)

## Related Docs
- `tools/rpg_measure/paired.py` module docstring (refusal = exit 2)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/rpg_measure/paired.py` (`refuse_non_pinned`, `refuse_wrong_dists`, `main`, `_refuse`)
- `tests/unit/tools/test_paired_env_key.py`

## Assumptions / Open Questions
- RESOLVED 2026-11-15 (rpg-planner): testing-implementer builds this fix, and rpg-planner reviews the PR by comment. rpg-planner approves the design only, not the merge. The testing approval path governs landing.
- rpg-planner's conditions: (1) the refusal semantics stay exactly as they are. Only these two errors are mapped to `_refuse`, and there is no broad `except` in `main()`. (2) The stub-child test must fail when `arm_child` takes `dists` from anywhere other than the tool checkout's own module. The PR shows it failing on revert. (3) Host: run pytest with `-n 1` at most. No heavy local run without first checking with rpg-planner; HOLD stage 2 holds the host.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
