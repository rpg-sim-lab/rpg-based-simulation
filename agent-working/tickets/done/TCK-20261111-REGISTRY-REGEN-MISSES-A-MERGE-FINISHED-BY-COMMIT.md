---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261111-REGISTRY-REGEN-MISSES-A-MERGE-FINISHED-BY-COMMIT
phase: done
date: 2026-11-11
tags: [delivery, process-improvement]
---

# TCK-20261111-REGISTRY-REGEN-MISSES-A-MERGE-FINISHED-BY-COMMIT

## Title
`docs/REGISTRY.yaml` isn't regenerated when a merge stops on another conflict and is finished with `git commit`, and pre-push check E skips a branch whose only registry-relevant change is `docs/REGISTRY.yaml`

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Finding by architecture-planner-u24 via lead-planner-u24: merge 27d1cebe1 on architecture-next-generation-engine-epic
dropped about 400 lines of main's `docs/REGISTRY.yaml` entries; a push check caught it and it was fixed by hand. Drafted by
agent-working-designer-u24 (main checkout
`.claude/handover/drafts/registry-regen-misses-a-merge-finished-by-commit-2026-11-11.md`, §1, §2 and Addendum). Lead
accepted §1 + §2 as one agent-working hotfix and placed the unowned `tools/hooks/` path with agent-working for this fix.
Dispatch waits for the owner's go (lead asks).

Cause: the `registry-regen` merge driver is `true` (keep ours). Regeneration happens only in the post-merge hook
(`tools/hooks/registry_post_merge_regen.sh`), and git runs post-merge only when `git merge` itself makes the commit. A merge
that stops on any conflict and is finished with `git commit` runs the commit hooks instead, so the registry keeps the "ours"
side. Pre-push check E (`tools/delivery/pre_push_advisory_hook.py::check_registry_fresh`, TCK-20261024) runs
`generate_registry.py --check` only when `origin/main...HEAD` changes a `.md` under the registry source roots, so a branch
with no doc/ticket `.md` of its own that merges main badly (three-dot diff shows only `docs/REGISTRY.yaml`) gets no warning.

## Scope
1. **Hook.** Append a merge-only block to `tools/hooks/post-commit-reindex.sh` (the one post-commit file both
   `make install-hooks` and `codebase/hooks/install_git_hooks.py` install; a second post-commit hook would be overwritten or
   refused). Guard: `git rev-parse -q --verify HEAD^2` and `tools/generate_registry.py` present. Run
   `generate_registry.py --check`; only on rc == 2 (same rule as the post-merge hook; other codes left alone) regenerate,
   `git add docs/REGISTRY.yaml`, commit `auto-regenerate docs/REGISTRY.yaml after merge`, and echo
   `[registry-post-commit] ...`. The draft §1 has the block. Idempotent: if post-merge already ran, `--check` returns 0;
   the regen commit has one parent, so it can't loop.
2. **Check E.** In `check_registry_fresh`, also trigger when the three-dot diff contains `docs/REGISTRY.yaml` itself. Still
   warn-only, never blocks. Adjust the warning text so it is true for that case too (today it says "this branch changes docs
   or tickets").
3. **Tests** (`tests/tools/`):
   - Hook, 3 cases: a temp git repo with a stub `tools/generate_registry.py` (`--check` exits 2 until it has run once),
     running the real `post-commit-reindex.sh` with `bash` (reindex part a no-op: no knowledge.db): a two-parent merge
     commit made with `git commit` gets exactly one regen commit; a non-merge commit does nothing; `--check` exiting 0 does
     nothing.
   - Check E, 2 cases in `tests/tools/test_delivery_pre_push_advisory.py`: a diff with only `docs/REGISTRY.yaml` and
     `--check` exit 2 warns; the same diff with exit 0 says nothing.

## Out of Scope
- CLAUDE.md driver wording (draft §3): lead routes it to the ubuntu lead (ubuntu holds those After Work lines, #715
  6720445592).
- Any blocking pre-push check; CI on backup pushes.
- Rebase and cherry-pick (stay covered by CI's Registry re-sync gate only).
- Regenerating in `prepare-commit-msg` (draft "Not proposed").
- Clones that never ran `make install-hooks` (existing per-clone limit).

## Acceptance Criteria
1. The 3 hook tests and 2 check-E tests pass.
2. Existing `tests/tools/test_delivery_pre_push_advisory.py` and `tests/codebase/test_code_health_install_git_hooks.py`
   cases pass unchanged (the latter pins the installed post-commit file; if it compares bytes against the source, it must
   still pass with the appended block).
3. Scoped tests only; never full `pytest tests/`.

## Related Tickets
- TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY (done; check E)
- TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX (done; the driver and post-merge hook)
- TCK-20260925-CLAUDE-MD-REGISTRY-DRIVER-SERVER-SIDE-CAVEAT (done; CLAUDE.md driver caveat)

## Related Docs
- docs/guides/delivery_process.md (pre-push advisory, registry driver)

## Related Stored Artifacts
- Designer draft (main checkout): `.claude/handover/drafts/registry-regen-misses-a-merge-finished-by-commit-2026-11-11.md`

## Related Code Areas
- tools/hooks/post-commit-reindex.sh, tools/hooks/registry_post_merge_regen.sh (reference, unchanged),
  tools/delivery/pre_push_advisory_hook.py, tests/tools/

## Assumptions / Open Questions
- Simpler-fix check (6698958617): the hook block is the cheapest fix that covers the path; the check-E condition is one
  `or` in the `feeds` test. No measurement runs. Leaves out rebase/cherry-pick and clones without installed hooks.
- `tools/hooks/` is unowned; lead placed it with agent-working for this fix only.

## Implementation Notes
Dispatched by agent-working-planner-u24; owner go #715 6786488899 (read by me). The merge-only block is appended to tools/hooks/post-commit-reindex.sh exactly as in the draft §1. Check E: `feeds` also accepts the path `docs/REGISTRY.yaml`; the warning now reads "changes docs, tickets or docs/REGISTRY.yaml and the registry is stale" and keeps the `make docs-registry` / `git add docs/REGISTRY.yaml` instructions (an existing test pins them). Warn-only. The hook's `[registry-post-commit]` line goes to stderr when git runs it from `git commit`.

## Test Summary
New tests/tools/test_post_commit_registry_regen.py (3: conflicted merge finished with git commit gets exactly one regen commit with one parent; non-merge commit does nothing; --check rc 0 does nothing) and 2 check-E tests in test_delivery_pre_push_advisory.py (REGISTRY-only diff: rc 2 warns, rc 0 silent). Scoped, single process: the new file plus test_delivery_pre_push_advisory.py 28 passed. tests/codebase/test_code_health_install_git_hooks.py: 37 of 50 in the three-file run passed; its 13 failures are the host's missing `prek` ("prek not found"), the same 13 that failed before this change and passed in CI on #856; the post-commit byte-compare test is among them and compares the installed file against the same source, so the appended block cannot change its outcome.

## Files Changed
tools/hooks/post-commit-reindex.sh; tools/delivery/pre_push_advisory_hook.py; tests/tools/test_post_commit_registry_regen.py (new); tests/tools/test_delivery_pre_push_advisory.py; this ticket; docs/REGISTRY.yaml; W46 monitoring shards. The branch also carries the record_review row for TCK-20261110-RETRO-READERS-SELECT-TOOL-ROWS-BY-TS (858#6769350134), 2 W46 shards.

## Completion Summary
A merge finished with `git commit` now gets docs/REGISTRY.yaml regenerated by the post-commit hook, and pre-push check E reaches a branch whose only registry-relevant change is the registry file. Known gap: clones that never ran `make install-hooks` still miss the hook; rebase and cherry-pick stay covered by CI only (both out of scope).
