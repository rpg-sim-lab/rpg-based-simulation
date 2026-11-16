---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-AN-ARM-RUNS-WHEN-THE-CACHE-PATH-IS-RELATIVE
phase: done
date: 2026-11-16
tags: [testing, determinism]
---

# TCK-20261116-AN-ARM-RUNS-WHEN-THE-CACHE-PATH-IS-RELATIVE

## Title
An arm runs when the cache path is relative: the child gets the arm tree as an absolute path, so the off-host paired-arms jobs can import `src`

## Status
DONE

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
1. `paired.run_one`: pass the child an absolute tree, both `cwd` and `PYTHONPATH` from `tree.resolve()`, and an absolute `out` (`out.resolve()`, since the child runs with cwd=tree; rpg-planner ask 1). Only path resolution changes. The env keys, `PYTHONHASHSEED` and the argv order stay exactly as they are (rpg-planner ask 2). That way a relative cache works on every path: local, `run-arm`, and anywhere `prepare_tree` returns a relative tree.
2. `tools/test_architecture/paired_arms.py run-arm`: resolve `--cache` once at argument parsing as defence in depth, so the cost and env files land at the same absolute place.
3. Tests, all with a relative cache under `monkeypatch.chdir(tmp_path)`:
   - (a) `run_one` with a stub arm tree whose `src` package the child needs to import. It succeeds, and it FAILS on f94417e6f's `run_one`. Show that revert in the Test Summary.
   - (b) `paired_arms run-arm` with a relative `--cache` and only the child faked. It writes the result, cost.json and env.json under the resolved cache.
   - (c) An absolute cache behaves byte-for-byte as before: the same result path and the same env.json.
   - (d) `run_one` given a relative `out` writes the result at the caller-relative location, not inside the tree.

## Out of Scope
- Changing `arm_child.py`, the cache key, env8 or any refusal. `child_hash()` must not move.
- Re-dispatching the workflow. That needs a separate owner ask after this merges, with the AC10 tool-commit question attached (see Assumptions).

## Acceptance Criteria
- [x] AC1: a relative cache runs an arm on the local path and on the `run-arm` path. The tests in Scope 3 pass and the revert evidence is recorded.
- [x] AC2: `arm_child.py` is unchanged and `child_hash()` equals its value at f94417e6f. The PR body says the cache keys do not move.
- [x] AC3: `test_paired_arms.py`, `test_paired_env_key.py`, `test_rpg_measure_collected.py`, `test_rpg_measure.py` and `test_arm_child_pinned_check.py` pass. Unit tests only, `-n 1` at most.
- [x] AC4 (B1, testing-planner review): `paired-arms.yml` has an optional `div` input (default `-`), passed to the compare step as `--div "${DIV}"`, so the CI table header and watch rows carry the step's div. `div` is a LABEL only (rpg-planner): it feeds no verdict, threshold or bar. With no input the output is exactly as before (`(div -)`, `| - |`); with `div=2.204` the verdict.json bytes are identical and the table differs only in the label. Pinned by `test_ci_paired_arms_workflow_shape.py` and the end-to-end test.
- [x] AC5 (B2): one end-to-end test runs the workflow's own commands in sequence in relative-cwd temp dirs (plan, every arm job, the Collect step in real bash, `assemble`, `paired --collected`), exit 0.

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
- RESOLVED 2026-11-16 (rpg-planner): testing builds this, and rpg-planner reviews the design before the push, the same arrangement as #928. rpg-planner does not object to option (B) below. Its reasons: for an absolute path, `resolve()` is the identity except for symlinks, `/mnt/data2/rpg-measure` has none, and the child_hash-equal assertion covers it. The owner row must say that the local table was run at tool f94417e6f, before the fix, and why the path change cannot move its hashes.
- AC10 (one fixed tool commit for both the local and CI sides) is open for the owner. The local PASS used f94417e6f with an absolute cache. For an absolute path, `tree.resolve()` returns the same path, so the local outputs do not depend on this fix. The choice:
  - (A) re-run the local step on the post-fix commit, about 2.2 h of host time, and keep AC10 strict;
  - (B) amend AC10 to say the two tool commits may differ only by this fix, then dispatch on the post-fix commit and compare against the existing local table.

## Implementation Notes
- `paired.run_one` resolves `tree` and `out` to absolute paths before the child starts (cwd, PYTHONPATH and the `out` argv are all absolute). `out` matters too: the child's cwd is the tree, so a relative `out` was written inside the tree and the parent never found it. Path resolution only: env keys, `PYTHONHASHSEED` and the argv order are unchanged.
- `paired_arms run-arm` resolves `--cache` once at argument parsing.
- A second bug found while testing the CLI path, fixed in the same change: `run-arm` printed `cost['cached']`, a key `run_arm` never returns, so every `run-arm` raised `KeyError: 'cached'` AFTER the arm had finished and its files were written (the job would have failed even with the path fix). The console line now says `cached` when the recorded wall is 0.0 (a cached arm records no wall and no RSS). The cost file and `run_arm`'s return value are unchanged (an existing test holds them equal).
- `arm_child.py` is unchanged: `child_hash()` is still `9d13c131`, asserted in a test, so no cache key moves (the AC1 keys `4eaab4d8b0a0-9d13c131-5000-aa066c26` stay valid).

## Test Summary
- New `tests/unit/tools/test_paired_relative_cache.py` (6 tests): run_one with a relative tree and out, absolute paths unchanged, relative out lands where the caller means, `run-arm` with a relative cache, the same key for an absolute and a relative cache, `child_hash() == "9d13c131"`. The stub child imports `src` from the stub arm tree.
- 146 passed (`-n 0`, unit and static only) across the new file, test_paired_arms, test_paired_env_key, test_rpg_measure_collected, test_rpg_measure, test_arm_child_pinned_check and test_ci_paired_arms_workflow_shape.
- Revert evidence: with `paired.py` at f94417e6f, `test_run_one_runs_an_arm_whose_tree_and_out_are_relative` FAILS with `ModuleNotFoundError: No module named 'src'` (the CI failure), and `test_a_relative_out_lands_where_the_caller_means_not_inside_the_tree` FAILS (`arm run failed`). With `paired_arms.py` at f94417e6f, both `run-arm` tests FAIL (the CLI path). The `run-arm` tests pass with only the paired.py revert because the parse-time resolve already makes the cache absolute (defence in depth, as the ticket intends).

- Added after review: (B1) the `div` input and `--div "${DIV}"` in `.github/workflows/paired-arms.yml`; (B2) `tests/unit/tools/test_paired_arms_workflow_end_to_end.py`. The test PARSES the arm steps, the assemble step and the compare command from the yml (`${VAR}` expanded from the job env) and runs them in-process, so the commands cannot drift; the Collect step runs as real bash. Retyped, because they are bash scripts with arrays: the `plan` arguments, and the artifact-name template is read from the upload step with its expressions filled in. Stubs: the arm child (writes a fixed valid document) and `prepare_tree` (no git); `run_one` is the real one in a real subprocess.
- End-to-end revert evidence: with `paired.py` at f94417e6f AND the `--cache` parse-time resolve removed, the test FAILS with `arm run failed` (the CI failure); with `paired_arms.py` at f94417e6f it FAILS with `KeyError: 'cached'`. With only `paired.py` reverted it passes, because the parse-time resolve covers it (the two layers). Removing `--div "${DIV}"` from the compare step FAILS the div test and the static shape test.
- 180 passed (`-n 0`): the new end-to-end file, test_paired_relative_cache, test_paired_arms, test_paired_env_key, test_rpg_measure_collected, test_rpg_measure, test_arm_child_pinned_check, the workflow shape test and the two workflow-guard tests.

## Files Changed
- .github/workflows/paired-arms.yml
- tests/unit/tools/test_paired_arms_workflow_end_to_end.py
- tests/static/test_ci_paired_arms_workflow_shape.py
- tools/rpg_measure/paired.py
- tools/test_architecture/paired_arms.py
- tests/unit/tools/test_paired_relative_cache.py

## Completion Summary
A relative `--cache` (the workflow's `arm-cache`) now runs an arm on the local and `run-arm` paths, and `run-arm` no longer crashes after finishing an arm. `arm_child.py` is unchanged, so the cache keys do not move.
