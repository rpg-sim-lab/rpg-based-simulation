---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261112-REGISTRY-REGEN-SKIPPED-BY-A-STALE-HOOK-OR-AN-UNTRACKED-DOC
phase: done
date: 2026-11-12
tags: [delivery, process-improvement]
---

# TCK-20261112-REGISTRY-REGEN-SKIPPED-BY-A-STALE-HOOK-OR-AN-UNTRACKED-DOC

## Title
The registry auto-regen is skipped when the installed post-commit hook is a stale copy, or when an untracked doc without frontmatter makes `generate_registry.py --check` return 1

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Finding by lead-planner-u24, 2026-11-12. Lane B (worktree `nonflight`, branch rpg-non-flight-free-swing) merged main twice,
at cd83111c5 and a56267bfd. Both merges were finished with `git commit` (the reflog says "commit (merge)"). `docs/REGISTRY.yaml`
was left stale, and CI failed `test_generate_registry.py::test_check_flag_detects_no_drift_against_real_registry` on #884
head a56267bfd. Scoped by agent-working-planner-u24. Lead decision 2026-11-12: file (B) plus a warn-only (A) as one hotfix.
Lead placed the unowned `tools/generate_registry.py` with agent-working for this edit. The lead has already done (0): it
ran `make install-hooks` in the main checkout, and the shared hook now matches main's script byte for byte.

Cause 1 (verified):
- The shared `.git/hooks/post-commit` was the #865 copy, installed 2026-11-11 11:41.
- #873 (6394c49ff) later made the reindex step opt-in and stopped its failure from ending the hook (`|| echo`). Nothing
  re-installed the hook: `codebase/hooks/install_git_hooks.py` keeps any post-commit hook that isn't byte-identical, and
  only `make install-hooks` overwrites it.
- In `nonflight`, knowledge.db exists and the merge touched 35 docs or ticket paths. The old hook therefore ran
  `knowledge_search.py build --incremental` with the system python3, which has no sentence_transformers. The build returned
  1 (`cmd_build_incremental`, the dependency guard), and `set -e` ended the hook before the registry block ran.

Cause 2 (verified in the main checkout):
- `generate_registry.py --check` returns 1 when any doc on disk lacks frontmatter, including an untracked doc that
  `_drop_unindexable` would leave out of the registry anyway.
- The main checkout's untracked `docs/guides/read.md` has no frontmatter, so `--check` returns 1 there.
- Both hooks treat any return code other than 2 as "skip", so the regen is skipped silently.

## Scope
1. **(B) `tools/generate_registry.py`:** count a doc frontmatter error only when its path would be indexed: in
   `indexable_paths(root)`, or in `include`. When `indexable_paths` returns None (not a git checkout), every path counts, as
   today. Apply the filter at both the `--check` short-circuit and the write path, so the two agree.
2. **(A, warn-only) `tools/delivery/pre_push_advisory_hook.py`:** add check F. If
   `$(git rev-parse --git-common-dir)/hooks/post-commit` exists and differs from HEAD's
   `tools/hooks/post-commit-reindex.sh`, warn and suggest `make install-hooks`. It never blocks. A missing hook says nothing.
   Any error says nothing, the same rule as checks A-E.
3. **Tests:**
   - (B), 2 tests in `tests/tools/test_generate_registry.py`:
     - an untracked doc with no frontmatter: `--check` returns 0 when in sync and 2 when drifted, never 1;
     - a tracked doc with no frontmatter still returns 1.
   - (A), 2 tests in `tests/tools/test_delivery_pre_push_advisory.py`:
     - an installed hook that differs from the script warns;
     - an identical hook, or no hook at all, says nothing.

## Out of Scope
- The shim that execs the worktree's own script. It needs codebase's `install_git_hooks.py`. If the warning proves too
  weak, raise the shim as a finding for codebase.
- Running `make install-hooks` on any host. u24 is done by the lead; ubuntu goes through the ubuntu lead.
- Making any check block. Changing the post-merge hook's return-code rule.
- `docs/guides/read.md` and the other untracked docs in the main checkout (the owner's files).

## Acceptance Criteria
1. The 4 new tests pass. The existing `test_generate_registry.py` (including the real-tree drift test) and
   `test_delivery_pre_push_advisory.py` pass unchanged.
2. Run in the main checkout as it stands (untracked `docs/guides/read.md`), `generate_registry.py --check` returns 0 or 2,
   not 1.
3. Check F adds no more than one `git rev-parse` and one file compare to the hook's 60 s budget.
4. Scoped tests only, never the full `pytest tests/`.

## Where it rides
No-code rule (#715 6793205403): this ticket changes tool behaviour, so it isn't a ride-along. The agent-working track has no
open PR, so it stands alone. If an agent-working implementation PR opens first, it rides that PR instead.

## Related Tickets
- TCK-20261111-REGISTRY-REGEN-MISSES-A-MERGE-FINISHED-BY-COMMIT (#865; the post-commit regen block, and the `set -e` edge
  noted in review 865#6786597253)
- TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY (check E)
- TCK-20261005-REGISTRY-REGEN-INDEXES-UNTRACKED-FILES-FROM-THE-WORKING-TREE (indexable_paths)
- TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED (#873; the opt-in reindex)

## Related Docs
- docs/guides/delivery_process.md (pre-push advisory)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/generate_registry.py (`generate_registry`, `indexable_paths`, `_drop_unindexable`),
  tools/delivery/pre_push_advisory_hook.py, tools/hooks/post-commit-reindex.sh (reference, unchanged), tests/tools/

## Assumptions / Open Questions
- Simpler-fix check (6698958617): (B) is one filter and the cheapest fix for cause 2. A warn-only (A) is the cheapest
  durable signal for cause 1; the shim is better but costs a codebase installer change. No measurement runs. Leaves out:
  hosts that never run a pre-push (the warning only fires on push), and rebase and cherry-pick (CI only).

## Implementation Notes
Dispatched by agent-working-planner-u24; S4 record #715 6813037927 (read by me). (B) generate_registry.py: after `_drop_unindexable`, doc_errors keep only paths in `indexable_paths | include`; None (not a git checkout) keeps every error. One filter before the `--check` short-circuit, so the check and write paths agree. (A) check F `check_installed_post_commit_current` in pre_push_advisory_hook.py, wired into `run_all_checks`: one `git rev-parse --git-common-dir`, one `git show HEAD:tools/hooks/post-commit-reindex.sh`, one file compare (HEAD's script, not the worktree's, so uncommitted edits do not count); warn-only; missing hook or any error says nothing.

## Test Summary
4 new tests: TestUntrackedDocWithoutFrontmatter x2 in test_generate_registry.py (untracked bare doc: --check 0 in sync and 2 when drifted, never 1; tracked bare doc: 1 on both check and write) and 2 check-F tests in test_delivery_pre_push_advisory.py (differing hook warns; identical hook, no hook, or git error silent). Scoped, single process: test_generate_registry.py, test_delivery_pre_push_advisory.py and test_post_commit_registry_regen.py, 101 tests, all pass once the registry carries this ticket (the real-tree drift test failed only while the staged ticket was missing from docs/REGISTRY.yaml, and passes after close). By hand, read-only: the main checkout's own script returns 1 (untracked docs/guides/read.md); this branch's fixed script run with --root on the main checkout against its docs/REGISTRY.yaml returns 0.

## Files Changed
tools/generate_registry.py; tools/delivery/pre_push_advisory_hook.py; tests/tools/test_generate_registry.py; tests/tools/test_delivery_pre_push_advisory.py; this ticket; docs/REGISTRY.yaml; W46 shards.

## Completion Summary
An untracked doc without frontmatter no longer turns `generate_registry.py --check` into exit 1, so both hooks regenerate when the registry drifts. Pre-push check F warns when the installed post-commit hook differs from HEAD's script. Known gap: hosts that never run a pre-push see no warning; the exec shim stays with codebase.
