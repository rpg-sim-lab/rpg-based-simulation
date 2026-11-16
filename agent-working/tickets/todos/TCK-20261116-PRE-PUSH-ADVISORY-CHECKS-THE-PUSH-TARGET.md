---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-PRE-PUSH-ADVISORY-CHECKS-THE-PUSH-TARGET
phase: open
date: 2026-11-16
tags: [ai, delivery]
---

# TCK-20261116-PRE-PUSH-ADVISORY-CHECKS-THE-PUSH-TARGET

## Title
The pre-push advisory checks the directory and branch being pushed, not the session's own directory, and fires only on real push commands.

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Filed by agent-working-planner on 2026-11-16. The finding is rpg-planner-ubuntu's. agent-working-designer verified it in the code and wrote the draft, and agent-working-planner re-checked the two code facts. Filing only: dispatch needs a separate owner go. P3, behind RPG (#715 6911759453).

What is wrong in `tools/delivery/pre_push_advisory_hook.py` at origin/main 94aa70f10:
- **Wrong directory.** `default_run_command` calls `subprocess.run(cmd, ...)` with no `cwd`, and `main()` never reads which directory the push targets. So all seven checks run against the branch checked out in the session's own directory:
  - A, commit subjects;
  - B, dirty monitoring shard;
  - C, squash-merged and finished;
  - D, CI lanes;
  - E, registry fresh;
  - F, installed post-commit hook current;
  - G, hand-edited parity-ledger shards.
- **Incident, 2026-11-16, reported by rpg-planner-ubuntu.**
  - rpg-implementer-ubuntu's session lives in the `rpg-ubuntu` worktree. It pushed `rpg-ubuntu-generator-resource-order` from the `rpg-ubuntu-generator` worktree.
  - The hook said the branch "looks squash-merged and finished". The commits it listed (6ea30c850, 65a9dcc2c) belong to `rpg-ubuntu-kgmcp-docs-archive`, the branch checked out in `rpg-ubuntu` (squash-merged as #939). Neither commit is on the pushed branch.
- **Missed and false matches.** `_GIT_PUSH_RE` (`(?:^|&&|;)\s*git\s+push\b`) matches `cd X && git push`, but not `git -C X push`, which is therefore never checked. It also matches text that isn't a command: a heredoc body containing "cd X && git push" made agent-working-designer's own `cat > file <<'E'` command print the dirty-shard advisory.
- **Explicit refspec.** In `git push origin other:other` the pushed branch is not HEAD, even when the directory is right.

The hook never blocks (it always exits 0). The harm is that the warnings lose credibility: a false "finished branch" warning teaches people to ignore it, and then a real one gets missed.

## Scope
1. Parse the push command for its target:
   - the directory, from a leading `cd <dir> &&` or from `git -C <dir>`;
   - the pushed ref, from an explicit refspec, or else that directory's current branch.
2. Run every check with `cwd` set to the target. Run the branch-sensitive checks (A, C, D, E, G, which use `HEAD` and `origin/main..HEAD`) against the pushed ref.
3. If the target can't be determined with confidence (a compound shell construct, a variable, `bash -c`), run no branch-sensitive check. Say so once, in one line. Never guess a directory.
4. Fire only on real push commands.
   - Match `git -C <dir> push` too.
   - Ignore `git push` that appears inside a heredoc body, a quoted string such as `echo "..."`, or a comment. Parse the command with `shlex` or a small tokenizer, and look only at real command positions.
   - If parsing fails, don't fire.
5. **Controls come first in the test file.** They use real fixtures: a temp repo with two worktrees, where worktree A holds a squash-merged branch and worktree B a fresh branch.
   - Positive: pushing from B while the hook's cwd is A gives no "finished branch" finding.
   - Positive: pushing A's branch from B's directory does give it.
   - Negative: an ordinary same-directory push behaves as before.
   - Also cover `cd X && git push`, `git -C X push`, an explicit refspec, an undeterminable command (skipped, with the one-line notice), and a heredoc, echo or comment that only mentions `git push` (fires nothing).

## Out of Scope
- Making the hook blocking.
- Changing what any check looks for.
- The hook registration in `.claude/settings.json`. It stays as it is, so this is not a governing edit.

## Acceptance Criteria
1. The controls pass and are the first tests in `tests/tools/test_delivery_pre_push_advisory.py`.
2. The existing tests pass unchanged.
3. A fixture reproduces the incident above. It fails before the fix and passes after.
4. The heredoc case from the Request Summary fires nothing after the fix.

## Related Tickets
- TCK-20260924-DELIVERY-PRE-PUSH-ADVISORY (origin of the hook)
- TCK-20261014-PRE-PUSH-CI-LANE-PARITY
- TCK-20261024-PRE-PUSH-WARNS-ON-A-STALE-DOCS-REGISTRY
- TCK-20261113-PRE-PUSH-CHECKS-HAND-EDITED-PARITY-LEDGER-SHARDS

## Related Docs
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/delivery/pre_push_advisory_hook.py (`default_run_command`, `main`, `_GIT_PUSH_RE`)
- tests/tools/test_delivery_pre_push_advisory.py

## Assumptions / Open Questions
- The other PreToolUse hooks that match `git push` by regex (if any) may have the same heredoc false positive. Check with a grep, and list any in the ticket. Fix them only if they are in `tools/delivery/`.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
