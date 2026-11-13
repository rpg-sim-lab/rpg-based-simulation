---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261113-GITHUB-MCP-ENV-FILE-OUTSIDE-REPO
phase: done
date: 2026-11-13
tags: [mcp, security, setup]
---

# TCK-20261113-GITHUB-MCP-ENV-FILE-OUTSIDE-REPO

## Title
The GitHub MCP server reads its token from a per-user file outside the repo, so it starts from every worktree

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Filed by lead-planner (`.mcp.json` owner) on 2026-11-13, owner yes on #715 6841435871 ("File the GitHub-token ticket").

`.mcp.json` starts the `github` server as `docker run -i --rm --env-file .env ghcr.io/github/github-mcp-server`. `--env-file .env` is resolved against the session's working directory. Only the main checkout has a `.env`: on ubuntu (2026-11-13), none of the 17 worktrees under `.claude/worktrees/` has one. So every seat that launches from a worktree has never had working GitHub MCP tools (`/mcp` reports a failed reconnect), while the main-checkout session works. This was already noted in `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_AUDIT.md:557` ("absent `.env` in worktrees").

Verified on 2026-11-13: the server itself starts and authenticates from the main checkout (`docker run ... --env-file .env` fetched its token scopes). The repo-root `.env` holds one variable, `GITHUB_PERSONAL_ACCESS_TOKEN`.

Copying `.env` into every worktree would spread the token into 17 places. Instead, point the server at one per-user file outside the repo, using Claude Code's environment-variable expansion in `.mcp.json` (already used in this file: `${VISUAL_ASSETS_CHECKOUT:-}`).

## Scope
1. `.mcp.json`: the `github` server's `--env-file` argument becomes `${HOME}/.config/rpg-sim/github-mcp.env` (absolute after expansion, so it works from any worktree on any host).
2. `tests/tools/test_mcp_json_registration.py::test_github_entry_is_byte_identical_to_its_pre_archival_shape`: update the pinned shape to the new argument (rename the test if "pre-archival" no longer describes it), and add an assertion that the `--env-file` argument is not a relative path (starts with `${HOME}/` or `/`), so a relative `.env` cannot come back.
3. Docs: a short setup note where the agent working environment is described (`docs/guidelines/agent_working_environment.md`) with the owner's one-time, per-host commands:
   ```
   mkdir -p ~/.config/rpg-sim
   chmod 700 ~/.config/rpg-sim
   cp <main checkout>/.env ~/.config/rpg-sim/github-mcp.env
   chmod 600 ~/.config/rpg-sim/github-mcp.env
   ```
   and that seats reconnect with `/mcp` after the change reaches their worktree.
4. Update the two runbook lines that quote the old command: `docs/runbooks/compose-api-key.md:24` (it explains why `.env` must not hold the API key: keep that point, now true of the per-user file) and the restart-impact line in `docs/runbooks/docker-image-store-move.md` if it quotes the argument. Those runbooks are platform-owned: ask platform-planner to review the wording, or leave them as-is if they stay correct.

## Out of Scope
- Creating the per-user file on any host (the owner's step; an agent never reads or copies the token).
- Changing the token, its scopes, or the image tag.
- The other MCP servers.
- Removing the repo-root `.env` (it can stay until both hosts have the new file).

## Acceptance Criteria
1. `.mcp.json` has `"--env-file", "${HOME}/.config/rpg-sim/github-mcp.env"` for the `github` server, and nothing else in the file changes.
2. The updated test passes and fails on a relative `--env-file` (positive control by a temporary edit, reverted).
3. After the owner creates the file on ubuntu and a worktree seat syncs, `/mcp` in that seat connects to github (owner observes; recorded in the ticket).
4. No token value appears in any committed file, ticket, log or agent output.

## Related Tickets
- TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY (found that `.mcp.json` passes `.env` whole into the MCP container; kept the API key out of `.env`).

## Related Docs
- `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_AUDIT.md` (line 557)
- `docs/guidelines/agent_working_environment.md`
- `docs/runbooks/compose-api-key.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `.mcp.json`
- `tests/tools/test_mcp_json_registration.py`

## Assumptions / Open Questions
- Claude Code expands `${HOME}` in `.mcp.json` `args` (documented for `command`, `args`, `env`, `url`, `headers`; the file already relies on it for `env`). The implementer confirms on the first `/mcp` after the change; if it does not expand, use `${HOME:-}` or stop and report.
- u24desktop needs the same per-user file before its seats pick up the change; lead-planner tells lead-planner-u24.

## Implementation Notes
Routing: `.mcp.json` is lead-planner's file; the test is agent-working's (`tests/tools/**`). Implemented by agent-working-implementer, dispatched by agent-working-planner (hotfix, S4; claim #634 6841468324).

## Test Summary

`tests/tools/test_mcp_json_registration.py`: 7 passed. `test_github_entry_is_byte_identical_to_its_pre_archival_shape` is renamed `test_github_entry_shape` and pins the new argument; the new `test_github_env_file_is_not_a_relative_path` requires the `--env-file` value to start with `${HOME}/` or `/`. Positive control: with the argument temporarily set back to `.env`, both github tests failed (2 failed, 5 passed); reverted, `git diff -- .mcp.json` is the one changed argument and 7 passed. No `.env` or `github-mcp.env` was read, copied or printed (AC4).

## Files Changed

- .mcp.json (one argument)
- tests/tools/test_mcp_json_registration.py
- docs/guidelines/agent_working_environment.md (setup subsection)
- docs/runbooks/compose-api-key.md (wording reviewed by platform-planner)
- docs/runbooks/docker-image-store-move.md (the same command, one substitution)

## Completion Summary

The `github` MCP server reads its token from `${HOME}/.config/rpg-sim/github-mcp.env`, so it can start from any worktree once the owner has created that file on a host. Acceptance criterion 3 (a worktree seat's `/mcp` connects to github after the owner creates the file) is the owner's to observe and is not yet recorded here. Left unchanged on purpose: the dated audit line `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_AUDIT.md:557`.

Known gap: `${HOME}` expansion in `.mcp.json` args is confirmed only by the first `/mcp` after the file exists; if it does not expand, the ticket says to use `${HOME:-}` or stop and report.
