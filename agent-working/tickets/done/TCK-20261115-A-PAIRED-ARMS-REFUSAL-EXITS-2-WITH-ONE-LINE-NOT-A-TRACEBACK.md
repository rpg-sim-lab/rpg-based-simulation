---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-A-PAIRED-ARMS-REFUSAL-EXITS-2-WITH-ONE-LINE-NOT-A-TRACEBACK
phase: done
date: 2026-11-15
tags: [testing, determinism]
---

# TCK-20261115-A-PAIRED-ARMS-REFUSAL-EXITS-2-WITH-ONE-LINE-NOT-A-TRACEBACK

## Title
An arm that is not runner PINNED, or whose dists differ from its key, is refused with exit 2 and one line, not exit 1 and a traceback

## Status
DONE

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
- [x] AC1: a non-PINNED arm exits 2 with one `REFUSED:` line and a REFUSED verdict, on both the local and the `--collected` path.
- [x] AC2: a dists mismatch does the same.
- [x] AC3: the source-text assertion is gone, and a stub-child test checks where `dists` comes from by behaviour. The PR body shows that test failing when `arm_child` reads `dists` from the arm tree's module.
- [x] AC4: `tests/unit/tools/test_paired_env_key.py`, `test_rpg_measure_collected.py`, `test_paired_arms.py` and `test_arm_child_pinned_check.py` pass. The child hash only moves if `arm_child.py` changes; if it does, the PR body says so.

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
- `paired.main()` gained one clause, `except (NotPinnedArmError, DistsMismatchError) as exc: return _refuse(verdict, str(exc))`, ahead of the existing `BaseException` handler. Only these two classes are caught (rpg-planner's condition 1); the `BaseException` handler is unchanged, so any other error still propagates and the verdict still records REFUSED for it. One clause covers the local path, `--collected`, and both neutral paths, since the errors are raised from `run_arm`, `_collected_runs` and the `refuse_non_pinned` calls under `_run`. The exception classes are kept.
- `arm_child.py` is NOT changed, so the child hash and every paired cache key stay where they are.
- The source-text test is replaced by two behaviour tests that run the real `arm_child.py` as a subprocess against a stub arm tree: the tool-checkout copy sits apart from the arm tree, the arm tree (cwd and PYTHONPATH) carries its own `tools/rpg_measure/env_digest.py` returning another value, and the document's `dists` must be the tool checkout's. A second case copies the real `env_digest.py` and compares with `installed_dists_digest()` in-process.

## Test Summary
- `test_paired_env_key.py`, `test_rpg_measure_collected.py`, `test_paired_arms.py`, `test_rpg_measure.py`, `test_arm_child_pinned_check.py`: 124 passed (`-n 0`, no simulation; the stub child takes 0.3 s).
- Revert evidence, arm_child reading dists through `importlib.import_module("tools.rpg_measure.env_digest")` (the arm tree's copy): both new stub-child tests FAIL (`'FROM-THE-ARM-TREE' == 'TOOL-ONE'`; `'FROM-THE-ARM-TREE' == '6655634d...'`). Restored, they pass.
- Revert evidence, the new `except` clause removed from `main()`: 7 tests FAIL (collected non-pinned x3, collected neutral, local non-pinned, collected dists, local dists), all with the raised error instead of exit 2. Restored, they pass.
- `test_only_the_two_named_refusals_are_mapped_other_errors_still_propagate` pins that an unrelated error still propagates.

## Files Changed
- tools/rpg_measure/paired.py
- tests/unit/tools/test_paired_env_key.py
- tests/unit/tools/test_rpg_measure_collected.py

## Completion Summary
A non-PINNED arm or a dists mismatch now exits 2 with one `REFUSED:` stderr line and a REFUSED verdict, on the local and `--collected` paths, with no traceback and no table. The brittle source-text assertion is replaced by behaviour tests with revert evidence. The child hash does not move.
