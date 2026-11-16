---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-AN-ARM-RUNS-WHEN-THE-CACHE-PATH-IS-RELATIVE
phase: open
date: 2026-11-16
tags: [testing, determinism]
---

# TCK-20261116-AN-ARM-RUNS-WHEN-THE-CACHE-PATH-IS-RELATIVE

## Title
An arm runs when the cache path is relative: the child gets the arm tree as an absolute path, so the off-host paired-arms jobs can import `src`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
On 2026-11-16, T2 AC1's first off-host dispatch failed: paired-arms.yml run 43790499533, on tool ref `paired-ac1-tool-f94417e6f` (owner #715 6905354304). All 9 arm jobs failed about 2 s into the "Base arm" step with this error:
`RuntimeError: arm run failed (4eaab4d8b0a0 crowded_frontier 42): ... arm_child.py", line 104 ... from src.engine.checkpoint import CanonicalStateHasher / ModuleNotFoundError: No module named 'src'`.
The cause: the workflow passes `--cache arm-cache`, a relative path. `paired.run_one` starts the child with `cwd=tree` and `PYTHONPATH=str(tree)`. That `tree` string is the relative path `arm-cache/trees/<sha12>`, so it resolves a second time from inside the tree, where nothing exists. A script does not put its cwd on `sys.path`, so `src` is not importable.
The local AC1 run (step 1, PASS) used the absolute cache `/mnt/data2/rpg-measure`, so it never hit this. The unit tests all use the absolute `tmp_path`. paired-arms.yml had never run end to end before this dispatch.
Local `paired.py --cache <relative>` has the same bug.

## Scope
1. `paired.run_one`: pass the child an absolute tree, both `cwd` and `PYTHONPATH` from `tree.resolve()`. That way a relative cache works on every path: local, `run-arm`, and anywhere `prepare_tree` returns a relative tree.
2. `tools/test_architecture/paired_arms.py run-arm`: resolve `--cache` once at argument parsing as defence in depth, so the cost and env files land at the same absolute place.
3. Tests, all with a relative cache under `monkeypatch.chdir(tmp_path)`:
   - (a) `run_one` with a stub arm tree whose `src` package the child needs to import. It succeeds, and it FAILS on f94417e6f's `run_one`. Show that revert in the Test Summary.
   - (b) `paired_arms run-arm` with a relative `--cache` and only the child faked. It writes the result, cost.json and env.json under the resolved cache.
   - (c) An absolute cache behaves byte-for-byte as before: the same result path and the same env.json.

## Out of Scope
- Changing `arm_child.py`, the cache key, env8 or any refusal. `child_hash()` must not move.
- Re-dispatching the workflow. That needs a separate owner ask after this merges, with the AC10 tool-commit question attached (see Assumptions).

## Acceptance Criteria
- [ ] AC1: a relative cache runs an arm on the local path and on the `run-arm` path. The tests in Scope 3 pass and the revert evidence is recorded.
- [ ] AC2: `arm_child.py` is unchanged and `child_hash()` equals its value at f94417e6f. The PR body says the cache keys do not move.
- [ ] AC3: `test_paired_arms.py`, `test_paired_env_key.py`, `test_rpg_measure_collected.py`, `test_rpg_measure.py` and `test_arm_child_pinned_check.py` pass. Unit tests only, `-n 1` at most.

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (parent T2. AC1's off-host run is blocked by this.)
- TCK-20261115-A-PAIRED-ARMS-REFUSAL-EXITS-2-WITH-ONE-LINE-NOT-A-TRACEBACK (#928, the last change to paired.py)

## Related Docs
- `.github/workflows/paired-arms.yml` (`--cache arm-cache`)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/rpg_measure/paired.py` (`run_one`, `prepare_tree`)
- `tools/test_architecture/paired_arms.py` (`run-arm`)

## Assumptions / Open Questions
- `paired.py` is an rpg_measure tool. I'm asking rpg-planner to confirm that testing builds this and rpg-planner reviews it, the same arrangement as #928.
- AC10 (one fixed tool commit for both the local and CI sides) is open for the owner. The local PASS used f94417e6f with an absolute cache. For an absolute path, `tree.resolve()` returns the same path, so the local outputs do not depend on this fix. The choice:
  - (A) re-run the local step on the post-fix commit, about 2.2 h of host time, and keep AC10 strict;
  - (B) amend AC10 to say the two tool commits may differ only by this fix, then dispatch on the post-fix commit and compare against the existing local table.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
