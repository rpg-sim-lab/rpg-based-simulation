---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261112-SOCIALUPDATE-MERGE-REUSES-ITS-LOOP-KEY-ACROSS-KEY-TYPES
phase: done
date: 2026-11-12
tags: []
---

# TCK-20261112-SOCIALUPDATE-MERGE-REUSES-ITS-LOOP-KEY-ACROSS-KEY-TYPES

## Title
SocialUpdate carries 6 mypy errors: merge reuses one loop variable across int-keyed and str-keyed dicts

## Status
DONE

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
- The cause was a reading of the code; it is now confirmed against the field annotations (see Implementation Notes).

## Implementation Notes
Cause confirmed from the field annotations on SocialUpdate: `trust_delta` and `grudge_delta` are `Dict[int, float]`, `place_attachment_delta` and `regional_reputation_delta` are `Dict[str, float]`. `merge()` used one name `k` for all the delta loops, so mypy fixed `k` as `int` at the trust loop and then flagged the two str-keyed loops: 2 assignment errors (`k` str -> int), 2 invalid-index errors and 2 `get()` overload errors.
Fix: the two str-keyed loops now use `region_id` (4 lines renamed in `src/core/update_models/social.py`); the int-keyed loops keep `k`. No behaviour change. Approved under S4: #715 6843079519.

## Test Summary
- Existing coverage: `test_regional_reputation_delta_merges_by_summing_per_region` (tests/unit/social/test_relationships.py) covers regional_reputation_delta only. Added `test_merge_sums_every_keyed_delta_dict_with_its_own_key_type` for the trust, grudge, place-attachment and combat-loss dicts; it passes both before and after the rename (checked by stashing the fix), as a behaviour-neutral change should.
- tests/unit/social/test_relationships.py, test_rejection_counts_kept.py and tests/unit/core/test_social_counts.py: 34 passed.
- `mypy src/ | mypy_baseline filter` (pipefail, raw output kept): 1276 -> 1270 errors, none in update_models/social.py; filter rc 0. `codebase.health check`: OK, 0 worse.

## Files Changed
src/core/update_models/social.py (4 lines: loop variable renames); codebase/baselines/mypy_baseline.txt (-6 lines, the 6 social.py entries, no re-key); tests/unit/social/test_relationships.py (+1 test); this ticket.

## Completion Summary
Done. The 6 mypy errors in SocialUpdate.merge are gone and mypy_baseline.txt is exactly 6 lines shorter. Behaviour-neutral renames only; no field, default or merge rule changed.
Play-neutral proof: plain 5000-tick cells on a git archive of eca569282 (pinned runner, PYTHONHASHSEED=0, MemoryMax 1G): crowded_frontier s42 e0e20c2044d7 and frontier_marches s42 908eb3bb1441, identical to main's references. Ref chain: #901's cells proved those hashes on its final src (9bb59824a), and main's src, data and config equal that reviewed head (`git diff --name-only 9bb59824a origin/main -- src data config` is empty); peaks 191 and 252 MB.
Known gap: the cells cover crowded_frontier s42 and frontier_marches s42 only.
Known gap: `make knowledge-index-update` not run: worktrees use main's index; lead-planner-u24, 2026-11-12.
