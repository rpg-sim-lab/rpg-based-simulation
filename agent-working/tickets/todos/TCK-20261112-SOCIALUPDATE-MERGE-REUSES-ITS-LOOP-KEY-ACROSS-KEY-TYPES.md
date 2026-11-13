---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261112-SOCIALUPDATE-MERGE-REUSES-ITS-LOOP-KEY-ACROSS-KEY-TYPES
phase: open
date: 2026-11-12
tags: []
---

# TCK-20261112-SOCIALUPDATE-MERGE-REUSES-ITS-LOOP-KEY-ACROSS-KEY-TYPES

## Title
SocialUpdate carries 6 mypy errors: merge reuses one loop variable across int-keyed and str-keyed dicts

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
This is a follow-on from TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS. The split moved SocialUpdate unchanged into src/core/update_models/social.py, and its 6 baselined mypy errors went with it. They were re-keyed in codebase/baselines/mypy_baseline.txt under #715 6813426261 (S5), and that ruling made fixing them a separate ticket (lead-planner-u24, 2026-11-12). rpg-planner filed it the same day.

The errors (social.py:96, 97, 100 and 101):
- 2 × `Incompatible types in assignment (expression has type "str", variable has type "int")`;
- 2 × `Invalid index type "int" for "dict[str, float]"`;
- 2 × `No overload variant of "get" of "dict" matches argument types "int", "float"`.

A read of SocialUpdate.merge (social.py:80-106) shows the probable cause. One loop variable `k` is reused across several `for k, v in … .items()` loops. The trust and grudge dicts are keyed by int, and the place-attachment and regional-reputation dicts by str. mypy fixes `k`'s type from the first loop and flags the later ones. At runtime, each loop rebinds `k`, so the merge looks correct. That makes this a typing defect, not a behaviour defect. Confirm that before fixing.

## Scope
1. Confirm the cause: the key types of each delta dict, from the field annotations on SocialUpdate.
2. Fix with behaviour-neutral renames only: a distinct, correctly typed loop variable per loop, or a small typed helper.
3. Remove the 6 lines from mypy_baseline.txt. The baseline must shrink, never be re-keyed again. `make typecheck-py` must pass.
4. Add a unit test that merges two SocialUpdates with entries in every delta dict and checks the sums. Add it only if no existing test already covers it; cite the test if one does.

## Out of Scope
- Any change to merge semantics, or to SocialUpdate's fields.
- The other SocialUpdate mypy or ruff findings, if any.

## Acceptance Criteria
- The 6 errors are gone, and mypy_baseline.txt is 6 lines shorter.
- The merge test passes. No other test changes.
- The diff touches only social.py (renames), mypy_baseline.txt and the test.

## Related Tickets
- TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS (where this was found)

## Related Docs
- docs/plans/codebase_health/handoffs/handoff_to_rpg.md (mypy debt)

## Related Stored Artifacts
- None.

## Related Code Areas
- src/core/update_models/social.py (SocialUpdate.merge)
- codebase/baselines/mypy_baseline.txt

## Assumptions / Open Questions
- The cause is a reading of the code, not yet confirmed against the field annotations.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
