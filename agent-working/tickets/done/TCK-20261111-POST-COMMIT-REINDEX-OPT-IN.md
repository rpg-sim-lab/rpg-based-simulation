---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-POST-COMMIT-REINDEX-OPT-IN
phase: done
date: 2026-11-11
tags: [delivery]
---

# TCK-20261111-POST-COMMIT-REINDEX-OPT-IN

## Title
The post-commit hook regenerates the registry by default and reindexes knowledge search only when a clone opts in

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Owner decision #715 6792268915 (relayed by lead-planner): the ubuntu clone does not run
`make install-hooks` for now, because `tools/hooks/post-commit-reindex.sh` does two jobs.
- **Registry regen for merge commits** (from #865). This one is wanted.
- **Knowledge reindex.** `python3 tools/knowledge_search.py build --incremental` runs after any
  commit that touches `docs/` or `agent-working/tickets/done/`, in every checkout that has
  `agent-working/.index/knowledge-index/knowledge.db`. Eight ubuntu checkouts have one. The
  reindex loads the embedding model and OOMs on this host
  (TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED). Through the hook it runs with no memory
  cap, on whichever seat commits.

The owner asked for the split: the registry regen installable alone, with the reindex opt-in.

## Scope
- In `tools/hooks/post-commit-reindex.sh`, the reindex block runs only when the clone opts in
  with `git config --bool knowledge.reindexOnCommit` = true (per clone, shared by its
  worktrees). The registry-regen block keeps running for merge commits, as now.
- The hook prints one line when it skips a reindex the commit would have triggered, naming the
  opt-in command and `make knowledge-index-update`.
- Make the `install-hooks` help text say what the hook does by default.
- `docs/guidelines/agent_working_environment.md` ("Git hooks (opt-in)"): the default and the
  opt-in.
- Tests: run the hook script in a temp repo, with opt-in unset and set, for a docs commit and a
  merge commit.

## Out of Scope
- `codebase/hooks/install_git_hooks.py` (codebase domain). It installs the same file byte for
  byte, so it picks up the change without an edit. If its byte-identity test pins content, tell
  codebase-planner rather than editing it.
- Making the reindex itself fit in memory (the OOM ticket).
- Renaming the hook file. Its name stays because two installers and the docs cite it.

## Acceptance Criteria
1. With opt-in unset, a commit touching `docs/` runs no reindex and prints the skip line.
2. With `knowledge.reindexOnCommit=true`, the same commit runs the incremental reindex, as today.
3. A merge commit that leaves REGISTRY stale gets the regen commit, whatever the opt-in says.
4. The Makefile help and the environment guide describe the default and the opt-in.

## Related Tickets
- TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED
- TCK-20261003-PREK-GIT-HOOKS-OPT-IN

## Related Docs
- docs/guidelines/agent_working_environment.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261003-PREK-GIT-HOOKS-OPT-IN/

## Related Code Areas
- tools/hooks/post-commit-reindex.sh (unowned; agent-working takes it here)
- Makefile `install-hooks` (lead's; help-text line only, named in the PR body)
- codebase/hooks/install_git_hooks.py (read only)

## Assumptions / Open Questions
- A per-clone git config is used rather than an env var, so that every session in the clone
  behaves the same whatever its shell profile.

## Implementation Notes
`tools/hooks/post-commit-reindex.sh`: the reindex block runs only when `git config --bool knowledge.reindexOnCommit` is true (per clone, shared by its worktrees). Otherwise a commit that would have triggered it prints one skip line naming the opt-in and `make knowledge-index-update`. The registry-regen block for merge commits is untouched and unconditional. The `install-hooks` help line in the Makefile (lead's file; help text only) and `docs/guidelines/agent_working_environment.md` describe the default and the opt-in.
`codebase/hooks/install_git_hooks.py` is untouched: its byte-identity test copies the repo file and passes, and the only content pin (`test_knowledge_search.py::test_hook_script_is_executable_shell`) still finds `knowledge_search.py` and `incremental` in the file.
Planner correction recorded: the hook never runs under pytest, so the pytest address-space limit (see TCK-20261111-KNOWLEDGE-INDEX-BUILD-MEMORY-BOUNDED) does not touch it; its issue was only an uncapped 1.4-1.6 GB build on whichever seat commits.

## Test Summary
`tests/tools/test_post_commit_reindex_opt_in.py`: 9 passed, running the real hook in a temp repo with a stub `knowledge_search.py` (unset: no reindex and the skip line; true: reindex runs; false/0/no skip; a commit that triggers nothing prints no skip line; no index prints nothing; a merge commit regenerates the registry with the opt-in unset and set). With `test_post_commit_registry_regen.py`, `tests/codebase/test_code_health_install_git_hooks.py` (venv python) and the hook-content test: 36 passed.

## Files Changed
tools/hooks/post-commit-reindex.sh, Makefile (install-hooks help text), docs/guidelines/agent_working_environment.md, tests/tools/test_post_commit_reindex_opt_in.py

## Completion Summary
The post-commit hook regenerates the registry by default and reindexes knowledge search only in clones that opt in with `git config --bool knowledge.reindexOnCommit true`.
